"""gen_synth.py: build the training corpora for one fiber condition.

Every condition uses the same state representation (28 bits), the same
vocabulary size (8 operations) and the same witness length, so task shape
is matched across conditions. Only the algebra of the operations differs,
which is what moves the fiber size.

Arms (matched character budget, mirroring Parts I and III):
  sy_trace     START + WITNESS + END      full witness
  sy_pair      START + END                endpoints only
  sy_endpoint  END                        endpoint only
  sy_shuffle   START + WRONG WITNESS + END  format exposure control

Also records the EXACT fiber size of every generated example, so the
supervision gap can be regressed against measured witness information
rather than an assumed proxy.

Usage:
  python3 gen_synth.py --opset q50 --L 6 --n 40000
Writes: data/<opset>/{arm}_train.jsonl, eval.jsonl, meta.json
"""
import argparse, json, os, random
from collections import Counter
from itertools import product

import fiber as F

S, W, E, END = "<|START|>", "<|WITNESS|>", "<|END_STATE|>", "<|EOD|>"


def state_str(x):
    return format(x, f"0{F.NBITS}b")


def wit_str(seq, names):
    return " ".join(names[k] for k in seq)


def doc(arm, s0, seq, s1, names, wrong=None):
    a, b = state_str(s0), state_str(s1)
    if arm == "sy_trace":
        return f"{S}\n{a}\n{W}\n{wit_str(seq, names)}\n{E}\n{b}\n{END}\n"
    if arm == "sy_shuffle":
        return f"{S}\n{a}\n{W}\n{wit_str(wrong, names)}\n{E}\n{b}\n{END}\n"
    if arm == "sy_pair":
        return f"{S}\n{a}\n{E}\n{b}\n{END}\n"
    return f"{E}\n{b}\n{END}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opset", required=True,
                    choices=["readable", "free", "q25", "q50",
                             "q75", "abelian"])
    ap.add_argument("--L", type=int, default=6)
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--n_eval", type=int, default=300)
    ap.add_argument("--budget", type=int, default=10_000_000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    ops = F.build_opset(args.opset)
    fns = [f for f, _ in ops]
    names = [n for _, n in ops]
    outdir = os.path.join("data", args.opset)
    os.makedirs(outdir, exist_ok=True)

    # exact fiber lookup for a fixed start: enumerate every witness once
    start = 0x0BADC0DE & F.MASK
    ends = Counter()
    for seq in product(range(len(ops)), repeat=args.L):
        s = start
        for k in seq:
            s = fns[k](s)
        ends[s] += 1
    total = len(ops) ** args.L
    mean_fiber = sum(c * c for c in ends.values()) / total

    # sample witnesses from the same fixed start, so every example's fiber
    # size is known exactly from the enumeration above
    samples = []
    for _ in range(args.n + args.n_eval * 3):
        seq = [rng.randrange(len(ops)) for _ in range(args.L)]
        s = start
        for k in seq:
            s = fns[k](s)
        samples.append((start, seq, s, ends[s]))
    rng.shuffle(samples)
    train, ev = samples[: args.n], samples[args.n: args.n + args.n_eval]

    # derangement for the shuffle control: a real witness from another example
    shifted = [t[1] for t in train[1:]] + [train[0][1]]

    for arm in ("sy_trace", "sy_pair", "sy_endpoint", "sy_shuffle"):
        used, k = 0, 0
        with open(os.path.join(outdir, f"{arm}_train.jsonl"), "w") as f:
            i = 0
            while used < args.budget * 0.98:
                s0, seq, s1, _ = train[i % len(train)]
                d = doc(arm, s0, seq, s1, names, shifted[i % len(shifted)])
                if used + len(d) > args.budget:
                    break
                f.write(json.dumps({"text": d}) + "\n")
                used += len(d)
                k += 1
                i += 1
                if i > len(train) and arm not in ("sy_endpoint",):
                    print(f"  WARNING: {arm} exhausted train data at "
                          f"{used/1e6:.1f}M of {args.budget/1e6:.1f}M budget; "
                          f"raise --n for a matched budget")
                    break
        print(f"  {arm:12s} {k:>7} docs  {used/1e6:.1f}M chars")

    with open(os.path.join(outdir, "eval.jsonl"), "w") as f:
        for s0, seq, s1, fib in ev:
            f.write(json.dumps(dict(start=state_str(s0),
                                    witness=wit_str(seq, names),
                                    end=state_str(s1), fiber=fib)) + "\n")

    meta = dict(opset=args.opset, L=args.L, n_ops=len(ops),
                op_names=names, state_bits=F.NBITS,
                total_witnesses=total, distinct_endpoints=len(ends),
                mean_fiber_exact=mean_fiber,
                mean_fiber_eval=sum(t[3] for t in ev) / len(ev),
                n_train=args.n, n_eval=len(ev), seed=args.seed)
    with open(os.path.join(outdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(f"  mean fiber (exact) {mean_fiber:.2f}   "
          f"eval mean {meta['mean_fiber_eval']:.2f}   "
          f"distinct endpoints {len(ends):,}")


if __name__ == "__main__":
    main()
