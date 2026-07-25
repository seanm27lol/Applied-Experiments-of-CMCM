"""ceiling.py: exact Bayes token-accuracy ceilings per condition.

At eval time both arms observe only the endpoint pair, so BOTH are capped
by the same ceiling: the endpoint-weighted mean over slots of the max
per-slot marginal within the fiber. The supervision gap is therefore
bounded by (ceiling minus the pair arm's score), at most (ceiling minus
chance). This is the arithmetic that retires the fiber-dial design: at
high fiber the bound collapses (0.065 at abelian), and at fiber 1 the
`free` condition shows both arms fail computationally despite a ceiling
of 1.0. Exact, from full enumeration of all 8^L witnesses.

Usage: python3 ceiling.py [--L 6]
"""
import argparse, math
from collections import defaultdict
from itertools import product

import fiber as F

CHANCE = 1 / 8


def ceiling(name, L, start=0x0BADC0DE & F.MASK):
    ops = F.build_opset(name)
    fns = [f for f, _ in ops]
    fibers = defaultdict(list)
    for seq in product(range(len(ops)), repeat=L):
        s = start
        for k in seq:
            s = fns[k](s)
        fibers[s].append(seq)
    total = len(ops) ** L
    c = 0.0
    for members in fibers.values():
        w = len(members) / total
        slot = 0.0
        for pos in range(L):
            counts = defaultdict(int)
            for m in members:
                counts[m[pos]] += 1
            slot += max(counts.values()) / len(members)
        c += w * (slot / L)
    mf = sum(len(m) ** 2 for m in fibers.values()) / total
    return math.log2(mf), c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=6)
    a = ap.parse_args()
    print(f"{'opset':<10}{'log2 fiber':>11}{'Bayes ceiling':>15}"
          f"{'max possible gap':>18}")
    for name in ("readable", "free", "q25", "q50", "q75", "abelian"):
        lf, c = ceiling(name, a.L)
        print(f"{name:<10}{lf:>11.2f}{c:>15.3f}{c - CHANCE:>18.3f}")
    print("\nmax possible gap = ceiling minus chance (0.125): the bound on")
    print("trace-minus-pair even with a Bayes-optimal trace arm and a")
    print("chance-level pair arm. It collapses at high fiber; and at")
    print("fiber 1 the free condition caps both arms computationally.")


if __name__ == "__main__":
    main()
