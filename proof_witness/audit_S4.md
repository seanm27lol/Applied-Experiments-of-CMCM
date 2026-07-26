# V0 audit sheet S4 (15 items)
Mark [x] ONLY if the negative could be VALID (tactic reproduces the recorded after-state).

### item 278  [UNC]
- [ ] MISLABELED?
GOAL:     g.toContinuousLinearMap.compContinuousMultilinearMap (iteratedFDerivWithin 𝕜 i f s x) | ⊢ ‖iteratedFDerivWithin 𝕜 i (⇑g ∘ f) s x‖ = ‖iteratedFDerivWithin 𝕜
TRUE AFTER: ⊢ ‖g.toContinuousLinearMap.compContinuousMultilinearMap (iteratedFDerivWithin 𝕜 i f s x)‖ = |     ‖iteratedFDerivWithin 𝕜 i f s x‖
GOLD: rw [this]
NEG : rw [F]

### item 62  [UNC]
- [ ] MISLABELED?
GOAL: e₂ : l₂ ++ a :: r₂ = x :: l₂✝ | ⊢ l₁ ++ r₁ ~ l₂ ++ r₂
TRUE AFTER:     l₁ ++ a :: r₁_1 = tail✝¹ ++ a :: r₁ → l₂ ++ a :: r₂_1 = tail✝ ++ a :: r₂ → l₁ ++ r₁_1 ~ l₂ ++ r₂_1 | ⊢ head✝ :: tail✝¹ ++ r₁ ~ head✝ :: tail✝ ++ r₂
GOLD: cases l₁ <;> cases l₂ <;> dsimp at e₁ e₂ <;> injections <;> subst_vars
NEG : simpa only [← <a>Complex.Gamma_ofReal</a>, <a>Complex.ofReal_cpow</a> <a>zero_le_two</a>, <a>Complex.ofReal_mul</a>, <a>

### item 294  [UNC]
- [ ] MISLABELED?
GOAL: hu : ThreeGPFree ↑u | ⊢ mulRothNumber (map (mulLeftEmbedding a) s) ≤ mulRothNumber s
TRUE AFTER: hu : ThreeGPFree ↑(map (mulLeftEmbedding a) u) | ⊢ mulRothNumber (map (mulLeftEmbedding a) s) ≤ mulRothNumber s
GOLD: obtain ⟨u, hus, rfl⟩ := hus
NEG : obtain ⟨u, a, rfl⟩ := hus

### item 158  [UNC]
- [ ] MISLABELED?
GOAL: _i : Fact (finrank ℝ E = 0) | ⊢ (- -positiveOrientation).volumeForm = -(-positiveOrientation).volumeForm
TRUE AFTER: _i : Fact (finrank ℝ E = 0) | ⊢ positiveOrientation.volumeForm = -(-positiveOrientation).volumeForm
GOLD: rw [<a>neg_neg</a> (<a>Module.Oriented.positiveOrientation</a> (R := ℝ))]
NEG : refine ⟨(<a>equivShrink</a> S).<a>Equiv.bundledInduced</a> L, ⟨S.subtype.comp (<a>Equiv.bundledInducedEquiv</a> L _).sym

### item 286  [UNC]
- [ ] MISLABELED?
GOAL: hw : w ∈ ball y δ | ⊢ w ∈ s
TRUE AFTER: i : ι | ⊢ z i ≤ w i
GOLD: refine hs (fun i => ?_) hz
NEG : refine hx (fun i => ?_) hz

### item 94  [UNC]
- [ ] MISLABELED?
GOAL: hb : b ∈ {b | orderOf b = n} | ⊢ ∃ a, f a = ⟨b, hb⟩
TRUE AFTER: hb : b ∈ {b | orderOf b = n} | ⊢ f ⟨a⁻¹ * b, ?mk.refine_1⟩ = ⟨b, hb⟩
GOLD: refine ⟨⟨a⁻¹ * b, ?_⟩, ?_⟩
NEG : refine ⟨⟨A⁻¹ * b, ?_⟩, ?_⟩

### item 54  [UNC]
- [ ] MISLABELED?
GOAL: ha : a ∈ s ∩ u | ⊢ False
TRUE AFTER: ha : a ∈ s ∩ u | ⊢ False
GOLD: rw [<a>Finset.insert_eq_self</a>.2 (<a>Finset.mem_inter</a>.1 ha).2] at hu
NEG : rw [<a>Finset.insert_eq_self</a>.2 (<a>Finset.mem_inter</a>.1 u).2] at hu

### item 102  [UNC]
- [ ] MISLABELED?
GOAL:     (∃ J', (↑J' = ↑J ∩ {y | y i ≤ x} ∨ ↑J' = ↑J ∩ {y | x < y i}) ∧ ↑x_1 = ↑I ∩ ↑J') → |       ↑x_1 = ↑I ∩ {y | y i ≤ x} ∨ ↑x_1 = ↑I ∩ {y | x < y i}
TRUE AFTER:     (∃ J', (↑J' = ↑J ∩ {y | y i ≤ x} ∨ ↑J' = ↑J ∩ {y | x < y i}) ∧ ↑x_1 = ↑I ∩ ↑J') → |       ↑x_1 = ↑I ∩ {y | y i ≤ x} ∨ ↑x_1 = ↑I ∩ {y | x < y i}
GOLD: have : ∀ s, (I ∩ s : <a>Set</a> (ι → ℝ)) ⊆ J := fun s => inter_subset_left.trans h
NEG : have : ∀ s, (I ∩ s : <a>Set</a> (ι → ℝ)) ⊆ J := fun s => inter_subset_left.trans i

### item 190  [UNC]
- [ ] MISLABELED?
GOAL: hts : ∀ (a b c : α), (a, b) ∈ t → (a * c, b * c) ∈ s | ⊢ s ∈ comap (Prod.mk 1 ∘ fun x => x.2 / x.1) (𝓤 α)
TRUE AFTER: hts : ∀ (a b c : α), (a, b) ∈ t → (a * c, b * c) ∈ s | ⊢ (Prod.mk 1 ∘ fun x => x.2 / x.1) ⁻¹' t ⊆ s
GOLD: refine ⟨_, ht, ?_⟩
NEG : refine ⟨_, hts, ?_⟩

### item 302  [UNC]
- [ ] MISLABELED?
GOAL: ha : ¬↑a = 0 | ⊢ ↑(legendreSym 2 a) = ↑a ^ (2 / 2)
TRUE AFTER: ha : ¬↑a = 0 | ⊢ ↑1 = ↑a ^ (2 / 2)
GOLD: rw [<a>legendreSym</a>, <a>quadraticChar_eq_one_of_char_two</a> hc ha]
NEG : apply hab.subset

### item 38  [UNC]
- [ ] MISLABELED?
GOAL: hmap : (map g (map X ℙ)).HaveLebesgueDecomposition ν | ⊢ HasPDF (g ∘ X) ℙ ν
TRUE AFTER: hmX : Measurable X | ⊢ HasPDF (g ∘ X) ℙ ν
GOLD: wlog hmX : <a>Measurable</a> X
NEG : wlog hmX : <a>Measurable</a> g

### item 150  [UNC]
- [ ] MISLABELED?
GOAL: h : eval M (matPolyEquiv (M.charpoly • 1)) = eval M (matPolyEquiv M.charmatrix.adjugate * (X - C M)) | ⊢ (aeval M) M.charpoly = 0
TRUE AFTER: h : eval M (matPolyEquiv (M.charpoly • 1)) = 0 | ⊢ (aeval M) M.charpoly = 0
GOLD: rw [<a>Polynomial.eval_mul_X_sub_C</a>] at h
NEG : rw [<a>Polynomial.eval_mul_X_sub_C</a>] at m

### item 14  [UNC]
- [ ] MISLABELED?
GOAL: this : ∀ (f : ↥(Lp.simpleFunc E p μ)), P ↑↑↑f | ⊢ ∀ ⦃f : α → E⦄, Memℒp f p μ → P f
TRUE AFTER: this : ∀ (f : ↥(Lp E p μ)), P ↑↑f | ⊢ ∀ ⦃f : α → E⦄, Memℒp f p μ → P f
GOLD: have : ∀ f : <a>MeasureTheory.Lp</a> E p μ, P f := fun f => (<a>MeasureTheory.Lp.simpleFunc.denseRange</a> hp_ne_top).<a
NEG : have : ∀ f : <a>MeasureTheory.Lp</a> E p μ, P f := fun f => (<a>MeasureTheory.Lp.simpleFunc.denseRange</a> hp_ne_top).<a

### item 310  [UNC]
- [x] MISLABELED?
GOAL: hseq_meas : ∀ (m : ℕ), MeasurableSet (seq m) | ⊢ Tendsto (fun m => densityProcess κ ν n a x (seq m)) atTop (𝓝 (densityProcess κ ν n a x ∅))
TRUE AFTER: ⊢ Tendsto (fun m => ((κ a) (countablePartitionSet n x ×ˢ seq m) / (ν a) (countablePartitionSet n x)).toReal) atTop |     (𝓝 ((κ a) (countablePartitionSet n x ×ˢ
GOLD: simp_rw [<a>ProbabilityTheory.kernel.densityProcess</a>]
NEG : simp_rw [<n>ProbabilityTheory.kernel.densityProcess</a>]

### item 262  [UNC]
- [ ] MISLABELED?
GOAL: H : Triangle.mk φ.hom g h ∈ distinguishedTriangles | ⊢ ∃ Z g h, Triangle.mk f g h ∈ L.essImageDistTriang
TRUE AFTER:       (L.map h ≫ (L.commShiftIso 1).hom.app ((𝟭 C).obj φ.left) ≫ (shiftFunctor D 1).map e.hom.left) ≅ |     L.mapTriangle.obj (Triangle.mk φ.hom g h)
GOLD: refine ⟨L.obj Z, e.inv.right ≫ L.map g, L.map h ≫ (L.commShiftIso (1 : ℤ)).hom.app _ ≫ e.hom.left⟦(1 : ℤ)⟧', _, ?_, H⟩
NEG : refine ⟨L.obj Z, e.inv.right ≫ L.map g, L.map h ≫ (L.commShiftIso (1 : ℤ)).hom.app _ ≫ e.hom.left⟦(1 : ℤ)⟧', _, ?_, this
