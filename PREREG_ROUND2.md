# Pre-registration: three follow-up runs (commit before any of them)

## R1. Dynamical-decoupling mirror rerun

Question: the mirror run undershot every M2 point prediction by 0.23 to
0.35, uniformly, and transpiled 2q counts do not explain it (mirror cost
is within +-15% of the sum of its arms). Post-hoc hypothesis from the
2026-07-24 session: the Part II per-arm fidelities were measured by
computational-basis histogram comparison, which is blind to phase errors
that do not change the output bitstring; a mirror never measures the
intermediate state, so mid-circuit Z errors propagate through O^-1 and
become visible. If the dominant hidden channel is dephasing during idle
time, suppressing it should raise the return probability.

Run: identical eight circuits, same seed, XY4 dynamical decoupling on
idle qubits, one interleaved job, 8192 shots.

R1a: every TRUE mirror return probability rises by at least +0.03
     relative to the no-DD run (all four, same direction).
R1b: mean rise across the four TRUE mirrors is at least +0.05.
R1c: DERANGED mirrors stay below 0.15 (DD must not manufacture signal).
Falsification: if TRUE mirrors do not rise, or rise in mixed directions,
the idle-dephasing form of the hypothesis is wrong. The metric-blindness
hypothesis would remain untested by this run and must be labelled as
such, not quietly retained.

## R2. Phase-2 transpile-seed rerun (mod_mult_55, seed 11)

Question: the registered mod_mult_55 run used seed_transpiler=7, which a
20-seed sweep later showed gave the optimized arm its worst routing of
all twenty (117 2q; min 102, median 112.5) while the baseline drew near
best (99; min 96). Seed 11 gives the optimized arm 102 2q and depth 190.

Run: qhw_seed.py --mode hw --pair mod_mult_55 --seed 11 --tag _seed11.

R2a: delta_fidelity exceeds the registered +0.067.
R2b: it does not exceed +0.15 (routing is not the whole story; the depth
     advantage was already doing most of the work).
Falsification / informative null: if the delta does NOT grow, routing
was not the mechanism and the duration reading strengthens, since the
optimized arm wins on depth regardless of its 2q count.

## R3. Multi-seed replication of Part III

Question: all four Part III arms ran a single training seed (0). The
reported effects (P1 +0.054 p=3e-13; C1 +0.039 p=1.4e-05; C2 +0.015
p=3.3e-05) are point estimates with no variance.

Run: seeds 1 and 2 for all four arms, identical data and protocol.

R3a: C1 remains positive with p < 0.05 in every seed.
R3b: across-seed standard deviation of the C1 mean delta is below 0.02.
R3c: P2 remains null (p > 0.05) in every seed.
Falsification: if C1 flips sign or loses significance in any seed, the
Part III content claim is seed-dependent and must be reported as such,
with the multi-seed range replacing the single-seed point estimate as
the headline.

## Notes
Committed before running any of R1, R2, R3. Deviations get dated lines
below. No metric definitions change from the original registrations.

## Verdicts, 2026-07-24

R1 (DD mirror, cross-job):
  R1a FAILED. True mirror deltas were mixed in sign, not all >= +0.03:
      mod5_4 -0.033, tof_3 +0.089, barenco +0.055, mod_mult_55 -0.115.
  R1b FAILED. Mean change -0.001, not >= +0.05.
  R1c CONFIRMED. Deranged mirrors max 0.086, under 0.15.

  Design error. DD and no-DD were separate jobs five hours apart
  (d9hq08shonhs73adf2ag at 13:25, d9hua4khonhs73adloe0 at 18:20). Part II
  interleaves compared conditions in one job precisely so that drift
  cannot masquerade as an effect, and this run did not follow that
  protocol. R1' repeats it correctly. The verdicts above stand as
  recorded but the run does not isolate a DD effect.

R2 (seed-11 rerun):
  R2a CONFIRMED. delta_fidelity +0.171 exceeds the registered +0.067.
  R2b FAILED. +0.171 also exceeds the +0.15 bound.

  Design error. seed_transpiler changes the layout, not only the routing.
  Arms landed on disjoint physical qubits (0/9 overlap) where the
  2026-07-18 runs shared 5/5, 5/5, 4/5 and 7/9. The +0.171 therefore
  compares two different qubit sets and is not comparable to +0.067.
  Execution-time calibration shows device CZ error barely moved
  (2.11e-3 to 2.26e-3), so the drop in both arms is placement, not
  calibration. R2' repeats it with placement controlled.

## Verdicts, 2026-07-24

R1 (DD mirror, cross-job):
  R1a FAILED. True mirror deltas were mixed in sign, not all >= +0.03:
      mod5_4 -0.033, tof_3 +0.089, barenco +0.055, mod_mult_55 -0.115.
  R1b FAILED. Mean change -0.001, not >= +0.05.
  R1c CONFIRMED. Deranged mirrors max 0.086, under 0.15.

  Design error. DD and no-DD were separate jobs five hours apart
  (d9hq08shonhs73adf2ag at 13:25, d9hua4khonhs73adloe0 at 18:20). Part II
  interleaves compared conditions in one job precisely so that drift
  cannot masquerade as an effect, and this run did not follow that
  protocol. R1' repeats it correctly. The verdicts above stand as
  recorded but the run does not isolate a DD effect.

R2 (seed-11 rerun):
  R2a CONFIRMED. delta_fidelity +0.171 exceeds the registered +0.067.
  R2b FAILED. +0.171 also exceeds the +0.15 bound.

  Design error. seed_transpiler changes the layout, not only the routing.
  Arms landed on disjoint physical qubits (0/9 overlap) where the
  2026-07-18 runs shared 5/5, 5/5, 4/5 and 7/9. The +0.171 therefore
  compares two different qubit sets and is not comparable to +0.067.
  Execution-time calibration shows device CZ error barely moved
  (2.11e-3 to 2.26e-3), so the drop in both arms is placement, not
  calibration. R2' repeats it with placement controlled.

## Verdicts, 2026-07-24

R1 (DD mirror, cross-job):
  R1a FAILED. True mirror deltas were mixed in sign, not all >= +0.03:
      mod5_4 -0.033, tof_3 +0.089, barenco +0.055, mod_mult_55 -0.115.
  R1b FAILED. Mean change -0.001, not >= +0.05.
  R1c CONFIRMED. Deranged mirrors max 0.086, under 0.15.

  Design error. DD and no-DD were separate jobs five hours apart
  (d9hq08shonhs73adf2ag at 13:25, d9hua4khonhs73adloe0 at 18:20). Part II
  interleaves compared conditions in one job precisely so that drift
  cannot masquerade as an effect, and this run did not follow that
  protocol. R1' repeats it correctly. The verdicts above stand as
  recorded but the run does not isolate a DD effect.

R2 (seed-11 rerun):
  R2a CONFIRMED. delta_fidelity +0.171 exceeds the registered +0.067.
  R2b FAILED. +0.171 also exceeds the +0.15 bound.

  Design error. seed_transpiler changes the layout, not only the routing.
  Arms landed on disjoint physical qubits (0/9 overlap) where the
  2026-07-18 runs shared 5/5, 5/5, 4/5 and 7/9. The +0.171 therefore
  compares two different qubit sets and is not comparable to +0.067.
  Execution-time calibration shows device CZ error barely moved
  (2.11e-3 to 2.26e-3), so the drop in both arms is placement, not
  calibration. R2' repeats it with placement controlled.
