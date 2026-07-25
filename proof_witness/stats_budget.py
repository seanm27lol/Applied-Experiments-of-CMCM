"""stats_budget.py: the Part V analysis.

For each stage-2 budget N, the paired supervision gap (pw_trace minus
pw_pair) on sim_minus_echo, then a regression of the gap on log2 N.

A negative slope reaching zero says the trace advantage is a data
efficiency effect that stage-2 data can buy. A flat positive gap says
something is transferred that endpoint data cannot supply at any budget.

Usage: python3 stats_budget.py [--seed 0]
"""
import argparse, json, math, os

from scipy.stats import wilcoxon, linregress


def load(arm, n, seed):
    suf = "" if seed == 0 else f"_s{seed}"
    p = f"results/eval_{arm}_n{n}{suf}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def sme(it):
    return it["sim"] - it["echo_ceiling"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budgets", type=int, nargs="+",
                    default=[125, 250, 500, 1000, 2000, 4000])
    args = ap.parse_args()

    rows = []
    print(f"{'N':>7}{'trace':>9}{'pair':>9}{'gap':>10}{'wins':>10}{'p':>11}")
    for n in args.budgets:
        a, b = load("pw_trace", n, args.seed), load("pw_pair", n, args.seed)
        if a is None or b is None:
            continue
        d = [sme(x) - sme(y) for x, y in zip(a["items"], b["items"])]
        gap = sum(d) / len(d)
        nz = [v for v in d if abs(v) > 1e-12]
        p = wilcoxon(nz)[1] if nz else 1.0
        w, l = sum(v > 0 for v in d), sum(v < 0 for v in d)
        ta = sum(sme(x) for x in a["items"]) / len(a["items"])
        pa = sum(sme(x) for x in b["items"]) / len(b["items"])
        rows.append((n, gap, p))
        print(f"{n:>7}{ta:>9.4f}{pa:>9.4f}{gap:>+10.4f}"
              f"{f'{w}-{l}':>10}{p:>11.3g}")

    if len(rows) >= 3:
        x = [math.log2(r[0]) for r in rows]
        y = [r[1] for r in rows]
        reg = linregress(x, y)
        print(f"\nP5a regression, gap on log2(stage-2 budget):")
        print(f"  slope {reg.slope:+.5f}   r^2 {reg.rvalue**2:.3f}   "
              f"p {reg.pvalue:.3g}   n={len(x)}")
        big = [r for r in rows if r[0] == max(r2[0] for r2 in rows)][0]
        print(f"\nP5b at the largest budget N={big[0]}: "
              f"gap {big[1]:+.4f}, p={big[2]:.3g}")
        if reg.slope < 0:
            xint = -reg.intercept / reg.slope if reg.slope else float("nan")
            print(f"  extrapolated zero-crossing at N = 2^{xint:.1f} "
                  f"= {2**xint:,.0f} examples")


if __name__ == "__main__":
    main()
