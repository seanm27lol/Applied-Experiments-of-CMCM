"""ols_sample_complexity.py: samples-to-fixed-excess-risk for an OLS
endpoint learner, per operation system. Committed reconstruction of the
uncommitted simulation reported in REGISTERED_NEGATIVE.md (addendum,
lines 34-44): n/variance ratios 1014/680/716/185 and
n*eps/(variance*rank) = 1.81/1.21/1.28/1.03 across q25/q50/q75/abelian.

Setup (as in identifiability.py / variance.py): all 8^6 = 262,144
length-6 paths from the fixed start are enumerated exactly
(variance.enumerate_paths, vectorized). A path's feature vector F is the
sum of the 28 bit indicators of visited states; the endpoint learner's
best possible features are the fiber-mean vectors Fbar = E[F | fiber(end)].
The effective rank is rank of the fiber-mean matrix (28/28/28/9), and the
label noise is the within-fiber cost variance V of variance.py
(ddof=1, size-weighted, trace/28: 0.1395/0.2792/0.3978/0.5534, matching
the registered values exactly).

Conventions (chosen from a documented scan over weight scale, label
noise model, and crossing statistic; the two surviving arms are printed
by __main__):

* training set: n paths drawn uniformly WITH REPLACEMENT from the 8^6
  enumeration; the learner sees (Fbar(end), label).
* fit: ordinary least squares, minimum-norm (ridge -> 0) via the
  eigendecomposition of the Gram matrix.
* excess risk: exact E[(w_hat . Fbar - w . Fbar)^2] over the endpoint
  distribution (fibers weighted by size, i.e. induced by uniform paths):
  risk = (w_hat - w)^T Sigma (w_hat - w), Sigma = E[Fbar Fbar^T].
* threshold: smallest grid n where the REP-AVERAGED risk <= eps = 0.05
  (absolute). The per-rep first-crossing mean is printed for contrast.
* Arm A (primary, closest match): labels y = w.Fbar + eps_i with i.i.d.
  Gaussian noise of variance V (the registered within-fiber variance;
  "the within-fiber cost variances ... are the label noise"). At fixed
  noise level the risk law is independent of the cost direction w, so w
  is taken unit-norm and only the noise is simulated (w_hat - w directly).
* Arm B (literal alternative): labels are the realized costs C = w.F(path)
  with w = all-ones, i.e. heteroscedastic within-fiber noise. With
  ||w|| = sqrt(28) the crossing moves to n ~ 10^3-10^4 where finite-n
  effects vanish; the ratios come out near the asymptotic law and
  UNDERshoot the registered constants (1.07/0.93/0.77/1.04 here), so
  Arm A is the reconstruction reported.

Outcome (REPS = 400, seed = 20260726): Arm A gives
n/variance = 789/663/654/199 and n*eps/(variance*rank) =
1.41/1.18/1.17/1.10 against the registered 1014/680/716/185 and
1.81/1.21/1.28/1.03 -- q50, q75 and abelian agree within about 9%;
q25 (smallest variance, hence smallest n and strongest finite-n
inflation) comes out about 22% low under every convention tried, so the
registered 1.81 for q25 is the least-well-reproduced number.

Why the inversion: abelian's fiber-mean features span only 9 of 28
dimensions, so its excess risk falls as ~9*sigma^2/n instead of
~28*sigma^2/n; despite the HIGHEST variance it needs the FEWEST samples,
and n/variance is by far the lowest. Both arms reproduce that direction.
"""
import time

import numpy as np

import fiber as F
import variance as V

L = 6
START = 0x0BADC0DE & F.MASK
NBITS = F.NBITS
NSEQ = 8 ** L
EPS = 0.05
REPS = 400
SEED = 20260726

OPSETS = ("q25", "q50", "q75", "abelian")
REG_NV = {"q25": 1014, "q50": 680, "q75": 716, "abelian": 185}
REG_C = {"q25": 1.81, "q50": 1.21, "q75": 1.28, "abelian": 1.03}


def endpoint_data(name):
    """Exact enumeration -> (inv, Fbar, Sigma, rank, variance, C_ones)."""
    states, feats = V.enumerate_paths(name)
    _, inv, counts = np.unique(states, return_inverse=True,
                               return_counts=True)
    M = len(counts)
    p = counts / counts.sum()
    Fbar = np.zeros((M, NBITS))
    np.add.at(Fbar, inv, feats)
    Fbar /= counts[:, None]
    rank = int(np.linalg.matrix_rank(Fbar, tol=1e-8))
    Sigma = Fbar.T @ (p[:, None] * Fbar)
    var = V.within_fiber_variance(name)
    C_ones = feats @ np.ones(NBITS)
    # Arm B's own label noise: size-weighted within-fiber variance of the
    # all-ones cost (ddof=0, the noise the simulation actually realizes)
    meanC = np.bincount(inv, weights=C_ones, minlength=M) / counts
    var_ones = float(np.mean((C_ones - meanC[inv]) ** 2))
    return inv, Fbar, Sigma, rank, var, C_ones, var_ones


