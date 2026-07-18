"""modal_witness.py: Modal orchestration for the edit-witness experiment.

Prereqs: `pip install modal`, a configured Modal token (already attached),
and this file sitting NEXT TO mine_mathlib_diffs.py, train_arms.py, and
eval_arms.py from the kit. The science, predictions, and interpretation
rules live in RUNBOOK_FOR_GPU_CLAUDE.md; this file only changes WHERE
things run. State persists on the Modal volume `witness-vol`.

Run order:
    modal run modal_witness.py --phase smoke
    modal run --detach modal_witness.py --phase stage1
    modal run --detach modal_witness.py --phase stage2
    modal run modal_witness.py --phase eval
Pull results:
    modal volume get witness-vol results ./results
    modal volume get witness-vol witness_results.tar.gz .
"""

import subprocess

import modal

app = modal.App("witness-experiment")
vol = modal.Volume.from_name("witness-vol", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install("torch", "transformers", "peft")
    .add_local_file("mine_mathlib_diffs.py", "/root/mine_mathlib_diffs.py")
    .add_local_file("train_arms.py", "/root/train_arms.py")
    .add_local_file("eval_arms.py", "/root/eval_arms.py")
)
# Older modal clients without Image.add_local_file: use
#   mounts=[modal.Mount.from_local_file("train_arms.py", "/root/train_arms.py"), ...]
# on each function instead, and delete the three add_local_file lines.

V = "/vol"
GPU = "T4"  # change to "A10G" or "L4" here if credits allow; T4 suffices
MODEL = "EleutherAI/pythia-410m"
SMOKE_MODEL = "EleutherAI/pythia-160m"
ARMS = ["diff", "after", "endpoint"]


def sh(*cmd):
    subprocess.run(list(cmd), check=True)


def _env():
    import os
    os.environ["HF_HOME"] = f"{V}/hf"
    os.makedirs(f"{V}/results", exist_ok=True)


@app.function(image=image, volumes={V: vol}, timeout=3600)
def setup_and_mine(depth: int = 20000):
    import os
    _env()
    if not os.path.exists(f"{V}/ml4"):
        sh("git", "clone", "--depth", str(depth), "--single-branch",
           "https://github.com/leanprover-community/mathlib4.git", f"{V}/ml4")
    if os.path.exists(f"{V}/edits.jsonl"):
        n = sum(1 for _ in open(f"{V}/edits.jsonl"))
        if n > 1000:
            print(f"edits.jsonl exists with {n} records; skipping re-mine")
            return n
    sh("python3", "/root/mine_mathlib_diffs.py",
       "--repo", f"{V}/ml4", "--out", f"{V}/edits.jsonl")
    vol.commit()
    n = sum(1 for _ in open(f"{V}/edits.jsonl"))
    print(f"mined records: {n}")
    if n < 2000:
        print("WARNING: under 2000 records; consider re-running with "
              "--depth 40000 (see runbook Phase 2).")
    return n


@app.function(image=image, gpu=GPU, volumes={V: vol}, timeout=4 * 3600)
def train(arm: str, model: str, target_tokens: int, out: str,
          init: str = "", seed: int = 0):
    _env()
    cmd = ["python3", "/root/train_arms.py",
           "--data", f"{V}/edits.jsonl", "--arm", arm, "--model", model,
           "--target-tokens", str(target_tokens),
           "--out", f"{V}/results/{out}", "--seed", str(seed)]
    if init:
        cmd += ["--init", f"{V}/results/{init}"]
    sh(*cmd)
    vol.commit()
    return out


@app.function(image=image, gpu=GPU, volumes={V: vol}, timeout=3600)
def evaluate(ckpt: str, base: str, n: int = 300):
    import json
    _env()
    outp = f"{V}/results/eval_{ckpt}.json"
    sh("python3", "/root/eval_arms.py",
       "--data", f"{V}/edits.jsonl", "--ckpt", f"{V}/results/{ckpt}",
       "--base", base, "--n", str(n), "--out", outp)
    vol.commit()
    r = json.load(open(outp))
    return {k: v for k, v in r.items() if k != "samples"}


@app.function(image=image, volumes={V: vol}, timeout=600)
def report():
    import glob, json
    _env()
    rows = []
    for p in sorted(glob.glob(f"{V}/results/eval_*.json")):
        r = json.load(open(p))
        rows.append((r["ckpt"].split("/")[-1], r["diff_exact_match"],
                     r["diff_similarity_mean"], r["after_window_ppl"]))
    print(f"{'ckpt':<16}{'EM':>8}{'sim':>8}{'ppl':>10}")
    for c, em, s, pp in rows:
        print(f"{c:<16}{em:>8}{s:>8}{pp:>10}")
    sh("tar", "czf", f"{V}/witness_results.tar.gz", "-C", V, "results")
    vol.commit()
    return rows


@app.local_entrypoint()
def main(phase: str = "smoke", seed: int = 0):
    if phase in ("smoke", "all"):
        print("records:", setup_and_mine.remote())
        calls = [train.spawn(arm=a, model=SMOKE_MODEL,
                             target_tokens=2_000_000,
                             out=f"smoke_{a}", seed=seed) for a in ARMS]
        for c in calls:
            print("smoke arm done:", c.get())
        print(evaluate.remote(ckpt="smoke_diff", base=SMOKE_MODEL, n=50))

    if phase in ("stage1", "all"):
        print("records:", setup_and_mine.remote())
        calls = [train.spawn(arm=a, model=MODEL,
                             target_tokens=20_000_000,
                             out=f"ck_{a}", seed=seed) for a in ARMS]
        for c in calls:
            print("stage1 arm done:", c.get())

    if phase in ("stage2", "all"):
        calls = [train.spawn(arm="diff", model=MODEL,
                             target_tokens=1_000_000,
                             out=f"ad_{a}", init=f"ck_{a}",
                             seed=seed) for a in ARMS]
        for c in calls:
            print("stage2 adapt done:", c.get())

    if phase in ("eval", "all"):
        for ck in ["ck_diff", "ck_after", "ck_endpoint",
                   "ad_diff", "ad_after", "ad_endpoint"]:
            print(evaluate.remote(ckpt=ck, base=MODEL))
        report.remote()
