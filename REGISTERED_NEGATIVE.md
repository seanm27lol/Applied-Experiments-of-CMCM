# Registered negative: cost-function identifiability (idea credit: Sean's
# friend, aero framing; logged 2026-07-26 before any experiment)

Conjecture (as proposed): attach a linear cost with nonzero coefficients
on every state component, aggregated along the witness; endpoint data
(start, end, total cost) cannot recover the cost function where paths
are ambiguous; witnesses can.

Computation (identifiability.py, exact, all 8^6 paths per system):
  opset      log2 fiber  rank trace  rank pair  deficit
  readable      0.00        19          19         9
  free          0.00        28          28         0
  q25           1.51        28          28         0
  q50           4.89        28          28         0
  q75           8.45        28          28         0
  abelian      11.33         9           9        19

Verdict: the identifiability version is FALSE here. Fiber-averaged
features span the full space wherever dynamics are rich (deficit 0), so
an exact endpoint learner recovers the cost completely; and where the
deficit is nonzero (abelian, readable) it binds the TRACE arm equally,
because unexcited state components are unidentifiable from any data
(persistence of excitation). Relative trace-vs-pair deficit: 0 in every
system tested.

What survives: the finite-sample form. The endpoint learner estimates
E[cost | endpoint]; its noise is the within-fiber cost variance, which
is strictly monotone in log fiber here (0.0004 / 0.1395 / 0.2792 /
0.3978 / 0.5534 for free/q25/q50/q75/abelian). Candidate computable
predictor of the supervision gap as a SAMPLE-COMPLEXITY quantity,
matching the direction of the Part V evidence. Status: hypothesis;
one theorem and one experiment short of a claim.

## Addendum, 2026-07-26: the surviving hypothesis, tested and corrected
The variance-alone predictor is falsified at the linear level by direct
simulation: samples-to-fixed-excess-risk for an OLS endpoint learner
gives n/variance ratios of 1014/680/716/185 across q25/q50/q75/abelian,
non-constant and direction-inverted (highest-variance system was
easiest, because its endpoint features span only 9 of 28 dimensions).
The corrected quantity is variance x effective rank of the endpoint
features: n * eps / (variance x rank) = 1.81/1.21/1.28/1.03 across the
same systems, consistent within a factor of two. Status: the two-factor
law holds for linear learners by construction and simulation; whether
neural learners obey it is open and would need its own registration.