def batched_pinv_solve(G, b, rcond=1e-10):
    """Minimum-norm (ridge->0) OLS solutions for a batch of R systems."""
    evals, evecs = np.linalg.eigh(G)                 # (R,d), (R,d,d)
    cutoff = rcond * np.maximum(evals[:, -1:], 1e-300)
    inv_ev = np.where(evals > cutoff, 1.0 / np.maximum(evals, 1e-300), 0.0)
    vt_b = np.einsum("rji,rj->ri", evecs, b)         # V^T b per system
    return np.einsum("rij,rj->ri", evecs, inv_ev * vt_b)


def risk_curves(inv, Fbar, Sigma, labels, target, noise_std, n_grid,
                reps, seed):
    """Excess-risk curves: draw reps training sets (prefix-reused along
    the grid), fit OLS at every grid size, return (reps, len(n_grid)).
    labels=None means Arm A: y = i.i.d. noise of the given std and
    target = 0, so w_hat - w = w_hat; otherwise y = labels[sel] and
    target = the true cost vector (Arm B)."""
    rng = np.random.default_rng(seed)
    n_max = n_grid[-1]
    R, d = reps, Fbar.shape[1]
    sel = rng.integers(0, NSEQ, size=(R, n_max))
    fib = inv[sel]                                   # (R, n_max)
    if labels is None:                               # Arm A: pure noise
        y = noise_std * rng.standard_normal((R, n_max))
    else:                                            # Arm B: realized costs
        y = labels[sel]
    G = np.zeros((R, d, d))
    b = np.zeros((R, d))
    risks = np.zeros((R, len(n_grid)))
    prev = 0
    for j, n in enumerate(n_grid):
        if n > prev:
            Xc = Fbar[fib[:, prev:n]]                # (R, chunk, d)
            G += Xc.transpose(0, 2, 1) @ Xc
            b += np.einsum("rci,rc->ri", Xc, y[:, prev:n])
            prev = n
        diff = batched_pinv_solve(G, b) - target
        risks[:, j] = np.einsum("ri,ij,rj->r", diff, Sigma, diff)
    return risks


def crossings(risks, n_grid):
    """Mean-curve crossing and per-rep first-crossing mean."""
    mean_curve = risks.mean(axis=0)
    hit = np.nonzero(mean_curve <= EPS)[0]
    n_curve = float(n_grid[hit[0]]) if len(hit) else np.nan
    firsts = []
    for row in risks:
        hit = np.nonzero(row <= EPS)[0]
        firsts.append(n_grid[hit[0]] if len(hit) else np.nan)
    return n_curve, float(np.nanmean(firsts))


def pct(mine, reg):
    return 100.0 * (mine / reg - 1.0)


def main():
    t0 = time.time()
    print(f"endpoint OLS sample complexity: {REPS} reps, eps={EPS}, "
          f"seed={SEED}")
    hdr = (f"{'opset':<9}{'var':>8}{'rank':>6}{'n(curve)':>10}"
           f"{'n/rep-first':>12}{'n/var':>8}{'reg':>7}{'agree':>7}"
           f"{'n*eps/(var*rank)':>18}{'reg':>7}{'agree':>7}")
    for arm in ("A", "B"):
        if arm == "A":
            n_grid = np.arange(20, 801, 5)
            print(f"\n== Arm A (primary): homoscedastic label noise = "
                  f"within-fiber variance ==")
        else:
            n_grid = np.arange(100, 12001, 50)
            print(f"\n== Arm B (literal): realized costs, w = all-ones ==")
        print(hdr)
        for name in OPSETS:
            inv, Fbar, Sigma, rank, var, C_ones, var_ones = \
                endpoint_data(name)
            if arm == "A":
                risks = risk_curves(inv, Fbar, Sigma, None,
                                    np.zeros(NBITS), np.sqrt(var),
                                    n_grid, REPS, SEED)
            else:
                var = var_ones
                risks = risk_curves(inv, Fbar, Sigma, C_ones,
                                    np.ones(NBITS), None,
                                    n_grid, REPS, SEED)
            n_c, n_first = crossings(risks, n_grid)
            nv, c = n_c / var, n_c * EPS / (var * rank)
            print(f"{name:<9}{var:>8.4f}{rank:>6}{n_c:>10.1f}"
                  f"{n_first:>12.1f}{nv:>8.1f}{REG_NV[name]:>7}"
                  f"{pct(nv, REG_NV[name]):>6.1f}%"
                  f"{c:>18.3f}{REG_C[name]:>7}"
                  f"{pct(c, REG_C[name]):>6.1f}%")
    print(f"\nruntime {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
