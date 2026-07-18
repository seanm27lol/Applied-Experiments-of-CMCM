# Two Pre-Registered Experiments: Witness Supervision in Language Model Training, and Verified ZX Compilation on Quantum Hardware

**Date:** 2026-07-18 · **Hardware:** NVIDIA DGX Spark (GB10), IBM `ibm_fez` · **Status:** both experiments complete, verdicts recorded against pre-registered protocols

This report closes out two linked bets. Both ask whether *witness structure* — information that endpoint-oriented pipelines normally throw away — survives transport to a real substrate. In Part I the substrate is gradient descent: does supervising a language model with explicit transformation witnesses (diffs) transfer better than supervising with endpoints? In Part II the substrate is a quantum device: do circuits optimized by machine-verified ZX-calculus rewriting measurably outperform their baselines on real silicon? Both were run under pre-registered protocols, and both came back with answers more precise than a simple yes or no.

---

## Part I — The edit-witness experiment

### Background and the v1 correction

The original protocol registered four predictions. P1: a diff-trained ("witness") arm shows a zero-shot lead when asked to predict edits. P2 (the headline): after a small shared adaptation to the diff task, the witness arm retains a durable advantage over endpoint-trained arms. P3: null on a control comparison. P4: protocol hygiene on both ends.

The v1 run (2026-07-17, Modal, T4) returned an *instructive null*: P1 confirmed, but P2's apparent confirmation dissolved under a skeptical second read — the v1 metric (mean character similarity to the gold diff) rewarded echoing the before-window, and all adapted arms sat at the context-echo ceiling (~0.243), indistinguishable on actual edit content. The v1 failure was a metric design gap: means were saved instead of per-item scores, and the measured quantity conflated copying with editing.

The v2 evaluation (this run) replaces the metric suite with artifact-proof measures computed per item over all 300 test items:

- `sim` — character similarity of generation vs gold diff (the v1 metric, kept for continuity)
- `sim_edit` — similarity on **+/− edit lines only** (context earns nothing)
- `echo_ceiling` — similarity of the *before-window itself* to the gold diff (what pure copying scores)
- `sim_minus_echo` — per-item `sim − echo_ceiling` (the artifact-proof headline)
- `applies` — does the generation's implied pre-image occur contiguously in the before-window
- `sim_applied` — similarity of the generation's implied **after-window** to the gold after-window (echo-resistant, semantic-ish)

### This run: independent local replication (seed 0)

Because the v1 artifacts were confined to a remote workspace, the full pipeline was rebuilt and rerun locally. This is an independent draw, not a re-measurement of v1's checkpoints.

- **Data:** 10,925 single-file edit records mined from the most recent 20,000 commits of `leanprover-community/mathlib4` (shallow clone, 2026-07-18; same window spec as v1, one day of commit drift). Records are date-sorted; the final 5% (~546 records) is the held-out test tail, never trained on; eval scores the first 300.
- **Model:** `EleutherAI/pythia-410m`, LoRA r=16, α=32, dropout 0.05 on `query_key_value`, seq-len 1024, batch 8192 tokens, lr 2e-4, seed 0. bf16 on GB10 (v1 ran fp32 on T4).
- **Stage 1 — three arms, identical data/budget/seed, only the format differs** (20M tokens each):
  - `ck_diff`: `### BEFORE {before} ### DIFF {diff}` — the witness
  - `ck_after`: `### BEFORE {before} ### AFTER {after}` — paired endpoint map
  - `ck_endpoint`: `{after}` alone — endpoint-only LM
- **Stage 2 — the transfer test:** each stage-1 checkpoint adapted on the **diff** format for 1M tokens → `ad_diff`, `ad_after`, `ad_endpoint`.
- **Eval:** all six checkpoints, greedy decoding, 300 test items, v2 metrics.

### Results

| arm | sim (v1) | edit-line sim | echo | sim−echo | applies | implied-after | loss |
|---|---|---|---|---|---|---|---|
| ck_diff | 0.2311 | 0.1634 | 0.2636 | −0.033 | 7.7% | 0.217 | 1.488 |
| ck_after | 0.1455 | 0.0036 | 0.2636 | −0.118 | 6.3% | 0.169 | 1.449 |
| ck_endpoint | 0.0887 | 0.0069 | 0.2636 | −0.175 | 0.7% | 0.065 | 1.444 |
| ad_diff | 0.2184 | **0.1645** | 0.2636 | −0.045 | 9.7% | **0.234** | 1.485 |
| ad_after | 0.2046 | 0.1428 | 0.2636 | −0.059 | 8.0% | 0.225 | 1.442 |
| ad_endpoint | 0.1706 | 0.1202 | 0.2636 | −0.093 | 5.3% | 0.099 | 1.443 |

