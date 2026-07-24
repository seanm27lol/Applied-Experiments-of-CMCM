"""prep_data.py: build the three stage-1 corpora and the eval set.

Splits by theorem full_name (no step from an eval theorem appears in any
training corpus). Matches total character budget across arms, since the
arms' documents have different natural lengths.

Usage: python3 prep_data.py [--n_steps 60000] [--n_eval 300] [--budget 30000000]
Writes: data/{pw_trace,pw_pair,pw_endpoint}_train.jsonl, data/eval.jsonl
"""
import argparse, re, hashlib, json, os, random

from datasets import load_dataset

B, T, A, E = "<|STATE_BEFORE|>", "<|TACTIC|>", "<|STATE_AFTER|>", "<|END|>"
MAX_STATE = 1200  # chars per state; keep the tail (the goal line is last)


def detag(s):
    return re.sub(r"</?a>", "", s or "")


def clip(s):
    s = (s or "").strip()
    return s[-MAX_STATE:] if len(s) > MAX_STATE else s


def doc(ex, arm, wrong_tactic=None):
    b, t, a = clip(ex["state"]), detag(ex["tactic"]).strip(), clip(ex["target_state"])
    if arm == "pw_trace":
        return f"{B}\n{b}\n{T}\n{t}\n{A}\n{a}\n{E}\n"
    if arm == "pw_shuffle":
        return f"{B}\n{b}\n{T}\n{wrong_tactic}\n{A}\n{a}\n{E}\n"
    if arm == "pw_pair":
        return f"{B}\n{b}\n{A}\n{a}\n{E}\n"
    return f"{A}\n{a}\n{E}\n"  # pw_endpoint


def eval_hold(name, frac=0.05):
    return int(hashlib.sha256(name.encode()).hexdigest(), 16) % 10000 < frac * 10000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cat-searcher/leandojo-benchmark-4-random")
    ap.add_argument("--n_steps", type=int, default=60000)
    ap.add_argument("--n_eval", type=int, default=300)
    ap.add_argument("--budget", type=int, default=30_000_000)  # chars per arm
    args = ap.parse_args()
    os.makedirs("data", exist_ok=True)
    rng = random.Random(0)

    train_pool, eval_pool = [], []
    for ex in load_dataset(args.dataset, split="train", streaming=True):
        if not ex["tactic"] or not ex["state"] or not ex["target_state"]:
            continue
        if len(detag(ex["tactic"])) > 300:  # drop giant term-mode blobs
            continue
        (eval_pool if eval_hold(ex["full_name"]) else train_pool).append(
            {k: ex[k] for k in ("full_name", "state", "tactic", "target_state")})
        if len(train_pool) >= args.n_steps and len(eval_pool) >= args.n_eval * 3:
            break
    rng.shuffle(train_pool)
    rng.shuffle(eval_pool)

    # derangement of tactics for the shuffle control: every step gets a
    # real tactic from a DIFFERENT step (format exposure, no valid witness)
    tactics = [detag(ex["tactic"]).strip() for ex in train_pool]
    shifted = tactics[1:] + tactics[:1]
    wrong = {id(ex): (shifted[i] if shifted[i] != tactics[i]
                      else tactics[(i + 2) % len(tactics)])
             for i, ex in enumerate(train_pool)}

    for arm in ("pw_trace", "pw_pair", "pw_endpoint", "pw_shuffle"):
        used, n = 0, 0
        with open(f"data/{arm}_train.jsonl", "w") as f:
            for ex in train_pool:
                d = doc(ex, arm, wrong.get(id(ex)))
                if used + len(d) > args.budget:
                    break
                f.write(json.dumps({"text": d}) + "\n")
                used += len(d)
                n += 1
            # endpoint docs are short; recycle to spend the same budget
            while used < args.budget * 0.98 and arm == "pw_endpoint":
                ex = rng.choice(train_pool)
                d = doc(ex, arm)
                f.write(json.dumps({"text": d}) + "\n")
                used += len(d)
                n += 1
        print(f"{arm}: {n} docs, {used/1e6:.1f}M chars")

    # shared stage-2 pool: same finetune examples for every arm, from
    # training theorems only (never eval theorems)
    with open("data/stage2_pool.jsonl", "w") as f:
        for ex in train_pool[: max(4000, args.n_steps // 10)]:
            f.write(json.dumps(ex) + "\n")

    with open("data/eval.jsonl", "w") as f:
        for ex in eval_pool[: args.n_eval]:
            f.write(json.dumps(ex) + "\n")
    print(f"eval: {min(len(eval_pool), args.n_eval)} held-out steps "
          f"({len({e['full_name'] for e in eval_pool[:args.n_eval]})} theorems)")


if __name__ == "__main__":
    main()
