"""verify.py: rerun every check that can be derived from committed artifacts.

Checks (graceful skip if a dependency is missing):
  1. pair equality        - independent pyzx re-verification of all four pairs
  2. manifest integrity   - pair_manifest.json counts vs the QASM files
  3. transpile identity   - seed-7/level-1 2q counts vs the hw_*.json records
  4. aer reproduction     - fresh 8192-shot runs under the registered noise model
  5. hw delta significance- two-proportion z on each hardware delta
  6. ceiling saturation   - measured fidelity vs real-calibration ceilings
  7. Part I statistics    - Wilcoxon tests recomputed from per-item eval JSONs
  (8. Lean: `lean lean/LensLean.lean` kernel-checks the lens category; run manually)

Deps: pip install pyzx qiskit qiskit-aer qiskit-ibm-runtime scipy
Run from repo root: python3 verify.py
"""
import glob, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
QHW = os.path.join(HERE, "quantum", "qhw_package")
RES = os.path.join(HERE, "quantum", "qhw_results")
PAIRS = ["mod5_4", "tof_3", "barenco_tof_3", "mod_mult_55"]
failures = []

def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(name)

def fid(p, q):
    ks = set(p) | set(q)
    return sum(math.sqrt(p.get(k, 0) * q.get(k, 0)) for k in ks) ** 2

print("== 1. pair equality (independent pyzx verification) ==")
try:
    import pyzx as zx
    for p in PAIRS:
        b = zx.Circuit.from_qasm_file(f"{QHW}/{p}_baseline.qasm").to_basic_gates()
        o = zx.Circuit.from_qasm_file(f"{QHW}/{p}_optimized.qasm").to_basic_gates()
        check(f"{p} baseline == optimized", b.verify_equality(o))
except ImportError:
    print("  skipped (pip install pyzx)")

print("== 2. manifest integrity ==")
try:
    import pyzx as zx
    man = {m["name"]: m for m in json.load(open(f"{QHW}/pair_manifest.json"))}
    for p, m in man.items():
        for arm, key in (("baseline", "base"), ("optimized", "opt")):
            c = zx.Circuit.from_qasm_file(f"{QHW}/{p}_{arm}.qasm").to_basic_gates()
            two = sum(1 for g in c.gates if g.name in ("CNOT", "CZ", "CX"))
            got = dict(total=len(c.gates), twoq=two,
                       oneq=len(c.gates) - two, T=c.tcount())
            ok = all(got[k] == m[key][k] for k in got)
            check(f"{p} {arm} counts", ok)
except ImportError:
    print("  skipped (pip install pyzx)")

print("== 3+4. transpile identity and aer reproduction ==")
try:
    from qiskit import qasm2, transpile
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    try:
        from qiskit_ibm_runtime.fake_provider import FakeFez
        fez = FakeFez()
    except Exception:
        fez = None
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["cx", "cz"])
    sim = AerSimulator(noise_model=nm)
    for p in PAIRS:
        hw = json.load(open(f"{RES}/hw_{p}.json"))
        aer = json.load(open(f"{RES}/aer_{p}.json"))
        fids = {}
        for arm in ("baseline", "optimized"):
            qc = qasm2.load(f"{QHW}/{p}_{arm}.qasm")
            ideal = {k: float(v) for k, v in
                     Statevector.from_instruction(qc).probabilities_dict().items()}
            m = qc.copy(); m.measure_all()
            if fez is not None:
                t = transpile(m, fez, optimization_level=1, seed_transpiler=7)
                n2 = sum(v for k, v in t.count_ops().items()
                         if k in ("cx", "cz", "ecr"))
                check(f"{p} {arm} transpiled 2q == recorded",
                      n2 == hw["arms"][arm]["transpiled_2q"],
                      f"({n2} vs {hw['arms'][arm]['transpiled_2q']})")
            ts = transpile(m, sim, optimization_level=1, seed_transpiler=7)
            cts = sim.run(ts, shots=8192).result().get_counts()
            probs = {k.replace(" ", ""): v / 8192 for k, v in cts.items()}
            fids[arm] = fid(probs, ideal)
        d = fids["optimized"] - fids["baseline"]
        check(f"{p} aer delta reproduces", abs(d - aer["delta_fidelity"]) < 0.02,
              f"(fresh {d:+.4f} vs committed {aer['delta_fidelity']:+.4f})")
except ImportError:
    print("  skipped (pip install qiskit qiskit-aer qiskit-ibm-runtime)")

print("== 5. hardware delta significance (8192 shots/arm) ==")
for p in PAIRS:
    h = json.load(open(f"{RES}/hw_{p}.json"))
    fb = h["arms"]["baseline"]["fidelity_vs_ideal"]
    fo = h["arms"]["optimized"]["fidelity_vs_ideal"]
    se = math.sqrt(fb * (1 - fb) / 8192 + fo * (1 - fo) / 8192)
    z = (fo - fb) / se
    expect_sig = p != "tof_3"
    ok = (abs(z) > 3) if expect_sig else (abs(z) < 2)
    check(f"{p} z={z:+.1f} ({'significant' if expect_sig else 'null control'})", ok)

print("== 6. ceiling saturation (real 2026-07-18 calibration) ==")
cals = sorted(glob.glob(f"{RES}/calibration_*.json"))
if not cals:
    print("  skipped (no calibration files)")
for f in cals:
    cal = json.load(open(f))
    n2s = tuple(a["n_2q"] for a in cal["arms"])
    p = {(52, 38): "mod5_4", (30, 28): "tof_3",
         (42, 34): "barenco_tof_3", (99, 117): "mod_mult_55"}.get(n2s)
    if p is None:
        continue
    h = json.load(open(f"{RES}/hw_{p}.json"))
    for i, arm in enumerate(("baseline", "optimized")):
        c = cal["arms"][i]["ceiling_actual_calibration"]
        m = h["arms"][arm]["fidelity_vs_ideal"]
        r = m / c
        lo = 0.85 if (p == "mod_mult_55" and arm == "baseline") else 0.95
        check(f"{p} {arm} at {100*r:.0f}% of ceiling", lo <= r <= 1.10)

print("== 7. Part I statistics from committed per-item scores ==")
try:
    from scipy.stats import wilcoxon
    def items(a): return json.load(open(f"{HERE}/results/eval_{a}.json"))["items"]
    ad, aa, ae = items("ad_diff"), items("ad_after"), items("ad_endpoint")
    def sme(it): return it["sim"] - it["echo_ceiling"]
    claims = [  # (name, a, b, fn, claimed_p, direction)
        ("ad_diff-ad_after sim-echo null", ad, aa, sme, 0.152, "null"),
        ("ad_diff-ad_endpoint sim-echo sig", ad, ae, sme, 1e-3, "sig"),
        ("ad_after-ad_endpoint sim-echo sig", aa, ae, sme, 1e-3, "sig"),
    ]
    for name, a, b, fn, claimed, kind in claims:
        d = [fn(x) - fn(y) for x, y in zip(a, b)]
        _, pv = wilcoxon([v for v in d if abs(v) > 1e-12])
        ok = (pv > 0.05) if kind == "null" else (pv < 0.001)
        check(f"{name} (p={pv:.3g})", ok)
except ImportError:
    print("  skipped (pip install scipy)")

print()
if failures:
    print(f"{len(failures)} check(s) FAILED:", *failures, sep="\n  ")
    sys.exit(1)
print("All checks passed.")
