/-
# Seminormed-Group Realization in Condensed Abelian Groups: Reconnaissance and Partial Construction

This file constructs the functor from `SemiNormedGrp` to `CondensedAb` sending a
seminormed abelian group V to the sheaf S ↦ C(S, V). It also records how this
relates to the motivating Banach-space setting. We audit Mathlib (v4.28.0) and
mark the remaining genuine gaps with `sorry`.

## Summary of Findings

### What EXISTS in Mathlib (verified by `inferInstance` or explicit construction):

1. **Continuous map spaces** (`Mathlib.Topology.ContinuousMap.Compact`):
   - `SeminormedAddCommGroup C(α, E)` for `[CompactSpace α] [SeminormedAddCommGroup E]` ✅
   - `NormedAddCommGroup C(α, E)` for `[CompactSpace α] [NormedAddCommGroup E]` ✅
   - `CompleteSpace C(α, E)` when `[CompleteSpace E]` ✅ (so C(S,V) is Banach when V is)
   - `Module (ULift ℤ) C(α, E)` ✅ (inferred through the ℤ-module structure)
   - `ContinuousMap.comp` for precomposition ✅
   - `ContinuousMap.compRightContinuousMap` for continuous precomposition ✅

2. **TopCat → CondensedSet functor** (`Mathlib.Condensed.TopComparison`):
   - `TopCat.toCondensedSet : TopCat → CondensedSet` ✅
   - `topCatToCondensedSet : TopCat ⥤ CondensedSet` ✅
   - `ContinuousMap.yonedaPresheaf G X : Cᵒᵖ ⥤ Type` ✅ (the underlying presheaf)
   - `equalizerCondition_yonedaPresheaf` ✅ (sheaf condition for Type-valued presheaf)
   - `PreservesFiniteProducts (yonedaPresheaf G X)` ✅
   - `Condensed.ofSheafCompHaus` ✅ (wraps a presheaf satisfying sheaf conditions)

3. **Sheaf condition infrastructure**:
   - `Presheaf.isSheaf_iff_preservesFiniteProducts_and_equalizerCondition` ✅:
     IsSheaf (coherentTopology CompHaus) F ↔ PreservesFiniteProducts F ∧ EqualizerCondition F
   - `forget (ModuleCat (ULift ℤ))` preserves limits ✅ and reflects limits ✅
   - `PreservesFiniteProducts` transfers via NatIso and reflects through `forget` ✅
   - `Presheaf.isSheaf_iff_isSheaf_comp` ✅ (for transferring sheaf conditions)
   - `Presheaf.isSheaf_of_iso_iff` ✅ (sheaf condition transfers along NatIso)
   - Universe-correct instances obtained via `hasLimitsOfSizeShrink` and
     `preservesLimitsOfSize_of_univLE` ✅

4. **Seminormed group category** (`Mathlib.Analysis.Normed.Group.SemiNormedGrp`):
   - `SemiNormedGrp` ✅: category of seminormed abelian groups with bounded homs
   - `SemiNormedGrp₁` ✅: subcategory with norm non-increasing maps
   - Uses `NormedAddGroupHom` as morphisms, with `map_add` and `map_zsmul`

5. **Condensed infrastructure**:
   - `CondensedAb = CondensedMod (ULift ℤ) = Condensed (ModuleCat (ULift ℤ))` ✅
   - `Abelian CondensedAb` ✅
   - `MonoidalCategory CondensedAb` ✅ (from `Sheaf.monoidalCategory`, see `MonoidalViaLocalization.lean`)

### What is MISSING from Mathlib:

1. **No `BanachCat` or `NormedAddCommGroupCat`** - There is `SemiNormedGrp` (seminormed groups
   with bounded homs), but no dedicated category of Banach spaces. We use `SemiNormedGrp`.

2. **No TopCat → CondensedAb functor** - `topCatToCondensedSet` goes to CondensedSet only.
   The algebraic structure on C(S,V) must be lifted manually (done below).

3. **No projective tensor product** - No `ProjectiveTensorProduct` or completed tensor product
   for normed spaces. Cannot connect Ban's monoidal structure to CondensedAb's.

4. **No packaged bridge found in the pinned Mathlib version** - The relevant normed-group
   and condensed components are not connected by an existing construction used here. We provide
   the specific bridge below without making a global priority claim.

### Dependency graph:

```
  ContinuousMap.instSeminormedAddCommGroup
         ↓
  banachPresheaf V : CompHausᵒᵖ ⥤ ModuleCat (ULift ℤ)           ← no sorry
         ↓
  ┌──────┴──────────────┐
  ↓                     ↓
  PreservesFiniteProducts       EqualizerCondition               ← no sorry
  (via yonedaPresheaf            (via isSheaf transfer
   + NatIso transfer)             through forget functor)
  └──────┬──────────────┘
         ↓
  banachCondensed V : CondensedAb                                ← no sorry
         ↓
  semiNormedGrpToCondensedAb : SemiNormedGrp ⥤ CondensedAb      ← no sorry
         ↓
  ┌───────────────┬──────────────────────┐
  ↓               ↓                      ↓
  Faithful        Not full               Preserves finite limits
  ← no sorry      ← no sorry             ← no sorry
```
-/

import Mathlib

open CategoryTheory CategoryTheory.Limits ContinuousMap

noncomputable section

/-! ## Part 1: Mathlib Audit - Continuous Map Spaces

We verify that Mathlib provides the algebraic and analytic structure on `C(S, V)`.
-/

section ContinuousMapAudit

