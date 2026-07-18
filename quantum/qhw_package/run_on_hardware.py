"""run_on_hardware.py: reference runner for the certified circuit pairs.

Usage (local plumbing test, no hardware needed):
    pip install qiskit qiskit-aer
    python run_on_hardware.py --pair mod5_4 --backend aer --shots 8192
    python run_on_hardware.py --pair mod5_4 --backend aer --noise 0.01

On IBM hardware (adapt to your stack; the QASM pairs are the ground
truth, this script is a reference):
    python run_on_hardware.py --pair mod5_4 --backend ibm:<device_name>

Design notes for whoever runs this:
  * Both arms are submitted IN ONE JOB (interleaved), so they share a
    calibration window. Please keep it that way.
  * The ideal distribution is computed locally from the same loaded
    circuit (Statevector), so bit-ordering is internally consistent.
  * Default transpile optimization_level=1. Level 3 may re-optimize the
    baseline and shrink the very difference under test; if you have the
    budget, run both levels and report both.
  * The two circuits in each pair were verified equal (up to global
    phase) by ZX-calculus reduction before shipping; the witness status
    is in pair_manifest.json.
"""

import argparse, json, math, sys

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

try:
    from qiskit import qasm2
    def load_qasm(p): return qasm2.load(p)
except Exception:
    def load_qasm(p): return QuantumCircuit.from_qasm_file(p)


def fidelity(p, q):
    keys = set(p) | set(q)
    return sum(math.sqrt(p.get(k, 0.0) * q.get(k, 0.0)) for k in keys) ** 2


def tvd(p, q):
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def counts_to_probs(counts):
    n = sum(counts.values())
    return {k.replace(" ", ""): v / n for k, v in counts.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, help="e.g. mod5_4")
    ap.add_argument("--backend", default="aer", help="aer | ibm:<name>")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--opt-level", type=int, default=1)
    ap.add_argument("--noise", type=float, default=0.0,
                    help="aer only: 2-qubit depolarizing rate, e.g. 0.01")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    arms = {}
    for arm in ("baseline", "optimized"):
        qc = load_qasm(f"{args.pair}_{arm}.qasm")
        ideal = Statevector.from_instruction(qc).probabilities_dict()
        m = qc.copy()
        m.measure_all()
        arms[arm] = dict(qc=m, ideal={k: float(v) for k, v in ideal.items()})

    if args.backend == "aer":
        from qiskit_aer import AerSimulator
        if args.noise > 0:
            from qiskit_aer.noise import NoiseModel, depolarizing_error
            nm = NoiseModel()
            nm.add_all_qubit_quantum_error(
                depolarizing_error(args.noise, 2), ["cx", "cz"])
            backend = AerSimulator(noise_model=nm)
        else:
            backend = AerSimulator()
        tqcs = [transpile(arms[a]["qc"], backend,
                          optimization_level=args.opt_level,
                          seed_transpiler=7)
                for a in ("baseline", "optimized")]
        result = backend.run(tqcs, shots=args.shots).result()
        counts = [result.get_counts(i) for i in range(2)]
    elif args.backend.startswith("ibm:"):
        # Reference path; adapt to your runtime version.
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        service = QiskitRuntimeService()
        backend = service.backend(args.backend.split(":", 1)[1])
        tqcs = [transpile(arms[a]["qc"], backend,
                          optimization_level=args.opt_level,
                          seed_transpiler=7)
                for a in ("baseline", "optimized")]
        job = SamplerV2(mode=backend).run(tqcs, shots=args.shots)
        res = job.result()
        counts = [r.data.meas.get_counts() for r in res]
    else:
        sys.exit(f"unknown backend {args.backend}")

    report = {"pair": args.pair, "backend": args.backend,
              "shots": args.shots, "opt_level": args.opt_level,
              "noise": args.noise, "arms": {}}
    for (arm, tqc, cts) in zip(("baseline", "optimized"), tqcs, counts):
        probs = counts_to_probs(cts)
        ideal = arms[arm]["ideal"]
        ops = tqc.count_ops()
        twoq = sum(v for k, v in ops.items() if k in ("cx", "cz", "ecr"))
        report["arms"][arm] = {
            "fidelity_vs_ideal": round(fidelity(probs, ideal), 5),
            "tvd_vs_ideal": round(tvd(probs, ideal), 5),
            "transpiled_2q": int(twoq),
            "transpiled_depth": int(tqc.depth()),
            "transpiled_ops": {k: int(v) for k, v in ops.items()},
        }
    b, o = report["arms"]["baseline"], report["arms"]["optimized"]
    report["delta_fidelity_optimized_minus_baseline"] = round(
        o["fidelity_vs_ideal"] - b["fidelity_vs_ideal"], 5)

    out = args.out or f"results_{args.pair}.json"
    json.dump(report, open(out, "w"), indent=1)
    print(json.dumps(report, indent=1))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
