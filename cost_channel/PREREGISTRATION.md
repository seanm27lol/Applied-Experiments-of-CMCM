# Pre-registration: the cost channel as an intermediate supervision rung

Commit before running. Deviations get dated lines at the bottom.

## Origin and credit

The construction is Sebastien Seboih's: give every action a unique nonzero
cost, integrate along the path, keep (start, end, cost), then delete the
path and try to reverse-engineer it. Because the cost is summed over
actions, it depends only on how many times each action occurs, never on
their order. The cost scalar therefore reveals the operation multiset
and nothing else, which places it exactly between endpoint-only
supervision and full witness supervision.

His follow-on refinement: also penalise distance from the goal along the
way, so a direct path costs less than an indirect one. That term is
state-dependent, so unlike the action term it IS order-sensitive, and it
raises the ceiling substantially (see the table). It is tested as a
fourth arm rather than as a replacement, because the order-blind version
is the one with the clean interpretation.

## Why this is testable where Part IV was not

Part IV predicted the supervision gap would grow with fiber size. That
gap must vanish at both ends (at fiber 1 the endpoints determine the
witness; at large fiber no arm can exceed a near-chance ceiling), so no
monotone law could exist and the design was retired.

The quantity here does not vanish. Exact Bayes ceilings, computed by
enumerating all 8^6 = 262,144 witnesses per system (ceilings.json):

  system    log2 fib   pair    cost   costd   d(cost)  d(costd)
  readable     0.00    1.000   1.000   1.000    0.000     0.000
  free         0.00    1.000   1.000   1.000    0.000     0.000
  q25          1.51    0.915   0.920   0.977    0.006     0.062
  q50          4.89    0.739   0.781   0.886    0.041     0.147
  q75          8.45    0.514   0.587   0.699    0.074     0.185
  abelian     11.33    0.190   0.363   0.393    0.173     0.202

Both difference columns are strictly monotone in log fiber (Spearman
+1.00 each). They are the maximum advantage each channel can confer, and
they grow rather than collapsing, because as fibers widen the channel
ceilings rise faster than the endpoint ceiling falls.

Note the non-monotone piece inside that: what the DISTANCE term adds on
top of the action term is +0.000 / +0.056 / +0.105 / +0.112 / +0.029,
peaking at q75 and nearly vanishing at abelian. The reason is exact: for
commuting flips on distinct bits, the distance from the current state to
the goal equals the number of flips not yet applied, which is the same
in every order. The order-sensitive term is order-blind precisely where
order is the only remaining unknown. This is a prediction, not an
observation, and C3 tests it.

## Design

Systems: the six of Part IV, unchanged in algebra. Rendering changed
from 28 binary characters to 7 hex digits, which was Part IV's fatal
flaw (P4c failed because the model could not parse bit strings). Under
hex rendering `readable` is a literal copy task: the last six hex
digits of the end state are the witness (verified).

Four arms, identical training budget, single stage, examples matched:
  sc_pair    START + END
  sc_cost    START + END + COST          (decimal scalar; costs are
                                          powers of 7, verified
                                          collision-free over all 6-draw
                                          multisets, so the scalar
                                          determines the multiset)
  sc_costd   START + END + COST + DIST   (adds the running distance-to-
                                          goal sum as a second labelled
                                          field, so both components stay
                                          readable and the experiment
                                          measures information use, not
                                          integer arithmetic)
  sc_counts  START + END + COUNTS        (the action information written
                                          out as eight per-operation
                                          counts)

sc_cost and sc_counts carry IDENTICAL information and differ only in
how much work it takes to read. That pair separates information from
accessibility, the distinction that retired Part IV and that also
governed its `free` condition.

Data: 30,000 distinct witnesses per system, 300 held out. Model
pythia-160m, fp32, lr 5e-5, 2 epochs, seed 0. Metric: token accuracy
over the six operation slots, chance 0.125. The witness alphabet is
disjoint from the state alphabet, so copying cannot beat chance.

States render as 8 hex digits, uniform width across all systems.

24 runs total.

## Predictions

A1 anchor: on `readable`, all three arms >= 0.90 token accuracy. This
   is a copy task; failure means the pipeline cannot measure anything
   and no other prediction may be interpreted. Chosen because a
   degenerate model cannot pass it (generation, 8-way per slot).
A2 accessibility: on `abelian`, sc_counts exceeds sc_pair by >= 0.05.
   If the model cannot use even fully explicit multiset information
   where the ceiling difference is largest (0.173), then C1 is
   untestable and the finding is about model capability, not about the
   channel.
C1 primary: across the five non-anchor systems, the measured advantage
   (sc_cost minus sc_pair) is positively rank-correlated with the
   ceiling difference (Spearman > 0), and the abelian advantage exceeds
   the free advantage by >= 0.05.
C2 secondary, no direction committed: sc_counts minus sc_cost is the
   decoding cost of identical information presented as an aggregate.
   Reported per system.
C3 order term: sc_costd minus sc_cost is what the order-sensitive
   distance penalty buys. Registered prediction, following the ceilings:
   this is largest in the middle systems and smaller at abelian than at
   q75. A monotone increasing result would contradict the ceiling
   analysis and require explanation.

## Falsification

If C1 fails with flat or negatively-correlated advantages while A1 and
A2 both pass, then models do not extract available information in
proportion to how much is present, and the ceiling table does not
predict learned behaviour. That is a real result and would be reported
as the outcome.

If A1 fails, stop. If A2 fails, report the capability finding and do not
interpret C1.

## Limitations stated in advance

Single seed, one model scale, synthetic systems. The cost channel is
tested through a language model's ability to read a numeric field, which
is a weak instrument; C2 exists to measure that weakness rather than
assume it away.