-- 1a. C(S, V) is a seminormed abelian group when S is compact and V is seminormed
example (S : Type*) [TopologicalSpace S] [CompactSpace S]
    (V : Type*) [SeminormedAddCommGroup V] : SeminormedAddCommGroup C(S, V) := inferInstance

-- 1b. C(S, V) is a normed group when V is normed (norm separates points)
example (S : Type*) [TopologicalSpace S] [CompactSpace S]
    (V : Type*) [NormedAddCommGroup V] : NormedAddCommGroup C(S, V) := inferInstance

-- 1c. C(S, V) is complete when V is complete (so Banach when V is Banach)
example (S : Type*) [TopologicalSpace S] [CompactSpace S]
    (V : Type*) [NormedAddCommGroup V] [CompleteSpace V] : CompleteSpace C(S, V) := inferInstance

-- 1d. C(S, V) is a module over ULift ℤ (needed for CondensedAb = ModuleCat (ULift ℤ))
example (S : Type*) [TopologicalSpace S] [CompactSpace S]
    (V : Type*) [SeminormedAddCommGroup V] : Module (ULift ℤ) C(S, V) := inferInstance

-- 1e. Precomposition by continuous maps
example (S T : Type*) [TopologicalSpace S] [TopologicalSpace T]
    (f : C(S, T)) (V : Type*) [TopologicalSpace V] (g : C(T, V)) : C(S, V) := g.comp f

-- 1f. The sup norm satisfies expected properties
example (S : Type*) [TopologicalSpace S] [CompactSpace S]
    (V : Type*) [NormedAddCommGroup V] (f : C(S, V)) :
    ‖f‖ = ⨆ x, ‖f x‖ := ContinuousMap.norm_eq_iSup_norm f

end ContinuousMapAudit

/-! ## Part 2: Mathlib Audit - Condensed Infrastructure -/

section CondensedAudit

-- 2a. The TopCat → CondensedSet functor exists
example : TopCat.{1} ⥤ CondensedSet.{0} := topCatToCondensedSet

-- 2b. Sheaf condition decomposes as finite products + equalizer
example (F : CompHaus.{0}ᵒᵖ ⥤ ModuleCat.{1} (ULift.{1} ℤ)) :
    Presheaf.IsSheaf (coherentTopology CompHaus.{0}) F ↔
    PreservesFiniteProducts F ∧ regularTopology.EqualizerCondition F :=
  Presheaf.isSheaf_iff_preservesFiniteProducts_and_equalizerCondition F

-- 2c. The forgetful functor preserves and reflects limits
example : PreservesLimits (forget (ModuleCat.{1} (ULift.{1} ℤ))) := inferInstance
example : ReflectsLimits (forget (ModuleCat.{1} (ULift.{1} ℤ))) := inferInstance
example : (forget (ModuleCat.{1} (ULift.{1} ℤ))).ReflectsIsomorphisms := inferInstance

-- 2d. The category of seminormed groups exists with bounded group hom morphisms
example : Category SemiNormedGrp := inferInstance

-- 2e. CondensedAb is abelian
example : Abelian CondensedAb := inferInstance
-- MonoidalCategory CondensedAb is available via Sheaf.monoidalCategory
-- (see MonoidalViaLocalization.lean for verification)

end CondensedAudit

/-! ## Part 3: Universe Infrastructure

The transfer of sheaf conditions from `Type`-valued presheaves to `ModuleCat`-valued ones
requires universe-correct instances for `HasLimitsOfSize` and `PreservesLimitsOfSize`.
`CompHaus.{0}` has `Category.{0, 1}`, while `ModuleCat.{1}` has `Category.{1, 2}`.
The key bridge uses `hasLimitsOfSizeShrink` and `preservesLimitsOfSize_of_univLE`.
-/

instance : HasLimitsOfSize.{0, 1, 1, 2} (ModuleCat.{1} (ULift.{1} ℤ)) :=
  hasLimitsOfSizeShrink.{0, 1, 1, 0} _

instance : PreservesLimitsOfSize.{0, 1, 1, 1, 2, 2}
    (forget (ModuleCat.{1} (ULift.{1} ℤ))) :=
  preservesLimitsOfSize_of_univLE.{1, 1, 0, 1} _

/-! ## Part 4: The Presheaf Construction

We define `banachPresheaf V : CompHausᵒᵖ ⥤ ModuleCat (ULift ℤ)` sending
`S ↦ C(S, V)` with precomposition as the functorial action.

We use `SeminormedAddCommGroup` rather than `NormedAddCommGroup` to match the
morphism type of `SemiNormedGrp`, Mathlib's categorical framework for normed groups.
-/

/-- The presheaf on `CompHaus` sending `S ↦ C(S, V)` as a `ULift ℤ`-module.
    For `f : S → T` in `CompHaus`, the map `C(T, V) → C(S, V)` is precomposition. -/
def banachPresheaf (V : Type 1) [SeminormedAddCommGroup V] :
    CompHaus.{0}ᵒᵖ ⥤ ModuleCat.{1} (ULift.{1} ℤ) where
  obj S := ModuleCat.of (ULift ℤ) C(S.unop, V)
  map f := ModuleCat.ofHom {
    toFun := fun g => g.comp ⟨f.unop, f.unop.hom.hom.continuous⟩
    map_add' := by intros; ext; simp
    map_smul' := by intros; ext; simp [ContinuousMap.smul_apply]
  }
  map_id := by intro S; ext g; simp
  map_comp := by intro S T U f g; ext h; simp

/-! ## Part 5: The Sheaf Condition

We show `banachPresheaf V` satisfies the two conditions needed for the coherent topology:
1. `PreservesFiniteProducts` - transferred from `yonedaPresheaf` via `NatIso`
2. `EqualizerCondition` - transferred via `Presheaf.isSheaf_iff_isSheaf_comp`
-/

