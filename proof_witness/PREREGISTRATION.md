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
## Deviation note, 2026-07-23
First training attempt diverged (NaN gradients from step ~50). Fixes:
fp32 instead of bf16, mean_resizing=False on token embedding resize,
lr1 3e-4 -> 5e-5, lr2 1e-4 -> 2e-5, warmup 3%, empty-doc filter, and a
finite-weights assertion after each stage. Plumbing only: arms, data,
metrics, and predictions unchanged.
