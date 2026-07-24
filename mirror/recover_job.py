"""recover_job.py: list recent IBM jobs, and score a completed mirror job
from its ID. Use when the submitting terminal died before results printed.

Usage:
  export QISKIT_IBM_TOKEN=<token>
  python3 recover_job.py                      # list recent jobs + status
  python3 recover_job.py <job_id> [--tag _dd] # score a mirror job
"""
import argparse, json, os, sys

from qiskit_ibm_runtime import QiskitRuntimeService

import mirror_witness as mw


def counts_from(result):
    out = []
    for r in result:
        data = r.data
        # register name varies (meas, c, cr...); take the first BitArray
        names = [k for k in dir(data) if not k.startswith("_")]
        arr = None
        for n in names:
            v = getattr(data, n)
            if hasattr(v, "get_counts"):
                arr = v
                break
        if arr is None:
            raise RuntimeError(f"no counts register found in {names}")
        out.append(arr.get_counts())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id", nargs="?")
    ap.add_argument("--tag", default="_recovered")
    ap.add_argument("--shots", type=int, default=8192)
    args = ap.parse_args()

    service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])

    if not args.job_id:
        print("recent jobs:")
        for j in service.jobs(limit=15):
            print(f"  {j.job_id()}  {j.backend().name:12s} "
                  f"{j.status():12s} {j.creation_date}")
        return

    job = service.job(args.job_id)
    print(f"job {args.job_id}: {job.status()} on {job.backend().name}")
    if str(job.status()) not in ("DONE", "JobStatus.DONE"):
        print("not finished yet; rerun this when it is DONE")
        return

    counts = counts_from(job.result())
    jobs = mw.build_all()
    if len(jobs) != len(counts):
        print(f"WARNING: built {len(jobs)} circuits but job has "
              f"{len(counts)} results; scoring may be misaligned")
    os.makedirs("results", exist_ok=True)
    mw.score(jobs, counts, "hw" + args.tag, args.shots)


if __name__ == "__main__":
    main()
