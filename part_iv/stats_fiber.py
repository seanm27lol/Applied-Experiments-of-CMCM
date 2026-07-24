"""stats_fiber.py: the Part IV analysis.

Per condition: the supervision gap (trace arm minus pair arm) on token
accuracy, plus the content/format decomposition against the shuffle arm.
Across conditions: regress the gap on log2 mean fiber, which is the
prediction the whole experiment exists to test.

Usage: python3 stats_fiber.py [--seed 0]
"""
import argparse, json, math, os

from scipy.stats import wilcoxon, linregress

ORDER = ["readable", "free", "q25", "q50", "q75", "abelian"]
ARMS = ["sy_trace", "sy_pair", "sy_endpoint", "sy_shuffle"]


def load(opset, arm, seed):
    suf = "" if seed == 0 else f"_s{seed}"
    p = f"results/{opset}/eval_{arm}{suf}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rows = []
    print(f"{'opset':<10}{'log2 fib':>9}{'trace':>8}{'pair':>8}{'endpt':>8}"
          f"{'shuf':>8}{'gap':>9}{'p':>10}")
    for o in ORDER:
        d = {a: load(o, a, args.seed) for a in ARMS}
        if d["sy_trace"] is None or d["sy_pair"] is None:
            continue
        meta = json.load(open(f"data/{o}/meta.json"))
        lf = math.log2(meta["mean_fiber_exact"])
        acc = {a: (d[a]["tok_acc_mean"] if d[a] else float("nan"))
               for a in ARMS}
        pair_d = [x["tok_acc"] - y["tok_acc"]
                  for x, y in zip(d["sy_trace"]["items"],
                                  d["sy_pair"]["items"])]
        gap = sum(pair_d) / len(pair_d)
        nz = [v for v in pair_d if abs(v) > 1e-12]
        p = wilcoxon(nz)[1] if nz else 1.0
        rows.append((o, lf, gap, p, acc))
        print(f"{o:<10}{lf:>9.2f}{acc['sy_trace']:>8.3f}"
              f"{acc['sy_pair']:>8.3f}{acc['sy_endpoint']:>8.3f}"
              f"{acc['sy_shuffle']:>8.3f}{gap:>+9.4f}{p:>10.2g}")

    print("\ncontent vs format decomposition (trace-shuffle, shuffle-pair):")
    for o, lf, gap, p, acc in rows:
        if not math.isnan(acc["sy_shuffle"]):
            c1 = acc["sy_trace"] - acc["sy_shuffle"]
            c2 = acc["sy_shuffle"] - acc["sy_pair"]
            share = c1 / gap if abs(gap) > 1e-9 else float("nan")
            print(f"  {o:<10} content {c1:+.4f}  format {c2:+.4f}  "
                  f"content share {share:.0%}")

    fib_rows = [r for r in rows if r[0] != "readable"]
    if len(fib_rows) >= 3:
        x = [r[1] for r in fib_rows]
        y = [r[2] for r in fib_rows]
        reg = linregress(x, y)
        print(f"\nP4a regression, gap on log2 fiber "
              f"(excluding 'readable', which holds fiber fixed):")
        print(f"  slope {reg.slope:+.5f}   r^2 {reg.rvalue**2:.3f}   "
              f"p {reg.pvalue:.3g}   n={len(x)}")

    r = {o: (lf, gap) for o, lf, gap, _, _ in rows}
    if "readable" in r and "free" in r:
        print(f"\nP4b computation axis at fixed fiber "
              f"(both fiber 1.0):")
        print(f"  readable gap {r['readable'][1]:+.4f}   "
              f"free gap {r['free'][1]:+.4f}   "
              f"difference {r['free'][1]-r['readable'][1]:+.4f}")


if __name__ == "__main__":
    main()
