import Mathlib
import RequestProject.BanachEmbedding
import RequestProject.FullnessCounterexample

/-!
# Profile of the embedding `semiNormedGrpToCondensedAb`

This file records two negative results about the realization functor
`semiNormedGrpToCondensedAb : SemiNormedGrp.{1} ⥤ CondensedAb.{0}` built in
`BanachEmbedding.lean`, completing its profile:

* **Stage 1 – it does not reflect isomorphisms.** On `ℕ →₀ ℤ` we compare the
  `ℓ¹` norm and the sup norm. The identity `V₁ ⟶ V∞` is a bounded map (constant `1`,
  since `‖a‖∞ ≤ ‖a‖₁`) which is *not* an isomorphism in `SemiNormedGrp` (its inverse
  would be a bounded map, contradicted by the indicators `wₙ`), yet the realized map
  in `CondensedAb` *is* an isomorphism, because both norms induce the discrete
  topology, so the set-theoretic identity in the reverse direction is continuous.

* **Stage 2 – it does not preserve epimorphisms (is not right exact).** With `ℝ`
  carrying the discrete group norm `‖x‖_d = |x| + [x ≠ 0]`, the identity
  `R_d ⟶ R` is a surjective bounded map, hence an epimorphism in `SemiNormedGrp`,
  but its realization is not an epimorphism in `CondensedAb`.

The `ℓ¹` norm and the discrete norm are built by hand exactly as the sup norm was
built in `FullnessCounterexample.lean`.

Note. `SheafFullnessCounterexample.lean` (one of the existing files) has a
pre-existing broken import (`import RequestProject.…`) and does not compile; since
the task forbids modifying existing files, it cannot be imported here. The small
amount of `ULift`/postcomposition machinery it contains is re-established below.
-/

open scoped BigOperators
open scoped Classical
open CategoryTheory
open ForgetfulNotFull

namespace EmbeddingProfile

/-! ## The `ℓ¹` norm on `ℕ →₀ ℤ` -/

/-- The `ℕ`-valued `ℓ¹` size: the sum of coordinatewise absolute values. -/
def l1Nat (a : ℕ →₀ ℤ) : ℕ := ∑ n ∈ a.support, (a n).natAbs

/-- Restricting the sum over the union of two supports back to one support. -/
lemma sum_union_eq_l1Nat (a b : ℕ →₀ ℤ) :
    ∑ n ∈ (a.support ∪ b.support), (a n).natAbs = l1Nat a := by
  unfold l1Nat
  refine (Finset.sum_subset Finset.subset_union_left ?_).symm
  intro n _ hn; simp [Finsupp.notMem_support_iff.mp hn]

/-- Triangle inequality for `l1Nat`. -/
lemma l1Nat_add_le (a b : ℕ →₀ ℤ) : l1Nat (a + b) ≤ l1Nat a + l1Nat b := by
  unfold l1Nat
  calc ∑ n ∈ (a+b).support, ((a+b) n).natAbs
      ≤ ∑ n ∈ (a.support ∪ b.support), ((a+b) n).natAbs :=
        Finset.sum_le_sum_of_subset Finsupp.support_add
    _ ≤ ∑ n ∈ (a.support ∪ b.support), ((a n).natAbs + (b n).natAbs) := by
        apply Finset.sum_le_sum; intro n _
        rw [Finsupp.add_apply]; exact Int.natAbs_add_le _ _
    _ = ∑ n ∈ (a.support ∪ b.support), (a n).natAbs
        + ∑ n ∈ (a.support ∪ b.support), (b n).natAbs := Finset.sum_add_distrib
    _ = l1Nat a + l1Nat b := by
        rw [sum_union_eq_l1Nat a b, Finset.union_comm, sum_union_eq_l1Nat b a]

/-- `l1Nat a = 0` forces `a = 0`. -/
lemma l1Nat_eq_zero (a : ℕ →₀ ℤ) (h : l1Nat a = 0) : a = 0 := by
  unfold l1Nat at h; rw [Finset.sum_eq_zero_iff] at h
  ext n
  by_cases hn : n ∈ a.support
  · have := h n hn; simpa using this
  · simpa using (Finsupp.notMem_support_iff.mp hn)

