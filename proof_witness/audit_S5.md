# V0 audit sheet S5 (8 items)
Mark [x] ONLY if the negative could be VALID (tactic reproduces the recorded after-state).

### item 592  [CONF]
- [ ] MISLABELED?
GOAL: hζ : IsPrimitiveRoot ζ n | ⊢ (cyclotomic n R).roots.Nodup
TRUE AFTER: no goals
GOLD: refine <a>Multiset.nodup_of_le</a> (<a>Polynomial.roots.le_of_dvd</a> (<a>Polynomial.X_pow_sub_C_ne_zero</a> (<a>NeZero.
NEG : AFTER swapped to: xl : Tendsto x atTop l | ⊢ Tendsto ((fun n => ∫⁻ (a : α), F n a ∂μ) ∘ x) atTop (𝓝 (∫⁻ (a : α), f a ∂μ))

### item 556  [CONF]
- [ ] MISLABELED?
GOAL: x✝ : α | ⊢ ↑(SimpleFunc.piecewise s hs (SimpleFunc.const α 0) (SimpleFunc.const α 0)) x✝ = ∅.indicator (fun x => 0) x✝
TRUE AFTER: no goals
GOLD: simp [<a>Function.const</a>]
NEG : AFTER swapped to: ⊢ { toFun := fun t => t.comp ↑A.symm, map_add' := ⋯ }.toFun (x • f) = |     (RingHom.id ℝ) x • { toFun := fun t => t.comp ↑A.symm, map_add' := ⋯ }.toFun f

### item 498  [CONF]
- [ ] MISLABELED?
GOAL: f : α → β | ⊢ Continuous f ↔ ContinuousOn f univ
TRUE AFTER: no goals
GOLD: simp [<a>continuous_iff_continuousAt</a>, <a>ContinuousOn</a>, <a>ContinuousAt</a>, <a>ContinuousWithinAt</a>, <a>nhdsWi
NEG : AFTER swapped to: hi' : repr ⟨v i, ⋯⟩ = Finsupp.single i' 1 ∧ f i' = i | ⊢ f i' = i

### item 576  [CONF]
- [ ] MISLABELED?
GOAL: hs : s ∈ f | ⊢ s⁻¹ ∈ f⁻¹
TRUE AFTER: no goals
GOLD: rwa [<a>Filter.mem_inv</a>, <a>Set.inv_preimage</a>, <a>inv_inv</a>]
NEG : AFTER swapped to: c : C | ⊢ Nonempty C

### item 570  [CONF]
- [ ] MISLABELED?
GOAL: l : ι →₀ R := Finsupp.mapDomain (⇑f) (repr ⟨v i, ⋯⟩) | ⊢ (Finsupp.total ι' M R (v ∘ ⇑f)) (repr ⟨v i, ⋯⟩) = v i
TRUE AFTER: no goals
GOLD: rw [(hv.comp f f.injective).<a>LinearIndependent.total_repr</a>]
NEG : AFTER swapped to: hc₁ : IsColimit (BinaryCofan.mk (c.inr ≫ i) h) | ⊢ H.IsVanKampen

### item 522  [CONF]
- [ ] MISLABELED?
GOAL: t : τ | ⊢ Continuous (uncurry ϕ.toFun)
TRUE AFTER: no goals
GOLD: exact ϕ.cont'
NEG : AFTER swapped to:             CategoryTheory.whiskerRight e₁₂ G₂₃ ≫ (L₁.associator G₁₂ G₂₃).hom ≫ CategoryTheory.whiskerLeft L₁ β) |     A

### item 490  [CONF]
- [ ] MISLABELED?
GOAL: inst✝ : Nontrivial R | ⊢ WithBot.unbot' 0 ↑n.totient = n.totient
TRUE AFTER: no goals
GOLD: norm_cast
NEG : AFTER swapped to: f✝ f : R[X] | ⊢ ∀ (m : ℕ), ↑f.natDegree < ↑m → f.reverse.coeff m = 0

### item 464  [CONF]
- [ ] MISLABELED?
GOAL: hg : Integrable g μ | ⊢ μ[f + -g|m] =ᶠ[ae μ] μ[f|m] + -μ[g|m]
TRUE AFTER: no goals
GOLD: exact (<a>MeasureTheory.condexp_add</a> hf hg.neg).<a>Filter.EventuallyEq.trans</a> (EventuallyEq.rfl.add (<a>MeasureThe
NEG : AFTER swapped to: hz' : -z ≠ 1 | ⊢ (-z) ^ n * (1 + z)⁻¹ = (1 + z)⁻¹ - ∑ j ∈ Finset.range n, (-1) ^ j * z ^ j