Edit-line production (zero-shot, stage 1): `ck_diff` emits ≥1 edit line on **95%** of items; `ck_after` 8%; `ck_endpoint` 18%. After adaptation, all arms emit edit lines ≥88% of the time — but `ad_endpoint` over-produces (mean 18.2 lines/item) with 5% applies and 0.099 implied-after: format without content.

Paired per-item tests (Wilcoxon signed-rank, n = 300):

| comparison | metric | mean Δ | wins–losses | p |
|---|---|---|---|---|
| ad_diff − ad_after | sim−echo | +0.014 | 159–140 | 0.152 |
| ad_diff − ad_after | edit-line sim | +0.022 | 159–136 | 0.063 |
| ad_diff − ad_after | implied-after | +0.009 | 151–148 | 0.327 |
| ad_diff − ad_after | applies (McNemar) | — | 25–20 | 0.552 |
| ad_diff − ad_endpoint | sim−echo | +0.048 | 187–113 | <0.001 |
| ad_diff − ad_endpoint | edit-line sim | +0.044 | 185–113 | <0.001 |
| ad_diff − ad_endpoint | implied-after | +0.135 | 242–58 | <0.001 |
| ad_after − ad_endpoint | sim−echo | +0.034 | 184–116 | <0.001 |
| ad_after − ad_endpoint | edit-line sim | +0.023 | 160–135 | 0.030 |
| ad_after − ad_endpoint | implied-after | +0.126 | 237–61 | <0.001 |

Bootstrap 95% CI for the headline (`ad_diff − ad_after`, sim−echo): **[−0.006, +0.034]** — includes zero. For edit-line sim: [+0.002, +0.042] — a marginal hint, unresolved at n = 300.

### Verdicts

- **P1: confirmed (again).** The witness arm's zero-shot lead is genuine edit content, replicating v1's five-sample autopsy at full n (95% vs 8%/18% edit-line production).
- **P2, strong form (explicit diff format > paired endpoints): not supported.** After identical adaptation, before→*after* training transfers to diff prediction statistically indistinguishably from before→*diff* training.
- **P2, weak form (paired path structure > endpoint-only): strongly supported.** Both paired-format arms beat the endpoint-only arm decisively on every artifact-proof metric.
- **The v1 artifact diagnosis: confirmed a second time.** Every arm scores below the echo ceiling on raw similarity (best 0.2311 vs ceiling 0.2636).

### Interpretation

What transfers is the **pairing** — supervision that keeps both states of the transformation in context — not the diff serialization. The before→after arm carries the witness's information implicitly (before + after determines the edit), and the model exploits it. What is actually fatal is integrating out the before-state (endpoint-only). In the program's framing: keep the section, not its integral — and the section turns out to be the (before, after) pair itself, with the explicit diff one way of writing it down rather than a privileged form. The marginal edit-line hint (p = 0.063) is the one thread left for a seed-1 run.

### Limitations

Single seed; one-day data-window drift relative to v1; bf16 vs v1's fp32; 410M scale; n = 300 gives limited power for the small edit-line effect; results are specific to Mathlib-style single-file edits.

### Reproduction

```bash
git clone --depth 20000 --single-branch https://github.com/leanprover-community/mathlib4.git ml4
python3 mine_mathlib_diffs.py --repo ./ml4 --out ./edits.jsonl
# stage 1 (three arms)
python3 train_arms.py --data edits.jsonl --arm {diff,after,endpoint} \
  --model EleutherAI/pythia-410m --target-tokens 20000000 --out results/ck_<arm> --seed 0
# stage 2 (shared diff adaptation, 1M tokens each)
python3 train_arms.py --data edits.jsonl --arm diff --model EleutherAI/pythia-410m \
  --target-tokens 1000000 --out results/ad_<arm> --init results/ck_<arm> --seed 0
# eval (all six)
python3 eval_arms.py --data edits.jsonl --ckpt results/<ckpt> \
  --base EleutherAI/pythia-410m --n 300 --out results/eval_<ckpt>.json
```

---

## Part II — Verified ZX compilation on IBM hardware

### Protocol