/-- The underlying Type-valued presheaf of `banachPresheaf V` is naturally isomorphic to
    `yonedaPresheaf compHausLikeToTop V`. This is the key link to the existing sheaf proofs
    in `Mathlib.Condensed.TopComparison`. -/
def banachPresheafForgetIso (V : Type 1) [SeminormedAddCommGroup V] :
    banachPresheaf V ⋙ forget (ModuleCat.{1} (ULift.{1} ℤ)) ≅
    yonedaPresheaf (CompHausLike.compHausLikeToTop (fun _ => True)) V :=
  NatIso.ofComponents (fun S => Iso.refl _) (by intros; ext; rfl)

/-- `banachPresheaf V` preserves finite products.

**Proof strategy**: The underlying Type-valued presheaf `banachPresheaf V ⋙ forget`
is naturally isomorphic to `yonedaPresheaf`, which preserves finite products
(instance from `Mathlib.Condensed.TopComparison`). We transfer via the NatIso using
`preservesLimitsOfShape_of_natIso`, then reflect back through `forget` using
`preservesFiniteProducts_of_reflects_of_preserves`. -/
instance banachPresheaf_preservesFiniteProducts (V : Type 1) [SeminormedAddCommGroup V] :
    PreservesFiniteProducts (banachPresheaf V) := by
  have : PreservesFiniteProducts (banachPresheaf V ⋙ forget (ModuleCat.{1} (ULift.{1} ℤ))) := by
    constructor; intro n
    have : PreservesLimitsOfShape (Discrete (Fin n))
        (yonedaPresheaf (CompHausLike.compHausLikeToTop (fun _ => True)) V) := inferInstance
    exact @preservesLimitsOfShape_of_natIso _ _ _ _ (Discrete (Fin n)) _ _ _
        (banachPresheafForgetIso V) this
  exact preservesFiniteProducts_of_reflects_of_preserves (banachPresheaf V)
    (forget (ModuleCat.{1} (ULift.{1} ℤ)))

/-- `banachPresheaf V` satisfies the equalizer condition for the regular topology.

**Proof strategy**: We transfer the sheaf condition from the Type-valued `yonedaPresheaf`
to our `ModuleCat`-valued `banachPresheaf` through the chain:
1. `equalizerCondition_iff_isSheaf`: EqualizerCondition ↔ IsSheaf for regular topology
2. `isSheaf_iff_isSheaf_comp`: IsSheaf for F ↔ IsSheaf for F ⋙ forget
3. `isSheaf_of_iso_iff`: IsSheaf transfers along the NatIso to yonedaPresheaf
4. `equalizerCondition_yonedaPresheaf`: the Type-valued presheaf satisfies EqualizerCondition -/
theorem banachPresheaf_equalizerCondition (V : Type 1) [SeminormedAddCommGroup V] :
    regularTopology.EqualizerCondition (banachPresheaf V) := by
  rw [regularTopology.equalizerCondition_iff_isSheaf]
  rw [Presheaf.isSheaf_iff_isSheaf_comp (regularTopology CompHaus.{0}) _
    (forget (ModuleCat.{1} (ULift.{1} ℤ)))]
  rw [Presheaf.isSheaf_of_iso_iff (banachPresheafForgetIso V)]
  rw [← regularTopology.equalizerCondition_iff_isSheaf]
  exact equalizerCondition_yonedaPresheaf
    (CompHausLike.compHausLikeToTop (fun _ => True)) V
    (fun Z B π he => IsQuotientMap.of_surjective_continuous
      (((CompHaus.effectiveEpi_tfae π).out 0 2).mp he) π.hom.hom.continuous)

/-! ## Part 6: The Condensed Abelian Group -/

/-- The condensed abelian group associated to a seminormed abelian group `V`.
    As a presheaf on `CompHaus`, it sends `S` to `C(S, V)` with the `ULift ℤ`-module structure.
    The sheaf condition follows from `PreservesFiniteProducts` and `EqualizerCondition`. -/
def banachCondensed (V : Type 1) [SeminormedAddCommGroup V] : CondensedAb :=
  ⟨banachPresheaf V,
   (Presheaf.isSheaf_iff_preservesFiniteProducts_and_equalizerCondition _).mpr
    ⟨inferInstance, banachPresheaf_equalizerCondition V⟩⟩

/-! ## Part 7: Functoriality in V - The Embedding Functor

We construct a functor `SemiNormedGrp ⥤ CondensedAb` sending `V ↦ banachCondensed V`.
A bounded group homomorphism `φ : V → W` induces `C(S, V) → C(S, W)` by postcomposition.
-/

/-- Postcomposition by a bounded group homomorphism, as a morphism of presheaves.
    For `φ : V ⟶ W` in `SemiNormedGrp`, the natural transformation sends
    `g : C(S, V)` to `φ ∘ g : C(S, W)` at each `S : CompHaus`. -/
def banachPresheafMap {V W : SemiNormedGrp.{1}} (φ : V ⟶ W) :
    banachPresheaf V ⟶ banachPresheaf W where
  app S := ModuleCat.ofHom {
    toFun := fun g => ⟨(ConcreteCategory.hom φ) ∘ g,
      (ConcreteCategory.hom φ).continuous.comp g.continuous⟩
    map_add' := by intros; ext x; exact map_add (ConcreteCategory.hom φ) _ _
    map_smul' := by intros; ext x; simp [ContinuousMap.smul_apply]
  }
  naturality := by intro S T f; ext g; simp [banachPresheaf]; rfl

