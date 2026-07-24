"""qhw_local.py: local runner for the certified ZX circuit pairs on IBM hardware.

Direct port of modal_hardware.py, Modal layer removed. Same logic:
  loads {pair}_{baseline,optimized}.qasm from qhw_package/,
  transpiles seed_transpiler=7 opt level 1,
  aer mode: ideal (or depolarizing) sim; hw mode: one SamplerV2 job per pair,
  both arms interleaved, least-busy device. Fidelity/TVD vs ideal + 2q/depth.

Setup:
  pip install qiskit qiskit-aer qiskit-ibm-runtime
  export QISKIT_IBM_TOKEN=<token>            # hw mode only
  # optional: QISKIT_IBM_CHANNEL / QISKIT_IBM_INSTANCE

Run order:
  python3 qhw_local.py --mode aer --pair mod5_4            # smoke, ~1.0
  python3 qhw_local.py --mode aer --pair all --noise 0.01  # optional
  python3 qhw_local.py --mode hw --pair all                # live
Results: printed + saved to ./qhw_results/{aer,hw}_{pair}.json
API drift: if service init fails, replace the marked line in ibm_backend()
with the exact snippet your IBM dashboard shows.
"""

import argparse, json, math, os

SEED = 7  # overridden by --seed in main()

PAIRS = ["mod5_4", "tof_3", "barenco_tof_3", "mod_mult_55"]
HERE = os.path.dirname(os.path.abspath(__file__))
QHW = os.path.join(HERE, "qhw_package")
OUT = os.path.join(HERE, "qhw_results")


def fidelity(p, q):
    ks = set(p) | set(q)
    return sum(math.sqrt(p.get(k, 0.0) * q.get(k, 0.0)) for k in ks) ** 2


def tvd(p, q):
    ks = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in ks)


def load_arms(pair):
    from qiskit import qasm2
    from qiskit.quantum_info import Statevector
    arms = {}
    for arm in ("baseline", "optimized"):
        qc = qasm2.load(os.path.join(QHW, f"{pair}_{arm}.qasm"))
        ideal = {k: float(v) for k, v in
                 Statevector.from_instruction(qc).probabilities_dict().items()}
        m = qc.copy()
        m.measure_all()
        arms[arm] = (m, ideal)
    return arms


def score(report, arm, tqc, counts, ideal):
    tot = sum(counts.values())
    probs = {k.replace(" ", ""): v / tot for k, v in counts.items()}
    ops = tqc.count_ops()
    report["arms"][arm] = dict(
        fidelity_vs_ideal=round(fidelity(probs, ideal), 5),
        tvd_vs_ideal=round(tvd(probs, ideal), 5),
        transpiled_2q=int(sum(v for k, v in ops.items()
                              if k in ("cx", "cz", "ecr"))),
        transpiled_depth=int(tqc.depth()),
    )


def ibm_backend(device):
    from qiskit_ibm_runtime import QiskitRuntimeService
    kw = dict(token=os.environ["QISKIT_IBM_TOKEN"])
    if os.environ.get("QISKIT_IBM_CHANNEL"):
        kw["channel"] = os.environ["QISKIT_IBM_CHANNEL"]
    if os.environ.get("QISKIT_IBM_INSTANCE"):
        kw["instance"] = os.environ["QISKIT_IBM_INSTANCE"]
    # API-drift spot: if this init fails, replace the line below with the
    # exact snippet shown on your IBM Quantum dashboard.
    service = QiskitRuntimeService(**kw)
    if device:
        return service.backend(device)
    return service.least_busy(operational=True, simulator=False)


def run_pair_hw(pair, device="", shots=8192, opt_level=1):
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2
    arms = load_arms(pair)
    backend = ibm_backend(device)
    tqcs = [transpile(arms[a][0], backend, optimization_level=opt_level,
                      seed_transpiler=SEED) for a in ("baseline", "optimized")]
    job = SamplerV2(mode=backend).run(tqcs, shots=shots)  # one job, interleaved
    res = job.result()
    counts = [r.data.meas.get_counts() for r in res]
    report = dict(pair=pair, backend=backend.name, shots=shots,
                  opt_level=opt_level, mode="hw", arms={})
    for arm, tqc, cts in zip(("baseline", "optimized"), tqcs, counts):
        score(report, arm, tqc, cts, arms[arm][1])
    report["delta_fidelity"] = round(
        report["arms"]["optimized"]["fidelity_vs_ideal"]
        - report["arms"]["baseline"]["fidelity_vs_ideal"], 5)
    return report


def run_pair_aer(pair, shots=8192, noise=0.0):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    arms = load_arms(pair)
    if noise > 0:
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(noise, 2),
                                       ["cx", "cz"])
        backend = AerSimulator(noise_model=nm)
    else:
        backend = AerSimulator()
    tqcs = [transpile(arms[a][0], backend, optimization_level=1,
                      seed_transpiler=SEED) for a in ("baseline", "optimized")]
    result = backend.run(tqcs, shots=shots).result()
    report = dict(pair=pair, backend="aer", shots=shots,
                  noise=noise, mode="aer", arms={})
    for i, arm in enumerate(("baseline", "optimized")):
        score(report, arm, tqcs[i], result.get_counts(i), arms[arm][1])
    report["delta_fidelity"] = round(
        report["arms"]["optimized"]["fidelity_vs_ideal"]
        - report["arms"]["baseline"]["fidelity_vs_ideal"], 5)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["aer", "hw"], default="aer")
    ap.add_argument("--pair", default="mod5_4")
    ap.add_argument("--device", default="")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--noise", type=float, default=0.0)
    ap.add_argument("--opt-level", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7,
                    help="seed_transpiler; registered runs used 7")
    ap.add_argument("--tag", default="",
                    help="suffix for output filenames, e.g. seed11")
    args = ap.parse_args()
    global SEED
    SEED = args.seed
    os.makedirs(OUT, exist_ok=True)
    targets = PAIRS if args.pair == "all" else [args.pair]
    for p in targets:
        r = (run_pair_aer(p, args.shots, args.noise) if args.mode == "aer"
             else run_pair_hw(p, args.device, args.shots, args.opt_level))
        path = os.path.join(OUT, f"{args.mode}_{p}{args.tag}.json")
        json.dump(r, open(path, "w"), indent=1)
        print(json.dumps(r, indent=1))
        print(f"saved -> {path}")


if __name__ == "__main__":
    main()