Four circuit pairs (`mod5_4`, `tof_3`, `barenco_tof_3`, `mod_mult_55`). In each pair both circuits implement the same unitary: a standard Amy/Maslov/Nam benchmark baseline, and a ZX-calculus-rewritten optimized version (Frobenius/bialgebra rules plus gate-level cleanup), with pair equality **machine-verified by ZX reduction** before shipping (all four PASS). Pre-registered predictions under a 1% two-qubit depolarizing model, in size order: mod5_4 +0.048 > mod_mult_55 +0.029 > barenco_tof_3 +0.020 > tof_3 +0.013 (near-parity control). Execution as registered: both arms interleaved in one job per pair (shared calibration window), 8,192 shots/arm, transpile optimization level 1, `seed_transpiler=7`, ideal distributions computed locally from the loaded QASM. Aer smoke test first: both arms fidelity 1.0 noiseless, delta 0.

Certified pairs (pre-transpile counts):

| circuit | qubits | 2q gates | T-count | depth | verified |
|---|---|---|---|---|---|
| mod5_4 | 5 | 28 → 20 | 28 → 8 | 48 → 20 | PASS |
| tof_3 | 5 | 18 → 16 | 21 → 15 | 31 → 30 | PASS |
| barenco_tof_3 | 5 | 24 → 22 | 28 → 16 | 42 → 43 | PASS |
| mod_mult_55 | 9 | 48 → 42 | 49 → 35 | 51 → 46 | PASS |

### Results — IBM `ibm_fez`, 2026-07-18

| pair | baseline F | optimized F | Δ observed | Δ predicted | transpiled 2q (b→o) | transpiled depth (b→o) |
|---|---|---|---|---|---|---|
| mod5_4 | 0.8648 | 0.8895 | **+0.0248** | +0.048 | 52 → 38 | 206 → 95 |
| mod_mult_55 | 0.6777 | 0.7448 | **+0.0670** | +0.029 | 99 → 117 | 217 → 204 |
| barenco_tof_3 | 0.9116 | 0.9283 | **+0.0167** | +0.020 | 42 → 34 | 164 → 126 |
| tof_3 (control) | 0.9410 | 0.9369 | **−0.0042** | +0.013 | 30 → 28 | 118 → 112 |

### Verdict — the protocol's branch two: *deltas positive but disordered*

- **Directional prediction: confirmed on all three effect pairs.** The control (`tof_3`) landed at −0.004, within shot noise of zero — as a near-parity control should, and ruling out a systematic interleaved-arm bias.
- **Structural prediction (effect-size ordering): falsified.** Observed order: mod_mult_55 ≫ mod5_4 > barenco_tof_3 > tof_3. The flagship underperformed (+0.025 vs +0.048); the 9-qubit circuit overperformed (+0.067 vs +0.029).
- **Mechanism check:** the winning 9-qubit arm carried *more* transpiled 2q gates than baseline (117 vs 99) and won through depth (204 vs 217): on a real device, coherence time prices circuits alongside gate error, so a uniform depolarizing model cannot rank them. Compilation pays on hardware; the simulator's ordering does not transfer.

### Limitations and follow-ups

One device, one calibration window, one transpile seed, 8,192 shots — a datapoint, not a study. Registered follow-ups, in order of information per dollar: transpile-seed sweep on `mod_mult_55` (routing skill vs seed luck); a second device on a different day (does the ordering scramble identically?); optimization level 3 (does the vendor transpiler equalize the arms — itself a finding); mirror-circuit protocol (P2 in the protocol appendix) if the package scales.

---

## The meta-result

Both bets were designed so that losing informatively was a registered outcome. The machinery fired as designed twice: in Part I, pre-registration plus a skeptical second read caught a metric artifact that would otherwise have become the quoted result — and the v2 rerun turned a confounded "confirmation" into a precise refinement (pairing, not serialization, is what transfers). In Part II, a pre-registered control pair and an explicit decision tree turned a scrambled ladder into a clean statement: verified compilation pays on silicon, and one-parameter noise models can't rank circuits against structured device noise. Zero results were moved; both nulls are recorded where they landed.

## Provenance

The ZX rewrite rules are the Frobenius equations formalized in the authors' Lean repository; every circuit pair ships with a machine-checked equality witness; predictions for both experiments were registered before hardware contact. Analysis for this report (paired statistics, figure tables) was machine-assisted and is fully reproducible from the committed JSON artifacts (`results/eval_*.json`, `qhw_results/hw_*.json`).
