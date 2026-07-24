/-
  WitnessRecoverability.lean

  Witness recoverability, formalised as faithfulness of the forgetful map
  from witnessed transformations to endpoint pairs.

  A witnessed transformation records how a state became another state, not
  just that it did. Forgetting the record gives an endpoint pair. The
  question this file makes precise is when that forgetting loses nothing:
  when the endpoints determine the witness, the record is redundant, and
  when they do not, the record carries information no endpoint pair can
  supply.

  Everything here is Mathlib-free and kernel-checks in seconds:
    lean WitnessRecoverability.lean

  Main content:
    Faithful           the recoverability predicate
    free_faithful      free systems are recoverable (the witness is readable
                       off the endpoints)
    abelian_not_faithful  commuting involutions are not (explicit witness
                       pair, checked by decide)
    fiber / #eval      the quantitative version, matching fiber.py
-/

namespace WitnessRecoverability

/-- A system of operations acting on a state space. -/
structure OpSystem (S Op : Type) where
  act : Op → S → S

/-- Run a witness (a list of operations) forward from a state. -/
def run {S Op : Type} (sys : OpSystem S Op) : List Op → S → S
  | [], s => s
  | o :: os, s => run sys os (sys.act o s)

/-- A witnessed transformation: a source, a record of how, and a target. -/
structure Witnessed (S Op : Type) where
  src : S
  wit : List Op
  tgt : S

/-- The witness actually realises the stated endpoints. -/
def Valid {S Op : Type} (sys : OpSystem S Op) (t : Witnessed S Op) : Prop :=
  run sys t.wit t.src = t.tgt

/-- The forgetful map: keep the endpoints, discard the record. This is the
    object-level part of the forgetful functor from witnessed
    transformations to endpoint pairs. -/
def forget {S Op : Type} (t : Witnessed S Op) : S × S := (t.src, t.tgt)

/-- Recoverability at a fixed source and witness length: any two valid
    witnesses with the same endpoints are equal. This is faithfulness of
    `forget` restricted to that fibre, and it is exactly the condition
    under which supervising on the witness can add nothing beyond
    supervising on the endpoint pair. -/
def Faithful {S Op : Type} (sys : OpSystem S Op) (s : S) (L : Nat) : Prop :=
  ∀ w₁ w₂ : List Op, w₁.length = L → w₂.length = L →
    run sys w₁ s = run sys w₂ s → w₁ = w₂

/-! ### The free system is faithful

  Taking the state space to be lists of operations and the action to be
  "push", the endpoint literally contains the witness, so recovering it is
  reading. This is the formal end of the spectrum the experiment calls
  `free`. -/

/-- The free system on `Op`: states are stacks, acting pushes. -/
def freeSys (Op : Type) : OpSystem (List Op) Op := ⟨fun o s => o :: s⟩

theorem run_free {Op : Type} (w s : List Op) :
    run (freeSys Op) w s = w.reverse ++ s := by
  induction w generalizing s with
  | nil => simp [run]
  | cons o os ih =>
    simp only [run]
    rw [ih]
    simp [freeSys]

/-- In the free system the endpoints determine the witness, at every
    length and from every source. The forgetful map is faithful. -/
theorem free_faithful {Op : Type} (s : List Op) (L : Nat) :
    Faithful (freeSys Op) s L := by
  intro w₁ w₂ _ _ h
  rw [run_free, run_free] at h
  have hr : w₁.reverse = w₂.reverse := List.append_cancel_right h
  have := congrArg List.reverse hr
  simpa using this

/-! ### Commuting involutions are not faithful

  Two bit flips on distinct positions commute, so the two orderings are
  distinct witnesses with identical endpoints. This is the formal end of
  the spectrum the experiment calls `abelian`. -/

/-- Two-bit state, two operations: flip the first, flip the second. -/
abbrev Bit2 := Bool × Bool

inductive Flip where
  | fst
  | snd
  deriving DecidableEq, Repr

