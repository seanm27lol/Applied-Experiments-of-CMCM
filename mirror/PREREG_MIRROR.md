# Pre-registration: hardware-native verification of equality witnesses

Commit before submitting any hardware job. Do not edit after.

## Question
The pair-equality witnesses (baseline B == optimized O) have only been
checked in software (pyzx). This experiment makes the hardware perform
the check: if B == O then B . O^-1 == I, so the composed circuit must
return |0...0> up to a tracked Pauli frame. No classical simulation of
outputs is required, which is exactly the regime where simulation-based
scoring stops scaling.

## Design
For each registered pair p in {mod5_4, tof_3, barenco_tof_3, mod_mult_55}:
  TRUE mirror:     X(x) . B_p . O_p^-1 on a random input |x> (seeded,
                   recorded); barriers so the transpiler cannot cancel
                   the halves. A true mirror must return exactly x.
  DERANGED mirror: X(x) . B_p . O_q^-1 with q != p; x is redrawn until
                   the ideal output differs from x (guards against inputs
                   that are accidental fixed points of the composition).
  Design note (pre-submission iteration, recorded honestly): the first
  draft placed a random Pauli layer at the JOINT. Check mode caught that
  this is wrong for non-Clifford circuits: the layer conjugates through
  B, so the expected string requires simulation to compute, defeating
  the protocol. Randomized inputs give the same protection against
  transpiler/coherent cancellation with a simulation-free expectation.
Padding: when B_p and O_q act on different qubit counts, the smaller
circuit acts on the first qubits of the larger register.
Metric: return probability r = P(measuring exactly x), 8192 shots, all circuits in ONE interleaved job,
optimization_level=1, seed_transpiler=7, on ibm_fez or the best
available Heron backend.

## Predictions (committed before submission)
M1: every TRUE mirror has r >= 0.25, and ordered contrast holds:
    r(true_p) > r(deranged_p) + 0.3 for every pair.
M2: point predictions for TRUE mirrors from the product of the July 18
    arm fidelities (r_pred = F_base(p) * F_opt(p)), tolerance +-0.15:
      tof_3          0.88
      barenco_tof_3  0.85
      mod5_4         0.77
      mod_mult_55    0.50
M3: every DERANGED mirror has r <= 0.15.
Falsification: any true mirror with r < 0.25, or any deranged mirror
with r > 0.3, means either a witness is wrong on hardware-relevant
terms or the protocol (barrier/Pauli frame) is broken; investigate
before any claim.

## Notes
Input randomization seed: 2026. Deviations get dated notes below.
