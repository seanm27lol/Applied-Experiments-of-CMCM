# Pre-registration: R1' and R2', drift- and placement-controlled reruns

Commit before submitting either job. Both correct design errors found in
the 2026-07-24 round-2 runs, which are recorded in PREREG_ROUND2.md and
are not withdrawn: their verdicts stand as measured, but neither isolated
the variable it was meant to isolate.

## R1'. Dynamical decoupling, drift-controlled

Design error in R1: DD and no-DD were separate jobs five hours apart, so
device drift and DD effect are inseparable. Part II's own protocol puts
compared conditions in one interleaved job; R1 did not follow it.

Fix: DD applied as a transpiler pass (XX sequence, native X gates) so all
sixteen circuits (eight mirrors x {no-DD, DD}) go in ONE job.

R1'a: mean paired delta (dd minus nodd) across the four TRUE mirrors is
      positive.
R1'b: all four TRUE mirror deltas share the same sign.
R1'c: DERANGED mirrors stay below 0.15 under DD.
Falsification: if R1'b fails, DD's effect is circuit-dependent rather
      than a uniform suppression of an idle-dephasing channel, and the
      idle-dephasing explanation for the mirror undershoot is rejected
      for this circuit family. If R1'a is negative, DD costs more than it
      saves at this scale and that is the reportable result.
No prediction is committed on magnitude: R1's magnitudes were confounded
and are not a usable prior.

## R2'. Compilation delta at matched placement

Design error in R2: seed_transpiler changes the LAYOUT, not only the
routing. The seed-11 job placed the two arms on disjoint physical qubits
(0/9 overlap, versus 7/9 on 2026-07-18), so its +0.171 delta compares two
different qubit sets. The registered +0.067 and the +0.171 are therefore
not comparable measurements.

Fix: both arms pinned to one shared layout
[141, 123, 143, 145, 124, 144, 136, 142, 140], chosen by search over
layouts the transpiler itself selects, serving both arms at cost close to
free transpilation (baseline 99 2q, optimized 102 2q). All circuits in
ONE job.

Circuits: baseline@seed1, optimized@seed1 (primary pair),
          optimized@seed6 (114 2q, worse routing, same layout).

R2'a: delta_matched_layout is positive.
R2'b: delta_matched_layout lies between +0.03 and +0.13, i.e. closer to
      the registered +0.067 than to the placement-confounded +0.171.
R2'c: routing_effect (optimized seed6 minus seed1) is negative, since
      seed 6 costs 12 more 2q gates and 18 more depth on identical
      qubits.
Falsification: if R2'b fails high (delta above +0.13 at matched
      placement), placement was NOT the explanation for the +0.171 and
      that must be stated; the round-2 confound analysis would then be
      wrong about the cause even though the confound is real. If R2'a
      fails, the compilation advantage does not survive placement
      control, which would materially weaken Part II's central claim and
      must be reported as such.

## Notes
Neither run is permitted to replace a previously registered result. The
2026-07-18 +0.067 remains the registered Part II figure; these are
follow-ups reported alongside it. Deviations get dated lines below.

## Verdicts, 2026-07-24

R1' (DD, interleaved, job d9hupjt0k0jc738iqq5g):
  R1'a FAILED. Mean paired delta across true mirrors -0.0355, negative.
  R1'b CONFIRMED. All four true mirror deltas share a sign (negative):
      mod5_4 -0.0763, tof_3 -0.0223, barenco -0.0046, mod_mult_55 -0.0388.
  R1'c CONFIRMED. Deranged max 0.0695, under 0.15.

  Result: XY-style DD (XX sequence, native X gates) is uniformly harmful
  for this circuit family at this scale. The added pulses, 80 to 225 per
  circuit, cost more error than the idle dephasing they suppress. Per the
  falsification clause, the idle-dephasing explanation for the mirror
  undershoot is rejected. The metric-blindness hypothesis remains
  UNTESTED by any run so far and is not carried forward as supported.

  R1 got two of four signs wrong. tof_3 read +0.089 across jobs and
  -0.022 within one job; barenco read +0.055 and -0.005. Both apparent
  improvements were drift.

  Drift measured directly, same circuits, same no-DD condition, different
  jobs: mod5_4 0.532 to 0.620, tof_3 0.531 to 0.692, barenco 0.509 to
  0.595, mod_mult_55 0.267 to 0.270. Up to +0.161 over five hours, and
  +0.027 to +0.079 over the thirty-two minutes between the 18:20 and
  18:52 jobs. Both exceed most effects measured in this repository,
  including the registered +0.067. Any cross-job comparison in this work
  is therefore uninterpretable.

  Caveat on the calibration file: ceilings recorded for the DD arms in
  calibration_d9hupjt0k0jc738iqq5g.json are artifacts. DD pads idle
  qubits across the full device register, so the qubit-extraction step
  counts all 156 qubits and the readout product collapses the ceiling to
  0.039. The no-DD arms' ceilings are valid; the DD arms' are not and
  must not be used.

