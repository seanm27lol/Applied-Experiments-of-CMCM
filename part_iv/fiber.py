"""fiber.py: exact witness-fiber statistics for an operation set.

The fiber over an endpoint pair (s,t) at witness length L is the number of
length-L operation sequences carrying s to t. Computed by exhaustive
enumeration from a fixed start, so the numbers are exact, not estimated.

Fiber 1 means the endpoints determine the witness: the forgetful functor
from witnessed transformations to endpoint pairs is faithful there, and
trace supervision should add nothing. Larger fibers mean the witness
carries information the endpoints do not.

The state space is deliberately much larger than the number of witnesses
(2^28 states vs 8^L sequences), so collisions reflect algebraic relations
among the operations rather than pigeonhole crowding.
"""
import argparse
from collections import Counter
from itertools import product

NBITS = 28
MASK = (1 << NBITS) - 1


def op_flip(i):
    return (lambda s: s ^ (1 << i)), f"FLIP{i}"


def op_affine(a, b):
    return (lambda s: (a * s + b) & MASK), f"AFF{a}_{b}"


def op_push(i):
    """Shift the state left one nibble and write this operation's index.
    The end state then contains the last seven operations verbatim, so the
    witness is both information-theoretically determined (fiber 1) and
    computationally trivial to read off. This is the `readable` pole."""
    def f(s):
        return ((s << 4) | i) & MASK
    return f, f"PUSH{i}"


def op_rotxor(k, m):
    def f(s):
        r = ((s << k) | (s >> (NBITS - k))) & MASK
        return r ^ m
    return f, f"RX{k}_{m}"


FREE = [op_affine(0x9E3779B1, 0x7F4A7C15), op_affine(0x85EBCA6B, 0xC2B2AE35),
        op_rotxor(7, 0x5BD1E995), op_rotxor(13, 0x1B873593),
        op_affine(0xCC9E2D51, 0x27D4EB2F), op_rotxor(5, 0x165667B1),
        op_affine(0x2545F491, 0x9E3779B9), op_rotxor(11, 0x94D049BB)]


def build_opset(name):
    """Every set has exactly 8 operations on the same 28-bit state, so
    vocabulary size, witness length and task shape are matched across
    conditions. Only the algebra differs."""
    if name == "readable":
        ops = [op_push(i) for i in range(8)]
        return [(f, f"OP{i}") for i, (f, _) in enumerate(ops)]
    n_comm = {"free": 0, "q25": 2, "q50": 4, "q75": 6, "abelian": 8}[name]
    ops = [op_flip(i) for i in range(n_comm)] + FREE[: 8 - n_comm]
    # opaque uniform names: the label must not reveal which family an
    # operation belongs to, and must not distort the character budget
    return [(f, f"OP{i}") for i, (f, _) in enumerate(ops)]


def fiber_stats(name, L, start=0x0BADC0DE & MASK):
    ops = build_opset(name)
    fns = [f for f, _ in ops]
    ends = Counter()
    for seq in product(range(len(ops)), repeat=L):
        s = start
        for k in seq:
            s = fns[k](s)
        ends[s] += 1
    total = len(ops) ** L
    counts = list(ends.values())
    # a uniformly random witness lands in a fiber of size c with
    # probability c/total, so the witness-weighted mean fiber is:
    mean_fiber = sum(c * c for c in counts) / total
    import math
    return dict(opset=name, L=L, n_ops=len(ops), total_witnesses=total,
                distinct_endpoints=len(counts), mean_fiber=mean_fiber,
                max_fiber=max(counts),
                log2_mean_fiber=math.log2(mean_fiber))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=6)
    a = ap.parse_args()
    print(f"state space 2^{NBITS} = {1<<NBITS:,}   witness length L={a.L}   "
          f"8^{a.L} = {8**a.L:,} witnesses\n")
    print(f"{'opset':<10}{'commuting':>11}{'distinct ends':>15}"
          f"{'mean fiber':>12}{'log2':>8}{'max':>10}")
    for name in ("readable", "free", "q25", "q50", "q75", "abelian"):
        r = fiber_stats(name, a.L)
        n_comm = {"readable": 0, "free": 0, "q25": 2, "q50": 4,
                  "q75": 6, "abelian": 8}[name]
        print(f"{name:<10}{n_comm:>11}{r['distinct_endpoints']:>15,}"
              f"{r['mean_fiber']:>12.1f}{r['log2_mean_fiber']:>8.2f}"
              f"{r['max_fiber']:>10,}")
