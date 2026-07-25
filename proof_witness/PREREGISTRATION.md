# Pre-registration: witness supervision vs witness recoverability (Part III)

Commit this file BEFORE running train.py on real data. Do not edit after.

## Question
Part I found diff supervision adds nothing over (before, after) pairing for
code edits. Hypothesis: that held because the witness (a diff) is cheaply
recoverable from the endpoints (edit distance is polynomial). In domains
where recovering the witness from endpoints is hard, explicit witness
supervision should retain an advantage. Lean tactic steps are such a domain:
given goal states (before, after), reconstructing the tactic is search;
checking it is cheap. This is the search/verification asymmetry that defines
NP, used as an experimental variable.

## Design
Data: LeanDojo benchmark 4 (mathlib4 tactic steps), split by theorem name.
Three stage-1 corpora, matched total token budget:
  - pw_trace:    STATE_BEFORE + TACTIC + STATE_AFTER   (full witness)
  - pw_pair:     STATE_BEFORE + STATE_AFTER            (endpoints only)
  - pw_endpoint: STATE_AFTER only
Stage 2 (equal for all arms): small finetune on the eval format
  STATE_BEFORE + STATE_AFTER -> TACTIC.
Eval: predict the tactic on held-out theorems. Metrics: exact match,
normalized similarity, similarity minus echo ceiling (copying any input
substring scores ~0, per the Part I metric lesson).

## Predictions (committed before any real run)
P1: pw_trace beats pw_pair on sim-minus-echo, paired Wilcoxon p < 0.05,
    mean delta >= +0.02. This is the reversal of Part I's null.
P2: pw_pair beats pw_endpoint (the before-state matters here too).
P3 (falsification branch): if pw_trace ~ pw_pair, the recoverability
    hypothesis is wrong: the Part I tie generalizes even to domains with a
    wide search/verification gap, and the complexity framing should be
    dropped from the writeup, not softened.

## Diagnostic (not a prediction)
Report gold-tactic recoverability: fraction of gold tactics appearing as a
substring of the concatenated input states. Expected low (contrast: diffs
in Part I are fully determined by their endpoints).

Model: EleutherAI/pythia-160m unless amended here before running.
Seeds: 0. Eval N: 300. Any deviation gets its own dated note below.

## Addendum, 2026-07-24: shuffle control (committed before running)
Confound in P1: pw_trace alone saw tactic-format text in stage 1, so its
advantage could be format exposure rather than witness content. Control:
pw_shuffle trains on BEFORE + wrong-but-real TACTIC + AFTER (derangement
over training steps). Predictions:
C1: pw_trace beats pw_shuffle on sim_minus_echo, p < 0.05, meanD >= +0.02
    (the advantage is witness CONTENT).
C2: no committed direction for pw_shuffle vs pw_pair; reported as observed.
Falsification: if pw_trace ~ pw_shuffle, P1's effect is format exposure
and the recoverability claim must be withdrawn, not softened.

## Verdicts, 2026-07-24: shuffle control and multi-seed replication

C1 CONFIRMED (seed 0). pw_trace minus pw_shuffle +0.0393, 169-119,
   p=1.39e-05, clearing the +0.02 and p<0.05 thresholds. The P1 advantage
   is witness content, not format exposure.
C2 observed positive (no direction was committed). pw_shuffle minus
   pw_pair +0.0146, 182-107, p=3.29e-05. Format exposure is real.
   Decomposition: C1 + C2 = 0.0539 against P1's +0.0540.

R3 (seeds 0, 1, 2):
  R3a CONFIRMED. C1 positive with p<0.05 in every seed: +0.0393
      (p=1.39e-05), +0.0500 (p=3.32e-09), +0.0240 (p=0.0055).
  R3b CONFIRMED. Across-seed standard deviation of the C1 mean delta
      0.0131, under the 0.02 bound.
  R3c CONFIRMED. P2 remains null in every seed: p=0.604, 0.275, 0.765;
      mean +0.0041, sd 0.0061.
  C2 across seeds: mean +0.0122, sd 0.0046, all p<0.05.
  Content share across seeds: 76%.

  Limitation to carry into any writeup: C1's magnitude ranges +0.024 to
  +0.050 across seeds, a factor of two. Sign and significance are robust;
  magnitude is not. Report the range, not the point estimate.

  Unchanged limitation from the original registration: all arms score
  below the copy baseline in absolute terms (sim_minus_echo negative
  throughout), so this is a valid comparison among models that cannot
  perform the task.

## Verdicts, 2026-07-24: shuffle control and multi-seed replication

C1 CONFIRMED (seed 0). pw_trace minus pw_shuffle +0.0393, 169-119,
   p=1.39e-05, clearing the +0.02 and p<0.05 thresholds. The P1 advantage
   is witness content, not format exposure.
C2 observed positive (no direction was committed). pw_shuffle minus
   pw_pair +0.0146, 182-107, p=3.29e-05. Format exposure is real.
   Decomposition: C1 + C2 = 0.0539 against P1's +0.0540.

R3 (seeds 0, 1, 2):
  R3a CONFIRMED. C1 positive with p<0.05 in every seed: +0.0393
      (p=1.39e-05), +0.0500 (p=3.32e-09), +0.0240 (p=0.0055).
  R3b CONFIRMED. Across-seed standard deviation of the C1 mean delta
      0.0131, under the 0.02 bound.
  R3c CONFIRMED. P2 remains null in every seed: p=0.604, 0.275, 0.765;
      mean +0.0041, sd 0.0061.
  C2 across seeds: mean +0.0122, sd 0.0046, all p<0.05.
  Content share across seeds: 76%.

  Limitation to carry into any writeup: C1's magnitude ranges +0.024 to
  +0.050 across seeds, a factor of two. Sign and significance are robust;
  magnitude is not. Report the range, not the point estimate.

  Unchanged limitation from the original registration: all arms score
  below the copy baseline in absolute terms (sim_minus_echo negative
  throughout), so this is a valid comparison among models that cannot
  perform the task.
