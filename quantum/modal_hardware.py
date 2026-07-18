"""modal_hardware.py: run the certified ZX circuit pairs on IBM hardware, via Modal.

Prereqs:
  1. IBM Quantum account (quantum.cloud.ibm.com, open plan). Copy the API
     token, and the instance CRN if your dashboard shows one.
  2. modal secret create ibm-quantum QISKIT_IBM_TOKEN=<token>
     (optionally add QISKIT_IBM_INSTANCE=<crn> and QISKIT_IBM_CHANNEL=<chan>)
  3. This file next to the qhw_package/ directory from the kit.

Run order:
  modal run modal_hardware.py --mode aer --pair mod5_4      # image smoke, no account
  modal run modal_hardware.py --mode hw --pair all          # real device, least busy
Results:
  modal volume get qhw-vol results ./qhw_results

The experiment design, pre-registered predictions, and interpretation rules
live in hardware_protocol.md inside qhw_package; this file only executes.
NOTE on API drift: IBM migrated platforms in 2025; if service init fails,
mirror the exact QiskitRuntimeService(...) snippet your dashboard shows at
the single marked spot in ibm_backend() below.
"""

import json
import math
import os

import modal

app = modal.App("zx-hardware")
vol = modal.Volume.from_name("qhw-vol", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("qiskit", "qiskit-aer", "qiskit-ibm-runtime")
    .add_local_dir("qhw_package", "/root/qhw")
)

V = "/vol"
PAIRS = ["mod5_4", "tof_3", "barenco_tof_3", "mod_mult_55"]


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
        qc = qasm2.load(f"/root/qhw/{pair}_{arm}.qasm")
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


@app.function(image=image, volumes={V: vol}, timeout=3600,
              secrets=[modal.Secret.from_name("ibm-quantum")])
def run_pair_hw(pair: str, device: str = "", shots: int = 8192,
                opt_level: int = 1):
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2
    os.makedirs(f"{V}/results", exist_ok=True)
    arms = load_arms(pair)
    backend = ibm_backend(device)
    tqcs = [transpile(arms[a][0], backend, optimization_level=opt_level,
                      seed_transpiler=7) for a in ("baseline", "optimized")]
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
    json.dump(report, open(f"{V}/results/hw_{pair}.json", "w"), indent=1)
    vol.commit()
    return report


@app.function(image=image, volumes={V: vol}, timeout=1800)
def run_pair_aer(pair: str, shots: int = 8192, noise: float = 0.0):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    os.makedirs(f"{V}/results", exist_ok=True)
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
                      seed_transpiler=7) for a in ("baseline", "optimized")]
    result = backend.run(tqcs, shots=shots).result()
    report = dict(pair=pair, backend="aer", shots=shots,
                  noise=noise, mode="aer", arms={})
    for i, arm in enumerate(("baseline", "optimized")):
        score(report, arm, tqcs[i], result.get_counts(i), arms[arm][1])
    report["delta_fidelity"] = round(
        report["arms"]["optimized"]["fidelity_vs_ideal"]
        - report["arms"]["baseline"]["fidelity_vs_ideal"], 5)
    json.dump(report, open(f"{V}/results/aer_{pair}.json", "w"), indent=1)
    vol.commit()
    return report


@app.local_entrypoint()
def main(mode: str = "aer", pair: str = "mod5_4", device: str = "",
         shots: int = 8192, noise: float = 0.0):
    targets = PAIRS if pair == "all" else [pair]
    for p in targets:
        if mode == "aer":
            r = run_pair_aer.remote(pair=p, shots=shots, noise=noise)
        else:
            r = run_pair_hw.remote(pair=p, device=device, shots=shots)
        print(json.dumps(r, indent=1))