/-- `l1Nat` is invariant under negation. -/
lemma l1Nat_neg (a : ℕ →₀ ℤ) : l1Nat (-a) = l1Nat a := by unfold l1Nat; simp

/-- Each coordinate is bounded by the `ℓ¹` size. -/
lemma coord_le_l1Nat (a : ℕ →₀ ℤ) (n : ℕ) : (a n).natAbs ≤ l1Nat a := by
  unfold l1Nat
  by_cases hn : n ∈ a.support
  · exact Finset.single_le_sum (f := fun m => (a m).natAbs) (by intros; positivity) hn
  · simp [Finsupp.notMem_support_iff.mp hn]

/-- The sup size is bounded by the `ℓ¹` size (`‖a‖∞ ≤ ‖a‖₁`). -/
lemma supNat_le_l1Nat (a : ℕ →₀ ℤ) : supNat a ≤ l1Nat a := by
  unfold supNat
  exact Finset.sup_le fun n _ => coord_le_l1Nat a n

/-! ## The `ℓ¹`-normed group `L1Base` -/

/-- A type synonym of `ℕ →₀ ℤ` carrying the `ℓ¹` norm (`ℕ →₀ ℤ` already carries the
sup norm globally, from `FullnessCounterexample`). -/
def L1Base := ℕ →₀ ℤ

noncomputable instance : AddCommGroup L1Base := inferInstanceAs (AddCommGroup (ℕ →₀ ℤ))

/-- The (identity) inclusion `L1Base → (ℕ →₀ ℤ)`. -/
def down1 (a : L1Base) : ℕ →₀ ℤ := a

/-- The (identity) inclusion `(ℕ →₀ ℤ) → L1Base`. -/
def up1 (a : ℕ →₀ ℤ) : L1Base := a

@[simp] lemma down1_up1 (a : ℕ →₀ ℤ) : down1 (up1 a) = a := rfl
@[simp] lemma up1_down1 (a : L1Base) : up1 (down1 a) = a := rfl
lemma down1_zero : down1 0 = 0 := rfl
lemma down1_add (a b : L1Base) : down1 (a + b) = down1 a + down1 b := rfl
lemma down1_neg (a : L1Base) : down1 (-a) = -down1 a := rfl

/-- The `ℓ¹` norm as an `AddGroupNorm` on `L1Base`. -/
noncomputable def l1Norm : AddGroupNorm L1Base where
  toFun a := (l1Nat (down1 a) : ℝ)
  map_zero' := by show ((l1Nat (down1 0) : ℝ)) = 0; rw [down1_zero]; simp [l1Nat]
  add_le' a b := by
    show ((l1Nat (down1 (a+b)) : ℝ)) ≤ (l1Nat (down1 a) : ℝ) + (l1Nat (down1 b) : ℝ)
    rw [down1_add]; exact_mod_cast l1Nat_add_le _ _
  neg' a := by
    show ((l1Nat (down1 (-a)) : ℝ)) = (l1Nat (down1 a) : ℝ)
    rw [down1_neg, l1Nat_neg]
  eq_zero_of_map_eq_zero' a h := by
    have : l1Nat (down1 a) = 0 := by exact_mod_cast h
    have := l1Nat_eq_zero (down1 a) this
    exact this

noncomputable instance instSeminormedL1Base : SeminormedAddCommGroup L1Base :=
  l1Norm.toNormedAddCommGroup.toSeminormedAddCommGroup

/-- The `ℓ¹` norm of an element of `L1Base` is the real cast of `l1Nat`. -/
lemma l1_norm_eq (a : L1Base) : ‖a‖ = (l1Nat (down1 a) : ℝ) := rfl

