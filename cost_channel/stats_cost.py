"""stats_cost.py: the analysis.

A1 anchor  : on `readable`, every arm >= 0.90 token accuracy.
A2 access  : on `abelian`, sc_counts beats sc_pair by >= 0.05.
C1 primary : measured (sc_cost - sc_pair) tracks the ceiling difference
             across the five non-anchor systems, Spearman > 0.
C2 access  : sc_counts - sc_cost, the decoding cost of identical
             information presented as an aggregate scalar.
C3 order   : sc_costd - sc_cost, what the order-sensitive distance term
             buys. Registered non-monotone: the ceiling says this peaks
             at q75 (+0.112) and nearly vanishes at abelian (+0.029),
             because for commuting flips on distinct bits the running
             distance to goal is order-independent.
"""
import json, os

from scipy.stats import spearmanr, wilcoxon

ORDER = ["readable", "free", "q25", "q50", "q75", "abelian"]
CEIL = json.load(open("ceilings.json"))


def load(s, a):
    p = f"results/{s}/{a}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    print(f"{'system':<10}{'ceil d':>8}{'pair':>7}{'cost':>7}{'costd':>7}"
          f"{'counts':>8}{'cost-pair':>11}{'p':>9}")
    meas, theo = [], []
    for s in ORDER:
        d = {a: load(s, a) for a in ("sc_pair", "sc_cost", "sc_costd",
                                     "sc_counts")}
        if not all(d.values()):
            continue
        gap = [x["tok_acc"] - y["tok_acc"]
               for x, y in zip(d["sc_cost"]["items"], d["sc_pair"]["items"])]
        m = sum(gap) / len(gap)
        nz = [v for v in gap if abs(v) > 1e-12]
        p = wilcoxon(nz)[1] if nz else 1.0
        print(f"{s:<10}{CEIL[s]['ceil_diff']:>8.3f}"
              f"{d['sc_pair']['tok_acc']:>7.3f}{d['sc_cost']['tok_acc']:>7.3f}"
              f"{d['sc_costd']['tok_acc']:>7.3f}"
              f"{d['sc_counts']['tok_acc']:>8.3f}{m:>+11.4f}{p:>9.2g}")
        if s != "readable":
            meas.append(m); theo.append(CEIL[s]["ceil_diff"])

    print()
    r = tuple(load("readable", a) for a in
              ("sc_pair", "sc_cost", "sc_costd", "sc_counts"))
    if all(r):
        accs = [x["tok_acc"] for x in r]
        print(f"A1 anchor (readable, all arms >= 0.90): "
              f"{'PASS' if min(accs) >= 0.90 else 'FAIL'}  {accs}")
    ab = load("abelian", "sc_counts"), load("abelian", "sc_pair")
    if all(ab):
        d = ab[0]["tok_acc"] - ab[1]["tok_acc"]
        print(f"A2 access (abelian, counts-pair >= 0.05): "
              f"{'PASS' if d >= 0.05 else 'FAIL'}  {d:+.4f}")
    if len(meas) >= 4:
        rho = spearmanr(theo, meas).correlation
        print(f"C1 primary (spearman measured vs ceiling diff > 0): "
              f"{'PASS' if rho > 0 else 'FAIL'}  rho={rho:+.2f}")
    print("\nC2 decoding cost (counts - cost), identical information:")
    for s in ORDER:
        a, b = load(s, "sc_counts"), load(s, "sc_cost")
        if a and b:
            print(f"  {s:<10}{a['tok_acc'] - b['tok_acc']:+.4f}")
    print("\nC3 order information (costd - cost) vs its ceiling:")
    for s in ORDER:
        a, b = load(s, "sc_costd"), load(s, "sc_cost")
        if a and b:
            theo = CEIL[s]["ceil_diff_d"] - CEIL[s]["ceil_diff"]
            print(f"  {s:<10}measured {a['tok_acc'] - b['tok_acc']:+.4f}"
                  f"   ceiling {theo:+.4f}")


if __name__ == "__main__":
    main()
