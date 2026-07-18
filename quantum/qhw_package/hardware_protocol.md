# Hardware Protocol: Verified ZX Compilation, Measured on a Real Device

## What this is

Four pairs of quantum circuits. In each pair, the two circuits implement the same unitary: the `baseline` is a standard benchmark circuit from the Amy/Maslov/Nam suite, the `optimized` version was produced by ZX-calculus rewriting (Frobenius/bialgebra rules) plus gate-level cleanup, and the equality of each pair was machine-verified by ZX reduction before shipping (witness status in `pair_manifest.json`; all four PASS). The experiment: run both arms of each pair on the same device in the same calibration window and see whether the compiled arm's fidelity advantage, predicted below, shows up on real hardware. Total ask: one script, four pairs, roughly fifteen minutes of attention plus queue time.

## The certified pairs

```
circuit         q   2q gates   1q gates   T-count    depth     verified
mod5_4          5   28 -> 20   35 -> 10   28 -> 8    48 -> 20    PASS
tof_3           5   18 -> 16   27 -> 24   21 -> 15   31 -> 30    PASS
barenco_tof_3   5   24 -> 22   34 -> 28   28 -> 16   42 -> 43    PASS
mod_mult_55     9   48 -> 42   71 -> 50   49 -> 35   51 -> 46    PASS
```

(arrow = baseline -> optimized, counts before device transpilation)

## Pre-registered predictions

Under a 1% two-qubit depolarizing model (20k shots, simulated before any hardware contact), the fidelity-vs-ideal deltas came out, in order:

```
mod5_4         delta = +0.048   (flagship: depth halved, 8 fewer 2q gates)
mod_mult_55    delta = +0.029   (moderate)
barenco_tof_3  delta = +0.020   (mixed: fewer 2q, depth roughly flat)
tof_3          delta = +0.013   (near-parity control: only 2 fewer 2q gates)
```

The prediction is therefore two-part. Directional: optimized beats baseline on all four. Structural: the effect sizes come out in roughly that order, with mod5_4 clearly largest and tof_3 smallest. The structural prediction is the interesting one; tof_3 is deliberately included as a small-effect control. Real-device deltas will differ in magnitude from the depolarizing model (crosstalk, T1/T2, readout error), but the ordering should be robust if the compilation story is right.

## Protocol

Run per pair: `python run_on_hardware.py --pair mod5_4 --backend ibm:<device> --shots 8192` (the script's IBM path uses SamplerV2; adapt freely to your stack, the QASM files are the ground truth). What the script guarantees and please preserve if adapting: both arms are submitted in one job, interleaved, so they share a calibration window; the ideal distribution is computed locally from the same loaded circuit, so bit-ordering is internally consistent; default transpile optimization_level is 1, because level 3 may re-optimize the baseline and shrink the very difference under test. If budget allows, run both levels and report both. Shots: 8192 minimum per arm (binomial error on a fidelity near 0.8 is then well under a point). Sanity check first with `--backend aer` locally; noiseless fidelity should print 1.0 for both arms.

What to send back: the four `results_*.json` files the script writes (they include fidelity and TVD versus ideal, plus the post-transpile two-qubit count and depth per arm, which is the covariate that explains everything). Device name and rough date are all the metadata needed.

## How to read the outcome

If the deltas are positive and ordered as predicted: the verified-compilation pipeline demonstrably pays on hardware, with the transpiled two-qubit counts as the mechanism check. If deltas are positive but disordered: compilation pays, the depolarizing model's ordering doesn't transfer, also interesting. If deltas are near zero or negative: most likely the device transpiler equalized the arms (check the transpiled 2q columns first) or routing overhead swamped the logical-level savings on the 9-qubit circuit; a null here is a real finding about where logical-level optimization stops mattering, and gets reported as such.

## Honest framing

This is not novel science and is not being sold as such: circuit-optimization-improves-NISQ-fidelity demonstrations exist in the literature, and the optimization method is Kissinger and van de Wetering's. What is distinctive here is the provenance chain: the rewrite rules are the Frobenius equations formalized in the sender's Lean repository, every pair ships with a machine-checked equality witness, the predictions were registered before hardware contact, and the whole loop (algebra to compiler to certified circuits to device data) is executed end to end by the people asking. Think of it as a rigorous datapoint with an unusually clean pedigree, destined for a repo readme and possibly an evaluation section, not a paper claim.

## Appendix: optional scalable variant (Protocol P2, mirror circuits)

If you'd rather not trust classical simulation of the ideal distribution (irrelevant at 5 to 9 qubits, relevant if this ever scales), the standard alternative is mirror benchmarking: run C followed by C-dagger and measure the return probability to the all-zeros string. Two cautions if you do this. Mirror each arm's own compiled circuit (baseline mirrored with baseline-dagger, optimized with optimized-dagger) and place a barrier at the midpoint, otherwise the transpiler cancels the circuit against its own inverse and you measure nothing. And naive C C-dagger can echo away coherent errors and flatter the device; the field-standard fix is a random Pauli layer at the midpoint, absorbed into the inverse half, as in Sandia's randomized mirror-circuit protocol. P1 is recommended for this package's sizes.
