import RequestProject.BanachEmbedding
import RequestProject.FullnessCounterexample

open CategoryTheory

noncomputable section

namespace SheafNotFull

open ForgetfulNotFull

/-! ## Sheaf-level non-fullness

`BanachEmbedding.lean` defines its realization functor on `SemiNormedGrp.{1}`.
We therefore lift the finitely supported integer sequences and the integers from
`Type 0` to homeomorphic copies in `Type 1`. The summation counterexample and
its norm estimates are unchanged by this universe lift.
-/

/-- The universe-lifted source of the summation counterexample. -/
abbrev LiftedFinsupp := ULift.{1} (ℕ →₀ ℤ)

/-- The universe-lifted target of the summation counterexample. -/
abbrev LiftedInt := ULift.{1} ℤ

/-- The lifted source is discrete because it is homeomorphic to the discrete
sup-norm group of finitely supported integer sequences. -/
local instance liftedFinsuppDiscrete : DiscreteTopology LiftedFinsupp :=
  (Homeomorph.ulift.symm : (ℕ →₀ ℤ) ≃ₜ LiftedFinsupp).discreteTopology

/-- Summation transported to the universe-lifted source and target. -/
def liftedSumHom : LiftedFinsupp →+ LiftedInt where
  toFun a := ULift.up (sumHom a.down)
  map_zero' := by
    apply ULift.down_injective
    simp
  map_add' a b := by
    apply ULift.down_injective
    simp [sumHom.map_add]

/-- Lifted summation is continuous because its source is discrete. -/
lemma liftedSumHom_continuous : Continuous liftedSumHom :=
  continuous_of_discreteTopology

/-- The lifted indicator of `{0, …, N}`. -/
def liftedWitness (N : ℕ) : LiftedFinsupp :=
  ULift.up (witness N)

/-- Lifted indicators still have norm one. -/
lemma norm_liftedWitness (N : ℕ) : ‖liftedWitness N‖ = 1 := by
  simp [liftedWitness, norm_witness]

/-- Lifted summation of the indicator of `{0, …, N}` is `N + 1`. -/
lemma liftedSumHom_witness (N : ℕ) :
    liftedSumHom (liftedWitness N) = ULift.up (N + 1 : ℤ) := by
  apply ULift.down_injective
  simp [liftedSumHom, liftedWitness, sumHom_witness]

/-- No bounded homomorphism between the lifted groups realizes summation. -/
theorem no_normedAddGroupHom_lifted :
    ¬ ∃ u : NormedAddGroupHom LiftedFinsupp LiftedInt,
      ∀ a, u a = liftedSumHom a := by
  rintro ⟨u, hu⟩
  obtain ⟨N, hN⟩ := exists_nat_gt ‖u‖
  have hb : ‖u (liftedWitness N)‖ ≤ ‖u‖ * ‖liftedWitness N‖ :=
    u.le_opNorm _
  rw [hu (liftedWitness N), norm_liftedWitness N, mul_one] at hb
  have hs : ‖liftedSumHom (liftedWitness N)‖ = (N : ℝ) + 1 := by
    rw [liftedSumHom_witness N]
    simp only [ULift.norm_up]
    push_cast [Int.norm_eq_abs]
    rw [abs_of_nonneg (by positivity)]
  rw [hs] at hb
  linarith

/-- Summation as a morphism of the `ModuleCat`-valued presheaves used by
`banachCondensed`. -/
def sumBanachPresheafMap :
    banachPresheaf LiftedFinsupp ⟶ banachPresheaf LiftedInt where
  app S := ModuleCat.ofHom {
    toFun := fun g =>
      (ContinuousMap.mk liftedSumHom liftedSumHom_continuous).comp g
    map_add' := by
      intro a b
      ext x
      simp [liftedSumHom.map_add]
    map_smul' := by
      intro n a
      ext x
      simp [ContinuousMap.smul_apply]
  }
  naturality := by
    intro S T f
    ext g
    rfl

/-- Summation packaged as a genuine morphism in `CondensedAb`. -/
def sumCondensedMap :
    banachCondensed LiftedFinsupp ⟶ banachCondensed LiftedInt :=
  ⟨sumBanachPresheafMap⟩

/-- The sheaf-level functor `semiNormedGrpToCondensedAb` is not full.

The continuous unbounded lifted summation map already defines a morphism
between the associated condensed abelian groups. If the functor were full, that
morphism would be induced by a bounded group homomorphism. -/
theorem semiNormedGrpToCondensedAb_not_full :
    ¬ semiNormedGrpToCondensedAb.Full := by
  intro hfull
  obtain ⟨f, hf⟩ :=
    (semiNormedGrpToCondensedAb.map_surjective
      (X := SemiNormedGrp.of LiftedFinsupp)
      (Y := SemiNormedGrp.of LiftedInt)) sumCondensedMap
  change (⟨banachPresheafMap f⟩ :
      banachCondensed LiftedFinsupp ⟶ banachCondensed LiftedInt) =
    ⟨sumBanachPresheafMap⟩ at hf
  injection hf with hnat
  have hval : ∀ a, f.hom a = liftedSumHom a := by
    intro a
    have happ := NatTrans.congr_app hnat (Opposite.op (CompHaus.of PUnit))
    have hconst := congrArg
      (fun m => m (ContinuousMap.const _ a)) happ
    simp only at hconst
    have hpoint := congrArg
      (fun (g : C((CompHaus.of PUnit : CompHaus), LiftedInt)) =>
        g PUnit.unit) hconst
    simpa [banachPresheafMap, sumBanachPresheafMap] using hpoint
  exact no_normedAddGroupHom_lifted ⟨f.hom, hval⟩

end SheafNotFull
