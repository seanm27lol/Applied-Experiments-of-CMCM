/-
# Monoidal Structure on Condensed Abelian Groups via Localization

This file documents the assembly of the monoidal category structure on
`CondensedAb` (condensed abelian groups) from existing Mathlib infrastructure.

**Attribution**: The underlying mathematics and Mathlib implementation are
entirely due to Joel Riou and Dagur Asgeirsson, in
`Mathlib.CategoryTheory.Sites.Monoidal` and related files. This file
contains no new mathematics. It records which components to assemble and
provides the specific instances for `CondensedAb`.

## Overview

The construction follows the localization approach:

1. The presheaf category inherits a monoidal structure from the pointwise
   tensor product in `ModuleCat`.
2. `presheafToSheaf J A` is a localization functor for `J.W`.
3. `J.W` is a monoidal morphism property (proved via internal hom, not stalks).
4. Localization machinery gives `MonoidalCategory (Sheaf J A)`.

## Key Mathlib Components (Riou-Asgeirsson)

- `GrothendieckTopology.W.monoidal`: `J.W` is monoidal when `A` is closed braided.
- `Sheaf.monoidalCategory`: Monoidal structure on `Sheaf J A` via localization.
- `Sheaf.braidedCategory` / `Sheaf.symmetricCategory`: Braided/symmetric refinements.
-/

import Mathlib

universe u

open CategoryTheory MonoidalClosed Enriched.FunctorCategory

noncomputable section

/-! ## The monoidal structure on CondensedAb

The class `J.W` of morphisms inverted by sheafification is monoidal.
The proof (Riou-Asgeirsson, `GrothendieckTopology.W.monoidal`) uses the
internal hom: for any sheaf `H`, `Hom(F tensor G, H)` is isomorphic to
`Hom(G, [F,H])` by adjunction, and `[F,H]` is a sheaf, so local
isomorphisms are preserved under tensoring.

This avoids stalks entirely, which matters because CompHaus with the
coherent topology does not have enough points in the classical sense.
-/

/-- `J.W` is a monoidal morphism property for the coherent topology on CompHaus. -/
instance condensedAb_W_isMonoidal :
    ((coherentTopology CompHaus.{u}).W
      (A := ModuleCat.{u+1} (ULift.{u+1} ℤ))).IsMonoidal :=
  GrothendieckTopology.W.monoidal

/-- Monoidal structure on condensed abelian groups via localization. -/
instance condensedAb_monoidalCategory :
    MonoidalCategory CondensedAb.{u} :=
  Sheaf.monoidalCategory _ _

/-- Braided structure on condensed abelian groups. -/
instance condensedAb_braidedCategory :
    @BraidedCategory CondensedAb.{u} _ condensedAb_monoidalCategory :=
  Sheaf.braidedCategory _ _

/-- Symmetric structure on condensed abelian groups. -/
instance condensedAb_symmetricCategory :
    @SymmetricCategory CondensedAb.{u} _ condensedAb_monoidalCategory :=
  Sheaf.symmetricCategory _ _

end
