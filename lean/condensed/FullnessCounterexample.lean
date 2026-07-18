import Mathlib

open scoped BigOperators
open scoped Real
open scoped Nat
open scoped Classical
open scoped Pointwise

set_option maxHeartbeats 8000000
set_option maxRecDepth 4000
set_option synthInstance.maxHeartbeats 40000
set_option synthInstance.maxSize 128

set_option relaxedAutoImplicit false
set_option autoImplicit false

set_option grind.warning false

open CategoryTheory

namespace ForgetfulNotFull

/-! ## The presheaf `S ↦ C(S, A)` for a topological abelian group `A` -/

/-- For a topological abelian group `A`, the presheaf on `CompHaus` sending a compact
Hausdorff space `S` to the group `C(S, A)` of continuous maps, with restriction by
precomposition. -/
noncomputable def condensedObj (A : Type) [TopologicalSpace A] [AddCommGroup A]
    [IsTopologicalAddGroup A] : CompHausᵒᵖ ⥤ AddCommGrpCat where
  obj S := AddCommGrpCat.of C((S.unop : CompHaus), A)
  map f := AddCommGrpCat.ofHom (ContinuousMap.compAddMonoidHom' f.unop.hom.hom)
  map_id := by intro S; rfl
  map_comp := by intro S T U f g; rfl

/-- A continuous additive group homomorphism `h : A → B` induces a morphism of presheaves
`condensedObj A ⟶ condensedObj B` by postcomposition. -/
noncomputable def condensedMap {A B : Type} [TopologicalSpace A] [AddCommGroup A]
    [IsTopologicalAddGroup A] [TopologicalSpace B] [AddCommGroup B] [IsTopologicalAddGroup B]
    (h : A →+ B) (hc : Continuous h) : condensedObj A ⟶ condensedObj B where
  app S := AddCommGrpCat.ofHom
    { toFun := fun g => (ContinuousMap.mk h hc).comp g
      map_zero' := by ext x; simp [h.map_zero]
      map_add' := by intro a b; ext x; simp [h.map_add] }
  naturality := by intro S T f; rfl

/-! ## Faithfulness: postcomposition is determined by its values on points -/

/-- Evaluating `condensedMap` at the one-point space recovers `h` pointwise: if two
continuous additive homomorphisms `h, h'` induce the same presheaf morphism, then they
agree on every point. -/
lemma condensedMap_eq_imp {A B : Type} [TopologicalSpace A] [AddCommGroup A]
    [IsTopologicalAddGroup A] [TopologicalSpace B] [AddCommGroup B] [IsTopologicalAddGroup B]
    (h h' : A →+ B) (hc : Continuous h) (hc' : Continuous h')
    (heq : condensedMap h hc = condensedMap h' hc') (a : A) : h a = h' a := by
  have happ := NatTrans.congr_app heq (Opposite.op (CompHaus.of PUnit))
  have h1 := congrArg
    (fun (m : _) => (AddCommGrpCat.Hom.hom m) (ContinuousMap.const _ a)) happ
  simp only at h1
  have h2 := congrArg
    (fun (g : C((CompHaus.of PUnit : CompHaus), B)) => g PUnit.unit) h1
  simpa [condensedMap] using h2

/-- **Faithfulness on morphisms.** For seminormed abelian groups `A`, `B`, postcomposition
is injective on bounded maps: if two bounded maps `φ ψ : NormedAddGroupHom A B` induce the
same presheaf morphism, then `φ = ψ`. -/
theorem condensedMap_injective {A B : Type} [SeminormedAddCommGroup A]
    [SeminormedAddCommGroup B] (u v : NormedAddGroupHom A B)
    (h : condensedMap u.toAddMonoidHom u.continuous
        = condensedMap v.toAddMonoidHom v.continuous) :
    u = v := by
  ext a
  exact condensedMap_eq_imp u.toAddMonoidHom v.toAddMonoidHom u.continuous v.continuous h a

/-! ## Packaging as a functor `E : SemiNormedGrp ⥤ (CompHausᵒᵖ ⥤ AddCommGrpCat)` -/

/-- The functor sending a seminormed group to the presheaf `S ↦ C(S, ·)` and a bounded map
to the postcomposition morphism. -/
noncomputable def E : SemiNormedGrp ⥤ (CompHausᵒᵖ ⥤ AddCommGrpCat) where
  obj X := condensedObj X
  map f := condensedMap f.hom.toAddMonoidHom f.hom.continuous
  map_id X := by ext S g; rfl
  map_comp f g := by ext S x; rfl

/-- `E` is faithful, by `condensedMap_injective`. -/
instance : E.Faithful where
  map_injective {X Y f g} h := by
    have hh : f.hom = g.hom := condensedMap_injective f.hom g.hom h
    exact SemiNormedGrp.ext_iff.mpr (congrFun (congrArg DFunLike.coe hh))

/-! ## The counterexample to fullness: the summation map -/

/-- The `ℕ`-valued sup of coordinatewise absolute values.  The sup-norm on `ℕ →₀ ℤ` is
the real cast of this.  Because all coordinates are integers, this norm is discrete around
`0`, so every additive map out of it is continuous; yet summation is unbounded for it. -/
def supNat (a : ℕ →₀ ℤ) : ℕ := a.support.sup fun n => (a n).natAbs

/-- Each coordinate is bounded by the sup. -/
lemma natAbs_le_supNat (a : ℕ →₀ ℤ) (n : ℕ) : (a n).natAbs ≤ supNat a := by
  by_cases hn : n ∈ a.support;
  · exact Finset.le_sup ( f := fun n => Int.natAbs ( a n ) ) hn;
  · aesop

/-- Triangle inequality for `supNat`. -/
lemma supNat_add_le (a b : ℕ →₀ ℤ) : supNat (a + b) ≤ supNat a + supNat b := by
  -- By definition of supremum, we know that for any $n \in (a + b).support$, $|(a + b) n| \leq |a n| + |b n|$.
  have h_bound : ∀ n ∈ (a + b).support, Int.natAbs ((a + b) n) ≤ Int.natAbs (a n) + Int.natAbs (b n) := by
    exact fun n hn => by rw [ Finsupp.add_apply ] ; exact Int.natAbs_add_le _ _;
  convert Finset.sup_le fun n hn => ?_;
  exact le_trans ( h_bound n hn ) ( add_le_add ( natAbs_le_supNat a n ) ( natAbs_le_supNat b n ) )

/-- `supNat` is preserved under negation. -/
lemma supNat_neg (a : ℕ →₀ ℤ) : supNat (-a) = supNat a := by
  unfold supNat; aesop;

/-- `supNat a = 0` forces `a = 0`. -/
lemma supNat_eq_zero (a : ℕ →₀ ℤ) (h : supNat a = 0) : a = 0 := by
  ext n;
  exact Int.natAbs_eq_zero.mp ( le_antisymm ( h ▸ natAbs_le_supNat a n ) ( Nat.zero_le _ ) )

noncomputable def supNorm : AddGroupNorm (ℕ →₀ ℤ) where
  toFun a := (supNat a : ℝ)
  map_zero' := by simp [supNat]
  add_le' a b := by exact_mod_cast supNat_add_le a b
  neg' a := by rw [supNat_neg]
  eq_zero_of_map_eq_zero' a h := by
    refine supNat_eq_zero a ?_
    exact_mod_cast h

noncomputable instance instSeminormedFinsupp : SeminormedAddCommGroup (ℕ →₀ ℤ) :=
  (supNorm.toNormedAddCommGroup).toSeminormedAddCommGroup

/-- The norm of a finitely supported integer sequence is the (real-cast of the) sup of the
coordinatewise absolute values. -/
lemma norm_finsupp_eq (a : ℕ →₀ ℤ) : ‖a‖ = (supNat a : ℝ) := rfl

/-- A nonzero finitely supported integer sequence has norm at least `1`. -/
lemma one_le_norm_of_ne_zero {a : ℕ →₀ ℤ} (ha : a ≠ 0) : (1 : ℝ) ≤ ‖a‖ := by
  -- By definition of `supNat`, we know that for any `a` with `a ≠ 0`, there exists `n ∈ a.support` such that `Int.natAbs (a n) ≥ 1`.
  obtain ⟨n, hn⟩ : ∃ n ∈ a.support, 1 ≤ Int.natAbs (a n) := by
    contrapose! ha; aesop;
  rw [ norm_finsupp_eq ] ; exact_mod_cast hn.2.trans ( natAbs_le_supNat a n )

/-- With the sup-norm, the group `ℕ →₀ ℤ` is discrete: distinct integer sequences are at
distance `≥ 1`. -/
instance instDiscreteFinsupp : DiscreteTopology (ℕ →₀ ℤ) := by
  refine' discreteTopology_iff_isOpen_singleton.mpr _;
  intro a;
  refine' Metric.isOpen_singleton_iff.mpr _;
  use 1; norm_num; intro y hy; contrapose! hy; simp_all +decide [ dist_eq_norm ] ;
  exact one_le_norm_of_ne_zero ( sub_ne_zero_of_ne hy )

/-- The summation homomorphism `a ↦ Σ_n a n` on finitely supported integer sequences. -/
def sumHom : (ℕ →₀ ℤ) →+ ℤ where
  toFun a := a.sum (fun _ v => v)
  map_zero' := by simp
  map_add' a b := by
    exact Finsupp.sum_add_index' (fun _ => rfl) (fun _ b₁ b₂ => rfl)

/-- Summation is continuous, since the source has the discrete topology. -/
lemma sumHom_continuous : Continuous (sumHom) := continuous_of_discreteTopology

/-- The natural transformation induced by summation. -/
noncomputable def sumNatTrans :
    condensedObj (ℕ →₀ ℤ) ⟶ condensedObj ℤ :=
  condensedMap sumHom sumHom_continuous

/-- The indicator of `{0, 1, …, N}` as a finitely supported integer sequence. -/
noncomputable def witness (N : ℕ) : ℕ →₀ ℤ :=
  ∑ i ∈ Finset.range (N + 1), Finsupp.single i (1 : ℤ)

/-- Summation of the indicator of `{0, …, N}` equals `N + 1`. -/
lemma sumHom_witness (N : ℕ) : sumHom (witness N) = (N + 1 : ℤ) := by
  unfold witness;
  unfold sumHom; norm_num;

/-- The sup-norm of the indicator of `{0, …, N}` is `1`. -/
lemma norm_witness (N : ℕ) : ‖witness N‖ = 1 := by
  -- By definition of `supNat`, we know that `supNat (witness N) = 1`.
  have h_supNat : supNat (witness N) = 1 := by
    refine' le_antisymm ( Finset.sup_le _ ) _;
    · intro b hb; unfold witness at hb ⊢; simp_all +decide [ Finsupp.single_apply, Finset.sum_apply' ] ;
    · convert natAbs_le_supNat ( witness N ) 0;
      unfold witness; norm_num [ Finsupp.single_apply ] ;
  rw [ norm_finsupp_eq, h_supNat, Nat.cast_one ]

/-- **No bounded map realizes summation.** There is no `NormedAddGroupHom (ℕ →₀ ℤ) ℤ`
whose underlying function is the summation map: summation is unbounded with respect to the
sup-norm (witnessed by the indicators of `{0, …, n}`, which have norm `1` and sum `n + 1`). -/
theorem no_normedAddGroupHom :
    ¬ ∃ u : NormedAddGroupHom (ℕ →₀ ℤ) ℤ, ∀ a, u a = sumHom a := by
  rintro ⟨u, hu⟩
  -- From boundedness of `u` and `u a = sumHom a`, we get `N + 1 ≤ ‖u‖` for all `N`.
  obtain ⟨N, hN⟩ := exists_nat_gt ‖u‖
  have hb : ‖u (witness N)‖ ≤ ‖u‖ * ‖witness N‖ := u.le_opNorm _
  rw [hu (witness N), norm_witness N, mul_one] at hb
  have : ‖sumHom (witness N)‖ = (N : ℝ) + 1 := by
    rw [sumHom_witness N]
    push_cast [Int.norm_eq_abs]
    rw [abs_of_nonneg (by positivity)]
  rw [this] at hb
  linarith

/-- **The embedding is not full.** The functor `E` is not full: the summation natural
transformation `sumNatTrans` has no preimage under `E`, since any such preimage would be a
bounded map realizing summation, contradicting `no_normedAddGroupHom`. -/
theorem embedding_not_full : ¬ E.Full := by
  intro hfull
  obtain ⟨f, hf⟩ := (E.map_surjective (X := SemiNormedGrp.of (ℕ →₀ ℤ))
    (Y := SemiNormedGrp.of ℤ)) sumNatTrans
  -- `E.map f = sumNatTrans = condensedMap sumHom …`
  have hval : ∀ a, f.hom a = sumHom a := by
    intro a
    have := condensedMap_eq_imp f.hom.toAddMonoidHom sumHom f.hom.continuous
      sumHom_continuous hf a
    simpa using this
  exact no_normedAddGroupHom ⟨f.hom, hval⟩

end ForgetfulNotFull
