"""uniqueness.py: existence-and-uniqueness of minimum-cost paths, exact.

Registered motivation for the search evaluation (PREREGISTRATION.md
addendum): the fraction of endpoint pairs whose minimum-cost path is
unique, and the mean number of co-optimal paths. Existence is trivial
(finite path set); uniqueness fails structurally in commuting systems,
because any reordering of a minimum-cost path reaches the same endpoint
at the same cost.

Exact computation over all 8^6 = 262,144 paths per system: group paths
by endpoint, take the minimum achievable cost, count how many paths
attain it. Registered values (free/q25/q50/q75/abelian):
  endpoints        262,098 / 207,107 / 111,593 / 39,510 / 127
  unique minimum   100.0%   / 90.7%   / 68.4%   / 35.2%  / 0.8%
  mean # minima    1.00     / 1.16    / 1.59    / 3.25   / 296.32
(readable is trivially 100% / 1.00: fiber 1, each endpoint has exactly
one path.)

Usage: python3 uniqueness.py            (all five systems)
"""
from collections import defaultdict
from itertools import product

import ops as O
from gen_cost import cost_of

L = 6


def analyze(name):
    fns = [f for f, _ in O.build(name)]
    best = {}
    n_min = defaultdict(int)
    for seq in product(range(8), repeat=L):
        s = O.START
        for k in seq:
            s = fns[k](s)
        c = cost_of(seq)
        if s not in best or c < best[s]:
            best[s] = c
            n_min[s] = 1
        elif c == best[s]:
            n_min[s] += 1
    n_end = len(best)
    uniq = sum(1 for v in n_min.values() if v == 1)
    mean_min = sum(n_min.values()) / n_end
    return n_end, 100.0 * uniq / n_end, mean_min


if __name__ == "__main__":
    print(f"{'system':<10}{'endpoints':>11}{'unique min':>12}"
          f"{'mean # minima':>15}")
    for name in ("free", "q25", "q50", "q75", "abelian"):
        n, u, m = analyze(name)
        print(f"{name:<10}{n:>11}{u:>11.1f}%{m:>15.2f}")
