"""stats.py: paired Wilcoxon tests between arms, Part I style.
Usage: python3 stats.py   (after eval.py has run for all three arms)
Tests P1 (trace vs pair) and P2 (pair vs endpoint) from PREREGISTRATION.md.
"""
import json
from scipy.stats import wilcoxon

def items(arm): return json.load(open(f"results/eval_{arm}.json"))["items"]

tr, pa, en = items("pw_trace"), items("pw_pair"), items("pw_endpoint")
for name, a, b, pred in [("P1 pw_trace - pw_pair", tr, pa, "trace wins"),
                         ("P2 pw_pair - pw_endpoint", pa, en, "pair wins")]:
    for m in ("sim_minus_echo", "sim", "exact"):
        d = [x[m] - y[m] for x, y in zip(a, b)]
        mean = sum(d) / len(d)
        nz = [v for v in d if abs(v) > 1e-12]
        if not nz:
            print(f"{name} {m}: all ties"); continue
        _, p = wilcoxon(nz)
        w, l = sum(v > 0 for v in d), sum(v < 0 for v in d)
        print(f"{name:28s}{m:16s} meanD {mean:+.4f}  {w}-{l}  p={p:.3g}")
print("\nrecoverability (diagnostic):",
      f"{sum(x['recoverable'] for x in tr)/len(tr):.3f}")
