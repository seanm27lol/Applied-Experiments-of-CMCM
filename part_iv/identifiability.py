"""identifiability.py: can the cost function be recovered from endpoint
data? Exact rank computation, per operation system.

Setup: fixed start state; a path visits states s_1..s_L; a linear cost
w . phi(s_t) accrues per visited state, phi = the 28 bit indicators.
Total cost C = w . F(path) where F = sum of phi over visited states.

Trace data reveals F(path) exactly, so w is identifiable iff the F
vectors span R^28: rank of the trace matrix.

Endpoint data reveals only (end, C), and C is not a function of the
endpoint when fibers exceed 1. The best any endpoint learner can do is
E[C | end] = w . E[F | fiber(end)]. So w is identifiable only up to the
row space of the fiber-averaged matrix: rank of the pair matrix. The
deficit (28 minus that rank) is the provably unrecoverable dimension.
"""
from collections import defaultdict
from itertools import product

import numpy as np

import fiber as F

L = 6
START = 0x0BADC0DE & F.MASK


def phi(s):
    return np.array([(s >> i) & 1 for i in range(F.NBITS)], dtype=float)


def analyze(name):
    ops = F.build_opset(name)
    fns = [f for f, _ in ops]
    fiber_feats = defaultdict(list)
    trace_rows = []
    for seq in product(range(len(ops)), repeat=L):
        s, feat = START, np.zeros(F.NBITS)
        for k in seq:
            s = fns[k](s)
            feat += phi(s)
        trace_rows.append(feat)
        fiber_feats[s].append(feat)
    T = np.array(trace_rows)
    P = np.array([np.mean(v, axis=0) for v in fiber_feats.values()])
    mf = sum(len(v) ** 2 for v in fiber_feats.values()) / len(trace_rows)
    rt = np.linalg.matrix_rank(T, tol=1e-8)
    rp = np.linalg.matrix_rank(P, tol=1e-8)
    return np.log2(mf), rt, rp, F.NBITS - rp


if __name__ == "__main__":
    print(f"{'opset':<10}{'log2 fiber':>11}{'rank trace':>12}"
          f"{'rank pair':>11}{'deficit':>9}")
    for name in ("readable", "free", "q25", "q50", "q75", "abelian"):
        lf, rt, rp, d = analyze(name)
        print(f"{name:<10}{lf:>11.2f}{rt:>12}{rp:>11}{d:>9}")