def flipSys : OpSystem Bit2 Flip :=
  ⟨fun o s => match o with
    | Flip.fst => (!s.1, s.2)
    | Flip.snd => (s.1, !s.2)⟩

/-- The two orderings are genuinely different witnesses. -/
theorem flips_distinct : [Flip.fst, Flip.snd] ≠ [Flip.snd, Flip.fst] := by
  decide

/-- They have identical endpoints. -/
theorem flips_same_endpoints :
    run flipSys [Flip.fst, Flip.snd] (false, false)
      = run flipSys [Flip.snd, Flip.fst] (false, false) := by
  decide

/-- So the forgetful map is not faithful: the record carries information
    the endpoints do not. -/
theorem abelian_not_faithful : ¬ Faithful flipSys (false, false) 2 := by
  intro h
  exact flips_distinct (h _ _ rfl rfl flips_same_endpoints)

/-! ### The quantitative version

  Faithfulness is the boolean shadow of a count: how many witnesses share a
  given endpoint pair. That count is the fibre, and it is what `fiber.py`
  computes exhaustively for the experimental operation sets. -/

/-- All operation sequences of a given length. -/
def seqs {Op : Type} (ops : List Op) : Nat → List (List Op)
  | 0 => [[]]
  | n + 1 => (seqs ops n).flatMap fun tl => ops.map fun o => o :: tl

/-- The fibre over the endpoint pair `(s, run sys w s)`: how many
    length-`L` witnesses from `s` land where `w` lands. -/
def fiber {S Op : Type} [DecidableEq S] (sys : OpSystem S Op)
    (ops : List Op) (s : S) (L : Nat) (w : List Op) : Nat :=
  ((seqs ops L).filter fun v => run sys v s == run sys w s).length

/-- Faithfulness is fibre size one, everywhere. -/
def AllFibersOne {S Op : Type} [DecidableEq S] (sys : OpSystem S Op)
    (ops : List Op) (s : S) (L : Nat) : Prop :=
  ∀ w ∈ seqs ops L, fiber sys ops s L w = 1

section Demo

def allFlips : List Flip := [Flip.fst, Flip.snd]

-- Every length-2 witness in the commuting system shares its endpoints with
-- one other: fibres of size 2, so log2 fibre = 1 bit of witness
-- information that endpoints cannot supply.
#eval (seqs allFlips 2).map (fiber flipSys allFlips (false, false) 2)

-- The free system on the same alphabet: every fibre is a singleton.
#eval (seqs allFlips 2).map (fiber (freeSys Flip) allFlips ([] : List Flip) 2)

-- Length 3, commuting: all eight witnesses collapse onto two endpoint
-- pairs, so every fibre has size 4 and three bits of witness information
-- are unrecoverable from the endpoints.
#eval (seqs allFlips 3).map (fiber flipSys allFlips (false, false) 3)

end Demo

/-- The commuting system fails `AllFibersOne` at length 2, and the free
    system on the same alphabet satisfies it. The experiment interpolates
    between these two poles by mixing commuting and free generators, and
    measures whether the supervision gap tracks the fibre size. -/
theorem demo_fibers_differ :
    ¬ AllFibersOne flipSys allFlips (false, false) 2
    ∧ AllFibersOne (freeSys Flip) allFlips ([] : List Flip) 2 := by
  refine ⟨?_, ?_⟩
  intro h
  have h1 := h [Flip.fst, Flip.snd] (by decide)
  have h2 : fiber flipSys allFlips (false, false) 2 [Flip.fst, Flip.snd] = 2 := by
    decide
  omega
  · show ∀ w ∈ seqs allFlips 2,
      fiber (freeSys Flip) allFlips ([] : List Flip) 2 w = 1
    decide

end WitnessRecoverability

-- Provenance: no sorries, no custom axioms.
#print axioms WitnessRecoverability.free_faithful
#print axioms WitnessRecoverability.abelian_not_faithful
#print axioms WitnessRecoverability.demo_fibers_differ
