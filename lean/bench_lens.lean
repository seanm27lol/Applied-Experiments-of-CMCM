/-
Track B: the cheap gradient principle, measured.

The reverse-mode (lens) gradient of a degree-P polynomial in Horner form
costs ONE backward pass, O(P). Central finite differences cost 2P forward
passes, O(P^2) total. This file computes both, times both, and
cross-checks them. The `horner` lens's bwd is the fused form of the
`comp`/`par` composite from LensLean.lean; the fusion is licensed by the
seven category and monoidal laws proved there.

Run: lean --run bench_lens.lean
-/

structure Lens (A B : Type) where
  fwd : A → B
  bwd : A → B → A

abbrev F := Float

/-- Horner-form polynomial p(x) = c0 + x(c1 + x(c2 + ...)),
as a lens from coefficient lists. Backward pass emits the full
gradient (x^0, x^1, ..., x^(P-1)) scaled by the cotangent, in one
O(P) sweep: reverse mode's entire value proposition. -/
def horner (x : F) : Lens (List F) F where
  fwd := fun l => l.foldr (fun c acc => c + x * acc) 0.0
  bwd := fun l d =>
    let rec go : List F → F → List F
      | [], _ => []
      | _ :: r, p => (d * p) :: go r (p * x)
    go l 1.0

def perturb (l : List F) (i : Nat) (h : F) : List F :=
  (List.range l.length).map fun j =>
    (l.getD j 0.0) + (if j == i then h else 0.0)

/-- Central finite differences: 2P forward evaluations. -/
def fdGrad (f : List F → F) (l : List F) : List F :=
  let h := 1e-6
  (List.range l.length).map fun i =>
    (f (perturb l i h) - f (perturb l i (-h))) / (2.0 * h)

def coeffs (p : Nat) : List F :=
  (List.range p).map fun i => Float.sin (i.toFloat + 1.0)

def analytic (x : F) (p : Nat) : List F :=
  let rec go : Nat → F → List F
    | 0, _ => []
    | n + 1, acc => acc :: go n (acc * x)
  go p 1.0

def maxRelErr (a b : List F) : F :=
  (a.zip b).foldl (fun m xy =>
    let e := Float.abs (xy.1 - xy.2) / (Float.abs xy.2 + 1e-12)
    if e > m then e else m) 0.0

def timeMs {α : Type} (reps : Nat) (act : Unit → α) : IO (Float × α) := do
  let t0 ← IO.monoNanosNow
  let mut r := act ()
  for _ in [1:reps] do
    r := act ()
  let t1 ← IO.monoNanosNow
  pure ((t1 - t0).toFloat / reps.toFloat / 1.0e6, r)

def main : IO Unit := do
  let x := 0.7
  IO.println "P | lens (ms) | FD (ms) | FD/lens | lens vs analytic | FD vs analytic (first 32)"
  for p in [8, 64, 256, 1024] do
    let cs := coeffs p
    let L := horner x
    let truth := analytic x p
    let (tL, gL) ← timeMs 200 (fun _ => L.bwd cs 1.0)
    let fdReps := if p ≤ 256 then 5 else 1
    let (tF, gF) ← timeMs fdReps (fun _ => fdGrad L.fwd cs)
    let eL := maxRelErr gL truth
    let eF := maxRelErr (gF.take 32) (truth.take 32)
    IO.println s!"{p} | {tL} | {tF} | {tF / tL} | {eL} | {eF}"
  IO.println ""
  IO.println "reading: lens time grows ~linearly in P, FD ~quadratically; the ratio"
  IO.println "is the cheap-gradient principle, measured. The lens gradient matches"
  IO.println "the analytic gradient exactly at every component; finite differences"
  IO.println "are trustworthy only where the derivative exceeds their noise floor"
  IO.println "(~1e-10 at h=1e-6), which is why FD is the witness at small P and"
  IO.println "analysis is the witness at large P. Interpreter timings: shapes are"
  IO.println "meaningful, absolute values are not."
