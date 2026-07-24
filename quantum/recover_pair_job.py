"""recover_pair_job.py: score a completed qhw_seed/qhw_local hardware job
from its ID, when the submitting terminal died before results printed.

Rebuilds the two arms, re-transpiles with the SAME seed against the same
backend to recover 2q/depth, and writes the usual qhw_results JSON.

Usage (from the quantum/ directory):
  export QISKIT_IBM_TOKEN=<token>
  python3 recover_pair_job.py <job_id> --pair mod_mult_55 --seed 11 --tag _seed11
"""
import argparse, json, os

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService

import qhw_seed as q


def counts_from(result):
    out = []
    for r in result:
        data = r.data
        arr = None
        for n in [k for k in dir(data) if not k.startswith("_")]:
            v = getattr(data, n)
            if hasattr(v, "get_counts"):
                arr = v
                break
        if arr is None:
            raise RuntimeError("no counts register found")
        out.append(arr.get_counts())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--pair", required=True)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--tag", default="_recovered")
    ap.add_argument("--opt-level", type=int, default=1)
    args = ap.parse_args()

    service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])
    job = service.job(args.job_id)
    print(f"job {args.job_id}: {job.status()} on {job.backend().name}")
    if str(job.status()) not in ("DONE", "JobStatus.DONE"):
        print("not finished yet; rerun when DONE")
        return

    backend = job.backend()
    counts = counts_from(job.result())
    arms = q.load_arms(args.pair)
    order = ("baseline", "optimized")
    if len(counts) != 2:
        print(f"WARNING: expected 2 results, got {len(counts)}. "
              "Is this a pair job?")
        return

    report = {"pair": args.pair, "mode": "hw", "backend": backend.name,
              "job_id": args.job_id, "seed_transpiler": args.seed,
              "arms": {}}
    for arm, c in zip(order, counts):
        m, ideal = arms[arm]
        tqc = transpile(m, backend, optimization_level=args.opt_level,
                        seed_transpiler=args.seed)
        q.score(report, arm, tqc, c, ideal)
    report["delta_fidelity"] = round(
        report["arms"]["optimized"]["fidelity_vs_ideal"]
        - report["arms"]["baseline"]["fidelity_vs_ideal"], 5)

    os.makedirs(q.OUT, exist_ok=True)
    path = os.path.join(q.OUT, f"hw_{args.pair}{args.tag}.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps(report, indent=1))
    print(f"saved -> {path}")


if __name__ == "__main__":
    main()
