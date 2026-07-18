import RequestProject.Cob2

/-!
# A diagonal finite-state Frobenius theory

This file instantiates the ordinary Frobenius presentation from `Cob2.lean` on
the rank-`n` module `Fin n → ℤ`. It computes the torus and the standard
connected genus-word family. Since the source presentation is not yet proved
to be the geometric symmetric-monoidal bordism category, these are algebraic
word-evaluation theorems rather than a completed geometric or finite-group
Dijkgraaf-Witten construction.
-/

open CategoryTheory MonoidalCategory
open ModuleCat.MonoidalCategory

noncomputable section

namespace DijkgraafWitten

abbrev ZnFun (n : ℕ) := Fin n → ℤ
abbrev ZnObj (n : ℕ) : ModuleCat ℤ := ModuleCat.of ℤ (ZnFun n)

private def znBasis (n : ℕ) : Module.Basis (Fin n) ℤ (ZnFun n) :=
  Pi.basisFun ℤ (Fin n)

private def znMul (n : ℕ) : ZnObj n ⊗ ZnObj n ⟶ ZnObj n :=
  ModuleCat.ofHom (LinearMap.mul' ℤ (ZnFun n))

private def znUnit (n : ℕ) : 𝟙_ (ModuleCat ℤ) ⟶ ZnObj n :=
  ModuleCat.ofHom (Algebra.linearMap ℤ (ZnFun n))

private def znComul (n : ℕ) : ZnObj n ⟶ ZnObj n ⊗ ZnObj n :=
  ModuleCat.ofHom <| ((znBasis n).constr ℤ) fun i ↦ (znBasis n i) ⊗ₜ[ℤ] (znBasis n i)

private def znCounit (n : ℕ) : ZnObj n ⟶ 𝟙_ (ModuleCat ℤ) :=
  ModuleCat.ofHom
    { toFun := fun x ↦ ∑ i, x i
      map_add' := by intro x y; simp [Finset.sum_add_distrib]
      map_smul' := by intro r x; simp [Finset.mul_sum] }

@[simp] lemma znMul_tmul (n : ℕ) (x y : ZnFun n) :
    znMul n (x ⊗ₜ[ℤ] y) = x * y := by
      rfl

@[simp] lemma znUnit_apply (n : ℕ) (r : ℤ) :
    znUnit n r = r • (1 : ZnFun n) := by
      exact Algebra.algebraMap_eq_smul_one r

@[simp] lemma znComul_basis (n : ℕ) (i : Fin n) :
    znComul n (znBasis n i) = (znBasis n i) ⊗ₜ[ℤ] (znBasis n i) := by
      convert ( znBasis n ).constr_basis ℤ ( fun i => ( znBasis n ) i ⊗ₜ[ℤ] ( znBasis n ) i ) i using 1

@[simp] lemma znCounit_apply (n : ℕ) (x : ZnFun n) :
    znCounit n x = ∑ i, x i := rfl

lemma zn_mul_assoc (n : ℕ) :
    znMul n ▷ ZnObj n ≫ znMul n =
      (α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom ≫ ZnObj n ◁ znMul n ≫ znMul n := by
        ext x;
        induction x using TensorProduct.induction_on;
        · aesop;
        · rename_i x y;
          induction x using TensorProduct.induction_on;
          · simp +decide [ znMul ];
          · rename_i a b;
            convert mul_assoc ( a ‹_› ) ( b ‹_› ) ( y ‹_› ) using 1;
          · simp_all +decide [ TensorProduct.add_tmul ];
        · simp_all +decide

lemma zn_unit_mul (n : ℕ) : znUnit n ▷ ZnObj n ≫ znMul n = (λ_ (ZnObj n)).hom := by
  exact tensor_ext fun m => congrFun rfl

lemma zn_mul_unit (n : ℕ) : ZnObj n ◁ znUnit n ≫ znMul n = (ρ_ (ZnObj n)).hom := by
  convert tensor_ext _;
  intro m n_1; simp +decide [ znMul, znUnit ] ;
  exact mul_comm _ _

lemma zn_comul_coassoc (n : ℕ) :
    znComul n ≫ ZnObj n ◁ znComul n =
      znComul n ≫ znComul n ▷ ZnObj n ≫ (α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom := by
  apply ModuleCat.hom_ext
  apply (znBasis n).ext
  intro i
  rw [ModuleCat.comp_apply, ModuleCat.comp_apply, ModuleCat.comp_apply,
    znComul_basis]
  change (ZnObj n ◁ znComul n) ((znBasis n i) ⊗ₜ[ℤ] (znBasis n i)) =
    (α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom
      ((znComul n ▷ ZnObj n) ((znBasis n i) ⊗ₜ[ℤ] (znBasis n i)))
  change (znBasis n i) ⊗ₜ[ℤ] znComul n (znBasis n i) =
    (α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom
      (znComul n (znBasis n i) ⊗ₜ[ℤ] (znBasis n i))
  rw [znComul_basis]
  rfl

lemma zn_counit_comul (n : ℕ) :
    znComul n ≫ znCounit n ▷ ZnObj n = (λ_ (ZnObj n)).inv := by
      unfold znComul znCounit;
      ext;
      simp +decide [ znBasis, Pi.basisFun ];
      erw [ ( Module.Basis.ofEquivFun ( LinearEquiv.refl ℤ ( Fin _ → ℤ ) ) ).constr_apply ];
      simp +decide [ Finsupp.sum_fintype, Pi.single_apply ];
      erw [ ModuleCat.MonoidalCategory.whiskerRight_apply ];
      erw [ ModuleCat.ofHom_apply ] ; aesop

lemma zn_comul_counit (n : ℕ) :
    znComul n ≫ ZnObj n ◁ znCounit n = (ρ_ (ZnObj n)).inv := by
      ext x;
      simp +decide [ znComul, znCounit, znBasis, Pi.basisFun ];
      erw [ ( Module.Basis.ofEquivFun ( LinearEquiv.refl ℤ ( Fin n → ℤ ) ) ).constr_apply ] ; simp +decide [ Finsupp.sum_fintype, Pi.single_apply ];
      erw [ ModuleCat.MonoidalCategory.whiskerLeft_apply ];
      erw [ ModuleCat.ofHom_apply ] ; aesop

lemma znComul_apply (n : ℕ) (x : ZnFun n) :
    znComul n x = ∑ i, x i • ((znBasis n i) ⊗ₜ[ℤ] (znBasis n i)) := by
      erw [ ( Module.Basis.ofEquivFun ( LinearEquiv.refl ℤ ( Fin n → ℤ ) ) ).constr_apply ];
      simp +decide [ Finsupp.sum_fintype ]

lemma znComul_mul_right (n : ℕ) (x y : ZnFun n) :
    znComul n (x * y) = ∑ i, (x i * y i) • ((znBasis n i) ⊗ₜ[ℤ] (znBasis n i)) := by
  rw [znComul_apply]
  rfl

lemma mul_znBasis (n : ℕ) (x : ZnFun n) (i : Fin n) :
    x * znBasis n i = x i • znBasis n i := by
      ext j; exact (by
      unfold znBasis; by_cases hi : j = i <;> aesop;)

lemma znBasis_mul_right (n : ℕ) (i : Fin n) (y : ZnFun n) :
    znBasis n i * y = y i • znBasis n i := by
  rw [mul_comm, mul_znBasis]

lemma znBasis_mul (n : ℕ) (i j : Fin n) :
    znBasis n i * znBasis n j = if i = j then znBasis n i else 0 := by
      ext k; split_ifs <;> simp_all +decide [ Pi.single_apply,znBasis ] ;
      tauto

lemma zn_comul_mul (n : ℕ) : znComul n ≫ znMul n = 𝟙 (ZnObj n) := by
  apply ModuleCat.hom_ext
  apply (znBasis n).ext
  intro i
  change znMul n (znComul n (znBasis n i)) = znBasis n i
  rw [znComul_basis, znMul_tmul, znBasis_mul]
  simp

lemma zn_frobenius_left (n : ℕ) :
    (ZnObj n ◁ znComul n) ≫ (α_ (ZnObj n) (ZnObj n) (ZnObj n)).inv ≫
        (znMul n ▷ ZnObj n) = znMul n ≫ znComul n := by
  ext x
  induction x using TensorProduct.induction_on with
  | zero => simp
  | tmul x y =>
    have key : ∀ (i j : Fin n),
        (znMul n ▷ ZnObj n) ((α_ (ZnObj n) (ZnObj n) (ZnObj n)).inv ((znBasis n i) ⊗ₜ[ℤ] znComul n (znBasis n j))) =
        znComul n (znMul n ((znBasis n i) ⊗ₜ[ℤ] (znBasis n j))) := by
      intro i j
      rw [znComul_basis]
      rw [ModuleCat.MonoidalCategory.associator_inv_apply]
      rw [ModuleCat.MonoidalCategory.whiskerRight_apply, znMul_tmul]
      simp [znBasis_mul]
      split_ifs with hij
      · subst hij; rw [znComul_basis]
      · simp
    -- Use the fact that both sides are linear in x and y
    -- Expand using the basis
    have hx : x = ∑ i, x i • znBasis n i := by
      apply funext
      simp [znBasis, Finset.sum_apply, Pi.single_apply]
    have hy : y = ∑ j, y j • znBasis n j := by
      apply funext
      simp [znBasis, Finset.sum_apply, Pi.single_apply]
    rw [hx, hy]
    simp only [TensorProduct.tmul_sum, TensorProduct.sum_tmul, TensorProduct.tmul_smul]
    simp only [ModuleCat.comp_apply]
    simp only [map_sum, map_smul]
    apply Finset.sum_congr rfl
    intro i _
    rw [Finset.smul_sum, Finset.smul_sum]
    apply Finset.sum_congr rfl
    intro j _
    have h := key j i
    rw [ModuleCat.MonoidalCategory.whiskerLeft_apply]
    rw [← TensorProduct.smul_tmul', ← TensorProduct.smul_tmul']
    simp only [map_smul, h]
  | add x y hx hy => simp_all

lemma zn_frobenius_right (n : ℕ) :
    (znComul n ▷ ZnObj n) ≫ (α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom ≫
        (ZnObj n ◁ znMul n) = znMul n ≫ znComul n := by
  ext x
  induction x using TensorProduct.induction_on with
  | zero => simp
  | tmul x y =>
    have key : ∀ (i j : Fin n),
        (ZnObj n ◁ znMul n) ((α_ (ZnObj n) (ZnObj n) (ZnObj n)).hom ((znComul n) (znBasis n i) ⊗ₜ[ℤ] znBasis n j)) =
        znComul n (znMul n ((znBasis n i) ⊗ₜ[ℤ] (znBasis n j))) := by
      intro i j
      rw [znComul_basis]
      rw [ModuleCat.MonoidalCategory.associator_hom_apply]
      rw [ModuleCat.MonoidalCategory.whiskerLeft_apply, znMul_tmul]
      simp [znBasis_mul]
      split_ifs with hij
      · subst hij; rw [znComul_basis]
      · simp
    -- Use the fact that both sides are linear in x and y
    -- Expand using the basis
    have hx : x = ∑ i, x i • znBasis n i := by
      apply funext
      simp [znBasis, Finset.sum_apply, Pi.single_apply]
    have hy : y = ∑ j, y j • znBasis n j := by
      apply funext
      simp [znBasis, Finset.sum_apply, Pi.single_apply]
    rw [hx, hy]
    simp only [TensorProduct.tmul_sum, TensorProduct.sum_tmul, TensorProduct.tmul_smul]
    simp only [ModuleCat.comp_apply]
    simp only [map_sum, map_smul]
    apply Finset.sum_congr rfl
    intro i _
    rw [Finset.smul_sum, Finset.smul_sum]
    apply Finset.sum_congr rfl
    intro j _
    have h := key j i
    rw [ModuleCat.MonoidalCategory.whiskerRight_apply]
    simp only [map_smul]
    rw [← TensorProduct.smul_tmul', ← TensorProduct.smul_tmul']
    simp only [map_smul, h]
  | add x y hx hy => simp_all

lemma zn_mul_comm (n : ℕ) :
    (β_ (ZnObj n) (ZnObj n)).hom ≫ znMul n = znMul n := by
      convert tensor_ext _;
      simp +decide;
      intro m n; erw [ ModuleCat.MonoidalCategory.braiding_hom_apply ] ;
      exact mul_comm _ _

/-- The rank-`n` diagonal commutative Frobenius algebra over `ℤ`. -/
def frobZn (n : ℕ) : CommFrobeniusData (ModuleCat ℤ) where
  X := ZnObj n
  mul := znMul n
  unit := znUnit n
  comul := znComul n
  counit := znCounit n
  mul_assoc' := zn_mul_assoc n
  unit_mul := zn_unit_mul n
  mul_unit := zn_mul_unit n
  comul_coassoc' := zn_comul_coassoc n
  counit_comul := zn_counit_comul n
  comul_counit := zn_comul_counit n
  frobenius_left := zn_frobenius_left n
  frobenius_right := zn_frobenius_right n
  mul_comm' := zn_mul_comm n

/-- Cap, copants, pants, then cup: a closed genus-one word. -/
def torusWord : Cob2Mor 0 0 :=
  .comp (.comp (.comp .η .δ) .μ) .ε

/-- Quotient-class version of `torusWord`. -/
def torus : Cob2Hom 0 0 := ⟦torusWord⟧

/-
Evaluation of the torus partition function at `1`.
-/
theorem Z_torus (n : ℕ) :
    ((frobZn n).toCob2Functor.map torus).hom ((1 : ℤ) : 𝟙_ (ModuleCat ℤ)) = (n : ℤ) := by
      unfold CommFrobeniusData.toCob2Functor;
      unfold torus;
      unfold torusWord; norm_num [ CommFrobeniusData.interpret ] ;
      convert Finset.sum_const ( 1 : ℤ ) using 1;
      any_goals exact Finset.univ ( α := Fin n );
      · convert znCounit_apply n ( znMul n ( znComul n ( znUnit n 1 ) ) ) using 1;
        simp +decide [ znMul, znComul, znUnit, znBasis ];
        erw [ ( Pi.basisFun ℤ ( Fin n ) ).constr_apply ] ; simp +decide [ Finsupp.sum_fintype ];
        simp +decide [ LinearMap.mul', Algebra.linearMap ];
        erw [ Finset.sum_congr rfl fun i hi => Finset.sum_congr rfl fun j hj => ?_ ];
        rotate_left;
        use fun i j => if i = j then 1 else 0;
        · erw [ TensorProduct.lift.tmul ] ; aesop;
        · simp +decide;
      · norm_num

/-- The torus morphism itself is multiplication by `n` on the monoidal unit. -/
theorem Z_torus_eq_smul_id (n : ℕ) :
    (frobZn n).toCob2Functor.map torus =
      (n : ℤ) • 𝟙 (𝟙_ (ModuleCat ℤ)) := by
  apply ModuleCat.hom_ext
  apply LinearMap.ext_ring
  refine (Z_torus n).trans ?_
  change (n : ℤ) = (n : ℤ) * 1
  simp

/-- A word of `g` successive split/merge handles on one circle. -/
def handleWord : (g : ℕ) → Cob2Mor 1 1
  | 0 => .id 1
  | g + 1 => .comp (handleWord g) (.comp .δ .μ)

/-- A genus-`g` closed word: birth, `g` successive split/merge handles, then death. -/
def genusWord (g : ℕ) : Cob2Mor 0 0 :=
  .comp (.comp .η (handleWord g)) .ε

section GenericHandleCalculus

variable {C : Type*} [Category C]

/-- The `g`-fold composite of an endomorphism, composed from left to right. -/
def endomorphismPower {X : C} (f : X ⟶ X) : (g : ℕ) → X ⟶ X
  | 0 => 𝟙 X
  | g + 1 => endomorphismPower f g ≫ f

@[simp] lemma endomorphismPower_id (X : C) (g : ℕ) :
    endomorphismPower (𝟙 X) g = 𝟙 X := by
  induction g with
  | zero => rfl
  | succ g ih => simp [endomorphismPower, ih]

variable [MonoidalCategory C] [BraidedCategory C]

/-- The handle operator of a Frobenius datum is comultiplication followed by multiplication. -/
def handleOperator (A : CommFrobeniusData C) : A.X ⟶ A.X :=
  A.comul ≫ A.mul

/-- The `g`-fold power of the handle operator. -/
def handlePower (A : CommFrobeniusData C) (g : ℕ) : A.X ⟶ A.X :=
  endomorphismPower (handleOperator A) g

/-- A raw handle word is the left-unitor conjugate of the corresponding handle power. -/
theorem interpret_handleWord_generic (A : CommFrobeniusData C) (g : ℕ) :
    A.interpret (handleWord g) =
      (λ_ A.X).hom ≫ handlePower A g ≫ (λ_ A.X).inv := by
  induction g with
  | zero => simp [handleWord, handlePower, endomorphismPower]
  | succ g ih =>
      rw [handleWord, CommFrobeniusData.interpret, ih]
      simp [handlePower, endomorphismPower, handleOperator,
        CommFrobeniusData.interpret, Category.assoc]

/-- A closed genus word evaluates as unit, the corresponding handle power, then counit. -/
theorem interpret_genusWord_generic (A : CommFrobeniusData C) (g : ℕ) :
    A.interpret (genusWord g) = A.unit ≫ handlePower A g ≫ A.counit := by
  simp only [genusWord, CommFrobeniusData.interpret]
  rw [interpret_handleWord_generic]
  simp [Category.assoc]

end GenericHandleCalculus

/-- The diagonal Frobenius datum is special: one handle acts trivially on its carrier. -/
lemma frobZn_isSpecial (n : ℕ) :
    handleOperator (frobZn n) = 𝟙 (ZnObj n) := by
  change znComul n ≫ znMul n = 𝟙 (ZnObj n)
  exact zn_comul_mul n

/-- Consequently, every power of the diagonal handle operator is the identity. -/
lemma frobZn_handlePower (n g : ℕ) :
    handlePower (frobZn n) g = 𝟙 (ZnObj n) := by
  unfold handlePower
  rw [frobZn_isSpecial]
  exact endomorphismPower_id _ _

/-- The one-handle member of the genus family is the torus word in the quotient. -/
lemma genusWord_one : (⟦genusWord 1⟧ : Cob2Hom 0 0) = torus := by
  unfold genusWord handleWord torus torusWord
  change
    ((Cob2.unit ≫ ((𝟙 (1 : ℕ)) ≫ (Cob2.comul ≫ Cob2.mul))) ≫ Cob2.counit) =
      (((Cob2.unit ≫ Cob2.comul) ≫ Cob2.mul) ≫ Cob2.counit)
  simp [Category.assoc]

lemma interpret_handleWord (n g : ℕ) :
    (frobZn n).interpret (handleWord g) = 𝟙 ((frobZn n).objPow 1) := by
  rw [interpret_handleWord_generic]
  rw [frobZn_handlePower]
  simp [frobZn]

/-- Every connected closed genus word has value `n` for the diagonal datum. -/
theorem Z_genus (n g : ℕ) :
    ((frobZn n).toCob2Functor.map (⟦genusWord g⟧ : Cob2Hom 0 0)).hom
      ((1 : ℤ) : 𝟙_ (ModuleCat ℤ)) = (n : ℤ) := by
  change (frobZn n).interpret (genusWord g) (1 : ℤ) = (n : ℤ)
  rw [interpret_genusWord_generic, frobZn_handlePower]
  simp only [frobZn]
  change znCounit n (znUnit n 1) = (n : ℤ)
  rw [znUnit_apply, znCounit_apply]
  simp

/-- Every corrected genus word acts by multiplication by `n` on the monoidal unit. -/
theorem Z_genus_eq_smul_id (n g : ℕ) :
    (frobZn n).toCob2Functor.map (⟦genusWord g⟧ : Cob2Hom 0 0) =
      (n : ℤ) • 𝟙 (𝟙_ (ModuleCat ℤ)) := by
  apply ModuleCat.hom_ext
  apply LinearMap.ext_ring
  refine (Z_genus n g).trans ?_
  change (n : ℤ) = (n : ℤ) * 1
  simp

end DijkgraafWitten
