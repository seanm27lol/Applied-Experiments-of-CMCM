# Pre-registration: verification vs generation (DRAFT, uncommitted)
# This file commits ONLY after the V0' audit numbers are entered below.

## Question
Part V showed the trace arm's GENERATION advantage is structural: not
purchasable with endpoint data across a 32x budget (+0.083 at N=4000,
p=1e-13). Does that advantage transfer to CHECKING a witness, the Valid
predicate of WitnessRecoverability.lean? If not, trace supervision
transfers search ability specifically, an empirical dissociation along
the search/verification asymmetry. If yes, it transfers a general
state-tactic correspondence. Both branches are interpretable.

## Design
Eval: 600 instances (300 valid + 300 stratified negatives) on the Part
III held-out stems. Negatives swap ONLY the tactic (S1-S4) or ONLY the
after-state (S5); labels rest on exact-after mismatch, near-certain
without execution. Goal-closing steps (131/300, 44%) are excluded as
tactic-swap targets because a coincidentally-closing swapped tactic
reproduces 'no goals' and silently mislabels; they serve as S5 targets.
Strata: S1 surface (n=43), S2 camouflaged (42+18 fallback), S3
same-proof (24), S4 in-context corruption (27+15 fallback), S5
after-swap (131). Scoring: single forward pass, logprob margin of the
single tokens ' yes' vs ' no' (asserted single-token). Training
negatives: same generator, same filter, TRAIN theorems only, identical
examples per (N, seed) across arms. Arms: pw_trace, pw_pair, pw_shuffle
stage-1 checkpoints reused. Budgets: 250, 1000, 4000. Seed 0.

## V0' label audit (two-tier), TO BE FILLED BEFORE COMMIT
Tier 1 (semantic strata): 15-item random samples of S2, S3, S4, audited
by hand. Retain a stratum iff mislabels <= 2/15.
Tier 2 (machine-confident): 8-item samples of S1 and S5. Pass iff
mislabels <= 1/16 pooled; else the confidence tiering is invalid and
tier-1-style audits extend to all strata.
  S2: 0/15   S3: 1/15   S4: 1/15   S1: 0/8   S5: 0/8
Fallback items (S2f/S4f) inherit their sheet's verdict.

## Predictions
V1 anchor: every arm >= 0.90 on S1 at N=4000. Fail -> one registered
   retry with verdict-masked loss; still fail -> stop, uninterpretable.
V2 floor: best arm >= 0.60 on S3 at N=4000, else S3/S4 are declared
   undecidable-without-execution and interpretation restricts to
   surviving strata.
V3 primary, at N=4000 on pooled surviving hard strata (S2-S5):
   equivalence branch: |trace - pair| <= 0.03 with 95% CI within
   +/-0.05  => checking gap absent while the generation gap on the same
   stems is present => trace supervision transfers search, not checking.
   transfer branch: (trace - pair) >= +0.05 with p < 0.05 => general
   correspondence transfer; dissociation rejected.
   Middle zone => indeterminate, reported as such.
V4 secondary: if a verification gap exists, direction of its budget
   trend across 250/1000/4000 (no magnitude committed).
V5 exploratory: pw_shuffle >= pw_pair on verification (its stage-1
   corpus is a corpus of invalid triples). Direction only.

## Known limitations, stated in advance
Residual label noise bounded by V0', not eliminated; verification here
is LM plausibility-judgment approximating the formal Valid predicate,
not kernel checking; S3 negatives expose same-theorem tactic text from
held-out proofs (labelled invalid here, gold elsewhere; both labels
drawn from the same proofs, so no exploitable direction); single seed;
fallback strata (S2f, S4f) reported separately.

## V0' verdict, 2026-07-26
S2 0/15, S3 1/15, S4 1/15, S1 0/8, S5 0/8. All strata retained under the
registered bounds. The two flagged negatives (S3 idx 268, S4 idx 310)
are excluded from verif_eval.jsonl; their paired valid instances remain.
Eval size: 598.
