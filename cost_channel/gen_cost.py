"""gen_cost.py: corpora for one system, three arms.

  sc_pair    START + END                     endpoints only
  sc_cost    START + END + COST              cost as a decimal scalar
  sc_counts  START + END + COUNTS            same information, spelled out

sc_cost and sc_counts carry IDENTICAL information (the costs are
collision-free, so the scalar determines the operation multiset). They
differ only in how much work it takes to read. That pair separates
"the information is there" from "the model can get at it", which is the
distinction that killed Part IV.

States render as 7 hex digits. Under that rendering the `readable`
system is a literal copy task: the last 6 hex digits of the end state
are the witness.

Usage: python3 gen_cost.py --system q50
"""
import argparse, json, os, random
from collections import Counter

import ops as O

S, E, C, N, W, D, DI = ("<|START|>", "<|END|>", "<|COST|>", "<|COUNTS|>",
                        "<|WITNESS|>", "<|EOD|>", "<|DIST|>")
# collision-free over all 6-draw multisets (verified): powers of 7
COSTS = [7 ** k for k in range(8)]


def cost_of(seq): return sum(COSTS[k] for k in seq)


def dist_of(seq, fns, start):
    """running distance-to-goal penalty: sum over visited states of the
    Hamming distance to the final state. Depends on the ORDER of the
    path, unlike the action-cost term."""
    s, vis = start, []
    for k in seq:
        s = fns[k](s); vis.append(s)
    end = s
    return sum(bin(v ^ end).count("1") for v in vis)
def counts_of(seq):
    c = Counter(seq)
    return " ".join(str(c.get(k, 0)) for k in range(8))


def doc(arm, a, b, seq, dist=None):
    w = " ".join(f"OP{k}" for k in seq)
    if arm == "sc_costd":
        return (f"{S}\n{a}\n{E}\n{b}\n{C}\n{cost_of(seq)}\n"
                f"{DI}\n{dist}\n{W}\n{w}\n{D}\n")
    if arm == "sc_pair":
        return f"{S}\n{a}\n{E}\n{b}\n{W}\n{w}\n{D}\n"
    if arm == "sc_cost":
        return f"{S}\n{a}\n{E}\n{b}\n{C}\n{cost_of(seq)}\n{W}\n{w}\n{D}\n"
    return f"{S}\n{a}\n{E}\n{b}\n{N}\n{counts_of(seq)}\n{W}\n{w}\n{D}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--L", type=int, default=6)
    ap.add_argument("--n", type=int, default=30000)
    ap.add_argument("--n_eval", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    fns = [f for f, _ in O.build(a.system)]
    out = os.path.join("data", a.system)
    os.makedirs(out, exist_ok=True)

    seen, rows = set(), []
    while len(rows) < a.n + a.n_eval:
        seq = tuple(rng.randrange(8) for _ in range(a.L))
        if seq in seen:
            continue
        seen.add(seq)
        s = O.START
        for k in seq:
            s = fns[k](s)
        rows.append((O.render(O.START), O.render(s), list(seq),
                     dist_of(seq, fns, O.START)))
    train, ev = rows[: a.n], rows[a.n:]

    for arm in ("sc_pair", "sc_cost", "sc_costd", "sc_counts"):
        with open(f"{out}/{arm}_train.jsonl", "w") as f:
            for st, en, seq, ds in train:
                f.write(json.dumps({"text": doc(arm, st, en, seq, ds)})
                        + "\n")
    with open(f"{out}/eval.jsonl", "w") as f:
        for st, en, seq, ds in ev:
            f.write(json.dumps(dict(start=st, end=en,
                                    witness=" ".join(f"OP{k}" for k in seq),
                                    cost=cost_of(seq), dist=ds,
                                    counts=counts_of(seq))) + "\n")
    print(f"{a.system}: {len(train)} train, {len(ev)} eval "
          f"(all witnesses distinct)")


if __name__ == "__main__":
    main()
