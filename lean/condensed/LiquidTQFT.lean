/-
# Condensed Abelian Groups as Candidate Targets for Monoidal Field Theories

This file collects categorical scaffolding relevant to investigating condensed
or liquid targets for field theories. It does not yet formalize a geometric
Atiyah-Segal TQFT.

## Mathematical scope

A standard `(d+1)`-dimensional TQFT is a **symmetric** monoidal functor from an
actual bordism category. The `AbstractTQFT` structure below is deliberately more
formal and less geometric: it packages a braided monoidal functor between
arbitrary braided monoidal categories. It is useful for proving a composition
lemma, but should not be identified with a complete TQFT formalization.

The file also records that `CondensedAb` is abelian and carries Mathlib's
symmetric monoidal structure. These facts can be useful in derived or analytic
constructions. Ordinary TQFT gluing, however, is functorial composition of
bordisms and does not require short exact sequences or an abelian target.

## What is formalized here

1. Balancedness of abelian categories: mono plus epi implies isomorphism.
2. Abstract braided monoidal theory data.
3. Transfer of that data along a braided monoidal functor.
4. Symmetric monoidal instances on `CondensedAb`, assembled from Mathlib.
5. A basic lemma unpacking the components of a short exact sequence.

The existence of the monoidal structure does not prove that tensoring in
`CondensedAb` is exact. No Liquid Tensor Experiment theorem is reproved here.
-/

import Mathlib

open CategoryTheory

noncomputable section

set_option synthInstance.maxHeartbeats 800000

/-! ## Part 1: A property of abelian categories -/

/-- In an abelian category, a morphism that is both monic and epic is an
isomorphism. This records the balancedness of abelian categories; it is not by
itself a TQFT gluing theorem. -/
theorem abelian_mono_epi_is_iso {C : Type*} [Category C] [Abelian C]
    {X Y : C} (f : X ⟶ Y) [Mono f] [Epi f] : IsIso f :=
  isIso_of_mono_of_epi f

/-! ## Part 2: Abstract braided monoidal theory -/

/-- An abstract braided monoidal theory with source category `S` and target
category `C`.

A standard Atiyah-Segal TQFT additionally requires an actual bordism source and
symmetric monoidal compatibility. -/
structure AbstractTQFT
    (S : Type*) [Category S] [MonoidalCategory S] [BraidedCategory S]
    (C : Type*) [Category C] [MonoidalCategory C] [BraidedCategory C] where
  /-- The underlying functor. -/
  Z : S ⥤ C
  /-- The strong monoidal structure on `Z`. -/
  monoidal : Z.Monoidal
  /-- Compatibility with the braidings. -/
  braided : Z.Braided

/-! ## Part 3: Transfer along braided monoidal functors -/

/-- Composition of an abstract braided monoidal theory with a braided monoidal
functor again gives an abstract braided monoidal theory. Applying this to an
analytic category and `CondensedAb` would still require constructing the
relevant braided monoidal comparison functor. -/
def AbstractTQFT.transfer
    {S : Type*} [Category S] [MonoidalCategory S] [BraidedCategory S]
    {C : Type*} [Category C] [MonoidalCategory C] [BraidedCategory C]
    {D : Type*} [Category D] [MonoidalCategory D] [BraidedCategory D]
    (T : AbstractTQFT S C)
    (F : C ⥤ D) [hF : F.Monoidal] [hFb : F.Braided] :
    AbstractTQFT S D where
  Z := T.Z ⋙ F
  monoidal := by
    letI := T.monoidal
    infer_instance
  braided := by
    letI := T.monoidal
    letI := T.braided
    infer_instance

/-! ## Part 4: Symmetric monoidal structure on `CondensedAb`

The declarations below instantiate existing Mathlib infrastructure. The
underlying mathematics and implementation are due to Joël Riou and Dagur
Asgeirsson; this file does not prove a new monoidal-structure theorem from
first principles.
-/

open MonoidalClosed Enriched.FunctorCategory

/-- Local isomorphisms for the coherent topology on `CompHaus`, with values in
`ModuleCat (ULift ℤ)`, form a monoidal morphism property. -/
instance condensedAb_W_isMonoidal :
    ((coherentTopology CompHaus.{0}).W
      (A := ModuleCat.{1} (ULift.{1} ℤ))).IsMonoidal :=
  GrothendieckTopology.W.monoidal

/-- `CondensedAb` admits the monoidal structure supplied by Mathlib's sheaf
localization machinery. -/
instance condensedAb_monoidal : MonoidalCategory CondensedAb.{0} :=
  Sheaf.monoidalCategory _ _

/-- The induced braided structure on `CondensedAb`. -/
instance condensedAb_braided :
    @BraidedCategory CondensedAb.{0} _ condensedAb_monoidal :=
  Sheaf.braidedCategory _ _

/-- The induced symmetric structure on `CondensedAb`. -/
instance condensedAb_symmetric :
    @SymmetricCategory CondensedAb.{0} _ condensedAb_monoidal :=
  Sheaf.symmetricCategory _ _

/-! ## Part 5: Short exact sequences as additional structure

Ordinary TQFT gluing is composition in the bordism category, while disjoint
union is encoded by the symmetric monoidal structure. Exact sequences may be
important in additional derived, homological, analytic, or factorization
constructions, but those applications require separate hypotheses.

The lemma below therefore makes no TQFT claim. It simply unpacks Mathlib's
`ShortExact` predicate.
-/

/-- A short exact sequence in an abelian category supplies a monomorphism, an
epimorphism, and exactness at the middle object. -/
theorem short_exact_components
    {C : Type*} [Category C] [Abelian C]
    {S : ShortComplex C} (hS : S.ShortExact) :
    Mono S.f ∧ Epi S.g ∧ S.Exact :=
  ⟨hS.mono_f, hS.epi_g, hS.exact⟩

end
