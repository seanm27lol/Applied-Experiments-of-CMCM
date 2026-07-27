"""variance.py: the within-fiber cost variance of Section 7.5, exactly
recomputed, per operation system.

Setup (as in identifiability.py): fixed start state; a path visits
states s_1..s_L; a linear cost w . phi(s_t) accrues per visited state,
phi = the 28 bit indicators. Total cost C = w . F(path) where F = sum
of phi over visited states. Fibers = groups of paths sharing an end
state.

An endpoint learner sees (start, end, C) and can at best predict
E[C | end]; its irreducible noise is the within-fiber variance of the
cost. Conventions (chosen to reproduce the registered values 0.0004 /
0.1395 / 0.2792 / 0.3978 / 0.5534 for free/q25/q50/q75/abelian, and
matching all five to the quoted precision):

* cost vector w: averaged over the unit sphere. E[ww^T] = I/28 gives
  E_w[Var(w.F | g)] = tr(Cov(F | g)) / 28, so the average is evaluated
  exactly as the trace of the within-fiber covariance divided by 28 --
  no Monte Carlo over w.
* within-fiber variance: the unbiased (ddof=1) sample variance per
  fiber, s_g^2 = SS_g / (c_g - 1); singleton fibers contribute zero.
  (This is the residual variance a finite-sample learner estimates;
  ddof=0 gives 0.0002 / 0.1222 / 0.2624 / 0.3899 / 0.5531 instead.)
* averaging over fibers: weighted by fiber size c_g, i.e. witnesses are
  drawn uniformly, so the number is the within-fiber variance faced by
  a uniformly random path:

    V = (1/28) * (1/8^L) * sum_g c_g * tr(SS_g) / (c_g - 1)

Sanity anchors: readable has fiber exactly 1, hence V = 0; free has
only 46 colliding path pairs, hence V is tiny but nonzero.
"""
import numpy as np

import fiber as F

L = 6
START = 0x0BADC0DE & F.MASK
BITS = np.arange(F.NBITS)

# registered in REGISTERED_NEGATIVE.md (lines 27-29); readable is not
# quoted there because its fibers are singletons and the variance is 0
REGISTERED = {"free": 0.0004, "q25": 0.1395, "q50": 0.2792,
              "q75": 0.3978, "abelian": 0.5534}


def vec_ops(name):
    """Vectorized (numpy array -> numpy array) equivalents of
    fiber.build_opset(name); semantics verified against the scalar
    originals in check()."""
    def push(i):
        return lambda s: ((s << 4) | i) & F.MASK

    def flip(i):
        return lambda s: s ^ (1 << i)

    def affine(a, b):
        return lambda s: (a * s + b) & F.MASK

    def rotxor(k, m):
        def f(s):
            return (((s << k) | (s >> (F.NBITS - k))) & F.MASK) ^ m
        return f

    free = [affine(0x9E3779B1, 0x7F4A7C15), affine(0x85EBCA6B, 0xC2B2AE35),
            rotxor(7, 0x5BD1E995), rotxor(13, 0x1B873593),
            affine(0xCC9E2D51, 0x27D4EB2F), rotxor(5, 0x165667B1),
            affine(0x2545F491, 0x9E3779B9), rotxor(11, 0x94D049BB)]
    if name == "readable":
        return [push(i) for i in range(8)]
    n_comm = {"free": 0, "q25": 2, "q50": 4, "q75": 6, "abelian": 8}[name]
    return [flip(i) for i in range(n_comm)] + free[: 8 - n_comm]


def check(name):
    """The vectorized ops must agree with fiber.build_opset, and the
    vectorized feature accumulation with the per-path loop of
    identifiability.py."""
    ref = [f for f, _ in F.build_opset(name)]
    mine = vec_ops(name)
    rng = np.random.default_rng(0)
    for x in rng.integers(0, F.MASK + 1, size=64):
        for fr, fm in zip(ref, mine):
            assert fr(int(x)) == int(fm(np.array([x], dtype=np.int64))[0])
    states, feats = enumerate_paths(name)
    fns = ref
    rng = np.random.default_rng(1)
    for _ in range(32):
        seq = tuple(rng.integers(0, len(fns), size=L))
        # blocking makes the first applied op the fastest-varying index
        row = np.ravel_multi_index(seq[::-1], (len(fns),) * L)
        s, feat = START, np.zeros(F.NBITS)
        for k in seq:
            s = fns[k](s)
            feat += (s >> BITS) & 1
        assert states[row] == s and np.array_equal(feats[row], feat)


def enumerate_paths(name):
    """All 8^L length-L paths: end states and summed feature vectors.
    Same recursion as identifiability.py, vectorized over paths."""
    ops = vec_ops(name)
    states = np.array([START], dtype=np.int64)
    feats = np.zeros((1, F.NBITS))
    for _ in range(L):
        states = np.concatenate([op(states) for op in ops])
        phi = ((states[:, None] >> BITS) & 1).astype(np.float64)
        feats = np.tile(feats, (len(ops), 1)) + phi
    return states, feats


def within_fiber_variance(name):
    states, feats = enumerate_paths(name)
    _, inv = np.unique(states, return_inverse=True)
    counts = np.bincount(inv).astype(np.float64)
    g = len(counts)
    sum_f = np.zeros((g, F.NBITS))
    sum_f2 = np.zeros((g, F.NBITS))
    np.add.at(sum_f, inv, feats)
    np.add.at(sum_f2, inv, feats ** 2)
    ss = sum_f2 - sum_f ** 2 / counts[:, None]      # within-fiber SS per dim
    multi = counts > 1                              # singletons: no variance
    v = (counts[multi] * ss[multi].sum(axis=1)
         / (counts[multi] - 1)).sum()               # ddof=1, size-weighted
    return v / (F.NBITS * inv.size)


if __name__ == "__main__":
    print(f"{'opset':<10}{'within-fiber cost var':>23}{'registered':>12}")
    for name in ("readable", "free", "q25", "q50", "q75", "abelian"):
        check(name)
        v = within_fiber_variance(name)
        reg = f"{REGISTERED[name]:.4f}" if name in REGISTERED else "-"
        print(f"{name:<10}{v:>23.4f}{reg:>12}")