## Addendum, registered before running: the search evaluation

Sebastien Seboih's follow-on procedure: fix (start, end), ask the trained
cost-conditioned model for progressively cheaper paths, and verify each
generation by running it forward. Generation is unreliable, verification
is cheap, so invalid candidates are discarded rather than trusted. This
is return-conditioned generation in the Decision Transformer sense, whose
documented weakness is that it does not extrapolate past the training
distribution; the verification step is what makes the loop sound anyway.

Implementation: only costs ACHIEVABLE for that endpoint pair are
requested (enumerated exactly), so a failure means the model failed
rather than that the request was impossible. Ladder per item: the true
cost, the median achievable cost, the minimum achievable cost, and one
value below the minimum as an impossible control. Items whose endpoint
admits only one achievable cost are skipped and counted; by system the
searchable fraction is free 0.0%, q25 15.8%, q50 43.8%, q75 58.3%,
abelian 92.3%, so the procedure is only meaningfully testable in the
three ambiguous systems.

Uniqueness, computed exactly and relevant to the motivation: the
fraction of endpoint pairs with a UNIQUE minimum-cost path is 100.0%
(free), 90.7% (q25), 68.4% (q50), 35.2% (q75), 0.8% (abelian), with
296.3 co-optimal paths on average in the abelian case. Existence is
trivial. Uniqueness fails structurally in commuting systems, because
any reordering of a minimum-cost path is also a minimum-cost path to the
same endpoint. Quantum gate sets commute extensively, so an existence-
and-uniqueness result for optimal circuits should be expected to fail on
the uniqueness half for the same reason.

Predictions:
R1 control: at the impossible rung, valid-and-cost-matching rate <= 0.05.
   A higher rate means the model ignores the cost field and no other
   search result may be interpreted.
R2 feasibility: at the true-cost rung, the valid-and-cost-matching rate
   is at least the arm's exact-match rate from the main evaluation.
R3 primary, no threshold committed: the valid-and-cost-matching rate at
   the minimum-cost rung, reported per system. This is the number the
   procedure produces.
R4 direction: R3 is higher in systems with more co-optimal paths, since
   more distinct targets satisfy the request. Ordering prediction:
   abelian > q75 > q50.

## A1 verdict, 2026-07-26: PASS
All four arms at 1.0000 token accuracy (exact match 1.0000) on the
readable copy task, against the registered 0.90 bar (script:
stats_cost.py, results/readable/*.json). The hex rendering repairs
Part IV's P4c failure mode — the pipeline can measure. C2 on readable
is +0.0000, as the design requires (sc_cost and sc_counts carry
identical information and the task is a copy). The queue continued to
the remaining five systems at 22:14 local.

## Main-run verdicts, 2026-07-27
Full table: results/stats_main.txt; per-item scores in
results/<system>/<arm>.json.

A1 anchor: PASS (all four arms 1.0000 on readable vs the 0.90 bar;
see the 2026-07-26 section).
A2 access: PASS. abelian counts - pair = +0.0716 vs the registered
>= 0.05 bar. The model can use fully explicit multiset information
where the ceiling difference is largest, so C1 is testable.
C1 primary: FAIL, in the registered direction of falsification.
Measured cost - pair advantages are +0.166 (free), +0.176 (q25),
+0.100 (q50), +0.051 (q75), +0.073 (abelian) against ceiling
differences 0.000 / 0.006 / 0.041 / 0.074 / 0.173: Spearman rho =
-0.80, and abelian does not exceed free (it is lower by 0.093). With
A1 and A2 both passing, the registered falsification clause fires:
models do not extract available information in proportion to how much
is present, and the ceiling table does not predict learned behaviour.
The cost channel helps everywhere but least where it should help
most. Reported as the outcome, per the registration.
C2 decoding cost: null everywhere (counts - cost between -0.007 and
+0.011 across systems). The aggregate scalar is as accessible as the
spelled-out counts, so the C1 failure is not a reading-instrument
effect: the information was available and legible.
C3 order term: registered non-monotone shape CONFIRMED. Measured
costd - cost: +0.032 (q25), +0.062 (q50), +0.062 (q75), +0.011
(abelian): largest in the middle systems, smaller at abelian than at
q75, not monotone increasing, matching the ceiling analysis (+0.056 /
+0.105 / +0.112 / +0.029) in shape at roughly half magnitude. The
order-sensitive term buys the most where order matters least and
nearly nothing where order is the only unknown, as computed.

## Search-eval verdicts, 2026-07-27
Full table: results/stats_search.txt; per-rung detail in
results/<system>/search_sc_cost.json. Searchable items 88 (q50),
108 (q75), 143 (abelian); single-cost endpoints skipped and counted
(62 / 42 / 7).

R1 control: PASS. Impossible-rung valid-and-cost rate 0.000 in all
three systems (vs the 0.05 bound). The models read the cost field;
the search numbers are interpretable.
R2 feasibility: PASS in all three systems (true rung 0.080 / 0.398 /
0.944 vs main exact-match 0.020 / 0.000 / 0.000).
R3 primary: minimum-cost valid-and-cost 0.102 (q50), 0.380 (q75),
0.783 (abelian). No threshold was committed; these are the numbers
the procedure produces.
R4 direction: PASS. R3 orders abelian > q75 > q50, matching the
co-optimal-path counts (296.3 / 3.25 / 1.59 mean minima): more
distinct valid targets, easier hits. Uniqueness failure helps the
search, as registered.
Post-hoc note (not a registered check): on abelian the minimum rung
(0.783) sits below true (0.944) and median (0.972); asking for the
cheapest path degrades validity even where achievable, the
return-conditioning non-extrapolation signature, muted but present.
