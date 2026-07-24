"""mirror_witness.py: hardware-native verification of equality witnesses.

Builds TRUE mirrors (B_p . Pauli . O_p^-1) and DERANGED mirrors
(B_p . Pauli . O_q^-1, q != p, verified non-identity), runs all in one
interleaved job, scores the Pauli-frame-adjusted return-to-zero
probability.

Modes:
  --mode check   build everything, verify ideals classically, NO submission
  --mode aer     run on noisy simulator (sanity)
  --mode hw      submit ONE job to IBM (requires QISKIT_IBM_TOKEN)
  --mode score --job_id <id>   score a completed hardware job

Run check first. Commit PREREG_MIRROR.md before hw.
"""
import argparse, json, os, random

from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.quantum_info import Statevector

PAIRS = ["mod5_4", "tof_3", "barenco_tof_3", "mod_mult_55"]
# deranged partner for each pair (avoid tof_3/barenco_tof_3 which may be
# the same unitary; verified non-identity in check mode regardless)
DERANGE = {"mod5_4": "tof_3", "tof_3": "mod5_4",
           "barenco_tof_3": "mod_mult_55", "mod_mult_55": "barenco_tof_3"}
SEED = 2026
QHW = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "quantum", "qhw_package")


def load(pair, arm):
    return qasm2.load(os.path.join(QHW, f"{pair}_{arm}.qasm"))


def build_mirror(base_pair, opt_pair, x_bits):
    """Randomized-input mirror: prepare |x>, run B, barrier, run O^-1.
    If B == O the output is exactly x, checked with zero simulation.
    (A Pauli layer at the JOINT is wrong for non-Clifford circuits: it
    conjugates through B, scrambling the expected string.)"""
    b = load(base_pair, "baseline")
    o = load(opt_pair, "optimized")
    n = max(b.num_qubits, o.num_qubits)
    qc = QuantumCircuit(n)
    for q, bit in enumerate(x_bits):
        if bit:
            qc.x(q)
    qc.barrier()
    qc.compose(b, qubits=range(b.num_qubits), inplace=True)
    qc.barrier()
    qc.compose(o.inverse(), qubits=range(o.num_qubits), inplace=True)
    return qc


def bits_to_string(x_bits, n):
    """Little-endian per Qiskit: qubit q at string position n-1-q."""
    bits = ["0"] * n
    for q, bit in enumerate(x_bits):
        if bit:
            bits[n - 1 - q] = "1"
    return "".join(bits)


def ideal_top(qc):
    probs = Statevector.from_instruction(qc).probabilities_dict()
    top = max(probs, key=probs.get)
    return top, float(probs[top])


def build_all():
    rng = random.Random(SEED)
    jobs = []
    for p in PAIRS:
        for kind, opp in (("true", p), ("deranged", DERANGE[p])):
            for attempt in range(20):
                nq = max(load(p, "baseline").num_qubits,
                         load(opp, "optimized").num_qubits)
                x = [rng.randint(0, 1) for _ in range(nq)]
                qc = build_mirror(p, opp, x)
                fs = bits_to_string(x, nq)
                top, pr = ideal_top(qc)
                # deranged inputs must actually produce a mismatch; redraw
                # if this x happens to be a fixed point of B_p o O_q^-1
                if kind == "deranged" and top == fs:
                    continue
                break
            jobs.append(dict(name=f"{kind}_{p}", kind=kind, base=p,
                             opt=opp, x="".join(map(str, x)),
                             frame_str=fs, ideal_top=top,
                             ideal_top_prob=round(pr, 6), circuit=qc))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True,
                    choices=["check", "aer", "hw", "score"])
    ap.add_argument("--job_id")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--dd", action="store_true",
                    help="enable dynamical decoupling (XY4) on idle qubits")
    ap.add_argument("--tag", default="",
                    help="suffix for the results filename")
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    jobs = build_all()

    if args.mode == "check":
        ok = True
        for j in jobs:
            det = j["ideal_top_prob"] > 0.999
            on_frame = j["ideal_top"] == j["frame_str"]
            if j["kind"] == "true":
                good = det and on_frame
                why = "" if good else "BAD: true mirror not identity"
            else:
                good = det and not on_frame
                why = "" if good else "BAD: deranged secretly identity"
            ok = ok and good
            print(f"  {j['name']:24s} n={j['circuit'].num_qubits} "
                  f"det={det} returns_frame={on_frame}  "
                  f"{'OK' if good else why}")
        print("check:", "PASS, safe to submit" if ok else "FAIL, fix first")
        return

    if args.mode == "aer":
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(0.01, 2),
                                       ["cx", "cz"])
        backend = AerSimulator(noise_model=nm)
    elif args.mode == "hw":
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        service = QiskitRuntimeService(
            token=os.environ["QISKIT_IBM_TOKEN"])
        backend = service.least_busy(operational=True, simulator=False,
                                     min_num_qubits=20)
        print("backend:", backend.name)

    if args.mode in ("aer", "hw"):
        circs = []
        for j in jobs:
            m = j["circuit"].copy()
            m.measure_all()
            circs.append(transpile(m, backend, optimization_level=1,
                                   seed_transpiler=7))
        if args.mode == "aer":
            res = backend.run(circs, shots=args.shots).result()
            counts = [res.get_counts(i) for i in range(len(circs))]
        else:
            sampler = SamplerV2(backend)
            if args.dd:
                sampler.options.dynamical_decoupling.enable = True
                sampler.options.dynamical_decoupling.sequence_type = "XY4"
                print("dynamical decoupling: XY4 enabled")
            job = sampler.run(circs, shots=args.shots)
            print("job id:", job.job_id(), "(waiting...)")
            res = job.result()
            counts = [getattr(r.data, list(r.data.keys())[0] if hasattr(
                r.data, 'keys') else 'meas').get_counts() for r in res]
        score(jobs, counts, args.mode + args.tag, args.shots)

    if args.mode == "score":
        raise SystemExit("score mode: fetch counts for --job_id via "
                         "fetch pattern in quantum/fetch_calibration.py, "
                         "then call score(); left manual by design.")


def score(jobs, counts, tag, shots):
    out = []
    for j, c in zip(jobs, counts):
        c = {k.replace(" ", ""): v for k, v in c.items()}
        r = c.get(j["frame_str"], 0) / shots
        out.append(dict(name=j["name"], kind=j["kind"],
                        expected=j["frame_str"], return_prob=round(r, 4)))
        print(f"  {j['name']:24s} return_prob={r:.4f}")
    with open(f"results/mirror_{tag}.json", "w") as f:
        json.dump(out, f, indent=1)
    trues = [o for o in out if o["kind"] == "true"]
    ders = [o for o in out if o["kind"] == "deranged"]
    print(f"\ntrue mirrors:     min r = {min(o['return_prob'] for o in trues):.3f}")
    print(f"deranged mirrors: max r = {max(o['return_prob'] for o in ders):.3f}")


if __name__ == "__main__":
    main()
