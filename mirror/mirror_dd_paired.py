"""mirror_dd_paired.py: R1', the drift-controlled DD comparison.

R1 compared a DD job against a no-DD job five hours apart, which cannot
separate a DD effect from calibration drift. This version applies DD as a
transpiler pass (XX sequence, native X gates) and submits all sixteen
circuits (eight mirrors x {no-DD, DD}) in ONE interleaved job, so both
conditions share a calibration window.

Modes:
  --mode check   build and report gate counts, no submission
  --mode hw      submit ONE job (requires QISKIT_IBM_TOKEN)

Run check first. Commit PREREG_ROUND3.md before hw.
"""
import argparse, json, os

from qiskit import transpile
from qiskit.circuit.library import XGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling

import mirror_witness as mw


def dd_manager(target):
    return PassManager([
        ALAPScheduleAnalysis(target=target),
        PadDynamicalDecoupling(target=target,
                               dd_sequence=[XGate(), XGate()]),
    ])


def build_pairs(backend):
    """Returns (specs, circuits) with no-DD and DD interleaved."""
    jobs = mw.build_all()
    pm = dd_manager(backend.target)
    specs, circs = [], []
    for j in jobs:
        m = j["circuit"].copy()
        m.measure_all()
        t = transpile(m, backend, optimization_level=1, seed_transpiler=7)
        for cond, c in (("nodd", t), ("dd", pm.run(t))):
            specs.append(dict(name=f"{j['name']}_{cond}", cond=cond,
                              kind=j["kind"], base=j["base"],
                              frame_str=j["frame_str"],
                              n_delay=c.count_ops().get("delay", 0),
                              n_x=c.count_ops().get("x", 0)))
            circs.append(c)
    return specs, circs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["check", "hw"])
    ap.add_argument("--shots", type=int, default=8192)
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)

    if args.mode == "check":
        from qiskit_ibm_runtime.fake_provider import FakeFez
        backend = FakeFez()
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])
        backend = service.least_busy(operational=True, simulator=False,
                                     min_num_qubits=20)
        print("backend:", backend.name)

    specs, circs = build_pairs(backend)
    print(f"{len(circs)} circuits ({len(circs)//2} mirrors x 2 conditions)")
    for s in specs:
        if s["cond"] == "dd":
            print(f"  {s['name']:32s} X pulses added: {s['n_x']}")

    if args.mode == "check":
        bad = [s for s in specs if s["cond"] == "dd" and s["n_x"] == 0]
        print("check:", "FAIL, DD added no pulses to " + str(len(bad))
              if bad else "PASS, safe to submit")
        return

    sampler = SamplerV2(backend)
    job = sampler.run(circs, shots=args.shots)
    print("job id:", job.job_id(), "(waiting...)")
    res = job.result()
    out = []
    for s, r in zip(specs, res):
        data = r.data
        arr = next(getattr(data, n) for n in dir(data)
                   if not n.startswith("_")
                   and hasattr(getattr(data, n), "get_counts"))
        c = {k.replace(" ", ""): v for k, v in arr.get_counts().items()}
        s["return_prob"] = round(c.get(s["frame_str"], 0) / args.shots, 4)
        out.append(s)
        print(f"  {s['name']:32s} r={s['return_prob']:.4f}")

    with open("results/mirror_dd_paired.json", "w") as f:
        json.dump(dict(job_id=job.job_id(), backend=backend.name,
                       shots=args.shots, results=out), f, indent=1)

    print("\npaired deltas (dd minus nodd), TRUE mirrors:")
    rises = []
    for base in ["mod5_4", "tof_3", "barenco_tof_3", "mod_mult_55"]:
        n = next(s for s in out if s["name"] == f"true_{base}_nodd")
        d = next(s for s in out if s["name"] == f"true_{base}_dd")
        delta = d["return_prob"] - n["return_prob"]
        rises.append(delta)
        print(f"  {base:16s} {n['return_prob']:.4f} -> "
              f"{d['return_prob']:.4f}  delta {delta:+.4f}")
    print(f"  mean delta {sum(rises)/len(rises):+.4f}   "
          f"all positive: {all(r > 0 for r in rises)}")
    dmax = max(s["return_prob"] for s in out if s["kind"] == "deranged")
    print(f"  deranged max r = {dmax:.4f}")


if __name__ == "__main__":
    main()