/-- The functor from seminormed groups to condensed abelian groups.
    Sends `V` to the condensed abelian group `S ↦ C(S, V)` and
    a bounded homomorphism `φ : V → W` to postcomposition by `φ`. -/
def semiNormedGrpToCondensedAb : SemiNormedGrp.{1} ⥤ CondensedAb.{0} where
  obj V := banachCondensed V
  map φ := ⟨banachPresheafMap φ⟩
  map_id := by intro V; ext S g; simp [banachPresheafMap]; rfl
  map_comp := by intro V W X φ ψ; ext S g; simp [banachPresheafMap]; rfl

/-! ## Part 8: Properties of the Embedding

Faithfulness is proved below. Fullness is false and is proved at the sheaf level
in `SheafFullnessCounterexample.lean`. The remaining placeholder in this file concerns preservation of equalizers.
-/

/-
PROBLEM
The embedding is faithful: distinct bounded maps V → W induce distinct maps on C(S, V).

    **Proof sketch**: For any `v : V`, the constant function `S → V` at `v` is in `C(S, V)`.
    If `φ` and `ψ` agree on all C(S, V), then `φ(v) = ψ(v)` for all `v` (evaluate the
    constant function at any point). Hence `φ = ψ`.

    **Mathlib API needed**: `ContinuousMap.const`, evaluation, `NormedAddGroupHom.ext`.

PROVIDED SOLUTION
To show the functor is faithful, we need: if φ ψ : V ⟶ W are morphisms in SemiNormedGrp such that semiNormedGrpToCondensedAb.map φ = semiNormedGrpToCondensedAb.map ψ, then φ = ψ.

Use Functor.Faithful constructor with map_injective. Given equality of the condensed maps, in particular at the component corresponding to the one-point CompHaus space (CompHaus.of PUnit), the maps on C(PUnit, V) agree. For any v : V, the constant map (ContinuousMap.const PUnit v) is in C(PUnit, V). Evaluating φ ∘ (const v) = ψ ∘ (const v) at PUnit.unit gives φ v = ψ v. By extensionality (NormedAddGroupHom.ext), φ = ψ.

Alternatively, at any component S, the maps on C(S, V) agree. Take S = CompHaus.of PUnit. For any v : V, const v : C(PUnit, V). Then (φ ∘ const v)(PUnit.unit) = (ψ ∘ const v)(PUnit.unit) gives φ v = ψ v.
-/
theorem semiNormedGrpToCondensedAb_faithful :
    semiNormedGrpToCondensedAb.Faithful := by
  constructor;
  intro X Y f g hfg;
  simp_all +decide [ semiNormedGrpToCondensedAb ];
  simp_all +decide [ banachPresheafMap ];
  injection hfg with hfg;
  simp_all +decide [ funext_iff ];
  ext x; specialize hfg ( Opposite.op ( CompHaus.of PUnit ) ) ; replace hfg := congr_arg ( fun f => f ( ContinuousMap.const _ x ) ) hfg ; aesop;

/-
**Fullness is FALSE for `SemiNormedGrp` in general.**

**Counterexample**: Let `V = c₀₀(ℕ, ℤ)` (eventually zero integer sequences with the sup norm) and
`W = ℤ` (with the absolute value norm). Define `f : V → W` by `f(a) = Σ aₙ` (a finite sum since
`a` is eventually zero).

- `f` is additive: clear.
- `f` is continuous: if `‖a‖_∞ < 1`, then `|aₙ| < 1` for all `n`, hence `aₙ = 0` for all `n`
  (integers), so `f(a) = 0`. Thus `f` is continuous at `0`, and since it's additive, continuous
  everywhere.
- `f` is **not** bounded: let `a⁽ⁿ⁾ = e₁ + ⋯ + eₙ` (1 in positions 1 through n). Then
  `‖a⁽ⁿ⁾‖_∞ = 1` but `f(a⁽ⁿ⁾) = n`, so `‖f(a⁽ⁿ⁾)‖ / ‖a⁽ⁿ⁾‖ = n → ∞`.

Since `f` is continuous and additive, postcomposition by `f` defines a natural transformation
`η : banachCondensed V ⟶ banachCondensed W` in `CondensedAb` (η_S(g) = f ∘ g is continuous,
additive, compatible with ULift ℤ-action, and natural by associativity of composition).
But since `f` is not bounded, there is no `NormedAddGroupHom V W` lifting `η`.

The issue is that continuous additive maps between seminormed abelian groups need not be
bounded - the standard proof of "continuous linear ⟹ bounded" requires scalar multiplication
by a dense subfield (e.g., ℝ), which is absent for general abelian groups.

Over real normed spaces, the immediate pointwise obstruction disappears because continuous
additive maps are real-linear and bounded. This does not by itself prove categorical fullness.
For complex or general valued fields, `CondensedAb` forgets scalar linearity; complex conjugation
is already a continuous additive but non-complex-linear map. A scalar-sensitive target such as
condensed modules is required for a genuinely linear fully faithful embedding.
-/
-- The sheaf-level non-fullness theorem is in `SheafFullnessCounterexample.lean`.

/-! ### Finite Products in SemiNormedGrp

Mathlib does not register `HasFiniteProducts SemiNormedGrp`. We construct them using
the Pi type `(i : ι) → V i` with the sup norm.
-/

/-- The product fan for a finite family of seminormed groups.
    The vertex is the Pi type with the sup norm; the projections are evaluations. -/
