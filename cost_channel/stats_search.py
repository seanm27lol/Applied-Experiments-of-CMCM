"""stats_search.py: verdicts for the registered search evaluation.

Reads results/<system>/search_sc_cost.json (written by search_cost.py)
and the main-run results/<system>/sc_cost.json (for the R2 floor), and
prints the four registered checks:

R1 control   : impossible rung, valid-and-cost-matching <= 0.05.
               Above that the model ignores the cost field and no other
               search result may be interpreted.
R2 feasibility: true-cost rung, valid-and-cost-matching >= the arm's
               exact-match rate from the main evaluation.
R3 primary   : minimum-cost rung, valid-and-cost-matching, reported per
               system. No threshold committed; this is the number the
               procedure produces.
R4 direction : R3 ordered abelian > q75 > q50 (more co-optimal paths
               means more distinct targets satisfy the request).

Usage: python3 stats_search.py     (after the search evaluation runs)
"""
import json, os

SYSTEMS = ["q50", "q75", "abelian"]


def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def main():
    rows = {}
    for s in SYSTEMS:
        srch = load(f"results/{s}/search_sc_cost.json")
        main_cost = load(f"results/{s}/sc_cost.json")
        if not srch:
            print(f"{s}: no search results yet "
                  f"(results/{s}/search_sc_cost.json missing)")
            continue
        rows[s] = (srch, main_cost)

    if not rows:
        return

    print(f"{'system':<10}{'items':>7}{'skipped':>9}{'true':>8}"
          f"{'median':>8}{'min':>8}{'imposs':>8}{'exact(main)':>12}")
    for s, (srch, main_cost) in rows.items():
        r = srch["rungs"]
        exact = main_cost["exact"] if main_cost else float("nan")
        print(f"{s:<10}{srch['n_items']:>7}"
              f"{srch['skipped_single_cost']:>9}"
              f"{r['true']['valid_and_cost']:>8.3f}"
              f"{r['median']['valid_and_cost']:>8.3f}"
              f"{r['min']['valid_and_cost']:>8.3f}"
              f"{r['impossible']['valid_and_cost']:>8.3f}"
              f"{exact:>12.4f}")

    imax = max(r["rungs"]["impossible"]["valid_and_cost"]
               for r, _ in rows.values())
    print(f"\nR1 control (impossible rung <= 0.05): "
          f"{'PASS' if imax <= 0.05 else 'FAIL'}  max {imax:.3f}")
    for s, (srch, main_cost) in rows.items():
        if not main_cost:
            continue
        t = srch["rungs"]["true"]["valid_and_cost"]
        ok = t >= main_cost["exact"] - 1e-9
        print(f"R2 feasibility ({s}: true rung >= main exact "
              f"{main_cost['exact']:.4f}): {'PASS' if ok else 'FAIL'}"
              f"  {t:.4f}")
    r3 = {s: srch["rungs"]["min"]["valid_and_cost"]
          for s, (srch, _) in rows.items()}
    print("R3 primary (minimum-cost rung, no threshold):")
    for s, v in r3.items():
        print(f"  {s:<10}{v:.4f}")
    if all(s in r3 for s in SYSTEMS):
        ok = r3["abelian"] > r3["q75"] > r3["q50"]
        print(f"R4 direction (abelian > q75 > q50): "
              f"{'PASS' if ok else 'FAIL'}  "
              f"{r3['abelian']:.3f} > {r3['q75']:.3f} > {r3['q50']:.3f}")


if __name__ == "__main__":
    main()
