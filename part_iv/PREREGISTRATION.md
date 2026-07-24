# Pre-registration: Part IV, does witness information predict the supervision gap

Commit before running any training. Do not edit afterwards; deviations get
dated lines at the bottom.

## Relation to existing work

Trace-versus-endpoint supervision is a well studied area under the name
process versus outcome supervision. Lightman et al. (2023) found process
supervision substantially outperformed outcome supervision on competition
mathematics; Uesato et al. (2022) reported related findings; earlier work
found the two comparable on easier grade-school problems. There is also
recent theory: an ICML 2025 result argues that under standard coverage
assumptions, outcome supervision is no more statistically difficult than
process supervision up to polynomial factors in horizon.

Parts I and III of this project are therefore not novel as a phenomenon.
They are a small-scale rediscovery: Part I found no benefit where the
witness is cheaply recoverable from endpoints (code diffs), Part III found
a large benefit where it is not (Lean tactic steps).

What is not supplied by that literature, as far as this project can
determine, is a quantity computable from a dataset before any training
that predicts how large the benefit will be. Part IV tests one candidate.

## The candidate quantity

Formalised in `WitnessRecoverability.lean` (kernel-checked, no sorries, no
custom axioms). A witnessed transformation is a triple (source, witness,
target). Forgetting the witness gives an endpoint pair. Recoverability is
faithfulness of that forgetful map. The quantitative version is the fiber:
the number of witnesses sharing an endpoint pair. Fiber 1 means the
endpoints determine the witness. The Lean file proves the free system is
faithful, proves commuting involutions are not, and computes fibers for
concrete small systems, matching `fiber.py`.

## Design

Six conditions, each with 8 operations on a 28-bit state and witness
length L=6. Vocabulary size, witness length, state representation, output
length and operation names are identical across conditions; operation
names are opaque (OP0..OP7) so no structure leaks through labels. Only the
algebra of the operations differs. Fiber sizes are computed exactly by
exhaustive enumeration of all 8^6 = 262,144 witnesses, not estimated:

  readable    mean fiber 1.00   log2 0.00    (state contains the witness)
  free        mean fiber 1.00   log2 0.00    (fiber 1 but hard to invert)
  q25         mean fiber 2.8    log2 1.51
  q50         mean fiber 29.7   log2 4.89
  q75         mean fiber 349.1  log2 8.45
  abelian     mean fiber 2581.0 log2 11.33

Four arms per condition, matched character budget, identical stage-2
finetune: sy_trace (start + witness + end), sy_pair (start + end),
sy_endpoint (end only), sy_shuffle (start + a real but wrong witness +
end, the format-exposure control that Part III showed was necessary).

Primary metric: token accuracy over the six operation slots. Chance is
0.125. The witness alphabet is disjoint from the state alphabet, so
copying the input cannot beat chance and no echo correction is required.

Supervision gap := token accuracy of sy_trace minus sy_pair, paired per
item.

## Predictions

P4a (primary): across the five fiber-varying conditions (free, q25, q50,
    q75, abelian), the supervision gap increases with log2 mean fiber.
    Regression slope positive with p < 0.05 and r^2 >= 0.5.

P4b: `readable` and `free` have identical fiber (1.00) but differ in
    whether the witness can be computed from the endpoints. Prediction:
    gap(free) exceeds gap(readable) by at least 0.05. If so, information
    and computation are separate axes and fiber size alone is an
    incomplete predictor, which must be stated as a limitation of the
    quantity rather than buried.

P4c: on `readable`, all four arms exceed 0.80 token accuracy and the gap
    is below 0.05 in absolute value. This is the sanity anchor: where the
    end state literally contains the witness, supervision format should
    not matter.

P4d: in the two highest-fiber conditions, the content share of the gap
    (trace minus shuffle, divided by trace minus pair) exceeds 50%, as it
    did in Part III (73%).

## Falsification

If P4a fails, with a null or negative slope, then fiber size does not
predict the supervision gap, and the recoverability explanation for the
Part I versus Part III contrast is wrong. Those two domains differ in
dataset, task, difficulty and absolute performance as well as
recoverability, and a null here means the contrast should be reported as
an unexplained difference between two domains rather than as evidence for
a mechanism. The paper's thesis would have to be rewritten, not softened.

If P4c fails, the pipeline is not measuring what it should and no other
prediction in this file may be interpreted until that is resolved.

## External validation, reported but not predicted

After the synthetic curve is fitted, Part I (code diffs) and Part III
(Lean tactic steps) will be placed on it. Their fiber sizes are not
exactly computable, so an estimate and its method will be reported with
explicit uncertainty. This is illustrative, not a test.

## Protocol

Model EleutherAI/pythia-160m, fp32, lr1 5e-5, lr2 2e-5, seed 0 for the
registered run, seeds 1 and 2 as replicates. Conditions may be run in any
order. No metric definitions change after this commit. If a run diverges,
the fix and rerun are both reported, as in Part III.
