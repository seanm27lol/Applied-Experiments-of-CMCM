"""fetch_calibration.py: recover the calibration snapshot from the 2026-07-18
hardware jobs and recompute the error-budget ceilings with real numbers.

Usage:
  export QISKIT_IBM_TOKEN=<token>
  python3 fetch_calibration.py                 # lists your recent jobs
  python3 fetch_calibration.py <job_id> ...    # analyzes given job(s)

For each job: pulls backend properties at execution time, extracts the CZ
error of every edge and readout error of every qubit the transpiled
circuits actually touched, recomputes per-arm ceilings, writes
calibration_<job_id>.json next to this script.
"""
import json, sys, os

from qiskit_ibm_runtime import QiskitRuntimeService

def main():
    service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])
    if len(sys.argv) == 1:
        print("Recent jobs (pass IDs to analyze):")
        for j in service.jobs(limit=25):
            print(f"  {j.job_id()}  {j.backend().name}  {j.creation_date}")
        return

    for job_id in sys.argv[1:]:
        job = service.job(job_id)
        backend = job.backend()
        props = backend.properties(datetime=job.creation_date)  # snapshot at run time
        out = {"job_id": job_id, "backend": backend.name,
               "date": str(job.creation_date), "arms": []}

        # circuits as executed: pull physical qubits + 2q edges from the inputs
        circuits = job.inputs.get("pubs") or job.inputs.get("circuits")
        for i, pub in enumerate(circuits):
            circ = pub[0] if isinstance(pub, (list, tuple)) else pub
            qubits, edges = set(), []
            for inst in circ.data:
                qs = [circ.find_bit(q).index for q in inst.qubits]
                qubits.update(qs)
                if inst.operation.num_qubits == 2:
                    edges.append(tuple(qs))
            cz_errs = []
            for e in edges:
                for name in ("cz", "ecr", "cx"):
                    try:
                        cz_errs.append(props.gate_error(name, list(e)))
                        break
                    except Exception:
                        continue
            ro_errs = [props.readout_error(q) for q in sorted(qubits)]
            ceiling = 1.0
            for e in cz_errs: ceiling *= (1 - e)
            for r in ro_errs: ceiling *= (1 - r)
            out["arms"].append({
                "index": i, "physical_qubits": sorted(qubits),
                "n_2q": len(edges),
                "cz_error_mean": sum(cz_errs)/len(cz_errs) if cz_errs else None,
                "readout_error_mean": sum(ro_errs)/len(ro_errs),
                "ceiling_actual_calibration": round(ceiling, 4),
            })
            print(f"{job_id} arm {i}: {len(edges)} 2q ops on qubits "
                  f"{sorted(qubits)}, mean CZ err "
                  f"{out['arms'][-1]['cz_error_mean']:.2e}, "
                  f"ceiling {ceiling:.4f}")
        fn = f"calibration_{job_id}.json"
        json.dump(out, open(fn, "w"), indent=1)
        print(f"written: {fn}\n")

if __name__ == "__main__":
    main()
