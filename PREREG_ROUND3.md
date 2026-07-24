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
