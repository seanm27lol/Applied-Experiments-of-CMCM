"""eval_arms.py (v2): decisive evaluation for the edit-witness experiment.

Drop-in replacement (same CLI as v1; modal_witness.py needs no changes).
What v2 adds, per test item, for all n items:
  sim           character similarity of generation vs gold diff (v1 metric)
  sim_edit      similarity computed on +/- EDIT LINES ONLY (context earns 0)
  echo_ceiling  sim(before-window, gold diff): what pure context-echo scores
  gen_pm / gold_pm   count of +/- lines in generation / gold
  applies       lenient check: the generation's implied pre-image lines
                occur contiguously in the before-window
  sim_applied   similarity of the generation's implied AFTER-window vs the
                gold after-window (semantic-ish, echo-resistant)
All generations are saved. Aggregates include paired deltas vs echo ceiling.
"""

import argparse, difflib, json, math

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def norm(s):
    return "\n".join(" ".join(l.split()) for l in s.strip().splitlines())


def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def pm_lines(text):
    out = []
    for l in text.splitlines():
        if (l.startswith("+") or l.startswith("-")) and \
                not l.startswith(("+++", "---")):
            out.append(" ".join(l[1:].split()))
    return "\n".join(out)


def parse_hunk(text):
    """Lenient unified-diff read: returns (pre_image_lines, post_image_lines)
    from context/minus/plus lines, ignoring headers and malformed lines."""
    pre, post = [], []
    for l in text.splitlines():
        if l.startswith(("+++", "---", "@@")) or not l:
            continue
        body = " ".join(l[1:].split())
        if l.startswith(" "):
            pre.append(body); post.append(body)
        elif l.startswith("-"):
            pre.append(body)
        elif l.startswith("+"):
            post.append(body)
    return pre, post


def contiguous_in(needle, hay):
    if not needle:
        return False
    n, h = len(needle), len(hay)
    return any(hay[i:i + n] == needle for i in range(h - n + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--test-frac", type=float, default=0.05)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = (torch.bfloat16 if device == "cuda"
             and torch.cuda.is_bf16_supported() else torch.float32)
    tok = AutoTokenizer.from_pretrained(args.ckpt)
    base = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=dtype)
    model = PeftModel.from_pretrained(base, args.ckpt).to(device).eval()

    recs = [json.loads(l) for l in open(args.data)]
    cut = int(len(recs) * (1 - args.test_frac))
    test = recs[cut:][: args.n]

    items, losses = [], []
    with torch.no_grad():
        for i, r in enumerate(test):
            prompt = f"### BEFORE\n{r['before']}\n### DIFF\n"
            ids = tok(prompt, return_tensors="pt", truncation=True,
                      max_length=1536).input_ids.to(device)
            gen = model.generate(ids, max_new_tokens=args.max_new,
                                 do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            out = tok.decode(gen[0][ids.shape[1]:],
                             skip_special_tokens=True).split("<END>")[0]

            g, gold = norm(out), norm(r["diff"])
            before_n = [" ".join(l.split())
                        for l in r["before"].splitlines() if l.strip()]
            pre, post = parse_hunk(out)
            gold_after_n = norm(r["after"])
            items.append(dict(
                i=i,
                sim=round(ratio(g, gold), 4),
                sim_edit=round(ratio(pm_lines(out), pm_lines(r["diff"])), 4),
                echo_ceiling=round(ratio(norm(r["before"]), gold), 4),
                gen_pm=len(pm_lines(out).splitlines()) if pm_lines(out) else 0,
                gold_pm=len(pm_lines(r["diff"]).splitlines()),
                applies=contiguous_in(pre, before_n),
                sim_applied=round(ratio("\n".join(post), gold_after_n), 4)
                            if post else 0.0,
                generated=out,
            ))
            aft = tok(r["after"], return_tensors="pt", truncation=True,
                      max_length=1024).input_ids.to(device)
            if aft.shape[1] > 1:
                losses.append(model(input_ids=aft, labels=aft).loss.item())

    n = len(items)
    mean = lambda k: round(sum(it[k] for it in items) / n, 4)
    mean_loss = sum(losses) / max(1, len(losses))
    report = dict(
        ckpt=args.ckpt, n=n, version=2,
        diff_exact_match=round(sum(
            it["sim"] == 1.0 for it in items) / n, 4),
        diff_similarity_mean=mean("sim"),
        edit_line_sim_mean=mean("sim_edit"),
        echo_ceiling_mean=mean("echo_ceiling"),
        sim_minus_echo_mean=round(sum(
            it["sim"] - it["echo_ceiling"] for it in items) / n, 4),
        applies_rate=round(sum(it["applies"] for it in items) / n, 4),
        applied_after_sim_mean=mean("sim_applied"),
        after_window_loss=round(mean_loss, 4),
        after_window_ppl=round(math.exp(min(mean_loss, 20)), 2),
        items=items,
    )
    json.dump(report, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "items"},
                     indent=1))


if __name__ == "__main__":
    main()
