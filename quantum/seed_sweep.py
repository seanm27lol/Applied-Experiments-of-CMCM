"""seed_sweep.py: registered follow-up #1 — transpile-seed sweep on
mod_mult_55 (routing skill vs seed luck).

Phase 1 (local, free): transpile both arms with seeds 0..19 against the
FakeFez snapshot, report the 2q/depth distribution, and flag whether
seed 7's optimized-arm blowup (42 logical -> 117 physical) is typical
or an outlier.

Phase 2 (hardware, run manually): take the best seed per arm printed at
the end, rerun with qhw_local.py --mode hw after setting seed_transpiler
accordingly. Compare the delta against the seed-7 delta (+0.067).

Usage: python3 seed_sweep.py [--pair mod_mult_55] [--seeds 20]
"""
import argparse, os, statistics as st

from qiskit import qasm2, transpile
from qiskit_ibm_runtime.fake_provider import FakeFez

HERE = os.path.dirname(os.path.abspath(__file__))
QHW = os.environ.get("QHW_DIR", os.path.join(HERE, "..", "quantum", "qhw_package"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="mod_mult_55")
    ap.add_argument("--seeds", type=int, default=20)
    args = ap.parse_args()

    bk = FakeFez()
    for arm in ("baseline", "optimized"):
        qc = qasm2.load(os.path.join(QHW, f"{args.pair}_{arm}.qasm"))
        qc.measure_all()
        rows = []
        for s in range(args.seeds):
            t = transpile(qc, bk, optimization_level=1, seed_transpiler=s)
            ops = t.count_ops()
            n2 = sum(v for k, v in ops.items() if k in ("cx", "cz", "ecr"))
            rows.append((s, n2, t.depth()))
        n2s = [r[1] for r in rows]
        best = min(rows, key=lambda r: (r[1], r[2]))
        s7 = next((r for r in rows if r[0] == 7), None)
        print(f"\n{args.pair} / {arm}:")
        print(f"  2q count over {args.seeds} seeds: "
              f"min {min(n2s)}, median {st.median(n2s)}, max {max(n2s)}")
        print(f"  seed 7 (the registered run): 2q={s7[1]}, depth={s7[2]}")
        print(f"  best seed: {best[0]} (2q={best[1]}, depth={best[2]})")
        if s7[1] > st.median(n2s):
            print("  -> seed 7 routed WORSE than median: blowup partly seed luck")
        else:
            print("  -> seed 7 at/below median: blowup is intrinsic to routing")

if __name__ == "__main__":
    main()