/-- A nonzero element has `ℓ¹` norm at least `1`. -/
lemma one_le_l1norm {a : L1Base} (ha : a ≠ 0) : (1:ℝ) ≤ ‖a‖ := by
  rw [l1_norm_eq]
  have hne : down1 a ≠ 0 := fun h => ha (by
    have : up1 (down1 a) = up1 0 := by rw [h]
    simpa using this)
  obtain ⟨n, hn⟩ : ∃ n, (down1 a) n ≠ 0 := by
    by_contra h; push_neg at h; exact hne (by ext n; simp [h n])
  have h1 : 1 ≤ ((down1 a) n).natAbs := Int.natAbs_pos.mpr hn
  calc (1:ℝ) ≤ (((down1 a) n).natAbs : ℝ) := by exact_mod_cast h1
    _ ≤ (l1Nat (down1 a) : ℝ) := by exact_mod_cast coord_le_l1Nat _ n

/-- `L1Base` is discrete: distinct elements are at `ℓ¹` distance `≥ 1`. -/
instance instDiscreteL1Base : DiscreteTopology L1Base := by
  refine discreteTopology_iff_isOpen_singleton.mpr ?_
  intro a
  refine Metric.isOpen_singleton_iff.mpr ⟨1, one_pos, ?_⟩
  intro y hy; by_contra hne
  rw [dist_eq_norm] at hy
  have := one_le_l1norm (a := y - a) (sub_ne_zero_of_ne hne)
  linarith

/-! ## Witness elements -/

