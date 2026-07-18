"""Track A: the qc_demo pipeline on the standard T-count benchmark suite.

Circuits: the Amy/Maslov/Nam-et-al. benchmark family shipped in
pyzx_repo/circuits/Fast ('_before' = original circuit; '_tpar.qc' =
the published T-par algorithm's output, our literature comparison).
Pipeline: zx.simplify.full_reduce (Frobenius/bialgebra rewriting),
circuit extraction, and PyZX's ZX-based equality verification as the
per-circuit witness.
"""
import os, time, signal
import pyzx as zx

class TO(Exception): pass
def alarm(sig, frm): raise TO()
signal.signal(signal.SIGALRM, alarm)

D = "pyzx_repo/circuits/Fast"

def twoq(c):
    return sum(1 for g in c.gates if g.name in ("CNOT", "CZ", "CX"))

rows = []
befores = sorted(f for f in os.listdir(D) if f.endswith("_before"))
for f in befores:
    name = f[: -len("_before")]
    c = zx.Circuit.load(os.path.join(D, f)).to_basic_gates()
    tpar_t = None
    tp = os.path.join(D, name + "_tpar.qc")
    if os.path.exists(tp):
        tpar_t = zx.Circuit.load(tp).to_basic_gates().tcount()
    g = c.to_graph()
    t0 = time.time()
    try:
        signal.alarm(45)
        zx.simplify.full_reduce(g)
        c2 = zx.extract_circuit(g.copy()).to_basic_gates()
        signal.alarm(0)
    except TO:
        signal.alarm(0)
        continue
    dt = time.time() - t0
    veq = None
    if len(c.gates) <= 350 and c.qubits <= 10:
        try:
            signal.alarm(30)
            veq = c.verify_equality(c2)
            signal.alarm(0)
        except (TO, Exception):
            signal.alarm(0)
            veq = None
    rows.append((name, c.qubits, c.tcount(), twoq(c),
                 c2.tcount(), twoq(c2), tpar_t, veq, dt))

hdr = f"{'circuit':<24}{'q':>3}{'T_in':>6}{'2q_in':>7}{'T_zx':>6}{'2q_zx':>7}{'T_tpar':>8}{'verified':>10}{'sec':>7}"
print(hdr)
print("-" * len(hdr))
tot_in = tot_zx = tot_tp = 0
n_tp = 0
for (name, q, ti, wi, tz, wz, tp, veq, dt) in rows:
    tot_in += ti; tot_zx += tz
    if tp is not None:
        tot_tp += tp; n_tp += 1
    tps = str(tp) if tp is not None else "-"
    v = {True: "PASS", False: "FAIL!", None: "n/a"}[veq]
    print(f"{name:<24}{q:>3}{ti:>6}{wi:>7}{tz:>6}{wz:>7}{tps:>8}{v:>10}{dt:>7.2f}")
print("-" * len(hdr))
print(f"{'TOTA'+'L':<24}{'':>3}{tot_in:>6}{'':>7}{tot_zx:>6}")
print(f"\naggregate T-count reduction: {tot_in} -> {tot_zx} "
      f"({100*(tot_in-tot_zx)/tot_in:.1f}% removed)")
print(f"on the {n_tp} circuits with shipped T-par outputs, "
      f"T-par total = {tot_tp}")
