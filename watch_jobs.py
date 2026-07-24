"""watch_jobs.py: poll the round-2 IBM jobs, show queue status live, and
run the right scorer automatically when each finishes.

Run from the repo root:
  export QISKIT_IBM_TOKEN=<token>
  python3 watch_jobs.py

Ctrl-C is safe at any time: the jobs keep running server-side and the
recovery scripts can score them later.
"""
import os, subprocess, sys, time
from datetime import datetime

from qiskit_ibm_runtime import QiskitRuntimeService

ROOT = os.path.dirname(os.path.abspath(__file__))

JOBS = [
    dict(name="R1 DD mirror", job_id="d9hua4khonhs73adloe0",
         cwd=os.path.join(ROOT, "mirror"),
         cmd=["python3", "recover_job.py", "d9hua4khonhs73adloe0",
              "--tag", "_dd"]),
    dict(name="R2 seed-11", job_id="d9hubfchonhs73adlr30",
         cwd=os.path.join(ROOT, "quantum"),
         cmd=["python3", "recover_pair_job.py", "d9hubfchonhs73adlr30",
              "--pair", "mod_mult_55", "--seed", "11",
              "--tag", "_seed11"]),
]
POLL = 30


def detail(job):
    """Whatever queue info this API version exposes."""
    bits = []
    for attr in ("position_in_queue", "queue_position"):
        try:
            v = getattr(job, attr)
            v = v() if callable(v) else v
            if v is not None:
                bits.append(f"queue #{v}")
                break
        except Exception:
            pass
    try:
        m = job.metrics() or {}
        for k, label in (("estimated_start_time", "starts"),
                         ("estimated_completion_time", "done by")):
            if m.get(k):
                bits.append(f"{label} {str(m[k])[11:19]}")
        pos = m.get("position_in_queue")
        if pos is not None and not any("queue" in b for b in bits):
            bits.append(f"queue #{pos}")
    except Exception:
        pass
    return "  ".join(bits)


def main():
    service = QiskitRuntimeService(token=os.environ["QISKIT_IBM_TOKEN"])
    last = {}
    done = set()
    print(f"watching {len(JOBS)} jobs, polling every {POLL}s. Ctrl-C is safe.\n")
    while len(done) < len(JOBS):
        for spec in JOBS:
            if spec["job_id"] in done:
                continue
            try:
                job = service.job(spec["job_id"])
                status = str(job.status()).replace("JobStatus.", "")
            except Exception as e:
                print(f"  [{spec['name']}] lookup failed: {e}")
                continue
            line = f"{status}  {detail(job)}".strip()
            if line != last.get(spec["job_id"]):
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] {spec['name']:14s} {line}")
                last[spec["job_id"]] = line
            if status in ("DONE", "ERROR", "CANCELLED"):
                done.add(spec["job_id"])
                if status != "DONE":
                    print(f"  {spec['name']} ended as {status}; not scoring")
                    continue
                print(f"\n=== {spec['name']} finished, scoring ===")
                r = subprocess.run(spec["cmd"], cwd=spec["cwd"])
                if r.returncode:
                    print(f"  scorer exited {r.returncode}; run manually:\n"
                          f"  cd {spec['cwd']} && {' '.join(spec['cmd'])}")
                print()
        if len(done) < len(JOBS):
            time.sleep(POLL)
    print("both jobs complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped watching; jobs continue server-side.")
