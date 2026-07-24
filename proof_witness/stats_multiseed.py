"""stats_multiseed.py: aggregate P1/P2/C1/C2 across training seeds.

Reads results/eval_<arm>[_s<k>].json for every seed present and reports,
per comparison: the paired Wilcoxon result within each seed, then the
across-seed mean and range. Seed 0 is the registered run.

Usage: python3 stats_multiseed.py [--metric sim_minus_echo]
"""
import argparse, glob, json, os, re, statistics as st

from scipy.stats import wilcoxon

ARMS = ["pw_trace", "pw_pair", "pw_endpoint", "pw_shuffle"]
COMPS = [("P1 trace-pair", "pw_trace", "pw_pair"),
         ("P2 pair-endpoint", "pw_pair", "pw_endpoint"),
         ("C1 trace-shuffle", "pw_trace", "pw_shuffle"),
         ("C2 shuffle-pair", "pw_shuffle", "pw_pair")]


def seeds_present():
    found = set()
    for f in glob.glob("results/eval_pw_trace*.json"):
        m = re.search(r"_s(\d+)\.json$", f)
        found.add(int(m.group(1)) if m else 0)
    return sorted(found)


def load(arm, seed):
    suf = "" if seed == 0 else f"_s{seed}"
    p = f"results/eval_{arm}{suf}.json"
    return json.load(open(p))["items"] if os.path.exists(p) else None


def val(it, metric):
    if metric == "sim_minus_echo":
        return it["sim"] - it["echo_ceiling"]
    return it[metric]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="sim_minus_echo")
    args = ap.parse_args()

    seeds = seeds_present()
    print(f"seeds found: {seeds}  metric: {args.metric}\n")

    for name, a_arm, b_arm in COMPS:
        deltas, ps = [], []
        for s in seeds:
            a, b = load(a_arm, s), load(b_arm, s)
            if a is None or b is None:
                continue
            d = [val(x, args.metric) - val(y, args.metric)
                 for x, y in zip(a, b)]
            mean = sum(d) / len(d)
            nz = [v for v in d if abs(v) > 1e-12]
            p = wilcoxon(nz)[1] if nz else 1.0
            deltas.append(mean)
            ps.append(p)
            print(f"  {name:20s} seed {s}: meanD {mean:+.4f}  p={p:.3g}")
        if len(deltas) > 1:
            print(f"  {name:20s} ACROSS {len(deltas)} seeds: "
                  f"mean {st.mean(deltas):+.4f}  "
                  f"sd {st.stdev(deltas):.4f}  "
                  f"range [{min(deltas):+.4f}, {max(deltas):+.4f}]  "
                  f"all p<0.05: {all(p < 0.05 for p in ps)}")
        elif deltas:
            print(f"  {name:20s} single seed only")
        print()


if __name__ == "__main__":
    main()
