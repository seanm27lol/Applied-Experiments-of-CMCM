# V0 audit sheet S3 (15 items)
Mark [x] ONLY if the negative could be VALID (tactic reproduces the recorded after-state).

### item 36  [UNC]
- [ ] MISLABELED?
GOAL: lead_ne : (C k - p).leadingCoeff ≠ 0 | ⊢ k ∈ (fun x => eval x p) '' σ a
TRUE AFTER: lead_unit : IsUnit ↑((Units.map ↑↑ₐ) (Units.mk0 (C k - p).leadingCoeff lead_ne)) | ⊢ k ∈ (fun x => eval x p) '' σ a
GOLD: have lead_unit := (<a>Units.map</a> ↑ₐ.<a>RingHom.toMonoidHom</a> (<a>Units.mk0</a> _ lead_ne)).<a>Units.isUnit</a>
NEG : have p_a_eq : <a>Polynomial.aeval</a> a (<a>Polynomial.C</a> k - p) = ↑ₐ k - <a>Polynomial.aeval</a> a p := by simp only

### item 68  [UNC]
- [ ] MISLABELED?
GOAL: cmp : Y' ⟶ Y'' := pullback.lift i' αY ⋯ | ⊢ IsPullback i' αY αZ i
TRUE AFTER: e₁ : (g' ≫ cmp) ≫ pullback.snd = αW ≫ c.inl | ⊢ IsPullback i' αY αZ i
GOLD: have e₁ : (g' ≫ cmp) ≫ <a>CategoryTheory.Limits.pullback.snd</a> = αW ≫ c.inl := by rw [<a>CategoryTheory.Category.assoc
NEG : rw [← <a>CategoryTheory.Category.id_comp</a> αZ, ← show cmp ≫ <a>CategoryTheory.Limits.pullback.snd</a> = αY from <a>Cat

### item 268  [UNC]
- [x] MISLABELED?
GOAL: hmain : ∀ (m : ℕ) (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-↑m - 1) * x₀) (2 ^ (-↑m) * x₀) → f z = 0 | ⊢ 0 ≤ -logb 2 (x / x₀)
TRUE AFTER: hmain : ∀ (m : ℕ) (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-↑m - 1) * x₀) (2 ^ (-↑m) * x₀) → f z = 0 | ⊢ logb 2 (x / x₀) ≤ 0
GOLD: rw [<a>neg_nonneg</a>]
NEG : norm_num

### item 308  [UNC]
- [ ] MISLABELED?
GOAL: ht : U ⊆ ⋃ i ∈ t, (b ∘ f') i | ⊢ ∀ i ∈ t, (b ∘ f') i ⊆ ⋃ i ∈ ↑(Finset.image f' t), b i
TRUE AFTER: hi : i ∈ t | ⊢ (b ∘ f') i ⊆ ⋃ i ∈ ↑(Finset.image f' t), b i
GOLD: intro i hi
NEG : subst this

### item 252  [UNC]
- [ ] MISLABELED?
GOAL: J : LieIdeal R L' | ⊢ (∀ (x : L') (y : L), ∃ z, ⁅x, f y⁆ = f z) → ∀ (x m : L') (x_1 : L), f x_1 = m → ∃ y, f y = ⁅x, m⁆
TRUE AFTER: hz : f z = y | ⊢ ∃ y_1, f y_1 = ⁅x, y⁆
GOLD: intro h x y z hz
NEG : constructor

### item 20  [UNC]
- [ ] MISLABELED?
GOAL: hb₂ : b₀ < b₂ | ⊢ ContinuousAt (fun b => ∫ (x : ℝ) in a..b, f x ∂μ) b₀
TRUE AFTER: hb₂ : b₀ < b₂ | ⊢ ContinuousWithinAt (fun b => ∫ (x : ℝ) in a..b, f x ∂μ) (Icc b₁ b₂) b₀
GOLD: apply <a>ContinuousWithinAt.continuousAt</a> _ (<a>Icc_mem_nhds</a> hb₁ hb₂)
NEG : intro b₀

### item 164  [UNC]
- [ ] MISLABELED?
GOAL: ⊢ toMvPolynomial (basis A b) (basis A bₘ).end (tensorProduct R A M M ∘ₗ baseChange A φ) ij = |     (MvPolynomial.map (algebraMap R A)) (toMvPolynomial b bₘ.end
TRUE AFTER:       (toMvPolynomial (basis A bₘ.end) (basis A bₘ).end (tensorProduct R A M M) ij) = |     toMvPolynomial (basis A b) (basis A bₘ.end) (baseChange A φ) ij
GOLD: rw [<a>LinearMap.toMvPolynomial_comp</a> _ (<a>Algebra.TensorProduct.basis</a> A (<a>Basis.end</a> bₘ)), ← <a>LinearMap.
NEG : rintro ij

### item 260  [UNC]
- [ ] MISLABELED?
GOAL: e : f ⁻¹ᵁ Y.basicOpen ((LocallyRingedSpace.IsOpenImmersion.invApp f U) r) = X.basicOpen r | ⊢ ↑(f ''ᵁ f ⁻¹ᵁ Y.basicOpen ((LocallyRingedSpace.IsOpenImmersion.inv
TRUE AFTER: ⊢ ⇑f.val.base '' (⇑f.val.base ⁻¹' ↑(Y.basicOpen ((LocallyRingedSpace.IsOpenImmersion.invApp f U) r))) = |     ↑(Y.basicOpen ((Hom.invApp f U) r))
GOLD: dsimp [<a>TopologicalSpace.Opens.map</a>]
NEG : refine <a>le_trans</a> (<a>AlgebraicGeometry.Scheme.basicOpen_le</a> _ _) (<a>le_of_eq</a> ?_)

### item 316  [UNC]
- [ ] MISLABELED?
GOAL: h : M.charpoly • 1 = M.charmatrix.adjugate * M.charmatrix | ⊢ (aeval M) M.charpoly = 0
TRUE AFTER: h : matPolyEquiv (M.charpoly • 1) = matPolyEquiv (M.charmatrix.adjugate * M.charmatrix) | ⊢ (aeval M) M.charpoly = 0
GOLD: apply_fun <a>matPolyEquiv</a> at h
NEG : rw [<a>Polynomial.eval_mul_X_sub_C</a>] at h

### item 4  [UNC]
- [ ] MISLABELED?
GOAL:       (ListBlank.map { f := Prod.snd, map_pt' := ⋯ } (ListBlank.map { f := Prod.mk false, map_pt' := ⋯ } L.tail)) = |     L
TRUE AFTER: L : ListBlank ((k : K) → Option (Γ k)) | ⊢ ListBlank.map { f := Prod.snd, map_pt' := ⋯ } (ListBlank.map { f := Prod.mk false, map_pt' := ⋯ } L.tail) = L.tail
GOLD: convert <a>Turing.ListBlank.cons_head_tail</a> L
NEG : rfl

### item 92  [UNC]
- [ ] MISLABELED?
GOAL: hT : T.IsSymmetric | ⊢ (∀ (x : E), ⟪T x, x⟫_𝕜 = 0) ↔ ∀ (x : E), T x = 0
TRUE AFTER: x : E | ⊢ T x = 0
GOLD: refine ⟨fun h x => ?_, fun h => by simp_rw [h, <a>inner_zero_left</a>, <a>forall_const</a>]⟩
NEG : simp_rw [<a>LinearMap.ext_iff</a>, <a>LinearMap.zero_apply</a>]

### item 28  [UNC]
- [ ] MISLABELED?
GOAL: L : ListBlank ((k : K) → Option (Γ k)) | ⊢ ListBlank.map { f := Prod.snd, map_pt' := ⋯ } (ListBlank.map { f := Prod.mk false, map_pt' := ⋯ } L.tail) = L.tail
TRUE AFTER: L L' : ListBlank ((k : K) → Option (Γ k)) | ⊢ ListBlank.map { f := Prod.snd, map_pt' := ⋯ } (ListBlank.map { f := Prod.mk false, map_pt' := ⋯ } L') = L'
GOLD: generalize <a>Turing.ListBlank.tail</a> L = L'
NEG : convert <a>Turing.ListBlank.cons_head_tail</a> L

### item 44  [UNC]
- [ ] MISLABELED?
GOAL: cmp : ∀ x ∈ Ioo a b, a < c x ∧ c x < x | ⊢ Tendsto ((fun x' => f' x' / g' x') ∘ c) (𝓝[Ioo a b] a) l
TRUE AFTER: cmp : ∀ x ∈ Ioo a b, a < c x ∧ c x < x | ⊢ Tendsto c (𝓝[Ioo a b] a) (𝓝[>] a)
GOLD: apply hdiv.comp
NEG : refine <a>tendsto_nhdsWithin_of_tendsto_nhds_of_eventually_within</a> _ (<a>tendsto_of_tendsto_of_tendsto_of_le_of_le'</

### item 60  [UNC]
- [ ] MISLABELED?
GOAL: j' : α i | ⊢ (single ⟨i, j⟩ x) ⟨i, j'⟩ = (single j x) j'
TRUE AFTER: hj : j ≠ j' | ⊢ (single ⟨i, j⟩ x) ⟨i, j'⟩ = (single j x) j'
GOLD: obtain rfl | hj := <a>eq_or_ne</a> j j'
NEG : rw [<a>DFinsupp.single_eq_of_ne</a>, <a>DFinsupp.single_eq_of_ne</a> hj]

### item 236  [UNC]
- [ ] MISLABELED?
GOAL: x₀_pos : 0 < x₀ | ⊢ ∀ (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-1) * x₀) x₀ → f z = 0
TRUE AFTER: hx : ∀ u ∈ Set.Icc (1 / 2 * x₀) x₀, f u ∈ Set.Icc (c₁ * f x₀) (c₂ * f x₀) | ⊢ ∀ (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-1) * x₀) x₀ → f z = 0
GOLD: specialize hx x₀ (<a>le_of_max_le_left</a> hx₀_ge)
NEG : rw [← <a>Real.rpow_intCast</a>, <a>Real.logb_rpow</a> (by norm_num) (by norm_num), ← <a>neg_le_neg_iff</a>]
