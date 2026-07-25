# Pre-registration: Part V, is the trace advantage a data-efficiency effect?

Commit before running. Deviations get dated lines at the bottom.

## Why this replaces the Part IV synthetic design

Part IV proposed a synthetic task whose witness-fiber size could be dialled
exactly, predicting that the supervision gap would grow with fiber. Its
pre-registered sanity check (P4c) failed on the first condition: every arm
scored at chance (0.121 to 0.161 against a chance level of 0.125) because
the state was rendered as a binary string and the model could not decode
nibbles. Per that registration, no other Part IV prediction may be
interpreted, and the sweep was stopped.

Working through the failure exposed a deeper problem than the encoding.
The gap must vanish at both ends of the fiber axis: at fiber 1 the inverse
is learnable and stage 2 alone teaches both arms, and at very large fiber
the witness is not determined by the endpoints, so no arm can exceed a
near-chance ceiling. Normalising by that ceiling does not help, because
the ceiling approaches chance as fiber grows. The synthetic design also
tests function inversion, whereas Part III measured distributional
learning. Part IV is therefore retired as an experiment. Its formal
content (WitnessRecoverability.lean, kernel-checked, and fiber.py) is
retained as a definition of recoverability, not as evidence for it.

## Question

Part III found pw_trace beats pw_pair by +0.024 to +0.050 across seeds
(p < 0.05 in all three), with roughly 76% of that attributable to witness
content rather than format exposure. The mechanism is untested. Two
candidates:

  Data efficiency. The pair arm never sees witness tokens in stage 1, so
  it must learn the witness vocabulary and distribution from stage 2
  alone. Enough stage-2 data should erase the difference.

  Structural transfer. Stage-1 trace exposure conveys something about the
  state-to-tactic correspondence that endpoint data cannot supply at any
  stage-2 budget.

These make opposite predictions about how the gap behaves as the stage-2
budget grows.

## Design

Domain and data unchanged from Part III: LeanDojo mathlib4 tactic steps,
same corpora, same held-out theorems, same metrics.

Stage 1 is trained ONCE per arm and reused, so the only thing varying is
the stage-2 budget. Stage-2 draws are nested: the N=125 set is a prefix of
the N=250 set and so on, and for a given (N, seed) every arm sees
identical examples in identical order. Verified before registration.

Budgets N: 125, 250, 500, 1000, 2000, 4000. Arms: pw_trace and pw_pair
(the two that define the gap). Seed 0 for the registered run; seeds 1 and
2 as replicates if the primary result warrants them.

Metric: sim_minus_echo, as in Part III. Gap := pw_trace minus pw_pair,
paired per item.

Note that N=2000 approximately reproduces the Part III condition. Two
known sources of slack, stated before running: Part III drew its stage-2
set with random.sample while this design uses shuffle-then-prefix to make
budgets nested, so the N=2000 subset differs from Part III's subset of the
same pool; and stage 1 runs as a separate process here, so the torch RNG
state entering stage 2 differs, perturbing batch order. Both are
seed-level noise. The anchor check is therefore distributional, not
exact.

Small-N caveat, stated before running: at N=125 stage 2 is roughly four
optimizer steps, so the smallest budgets carry high variance. All six
points enter the regression regardless.

## Predictions

P5a (primary): the gap decreases with log2 N. Regression slope negative
     with p < 0.05.
P5b: at N=4000 the gap is below +0.02 and no longer significant at
     p < 0.05.
P5c (anchor): at N=2000 the gap falls within +/-0.025 of the Part III
     seed-0 value of +0.054. The tolerance reflects the two slack sources
     above plus Part III's own cross-seed spread (C1 sd 0.013).

## Falsification and interpretation

If P5a and P5b both hold, the trace advantage is a data-efficiency effect:
stage-1 witness exposure substitutes for stage-2 examples, and enough of
the latter erases it. This would mean the Part I versus Part III contrast
reflects how much stage-2 data each domain effectively needs, not an
information-theoretic property of the domains, and the recoverability
framing must be withdrawn from the paper's thesis rather than softened.

If P5a fails, with a flat or positive slope, the gap survives arbitrary
stage-2 budgets and something structural is being transferred. That
supports the recoverability framing but does not establish it, since this
experiment does not vary recoverability.

If P5a holds but P5b fails, with a declining but still significant gap at
N=4000, both mechanisms are contributing, and the extrapolated
zero-crossing should be reported with the caveat that it is an
extrapolation beyond the tested range.

If P5c fails, stop and resolve before interpreting anything else.

Conditional secondary, registered now: if the gap at N=4000 remains
significant at p < 0.05 (P5b fails), run pw_shuffle stage 1 and one
N=4000 fine-tune, and decompose the surviving gap into content
(trace minus shuffle) and format (shuffle minus pair), as Part III did.
No numeric prediction is committed for the decomposition.

## Protocol

EleutherAI/pythia-160m, fp32, lr1 5e-5 (stage 1), lr2 2e-5 (stage 2),
same as Part III. Stage-1 checkpoints are reused across all budgets, so
any stage-1 rerun invalidates every downstream point and must be noted.
