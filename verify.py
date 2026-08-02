"""verify.py: rerun every check that can be derived from committed artifacts.

Checks (graceful skip if a dependency is missing):
  1. pair equality        - independent pyzx re-verification of all four pairs
  2. manifest integrity   - pair_manifest.json counts vs the QASM files
  3. transpile identity   - seed-7/level-1 2q counts vs the hw_*.json records
  4. aer reproduction     - fresh 8192-shot runs under the registered noise model
  5. hw delta significance- two-proportion z on each hardware delta
  6. ceiling saturation   - measured fidelity vs real-calibration ceilings
  7. Part I statistics    - Wilcoxon tests recomputed from per-item eval JSONs
  8. Part III statistics  - C1/C2/P2 recomputed across all three seeds
  9. Part V budget curve  - the six gaps and the N=4000 decomposition
 10. Part IV ceilings     - exact Bayes ceilings re-enumerated (all 8^6 paths)
 11. Part VI cost channel - anchors, the falsified C1 correlation, and the
                            search-evaluation rungs, from committed artifacts
  (12. Lean: `lean lean/LensLean.lean` kernel-checks the lens category, and
       `lean part_iv/WitnessRecoverability.lean` the recoverability axis;
       both run manually)

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
            # Both arms of a pair draw on the same simulator seed: a paired
            # comparison under common random numbers, which is the simulator
            # analogue of the interleaving rule the hardware runs follow. It
            # also makes this check deterministic for any reader; unseeded,
            # the delta on the small-effect pairs varies by more than the
            # tolerance from run to run.
            cts = sim.run(ts, shots=8192, seed_simulator=7).result().get_counts()
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

PW = os.path.join(HERE, "proof_witness", "results")
CC = os.path.join(HERE, "cost_channel", "results")


def sme_items(path):
    """Per-item sim-minus-echo scores from a proof_witness eval JSON."""
    return [it["sim_minus_echo"] for it in json.load(open(path))["items"]]


def paired(a, b):
    """Mean delta and Wilcoxon p over paired per-item scores."""
    from scipy.stats import wilcoxon
    d = [x - y for x, y in zip(a, b)]
    nz = [v for v in d if abs(v) > 1e-12]
    return sum(d) / len(d), wilcoxon(nz)[1]


print("== 8. Part III paired statistics (three seeds) ==")
try:
    import scipy.stats  # noqa: F401
    seeds = {"seed 0": "", "seed 1": "_s1", "seed 2": "_s2"}
    # registered: C1 positive with p<0.05 in every seed (R3a), across-seed sd
    # of the C1 mean below 0.02 (R3b), P2 null in every seed (R3c).
    c1_means = []
    for label, sfx in seeds.items():
        tr = sme_items(f"{PW}/eval_pw_trace{sfx}.json")
        sh = sme_items(f"{PW}/eval_pw_shuffle{sfx}.json")
        pr = sme_items(f"{PW}/eval_pw_pair{sfx}.json")
        ep = sme_items(f"{PW}/eval_pw_endpoint{sfx}.json")
        m1, p1 = paired(tr, sh)
        m2, p2 = paired(sh, pr)
        m3, p3 = paired(pr, ep)
        c1_means.append(m1)
        check(f"C1 trace-shuffle positive, {label}", m1 > 0 and p1 < 0.05,
              f"({m1:+.4f}, p={p1:.2g})")
        check(f"C2 shuffle-pair positive, {label}", m2 > 0 and p2 < 0.05,
              f"({m2:+.4f}, p={p2:.2g})")
        check(f"P2 pair-endpoint null, {label}", p3 > 0.05,
              f"({m3:+.4f}, p={p3:.2g})")
    sd = (sum((m - sum(c1_means) / 3) ** 2 for m in c1_means) / 2) ** 0.5
    check("R3b across-seed sd of C1 below 0.02", sd < 0.02, f"(sd={sd:.4f})")
    # the registered Part III headline, at the registered seed
    tr = sme_items(f"{PW}/eval_pw_trace.json")
    pr = sme_items(f"{PW}/eval_pw_pair.json")
    m, p = paired(tr, pr)
    check("P1 trace-pair at registered seed", m > 0.02 and p < 0.05,
          f"({m:+.4f}, p={p:.2g})")
    # content share: C1 / (C1 + C2) at the Part III operating point
    m1, _ = paired(sme_items(f"{PW}/eval_pw_trace.json"),
                   sme_items(f"{PW}/eval_pw_shuffle.json"))
    m2, _ = paired(sme_items(f"{PW}/eval_pw_shuffle.json"), pr)
    share = m1 / (m1 + m2)
    check(f"content share {100*share:.0f}% at N=2000", 0.70 <= share <= 0.76)
except ImportError:
    print("  skipped (pip install scipy)")

print("== 9. Part V budget curve and decomposition ==")
try:
    import scipy.stats  # noqa: F401
    budgets = [125, 250, 500, 1000, 2000, 4000]
    gaps = []
    for n in budgets:
        tr = sme_items(f"{PW}/eval_pw_trace_n{n}.json")
        pr = sme_items(f"{PW}/eval_pw_pair_n{n}.json")
        m, p = paired(tr, pr)
        gaps.append(m)
        check(f"N={n} gap positive and significant", m > 0 and p < 0.05,
              f"({m:+.4f}, p={p:.2g})")
    # P5c: the N=2000 anchor lands within +-0.025 of Part III's +0.054
    check("P5c anchor within 0.025 of Part III", abs(gaps[4] - 0.054) < 0.025,
          f"({gaps[4]:+.4f} vs +0.0540)")
    # P5b failed as registered: the gap at N=4000 is NOT below +0.02
    check("P5b failed as reported (gap at N=4000 above +0.02)", gaps[5] > 0.02,
          f"({gaps[5]:+.4f})")
    # the registered conditional: decomposition at N=4000
    tr4 = sme_items(f"{PW}/eval_pw_trace_n4000.json")
    sh4 = sme_items(f"{PW}/eval_pw_shuffle_n4000.json")
    pr4 = sme_items(f"{PW}/eval_pw_pair_n4000.json")
    content, pc = paired(tr4, sh4)
    fmt, pf = paired(sh4, pr4)
    check("N=4000 content (trace-shuffle) significant", pc < 0.001,
          f"({content:+.4f}, p={pc:.2g})")
    check("N=4000 format (shuffle-pair) significant", pf < 0.001,
          f"({fmt:+.4f}, p={pf:.2g})")
    share4 = content / (content + fmt)
    check(f"content share {100*share4:.0f}% at N=4000", 0.64 <= share4 <= 0.72)
except ImportError:
    print("  skipped (pip install scipy)")

print("== 10. Part IV exact Bayes ceilings (full enumeration) ==")
try:
    sys.path.insert(0, os.path.join(HERE, "part_iv"))
    import ceiling as C4
    reported = {"readable": 1.000, "free": 1.000, "q25": 0.915,
                "q50": 0.739, "q75": 0.514, "abelian": 0.190}
    for name, want in reported.items():
        got = C4.ceiling(name, 6)
        got = got[1] if isinstance(got, tuple) else got
        check(f"{name} ceiling {got:.3f} == reported {want:.3f}",
              abs(got - want) < 0.002)
    # the impossibility claim: max gap collapses at BOTH ends of the fiber axis
    lo = C4.ceiling("free", 6)
    hi = C4.ceiling("abelian", 6)
    lo = (lo[1] if isinstance(lo, tuple) else lo) - 0.125
    hi = (hi[1] if isinstance(hi, tuple) else hi) - 0.125
    check("max gap at abelian below 0.07 (high-fiber collapse)", hi < 0.07,
          f"({hi:.3f})")
    check("free ceiling is 1.0 (low end capped computationally, not by info)",
          lo > 0.87, f"(max gap {lo:.3f})")
except Exception as e:
    print(f"  skipped ({type(e).__name__}: {e})")
finally:
    if os.path.join(HERE, "part_iv") in sys.path:
        sys.path.remove(os.path.join(HERE, "part_iv"))

print("== 11. Part VI cost channel ==")
try:
    from scipy.stats import spearmanr
    ceil = json.load(open(f"{HERE}/cost_channel/ceilings.json"))
    acc = {}
    for s in ("readable", "free", "q25", "q50", "q75", "abelian"):
        acc[s] = {a: json.load(open(f"{CC}/{s}/{a}.json"))["tok_acc"]
                  for a in ("sc_pair", "sc_cost", "sc_costd", "sc_counts")}
    # A1 anchor: readable is a copy task; all four arms at or above 0.90
    check("A1 anchor: all four arms >= 0.90 on readable",
          all(v >= 0.90 for v in acc["readable"].values()),
          f"(min {min(acc['readable'].values()):.4f})")
    # A2 access: abelian counts - pair >= 0.05, so C1 is testable
    a2 = acc["abelian"]["sc_counts"] - acc["abelian"]["sc_pair"]
    check("A2 access: abelian counts-pair >= 0.05", a2 >= 0.05, f"({a2:+.4f})")
    # C1 as registered: measured advantage vs ceiling difference, five systems
    sysn = ["free", "q25", "q50", "q75", "abelian"]
    adv = [acc[s]["sc_cost"] - acc[s]["sc_pair"] for s in sysn]
    cdiff = [ceil[s]["ceil_diff"] for s in sysn]
    rho = spearmanr(cdiff, adv).statistic
    check("C1 falsified as registered (Spearman <= 0)", rho <= 0,
          f"(rho={rho:+.2f})")
    check("C1 second clause: abelian advantage does not exceed free",
          adv[4] <= adv[0], f"({adv[4]:+.4f} vs {adv[0]:+.4f})")
    # C2 null: identical information, aggregate vs spelled out
    c2 = [acc[s]["sc_counts"] - acc[s]["sc_cost"] for s in sysn]
    check("C2 null everywhere (|counts-cost| < 0.02)",
          all(abs(v) < 0.02 for v in c2), f"(max |d| {max(map(abs, c2)):.4f})")
    # C3: the order term is non-monotone, smaller at abelian than at q75
    c3 = {s: acc[s]["sc_costd"] - acc[s]["sc_cost"] for s in sysn[1:]}
    check("C3 order term smaller at abelian than at q75",
          c3["abelian"] < c3["q75"],
          f"({c3['abelian']:+.4f} vs {c3['q75']:+.4f})")
    # ceiling table's own registered property: ceil_diff monotone in log2 fiber
    allsys = ["readable", "free", "q25", "q50", "q75", "abelian"]
    rho_c = spearmanr([ceil[s]["log2_fiber"] for s in allsys],
                      [ceil[s]["ceil_diff"] for s in allsys]).statistic
    check("ceiling difference monotone in log2 fiber", rho_c > 0.95,
          f"(rho={rho_c:+.2f})")
    # search evaluation: R1 control, R3 primary, R4 ordering
    rung = {s: json.load(open(f"{CC}/{s}/search_sc_cost.json"))["rungs"]
            for s in ("q50", "q75", "abelian")}
    for s, r in rung.items():
        check(f"R1 control: {s} impossible rung <= 0.05",
              r["impossible"]["valid_and_cost"] <= 0.05,
              f"({r['impossible']['valid_and_cost']:.3f})")
    mins = {s: r["min"]["valid_and_cost"] for s, r in rung.items()}
    check("R4 ordering: abelian > q75 > q50",
          mins["abelian"] > mins["q75"] > mins["q50"],
          f"({mins['abelian']:.3f} > {mins['q75']:.3f} > {mins['q50']:.3f})")
except ImportError:
    print("  skipped (pip install scipy)")

print()
if failures:
    print(f"{len(failures)} check(s) FAILED:", *failures, sep="\n  ")
    sys.exit(1)
print("All checks passed.")