def SemiNormedGrp.piFan {n : ℕ} (V : Fin n → SemiNormedGrp.{1}) :
    Fan V :=
  Fan.mk (SemiNormedGrp.of ((i : Fin n) → V i))
    (fun i => SemiNormedGrp.ofHom
      { toFun := fun f => f i
        map_add' := fun _ _ => rfl
        bound' := ⟨1, fun f => by simp only [one_mul]; exact norm_le_pi_norm f i⟩ })

/-
PROBLEM
The product fan is a limit: given any compatible family of bounded homs,
    the tupling map is bounded.

PROVIDED SOLUTION
Use `mkFanLimit` with:
- lift: s ↦ SemiNormedGrp.ofHom { toFun := fun x i => ConcreteCategory.hom (s.proj i) x, map_add' := ..., bound' := ... }
- The bound for the lift: use NormedAddGroupHom.norm_def and the fact that ‖(fun i => f_i(x))‖ = Finset.univ.sup (fun i => ‖f_i(x)‖₊). Each ‖f_i(x)‖ ≤ ‖f_i‖ * ‖x‖ ≤ (Finset.univ.sup ‖f_i‖) * ‖x‖. So ‖lift(x)‖ ≤ (sup_i ‖f_i‖) * ‖x‖, giving C = (Finset.univ.sup (fun i => ‖(s.proj i).hom‖₊)) as the bound.
- The projection property: lift s ≫ piFan.proj i = s.proj i follows by ext (components agree).
- Uniqueness: if m ≫ piFan.proj i = s.proj i for all i, then m = lift s by ext (each component agrees).

Key: use `SemiNormedGrp.hom_ext` or ext for morphism equality. The norm bound for the pi type uses `pi_norm_le_iff` or similar.
-/
/-- The lift map for the product fan: given a cone `s` over a family `V`,
    the tupling map `s.pt → ∏ V_i` is bounded. -/
def SemiNormedGrp.piFanLift {n : ℕ} {V : Fin n → SemiNormedGrp.{1}} (s : Fan V) :
    s.pt ⟶ (SemiNormedGrp.piFan V).pt :=
  SemiNormedGrp.ofHom
    { toFun := fun x => fun i => (s.proj i).hom x
      map_add' := fun x y => funext fun i => map_add (s.proj i).hom x y
      bound' := ⟨↑(Finset.univ.sup fun i => ‖(s.proj i).hom‖₊), fun x => by
        simp only [Pi.norm_def]
        rw [show (↑(Finset.univ.sup fun i => ‖(s.proj i).hom‖₊) : ℝ) * ‖x‖ =
          ↑((Finset.univ.sup fun i => ‖(s.proj i).hom‖₊) * ‖x‖₊) from by push_cast; ring]
        exact_mod_cast Finset.sup_le fun i _ =>
          ((by exact_mod_cast (s.proj i).hom.le_opNorm x :
            ‖(s.proj i).hom x‖₊ ≤ ‖(s.proj i).hom‖₊ * ‖x‖₊)).trans
            (mul_le_mul_of_nonneg_right (Finset.le_sup
              (f := fun j => ‖(s.proj j).hom‖₊) (Finset.mem_univ i)) (zero_le _))⟩ }

/-- The product fan is a limit. -/
def SemiNormedGrp.piFanIsLimit {n : ℕ} (V : Fin n → SemiNormedGrp.{1}) :
    IsLimit (SemiNormedGrp.piFan V) :=
  mkFanLimit _ (fun s => SemiNormedGrp.piFanLift s)
    (fun s i => by apply SemiNormedGrp.hom_ext; ext x; rfl)
    (fun s m hm => by
      apply SemiNormedGrp.hom_ext; ext x; funext i
      exact congr_arg (fun f => f.hom x) (hm i))

instance SemiNormedGrp.hasProduct' {n : ℕ} (V : Fin n → SemiNormedGrp.{1}) :
    HasProduct V :=
  HasLimit.mk ⟨SemiNormedGrp.piFan V, SemiNormedGrp.piFanIsLimit V⟩

/-- `SemiNormedGrp` has all finite products: the product `∏_i V_i` is the Pi type
    with the sup norm. -/
instance SemiNormedGrp.hasFiniteProducts : HasFiniteProducts SemiNormedGrp.{1} := by
  refine ⟨fun n => ⟨fun {K} => ?_⟩⟩
  exact hasLimit_of_iso (Discrete.natIsoFunctor (F := K)).symm

/- The instance `semiNormedGrpToCondensedAb_preservesEqualizers` is defined below,
   after the pointwise `continuousMapTypeFunctor` infrastructure it reuses. -/

/-- The underlying type-valued functor obtained by evaluating the condensed realization at `S`. -/
def continuousMapTypeFunctor (S : CompHaus.{0}ᵒᵖ) :
    SemiNormedGrp.{1} ⥤ Type 1 where
  obj V := C(S.unop, V)
  map φ g :=
    ⟨(ConcreteCategory.hom φ) ∘ g,
      (ConcreteCategory.hom φ).continuous.comp g.continuous⟩
  map_id := by
    intro V
    ext g x
    rfl
  map_comp := by
    intro X Y Z φ ψ
    ext g x
    rfl

/-- Evaluating the sheaf-level realization and forgetting the module structure is
naturally isomorphic to the explicit continuous-map functor. -/
def evaluatedForgetIso (S : CompHaus.{0}ᵒᵖ) :
    (((semiNormedGrpToCondensedAb ⋙
      sheafToPresheaf (coherentTopology CompHaus.{0})
        (ModuleCat.{1} (ULift.{1} ℤ))) ⋙
      (evaluation CompHaus.{0}ᵒᵖ (ModuleCat.{1} (ULift.{1} ℤ))).obj S) ⋙
      forget (ModuleCat.{1} (ULift.{1} ℤ))) ≅
      continuousMapTypeFunctor S :=
  NatIso.ofComponents (fun _ => Iso.refl _) (by
    intro X Y f
    rfl)

/-- The mapped explicit product cone is limiting after evaluating at `S` and
forgetting to types. -/
def continuousMapTypePiIsLimit (S : CompHaus.{0}ᵒᵖ) {n : ℕ}
    (V : Fin n → SemiNormedGrp.{1}) :
    IsLimit ((continuousMapTypeFunctor S).mapCone (SemiNormedGrp.piFan V)) where
  lift s x := ContinuousMap.pi (fun i => (s.π.app (Discrete.mk i)) x)
  fac s j := by
    rcases j with ⟨i⟩
    rfl
  uniq s m hm := by
    funext x
    apply ContinuousMap.ext
    intro y
    funext i
    have h := congrFun (hm (Discrete.mk i)) x
    exact congrArg (fun f : C(S.unop, V i) => f y) h

/-- Continuous maps into a finite product preserve that product at the level of types. -/
theorem continuousMapTypeFunctor_preservesFiniteProducts (S : CompHaus.{0}ᵒᵖ) :
    PreservesFiniteProducts (continuousMapTypeFunctor S) := by
  constructor
  intro n
  constructor
  intro K
  let V : Fin n → SemiNormedGrp.{1} := fun i => K.obj (Discrete.mk i)
  haveI : PreservesLimit
      (Discrete.functor (K.obj ∘ Discrete.mk))
      (continuousMapTypeFunctor S) := by
    change PreservesLimit (Discrete.functor V) (continuousMapTypeFunctor S)
    exact preservesLimit_of_preserves_limit_cone
      (SemiNormedGrp.piFanIsLimit V)
      (continuousMapTypePiIsLimit S V)
  exact preservesLimit_of_iso_diagram
    (continuousMapTypeFunctor S)
    (Discrete.natIsoFunctor (F := K)).symm

/-- The evaluated presheaf-valued realization preserves finite products. -/
theorem evaluatedRealization_preservesFiniteProducts (S : CompHaus.{0}ᵒᵖ) :
    PreservesFiniteProducts
      ((semiNormedGrpToCondensedAb ⋙
        sheafToPresheaf (coherentTopology CompHaus.{0})
          (ModuleCat.{1} (ULift.{1} ℤ))) ⋙
        (evaluation CompHaus.{0}ᵒᵖ (ModuleCat.{1} (ULift.{1} ℤ))).obj S) := by
  let F :=
    (semiNormedGrpToCondensedAb ⋙
      sheafToPresheaf (coherentTopology CompHaus.{0})
        (ModuleCat.{1} (ULift.{1} ℤ))) ⋙
      (evaluation CompHaus.{0}ᵒᵖ (ModuleCat.{1} (ULift.{1} ℤ))).obj S
  haveI : PreservesFiniteProducts (continuousMapTypeFunctor S) :=
    continuousMapTypeFunctor_preservesFiniteProducts S
  haveI : PreservesFiniteProducts (F ⋙ forget (ModuleCat.{1} (ULift.{1} ℤ))) := by
    constructor
    intro n
    exact preservesLimitsOfShape_of_natIso (evaluatedForgetIso S).symm
  constructor
  intro n
  exact preservesLimitsOfShape_of_reflects_of_preserves
    F (forget (ModuleCat.{1} (ULift.{1} ℤ)))

/-- The presheaf underlying the condensed realization preserves finite products. -/
theorem realizationPresheaf_preservesFiniteProducts :
    PreservesFiniteProducts
      (semiNormedGrpToCondensedAb ⋙
        sheafToPresheaf (coherentTopology CompHaus.{0})
          (ModuleCat.{1} (ULift.{1} ℤ))) := by
  constructor
  intro n
  apply preservesLimitsOfShape_of_evaluation
  intro S
  haveI := evaluatedRealization_preservesFiniteProducts S
  infer_instance

/-- The sheaf-level realization preserves finite products. -/
instance semiNormedGrpToCondensedAb_preservesFiniteProducts :
    PreservesFiniteProducts semiNormedGrpToCondensedAb := by
  haveI := realizationPresheaf_preservesFiniteProducts
  constructor
  intro n
  let G := sheafToPresheaf (coherentTopology CompHaus.{0})
    (ModuleCat.{1} (ULift.{1} ℤ))
  haveI : CreatesLimitsOfShape (Discrete (Fin n)) G :=
    CategoryTheory.Sheaf.createsLimitsOfShape
  haveI : ReflectsLimitsOfShape (Discrete (Fin n)) G :=
    reflectsLimitsOfShapeOfCreatesLimitsOfShape G
  exact preservesLimitsOfShape_of_reflects_of_preserves
    semiNormedGrpToCondensedAb G

/-! ### Equalizers

We mirror the finite-products development for the shape `WalkingParallelPair`.  The canonical
equalizer fork in `SemiNormedGrp` is `SemiNormedGrp.fork f g`, whose vertex is `ker (f - g)`
with the subspace topology.  Postcomposition (`continuousMapTypeFunctor S`) sends this fork to a
limit fork of types, because a continuous map `S → V` equalizing `f` and `g` lands in
`ker (f - g)` and corestricts continuously (`ContinuousMap`/`Continuous.subtype_mk`). -/

/-- The `IsLimit` witness for the canonical equalizer fork in `SemiNormedGrp`, reconstructed
explicitly (mirroring `Mathlib.Analysis.Normed.Group.SemiNormedGrp.Kernels`). -/
noncomputable def SemiNormedGrp.forkIsLimit {V W : SemiNormedGrp.{1}} (f g : V ⟶ W) :
    IsLimit (SemiNormedGrp.fork f g) :=
  have cond := fun (c : Fork f g) =>
    show NormedAddGroupHom.compHom (f - g).hom c.ι.hom = 0 by
      rw [SemiNormedGrp.hom_sub, map_sub, AddMonoidHom.sub_apply, sub_eq_zero]
      exact congr_arg SemiNormedGrp.Hom.hom c.condition
  Fork.IsLimit.mk _
    (fun c => SemiNormedGrp.ofHom <| NormedAddGroupHom.ker.lift (Fork.ι c).hom _ (cond c))
    (fun c => SemiNormedGrp.hom_ext <| NormedAddGroupHom.ker.incl_comp_lift _ _ (cond c))
    (fun c m h => by ext x; dsimp; simp_rw [← h]; rfl)

/-- A cone leg equalizing postcomposition by `f` and `g` lands, pointwise, in `ker (f - g)`. -/
theorem continuousMapTypeForkMem (S : CompHaus.{0}ᵒᵖ) {V W : SemiNormedGrp.{1}} (f g : V ⟶ W)
    (s : Fork ((continuousMapTypeFunctor S).map f) ((continuousMapTypeFunctor S).map g))
    (x : s.pt) (p : S.unop) :
    (show C(S.unop, V) from s.ι x) p ∈ (f - g).hom.ker := by
  have keyp : (ConcreteCategory.hom f) ((show C(S.unop, V) from s.ι x) p)
      = (ConcreteCategory.hom g) ((show C(S.unop, V) from s.ι x) p) :=
    congrFun (congrArg (fun (cc : C(S.unop, W)) => cc.toFun) (congrFun s.condition x)) p
  rw [NormedAddGroupHom.mem_ker, SemiNormedGrp.hom_sub]
  simp only [NormedAddGroupHom.sub_apply, sub_eq_zero]
  exact keyp

/-- The image under `continuousMapTypeFunctor S` of the canonical equalizer fork is a limit
fork of types. -/
noncomputable def continuousMapTypeForkIsLimit (S : CompHaus.{0}ᵒᵖ) {V W : SemiNormedGrp.{1}}
    (f g : V ⟶ W) :
    IsLimit (Fork.ofι ((continuousMapTypeFunctor S).map (Fork.ι (SemiNormedGrp.fork f g)))
        (by rw [← Functor.map_comp, ← Functor.map_comp, Fork.condition]) :
      Fork ((continuousMapTypeFunctor S).map f) ((continuousMapTypeFunctor S).map g)) :=
  Fork.IsLimit.mk _
    (fun s x => ⟨fun p => ⟨(show C(S.unop, V) from s.ι x) p, continuousMapTypeForkMem S f g s x p⟩,
      (show C(S.unop, V) from s.ι x).continuous.subtype_mk (continuousMapTypeForkMem S f g s x)⟩)
    (fun s => by ext x; rfl)
    (fun s m hm => by
      ext x
      apply ContinuousMap.ext
      intro p
      apply Subtype.ext
      exact congrFun (congrArg (fun (c : C(S.unop, V)) => c.toFun) (congrFun hm x)) p)

/-- The evaluated type-valued functor preserves equalizers. -/
theorem continuousMapTypeFunctor_preservesEqualizers (S : CompHaus.{0}ᵒᵖ) :
    PreservesLimitsOfShape WalkingParallelPair (continuousMapTypeFunctor S) := by
  constructor
  intro K
  haveI : PreservesLimit (parallelPair (K.map WalkingParallelPairHom.left)
      (K.map WalkingParallelPairHom.right)) (continuousMapTypeFunctor S) := by
    refine preservesLimit_of_preserves_limit_cone (SemiNormedGrp.forkIsLimit _ _) ?_
    exact (isLimitMapConeForkEquiv (continuousMapTypeFunctor S)
      (SemiNormedGrp.fork _ _).condition).symm (continuousMapTypeForkIsLimit S _ _)
  exact preservesLimit_of_iso_diagram (continuousMapTypeFunctor S)
    (diagramIsoParallelPair K).symm

/-- The evaluated presheaf-valued realization preserves equalizers. -/
theorem evaluatedRealization_preservesEqualizers (S : CompHaus.{0}ᵒᵖ) :
    PreservesLimitsOfShape WalkingParallelPair
      ((semiNormedGrpToCondensedAb ⋙
        sheafToPresheaf (coherentTopology CompHaus.{0})
          (ModuleCat.{1} (ULift.{1} ℤ))) ⋙
        (evaluation CompHaus.{0}ᵒᵖ (ModuleCat.{1} (ULift.{1} ℤ))).obj S) := by
  let F :=
    (semiNormedGrpToCondensedAb ⋙
      sheafToPresheaf (coherentTopology CompHaus.{0})
        (ModuleCat.{1} (ULift.{1} ℤ))) ⋙
      (evaluation CompHaus.{0}ᵒᵖ (ModuleCat.{1} (ULift.{1} ℤ))).obj S
  haveI : PreservesLimitsOfShape WalkingParallelPair (continuousMapTypeFunctor S) :=
    continuousMapTypeFunctor_preservesEqualizers S
  haveI : PreservesLimitsOfShape WalkingParallelPair
      (F ⋙ forget (ModuleCat.{1} (ULift.{1} ℤ))) :=
    preservesLimitsOfShape_of_natIso (evaluatedForgetIso S).symm
  exact preservesLimitsOfShape_of_reflects_of_preserves
    F (forget (ModuleCat.{1} (ULift.{1} ℤ)))

/-- The presheaf underlying the condensed realization preserves equalizers. -/
theorem realizationPresheaf_preservesEqualizers :
    PreservesLimitsOfShape WalkingParallelPair
      (semiNormedGrpToCondensedAb ⋙
        sheafToPresheaf (coherentTopology CompHaus.{0})
          (ModuleCat.{1} (ULift.{1} ℤ))) := by
  apply preservesLimitsOfShape_of_evaluation
  intro S
  haveI := evaluatedRealization_preservesEqualizers S
  infer_instance

/-- The embedding preserves equalizers.

    **Proof strategy**: identical routing to `semiNormedGrpToCondensedAb_preservesFiniteProducts`,
    with `WalkingParallelPair` in place of `Discrete (Fin n)`.  The presheaf-level statement is
    `realizationPresheaf_preservesEqualizers`, and `sheafToPresheaf` creates (hence reflects)
    limits of this shape. -/
instance semiNormedGrpToCondensedAb_preservesEqualizers :
    PreservesLimitsOfShape WalkingParallelPair semiNormedGrpToCondensedAb := by
  haveI := realizationPresheaf_preservesEqualizers
  let G := sheafToPresheaf (coherentTopology CompHaus.{0})
    (ModuleCat.{1} (ULift.{1} ℤ))
  haveI : CreatesLimitsOfShape WalkingParallelPair G :=
    CategoryTheory.Sheaf.createsLimitsOfShape
  haveI : ReflectsLimitsOfShape WalkingParallelPair G :=
    reflectsLimitsOfShapeOfCreatesLimitsOfShape G
  exact preservesLimitsOfShape_of_reflects_of_preserves
    semiNormedGrpToCondensedAb G


/-- The embedding preserves finite limits (left exact).

    **Proof**: Follows from preservation of finite products and equalizers,
    using `preservesFiniteLimits_of_preservesEqualizers_and_finiteProducts`. -/
theorem semiNormedGrpToCondensedAb_preservesFiniteLimits :
    PreservesFiniteLimits semiNormedGrpToCondensedAb :=
  preservesFiniteLimits_of_preservesEqualizers_and_finiteProducts semiNormedGrpToCondensedAb

/-! ## Part 9: Monoidal Structure (Far Future)

The following would make the embedding a braided monoidal functor, which would be needed to apply the abstract braided-monoidal transfer construction
in `LiquidTQFT.lean`.

### What would be needed:

1. **Projective tensor product** on normed spaces: `V ⊗̂ W` with its completed π-topology.
   - Not in Mathlib at all. Would need:
     - Definition of the projective tensor norm
     - Completion to get a Banach space
     - Universal property: bounded bilinear maps V × W → Z ↔ bounded maps V ⊗̂ W → Z
   - This would give `MonoidalCategory SemiNormedGrp` (or a Banach subcategory)

2. **Comparison**: `C(S, V ⊗̂ W) ≅ C(S, V) ⊗_{condensed} C(S, W)`
   - Requires understanding the condensed tensor product (= sheafification
     of the pointwise tensor product of presheaves)
   - The isomorphism is non-trivial and related to nuclearity

3. **Braided structure**: The embedding should send the symmetric braiding on Ban
   to the symmetric braiding on `CondensedAb`.

All of this is well beyond current Mathlib and constitutes a significant formalization project.
-/

/-! ## Part 10: Summary of Progress

### Fully proved (no sorry):
- `banachPresheaf V : CompHausᵒᵖ ⥤ ModuleCat (ULift ℤ)` - presheaf construction
- `banachPresheafForgetIso V` - NatIso to Type-valued yonedaPresheaf
- `PreservesFiniteProducts (banachPresheaf V)` - via yonedaPresheaf transfer
- `banachPresheaf_equalizerCondition` - via isSheaf transfer through `forget`
- `banachCondensed V : CondensedAb` - condensed abelian group construction
- `banachPresheafMap φ` - postcomposition as natural transformation
- `semiNormedGrpToCondensedAb : SemiNormedGrp ⥤ CondensedAb` - the embedding functor
- `semiNormedGrpToCondensedAb_faithful` - distinct bounded maps give distinct condensed maps
- `SemiNormedGrp.hasFiniteProducts` - **new**: Pi type with sup norm as categorical product
- `semiNormedGrpToCondensedAb_preservesFiniteProducts` - pointwise continuous-map product comparison
- `semiNormedGrpToCondensedAb_preservesEqualizers` - pointwise continuous-map equalizer
  comparison: the canonical `SemiNormedGrp.fork` (vertex `ker (f - g)` with the subspace
  topology) is sent to a limit fork of types via `ContinuousMap`/`Continuous.subtype_mk`,
  lifted pointwise (`preservesLimitsOfShape_of_evaluation`) and through `sheafToPresheaf`
- `semiNormedGrpToCondensedAb_preservesFiniteLimits` - follows from the proved
  finite-product and equalizer instances

### Disproved:
- `semiNormedGrpToCondensedAb_full` - **FALSE** for general `SemiNormedGrp`.
  `SheafFullnessCounterexample.lean` proves the sheaf-level non-fullness theorem
  using the continuous unbounded summation map on `c₀₀(ℕ, ℤ)`.
  Over ℝ the immediate boundedness obstruction disappears, but categorical fullness is not proved;
  over ℂ and general fields a target retaining scalar linearity is required.

### Long-term (requires new Mathlib infrastructure):
- Scalar-sensitive normed-space and condensed-module categories for a correctly stated fullness problem
- Projective tensor product → `MonoidalCategory BanachCat`
- Right exactness (open mapping theorem)
- Monoidal functor structure on the embedding
-/

end