/-- The coordinatewise description of the indicator `witness N`. -/
lemma witness_apply (N k : ℕ) :
    (witness N) k = if k ∈ Finset.range (N+1) then 1 else 0 := by
  unfold witness; rw [Finset.sum_apply']; simp [Finsupp.single_apply]

/-- The `ℓ¹` size of the indicator of `{0, …, N}` is `N + 1`. -/
lemma l1Nat_witness (N : ℕ) : l1Nat (witness N) = N + 1 := by
  unfold l1Nat
  have hsupp : (witness N).support = Finset.range (N+1) := by
    ext k
    rw [Finsupp.mem_support_iff, witness_apply]
    by_cases hk : k ∈ Finset.range (N+1) <;> simp [hk]
  rw [hsupp]
  have hval : ∀ k ∈ Finset.range (N+1), ((witness N) k).natAbs = 1 := by
    intro k hk; rw [witness_apply]; simp [hk]
  rw [Finset.sum_congr rfl hval]; simp

/-! ## The two seminormed-group objects and the identity map -/

/-- `ℕ →₀ ℤ` with the sup norm, universe-lifted to `Type 1`. -/
noncomputable def Vinf : SemiNormedGrp.{1} := SemiNormedGrp.of (ULift.{1} (ℕ →₀ ℤ))

/-- `ℕ →₀ ℤ` with the `ℓ¹` norm, universe-lifted to `Type 1`. -/
noncomputable def Vone : SemiNormedGrp.{1} := SemiNormedGrp.of (ULift.{1} L1Base)

/-- The lifted source is discrete. -/
instance : DiscreteTopology (ULift.{1} (ℕ →₀ ℤ)) :=
  (Homeomorph.ulift.symm : (ℕ →₀ ℤ) ≃ₜ ULift.{1} (ℕ →₀ ℤ)).discreteTopology

/-- The lifted `ℓ¹` group is discrete. -/
instance : DiscreteTopology (ULift.{1} L1Base) :=
  (Homeomorph.ulift.symm : L1Base ≃ₜ ULift.{1} L1Base).discreteTopology

/-- The set-theoretic identity `V₁ → V∞`, as a bounded map with constant `1`
(since `‖a‖∞ ≤ ‖a‖₁`). -/
noncomputable def iotaNAGH : NormedAddGroupHom (ULift.{1} L1Base) (ULift.{1} (ℕ →₀ ℤ)) where
  toFun a := ULift.up (down1 a.down)
  map_add' a b := rfl
  bound' := ⟨1, fun a => by
    have h1 : ‖(ULift.up (down1 a.down) : ULift.{1} (ℕ →₀ ℤ))‖ = (supNat (down1 a.down) : ℝ) := by
      rw [show ‖(ULift.up (down1 a.down) : ULift.{1} (ℕ →₀ ℤ))‖ = ‖down1 a.down‖ from rfl,
        norm_finsupp_eq]
    have h2 : ‖a‖ = (l1Nat (down1 a.down) : ℝ) := by
      rw [show ‖a‖ = ‖a.down‖ from rfl, l1_norm_eq]
    rw [h1, h2, one_mul]
    exact_mod_cast supNat_le_l1Nat (down1 a.down)⟩

/-- The identity `V₁ ⟶ V∞` in `SemiNormedGrp`. -/
noncomputable def iotaHom : Vone ⟶ Vinf := SemiNormedGrp.ofHom iotaNAGH

/-- The lifted indicator, as an element of `V₁`. -/
noncomputable def wit (N : ℕ) : ULift.{1} L1Base := ULift.up (up1 (witness N))

lemma norm_wit (N : ℕ) : ‖wit N‖ = (N + 1 : ℝ) := by
  rw [show ‖wit N‖ = ‖(up1 (witness N) : L1Base)‖ from rfl, l1_norm_eq, down1_up1, l1Nat_witness]
  push_cast; ring

lemma iotaHom_wit (N : ℕ) :
    iotaHom.hom (wit N) = (ULift.up (witness N) : ULift.{1} (ℕ →₀ ℤ)) := rfl

lemma norm_iotaHom_wit (N : ℕ) : ‖iotaHom.hom (wit N)‖ = 1 := by
  rw [iotaHom_wit, show ‖(ULift.up (witness N) : ULift.{1} (ℕ →₀ ℤ))‖ = ‖witness N‖ from rfl,
    norm_witness]

/-- **`ι` is not an isomorphism in `SemiNormedGrp`.** Any inverse would be a bounded
homomorphism `V∞ ⟶ V₁` agreeing with the identity; evaluated on the indicators `wₙ`
(sup norm `1`, `ℓ¹` norm `N+1`) this forces `N + 1 ≤ C` for all `N`. -/
theorem iotaHom_not_isIso : ¬ IsIso iotaHom := by
  intro h
  set g : Vinf ⟶ Vone := inv iotaHom with hg
  have hcomp : iotaHom ≫ g = 𝟙 Vone := IsIso.hom_inv_id iotaHom
  -- `g` recovers the identity on the witnesses
  have hrec : ∀ N, g.hom (iotaHom.hom (wit N)) = wit N := by
    intro N
    exact congrArg (fun (m : Vone ⟶ Vone) => m.hom (wit N)) hcomp
  -- boundedness of `g`
  obtain ⟨N, hN⟩ := exists_nat_gt ‖g.hom‖
  have hb : ‖g.hom (iotaHom.hom (wit N))‖ ≤ ‖g.hom‖ * ‖iotaHom.hom (wit N)‖ :=
    g.hom.le_opNorm _
  rw [hrec N, norm_wit N, norm_iotaHom_wit N, mul_one] at hb
  linarith

/-! ## The realized map is an isomorphism in `CondensedAb`

Both norms induce the discrete topology, so the set-theoretic identity in the reverse
direction is continuous and additive. Postcomposition by it produces a two-sided
inverse to `semiNormedGrpToCondensedAb.map ι`. -/

/-- Postcomposition by a continuous additive map, as a morphism of the `ModuleCat`-valued
presheaves underlying `banachCondensed` (a generic version of `banachPresheafMap`, valid
for maps that need not be bounded). -/
def contPostcomp {A B : Type 1} [SeminormedAddCommGroup A] [SeminormedAddCommGroup B]
    (h : A →+ B) (hc : Continuous h) : banachPresheaf A ⟶ banachPresheaf B where
  app S := ModuleCat.ofHom {
    toFun := fun g => (ContinuousMap.mk h hc).comp g
    map_add' := by intro a b; ext x; exact map_add h _ _
    map_smul' := by intro n a; ext x; simp [ContinuousMap.smul_apply] }
  naturality := by intro S T f; ext g; rfl

/-- The reverse set-theoretic identity `V∞ → V₁`, additive. -/
noncomputable def rhoHom : (ULift.{1} (ℕ →₀ ℤ)) →+ (ULift.{1} L1Base) where
  toFun a := ULift.up (up1 a.down)
  map_zero' := rfl
  map_add' _ _ := rfl

/-- The reverse identity is continuous because its source is discrete. -/
lemma rhoHom_continuous : Continuous rhoHom := continuous_of_discreteTopology

/-- The inverse condensed morphism, given by postcomposition by the reverse identity. -/
noncomputable def invCond :
    banachCondensed (ULift.{1} (ℕ →₀ ℤ)) ⟶ banachCondensed (ULift.{1} L1Base) :=
  ⟨contPostcomp rhoHom rhoHom_continuous⟩

/-- **The realized map `semiNormedGrpToCondensedAb.map ι` is an isomorphism.** Its inverse
is postcomposition by the (continuous, additive) reverse identity; the two composites are
the identity because `ρ ∘ ι` and `ι ∘ ρ` are the identity pointwise. -/
theorem map_iotaHom_isIso : IsIso (semiNormedGrpToCondensedAb.map iotaHom) := by
  refine ⟨⟨invCond, ?_, ?_⟩⟩
  · apply Sheaf.Hom.ext
    rw [Sheaf.comp_val, Sheaf.id_val]
    ext S g₀
    rfl
  · apply Sheaf.Hom.ext
    rw [Sheaf.comp_val, Sheaf.id_val]
    ext S g₀
    rfl

/-- **The embedding does not reflect isomorphisms.** There is a morphism `f` of seminormed
groups whose realization is an isomorphism of condensed abelian groups while `f` itself is
not an isomorphism. -/
theorem semiNormedGrpToCondensedAb_not_reflects_isos :
    ∃ (A B : SemiNormedGrp.{1}) (f : A ⟶ B),
      IsIso (semiNormedGrpToCondensedAb.map f) ∧ ¬ IsIso f :=
  ⟨Vone, Vinf, iotaHom, map_iotaHom_isIso, iotaHom_not_isIso⟩

/-!
# Stage 2: the embedding does not preserve epimorphisms

We put on `ℝ` the *discrete* group norm `‖x‖_d = |x| + [x ≠ 0]`, giving `R_d`. The
identity `R_d ⟶ R` (to `ℝ` with its usual norm) is a surjective bounded map, hence an
epimorphism in `SemiNormedGrp`; but its realization is not an epimorphism in `CondensedAb`.
-/

/-- A type synonym of `ℝ` carrying the discrete group norm `‖x‖_d = |x| + [x ≠ 0]`. -/
def Rd := ℝ

noncomputable instance : AddCommGroup Rd := inferInstanceAs (AddCommGroup ℝ)

/-- The (identity) inclusion `Rd → ℝ`. -/
def downR (x : Rd) : ℝ := x
/-- The (identity) inclusion `ℝ → Rd`. -/
def upR (x : ℝ) : Rd := x
@[simp] lemma downR_up (x : ℝ) : downR (upR x) = x := rfl
@[simp] lemma up_downR (x : Rd) : upR (downR x) = x := rfl
lemma downR_zero : downR 0 = 0 := rfl
lemma downR_add (x y : Rd) : downR (x + y) = downR x + downR y := rfl
lemma downR_neg (x : Rd) : downR (-x) = - downR x := rfl
lemma downR_inj {a : Rd} (h : downR a = 0) : a = 0 := h

/-- The indicator part of the discrete norm obeys the triangle inequality. -/
lemma ind_add_le (x y : ℝ) :
    (if x + y = 0 then (0:ℝ) else 1) ≤ (if x = 0 then 0 else 1) + (if y = 0 then 0 else 1) := by
  by_cases hx : x = 0 <;> by_cases hy : y = 0 <;> by_cases hxy : x + y = 0 <;> simp_all

/-- The discrete group norm on `Rd`. -/
noncomputable def dNorm : AddGroupNorm Rd where
  toFun a := |downR a| + (if downR a = 0 then (0:ℝ) else 1)
  map_zero' := by rw [downR_zero]; simp
  add_le' a b := by
    rw [downR_add]
    have h1 : |downR a + downR b| ≤ |downR a| + |downR b| := abs_add_le _ _
    have h2 := ind_add_le (downR a) (downR b)
    calc |downR a + downR b| + (if downR a + downR b = 0 then (0:ℝ) else 1)
        ≤ (|downR a| + |downR b|)
            + ((if downR a = 0 then (0:ℝ) else 1) + (if downR b = 0 then 0 else 1)) :=
          add_le_add h1 h2
      _ = _ := by ring
  neg' a := by rw [downR_neg, abs_neg]; simp [neg_eq_zero]
  eq_zero_of_map_eq_zero' a h := by
    have hnn : (0:ℝ) ≤ (if downR a = 0 then (0:ℝ) else 1) := by split_ifs <;> norm_num
    have habs : |downR a| = 0 := le_antisymm (by nlinarith [abs_nonneg (downR a)]) (abs_nonneg _)
    exact downR_inj (abs_eq_zero.mp habs)

noncomputable instance instSeminormedRd : SeminormedAddCommGroup Rd :=
  dNorm.toNormedAddCommGroup.toSeminormedAddCommGroup

lemma dNorm_eq (a : Rd) : ‖a‖ = |downR a| + (if downR a = 0 then (0:ℝ) else 1) := rfl

/-- The usual norm on `ℝ` bounds the absolute value part; a nonzero element has discrete
norm at least `1`. -/
lemma one_le_dNorm {a : Rd} (ha : a ≠ 0) : (1:ℝ) ≤ ‖a‖ := by
  rw [dNorm_eq]
  have hne : downR a ≠ 0 := fun h => ha (downR_inj h)
  rw [if_neg hne]; have := abs_nonneg (downR a); linarith

lemma abs_le_dNorm (a : Rd) : |downR a| ≤ ‖a‖ := by
  rw [dNorm_eq]; split_ifs <;> linarith [abs_nonneg (downR a)]

/-- `Rd` is discrete. -/
instance instDiscreteRd : DiscreteTopology Rd := by
  refine discreteTopology_iff_isOpen_singleton.mpr ?_
  intro a
  refine Metric.isOpen_singleton_iff.mpr ⟨1, one_pos, ?_⟩
  intro y hy; by_contra hne
  rw [dist_eq_norm] at hy
  have := one_le_dNorm (a := y - a) (sub_ne_zero_of_ne hne); linarith

/-- The lifted discrete real line is discrete. -/
instance : DiscreteTopology (ULift.{1} Rd) :=
  (Homeomorph.ulift.symm : Rd ≃ₜ ULift.{1} Rd).discreteTopology

/-! ## The surjective epimorphism `π : R_d ⟶ R` -/

/-- `ℝ` with the discrete norm, universe-lifted to `Type 1`. -/
noncomputable def Rdobj : SemiNormedGrp.{1} := SemiNormedGrp.of (ULift.{1} Rd)

/-- `ℝ` with its usual norm, universe-lifted to `Type 1`. -/
noncomputable def Robj : SemiNormedGrp.{1} := SemiNormedGrp.of (ULift.{1} ℝ)

/-- The set-theoretic identity `R_d → R`, bounded with constant `1` (since `|x| ≤ ‖x‖_d`). -/
noncomputable def piNAGH : NormedAddGroupHom (ULift.{1} Rd) (ULift.{1} ℝ) where
  toFun a := ULift.up (downR a.down)
  map_add' _ _ := rfl
  bound' := ⟨1, fun a => by
    have h1 : ‖(ULift.up (downR a.down) : ULift.{1} ℝ)‖ = |downR a.down| := by
      rw [show ‖(ULift.up (downR a.down) : ULift.{1} ℝ)‖ = ‖downR a.down‖ from rfl,
        Real.norm_eq_abs]
    rw [h1, one_mul, show ‖a‖ = ‖a.down‖ from rfl]
    exact abs_le_dNorm a.down⟩

/-- The identity `R_d ⟶ R` in `SemiNormedGrp`. -/
noncomputable def piHom : Rdobj ⟶ Robj := SemiNormedGrp.ofHom piNAGH

/-- `π` is surjective. -/
lemma piHom_surjective : Function.Surjective piHom.hom := by
  intro y
  exact ⟨ULift.up (upR y.down), rfl⟩

/-- **`π` is an epimorphism in `SemiNormedGrp`**, being surjective. -/
theorem piHom_epi : Epi piHom := by
  constructor
  intro C g h hgh
  apply SemiNormedGrp.hom_ext
  apply NormedAddGroupHom.ext
  intro b
  obtain ⟨a, rfl⟩ := piHom_surjective b
  exact congrArg (fun (m : Rdobj ⟶ C) => m.hom a) hgh

/-! ## The realization of `π` is not an epimorphism -/

/-- The unit interval `[0,1]` as a compact Hausdorff space. -/
noncomputable def II : CompHaus.{0} := CompHaus.of (↑(Set.Icc (0:ℝ) 1))

/-- The inclusion `[0,1] ↪ ℝ`, as a section of `banachCondensed (ULift ℝ)` over `II`. -/
def inclSection : C(↑(Set.Icc (0:ℝ) 1), ULift.{1} ℝ) :=
  ⟨fun s => ULift.up s.val, by fun_prop⟩

/-- **Key obstruction.** A continuous map `x` from a compact space into the *discrete*
`ULift R_d` has finite image; if its underlying real values equal `φ`, a surjection onto
`[0,1]`, then `[0,1]` would be finite - impossible. -/
lemma finite_range_contradiction {S' : Type} [TopologicalSpace S'] [CompactSpace S']
    (x : C(S', ULift.{1} Rd)) (φ : S' → ↑(Set.Icc (0:ℝ) 1))
    (hsurj : Function.Surjective φ)
    (heq : ∀ s', downR (x s').down = (φ s').val) : False := by
  have hxfin : (Set.range x).Finite := (isCompact_range x.continuous).finite_of_discrete
  have hfin : (Set.range (fun s' => downR (x s').down)).Finite := by
    have hsub : Set.range (fun s' => downR (x s').down)
        ⊆ (fun u : ULift.{1} Rd => downR u.down) '' (Set.range x) := by
      rintro _ ⟨s', rfl⟩; exact ⟨x s', ⟨s', rfl⟩, rfl⟩
    exact (hxfin.image _).subset hsub
  have hrange : Set.range (fun s' => downR (x s').down) = Set.Icc (0:ℝ) 1 := by
    have hf : (fun s' => downR (x s').down) = (Subtype.val ∘ φ) := funext heq
    rw [hf, Set.range_comp, hsurj.range_eq, Set.image_univ, Subtype.range_coe]
  rw [hrange] at hfin
  exact (Set.infinite_coe_iff.mp (Set.Icc.infinite (by norm_num : (0:ℝ) < 1))) hfin

/-- **The realization of `π` is not an epimorphism in `CondensedAb`.** By the local
surjectivity criterion, the section `[0,1] ↪ ℝ` admits no local lift: any lift along a
jointly surjective family would be a continuous map from a compact space into the discrete
`R_d`, hence of finite image, contradicting the infinitude of `[0,1]`. -/
theorem map_piHom_not_epi : ¬ Epi (semiNormedGrpToCondensedAb.map piHom) := by
  rw [CondensedMod.epi_iff_locallySurjective_on_compHaus (ULift.{1} ℤ)
    (semiNormedGrpToCondensedAb.map piHom)]
  push_neg
  refine ⟨II, inclSection, ?_⟩
  intro S' φ hsurj x heq
  apply finite_range_contradiction x (fun s' => (ConcreteCategory.hom φ) s') hsurj
  intro s'
  exact congrArg (fun (g : C((S' : CompHaus), ULift.{1} ℝ)) => (g s').down) heq

/-- **The embedding does not preserve epimorphisms** (hence is not right exact). There is
an epimorphism `f` in `SemiNormedGrp` whose realization is not an epimorphism in
`CondensedAb`. -/
theorem semiNormedGrpToCondensedAb_not_preserves_epi :
    ∃ (A B : SemiNormedGrp.{1}) (f : A ⟶ B),
      Epi f ∧ ¬ Epi (semiNormedGrpToCondensedAb.map f) :=
  ⟨Rdobj, Robj, piHom, piHom_epi, map_piHom_not_epi⟩

end EmbeddingProfile
