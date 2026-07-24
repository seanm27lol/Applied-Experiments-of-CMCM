"""pair_matched_layout.py: R2', the placement-controlled compilation delta.

R2 varied seed_transpiler, which changes the LAYOUT as well as the routing.
The seed-11 run put the two arms on disjoint physical qubits (0/9 overlap),
so its +0.171 delta compares two different pieces of hardware. This version
pins both arms to the same physical qubits and submits everything in ONE
interleaved job, so the only difference between the primary two circuits is
the circuit itself.

Circuits submitted (one job):
  0. baseline  @ LAYOUT, routing seed A
  1. optimized @ LAYOUT, routing seed A     <- primary comparison vs 0
  2. optimized @ LAYOUT, routing seed B     <- routing sensitivity vs 1

Modes:
  --mode check   build, report gate counts, verify layouts match
  --mode hw      submit ONE job (requires QISKIT_IBM_TOKEN)
"""
import argparse, json, math, os

from qiskit import qasm2, transpile
from qiskit.quantum_info import Statevector

HERE = os.path.dirname(os.path.abspath(__file__))
QHW = os.path.join(HERE, "qhw_package")
OUT = os.path.join(HERE, "qhw_results")
PAIR = "mod_mult_55"
# shared layout serving both arms well, found by search over layouts the
# transpiler itself chooses; same neighbourhood as the 2026-07-18 runs
LAYOUT = [141, 123, 143, 145, 124, 144, 136, 142, 140]
SEED_A = 1
SEED_B = 6


def fidelity(p, q):
    ks = set(p) | set(q)
    return sum(math.sqrt(p.get(k, 0.0) * q.get(k, 0.0)) for k in ks) ** 2


def load(arm):
    qc = qasm2.load(os.path.join(QHW, f"{PAIR}_{arm}.qasm"))
    ideal = {k: float(v) for k, v in
             Statevector.from_instruction(qc).probabilities_dict().items()}
    m = qc.copy()
    m.measure_all()
    return m, ideal


def build(backend):
    specs = []
    for label, arm, seed in (("baseline_A", "baseline", SEED_A),
                             ("optimized_A", "optimized", SEED_A),
                             ("optimized_B", "optimized", SEED_B)):
        m, ideal = load(arm)
        t = transpile(m, backend, optimization_level=1,
                      seed_transpiler=seed, initial_layout=LAYOUT)
        n2 = sum(v for k, v in t.count_ops().items()
                 if k in ("cx", "cz", "ecr"))
        specs.append(dict(label=label, arm=arm, seed=seed, circuit=t,
                          ideal=ideal, n2q=n2, depth=t.depth(),
                          qubits=sorted(set(LAYOUT))))
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["check", "hw"])
    ap.add_argument("--shots", type=int, default=8192)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    if args.mode == "check":
        from qiskit_ibm_runtime.fake_provider import FakeFez
        backend = FakeFez()
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])
        backend = service.least_busy(operational=True, simulator=False,
                                     min_num_qubits=20)
        print("backend:", backend.name)

    specs = build(backend)
    for s in specs:
        print(f"  {s['label']:14s} 2q={s['n2q']:>4} depth={s['depth']:>4} "
              f"qubits={s['qubits']}")
    same = len({tuple(s["qubits"]) for s in specs}) == 1
    print(f"  all three on identical physical qubits: {same}")
    if args.mode == "check":
        print("check:", "PASS, safe to submit" if same
              else "FAIL, layouts differ")
        return
    if not same:
        raise SystemExit("layouts differ; refusing to submit")

    sampler = SamplerV2(backend)
    job = sampler.run([s["circuit"] for s in specs], shots=args.shots)
    print("job id:", job.job_id(), "(waiting...)")
    res = job.result()

    for s, r in zip(specs, res):
        data = r.data
        arr = next(getattr(data, n) for n in dir(data)
                   if not n.startswith("_")
                   and hasattr(getattr(data, n), "get_counts"))
        probs = {k.replace(" ", ""): v / args.shots
                 for k, v in arr.get_counts().items()}
        s["fidelity"] = round(fidelity(probs, s["ideal"]), 5)
        print(f"  {s['label']:14s} fidelity={s['fidelity']:.5f}")

    d = {s["label"]: s["fidelity"] for s in specs}
    report = dict(pair=PAIR, backend=backend.name, job_id=job.job_id(),
                  layout=LAYOUT, seed_A=SEED_A, seed_B=SEED_B,
                  arms={s["label"]: {k: s[k] for k in
                                     ("arm", "seed", "n2q", "depth",
                                      "fidelity")} for s in specs},
                  delta_matched_layout=round(
                      d["optimized_A"] - d["baseline_A"], 5),
                  routing_effect=round(
                      d["optimized_B"] - d["optimized_A"], 5))
    path = os.path.join(OUT, f"hw_{PAIR}_matched_layout.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=1)
    print(f"\n  delta at matched layout: {report['delta_matched_layout']:+.5f}")
    print(f"  routing effect (B - A):  {report['routing_effect']:+.5f}")
    print(f"  (registered 2026-07-18 delta was +0.06700)")
    print(f"saved -> {path}")


if __name__ == "__main__":
    main()
