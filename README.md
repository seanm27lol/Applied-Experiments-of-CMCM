# witness-zx-experiments
![provenance](Provenance.jpeg)
Two pre-registered experiments on witness preservation, plus the Lean
formalization layer behind them. Full write-up: **REPORT.md**.

- `witness/` — the edit-witness experiment: does supervising a language model
  with transformation witnesses (diffs) transfer better than endpoints?
  Verdict: pairing transfers, serialization doesn't; endpoint-only loses.
- `quantum/` — verified ZX compilation on IBM hardware: four certified
  circuit pairs, one interleaved job per pair, pre-registered delta ladder.
  Verdict: positive but disordered — optimization pays, the depolarizing
  model's ordering doesn't transfer.
- `results/`, `quantum/qhw_results/` — the raw JSON every number comes from.
- `lean/` — `LensLean.lean` (reverse-mode AD as a category of lenses; seven
  category/monoidal laws, all `rfl`), `bench_lens.lean` (Track B),
  `frobenius/` (the equations behind the circuits), `condensed/` (the
  SemiNormedGrp → CondensedAb embedding profile).
- `benchmarks_report.md` — classical suite: 46% aggregate T-count reduction,
  2753-vs-2829 vs T-par, equality witnesses green.

## Building the Lean layer
- `lean/LensLean.lean`, `lean/bench_lens.lean` — core Lean 4, no deps:
  `lean --run bench_lens.lean`.
- `lean/frobenius/`, `lean/condensed/` — Mathlib via included toolchain:
  `lake exe cache get && lake build`.

## Reproducing the experiments
See REPORT.md — exact commands for mining, training (stages 1–2), the
six-way eval, and the hardware run.