R2' (matched layout, job d9huqq4honhs73admhag):
  R2'a CONFIRMED. delta_matched_layout +0.0604, positive.
  R2'b CONFIRMED. +0.0604 lies in [+0.03, +0.13], close to the
      registered +0.067 rather than the placement-confounded +0.171.
  R2'c CONFIRMED. routing_effect -0.1346, negative.

  Result: the registered Part II figure replicates under stricter
  control. Six days later, same nine physical qubits for both arms, one
  interleaved job, the compilation advantage measures +0.060 against
  +0.067. The +0.171 was placement.

  The routing arm is the most tightly controlled measurement in this
  work: identical physical qubits, identical job, identical logical
  circuit, only SWAP insertion differs. Seed 6 costs 12 more two-qubit
  gates and 18 more depth than seed 1 and loses 0.135 fidelity.
  Execution-time calibration shows seed 6 also routes through
  worse-quality edges (mean CZ 5.38e-3 versus 4.63e-3), so the ceiling
  model, which accounts for both gate count and edge quality, predicts a
  drop of 0.077 (ceiling 0.580 to 0.503). That leaves roughly 0.058
  unexplained by gate quality or count, tracking depth. An earlier
  informal estimate in the working session put the unexplained share far
  higher by using the wrong CZ error; this corrected figure supersedes it.

  Device state: CZ errors on these qubits were 4.48e-3 to 5.38e-3, more
  than double the 2.11e-3 recorded on 2026-07-18. All three arms measured
  above their calibration ceilings (107%, 121%, 112%), consistent with
  the known conservatism of RB-derived ceilings for computational-basis
  outputs.

## Verdicts, 2026-07-24

R1' (DD, interleaved, job d9hupjt0k0jc738iqq5g):
  R1'a FAILED. Mean paired delta across true mirrors -0.0355, negative.
  R1'b CONFIRMED. All four true mirror deltas share a sign (negative):
      mod5_4 -0.0763, tof_3 -0.0223, barenco -0.0046, mod_mult_55 -0.0388.
  R1'c CONFIRMED. Deranged max 0.0695, under 0.15.

  Result: XY-style DD (XX sequence, native X gates) is uniformly harmful
  for this circuit family at this scale. The added pulses, 80 to 225 per
  circuit, cost more error than the idle dephasing they suppress. Per the
  falsification clause, the idle-dephasing explanation for the mirror
  undershoot is rejected. The metric-blindness hypothesis remains
  UNTESTED by any run so far and is not carried forward as supported.

  R1 got two of four signs wrong. tof_3 read +0.089 across jobs and
  -0.022 within one job; barenco read +0.055 and -0.005. Both apparent
  improvements were drift.

  Drift measured directly, same circuits, same no-DD condition, different
  jobs: mod5_4 0.532 to 0.620, tof_3 0.531 to 0.692, barenco 0.509 to
  0.595, mod_mult_55 0.267 to 0.270. Up to +0.161 over five hours, and
  +0.027 to +0.079 over the thirty-two minutes between the 18:20 and
  18:52 jobs. Both exceed most effects measured in this repository,
  including the registered +0.067. Any cross-job comparison in this work
  is therefore uninterpretable.

  Caveat on the calibration file: ceilings recorded for the DD arms in
  calibration_d9hupjt0k0jc738iqq5g.json are artifacts. DD pads idle
  qubits across the full device register, so the qubit-extraction step
  counts all 156 qubits and the readout product collapses the ceiling to
  0.039. The no-DD arms' ceilings are valid; the DD arms' are not and
  must not be used.

R2' (matched layout, job d9huqq4honhs73admhag):
  R2'a CONFIRMED. delta_matched_layout +0.0604, positive.
  R2'b CONFIRMED. +0.0604 lies in [+0.03, +0.13], close to the
      registered +0.067 rather than the placement-confounded +0.171.
  R2'c CONFIRMED. routing_effect -0.1346, negative.

  Result: the registered Part II figure replicates under stricter
  control. Six days later, same nine physical qubits for both arms, one
  interleaved job, the compilation advantage measures +0.060 against
  +0.067. The +0.171 was placement.

  The routing arm is the most tightly controlled measurement in this
  work: identical physical qubits, identical job, identical logical
  circuit, only SWAP insertion differs. Seed 6 costs 12 more two-qubit
  gates and 18 more depth than seed 1 and loses 0.135 fidelity.
  Execution-time calibration shows seed 6 also routes through
  worse-quality edges (mean CZ 5.38e-3 versus 4.63e-3), so the ceiling
  model, which accounts for both gate count and edge quality, predicts a
  drop of 0.077 (ceiling 0.580 to 0.503). That leaves roughly 0.058
  unexplained by gate quality or count, tracking depth. An earlier
  informal estimate in the working session put the unexplained share far
  higher by using the wrong CZ error; this corrected figure supersedes it.

  Device state: CZ errors on these qubits were 4.48e-3 to 5.38e-3, more
  than double the 2.11e-3 recorded on 2026-07-18. All three arms measured
  above their calibration ceilings (107%, 121%, 112%), consistent with
  the known conservatism of RB-derived ceilings for computational-basis
  outputs.
