# V0 audit sheet S2 (15 items)
Mark [x] ONLY if the negative could be VALID (tactic reproduces the recorded after-state).

### item 210  [UNC]
- [ ] MISLABELED?
GOAL: hβ : ∀ (a : α), (f ⁻¹' {a}).WellFoundedOn (rβ on g) | ⊢ WellFounded (Prod.Lex rα rβ on fun c => (f c, g c))
TRUE AFTER: h : (Prod.Lex rα rβ on fun c => (f c, g c)) c c' | ⊢ ((PSigma.Lex (fun a b => rα ↑a ↑b) fun a a_1 b => (rβ on g) ↑a_1 ↑b) on fun c => ⟨⟨f c, ⋯⟩, ⟨c, ⋯⟩⟩) c c'
GOLD: refine ((<a>PSigma.lex_wf</a> (<a>Set.wellFoundedOn_range</a>.2 hα) fun a => hβ a).<a>WellFounded.onFun</a> (f := fun c
NEG : subst h

### item 18  [UNC]
- [ ] MISLABELED?
GOAL: h₃ : ∀ᵐ (ω : Ω) ∂μ, ∀ (n : ℕ), 0 ≤ (μ[f (n + 1) - f n|↑ℱ n]) ω | ⊢ ∀ᵐ (ω : Ω) ∂μ, Tendsto (fun n => f n ω) atTop atTop ↔ Tendsto (fun n => predictablePart f ℱ μ
TRUE AFTER: hω₄ : ∀ (n : ℕ), f n ω ≤ f (n + 1) ω | ⊢ Tendsto (fun n => f n ω) atTop atTop ↔ Tendsto (fun n => predictablePart f ℱ μ n ω) atTop atTop
GOLD: filter_upwards [h₁, h₂, h₃, hfmono] with ω hω₁ hω₂ hω₃ hω₄
NEG : obtain ⟨ha, hf⟩ := h

### item 186  [UNC]
- [ ] MISLABELED?
GOAL: c : 𝕜ˣ | ⊢ HasFiniteIntegral (↑c • f) μ ↔ HasFiniteIntegral f μ
TRUE AFTER: c : 𝕜ˣ | ⊢ HasFiniteIntegral f μ → HasFiniteIntegral (↑c • f) μ
GOLD: constructor
NEG : intro n

### item 84  [UNC]
- [ ] MISLABELED?
GOAL: this : g 0 = 0 | ⊢ g j = 0
TRUE AFTER: this : g 0 = 0 | ⊢ g j = 0
GOLD: rw [this, <a>zero_smul</a>, <a>zero_add</a>] at total_eq
NEG : rw [← <a>MonoidHom.range_eq_map</a>, <a>Subgroup.subtype_range</a>, <a>Subgroup.normalClosure</a>, <a>MonoidHom.map_clos

### item 12  [UNC]
- [ ] MISLABELED?
GOAL: hxy : (x ^ 2 - ↑a * y ^ 2) * y⁻¹ ^ 2 = 0 | ⊢ legendreSym p a = 1
TRUE AFTER: hxy : x * y⁻¹ * (x * y⁻¹) = ↑a | ⊢ legendreSym p a = 1
GOLD: rw [(by ring : (x ^ 2 - ↑a * y ^ 2) * y⁻¹ ^ 2 = (x * y⁻¹) ^ 2 - a * (y * y⁻¹) ^ 2), <a>mul_inv_cancel</a> hy, <a>one_pow
NEG : dsimp only [<a>Num.succ'</a>] at ep

### item 34  [UNC]
- [ ] MISLABELED?
GOAL: hz : 1 + z ∈ slitPlane | ⊢ (-z) ^ n * (1 + z)⁻¹ = (1 + z)⁻¹ - ∑ j ∈ Finset.range n, (-1) ^ j * z ^ j
TRUE AFTER: hz' : -z ≠ 1 | ⊢ (-z) ^ n * (1 + z)⁻¹ = (1 + z)⁻¹ - ∑ j ∈ Finset.range n, (-1) ^ j * z ^ j
GOLD: have hz' : -z ≠ 1 := by intro H rw [<a>neg_eq_iff_eq_neg</a>] at H simp only [H, <a>add_right_neg</a>] at hz exact <a>Co
NEG : intro n

### item 156  [UNC]
- [ ] MISLABELED?
GOAL: hN₀ : 0 < ↑N | ⊢ √(log ↑N) + 1 ≤ 2 * √(log ↑N)
TRUE AFTER: hN₀ : 0 < ↑N | ⊢ 1 ≤ √(log ↑N)
GOLD: rw [<a>two_mul</a>, <a>add_le_add_iff_left</a>]
NEG : rintro ⟨i, ⟨h⟩⟩

### item 154  [UNC]
- [ ] MISLABELED?
GOAL: hbot : f i ≠ ⊥ | ⊢ ∀ b < f i, b = ⊥
TRUE AFTER: hb : b < f i | ⊢ b = ⊥
GOLD: intro b hb
NEG : intro h

### item 26  [UNC]
- [ ] MISLABELED?
GOAL:         (IntegrableOn f (⋃ i ∈ s, t i) μ ↔ ∀ i ∈ s, IntegrableOn f (t i) μ) → |           (IntegrableOn f (⋃ i ∈ insert a s, t i) μ ↔ ∀ i ∈ insert a s, Integrab
TRUE AFTER: hf : IntegrableOn f (⋃ i ∈ s, t i) μ ↔ ∀ i ∈ s, IntegrableOn f (t i) μ | ⊢ IntegrableOn f (⋃ i ∈ insert a s, t i) μ ↔ ∀ i ∈ insert a s, IntegrableOn f (t i) μ
GOLD: intro a s _ _ hf
NEG : funext α f a n

### item 98  [UNC]
- [ ] MISLABELED?
GOAL: h_lim : ∀ᵐ (a : α) ∂μ, Tendsto (fun n => F n a) l (𝓝 (f a)) | ⊢ ∀ (x : ℕ → ι), Tendsto x atTop l → Tendsto ((fun n => ∫⁻ (a : α), F n a ∂μ) ∘ x) atTop (𝓝 (∫⁻ (a
TRUE AFTER: xl : Tendsto x atTop l | ⊢ Tendsto ((fun n => ∫⁻ (a : α), F n a ∂μ) ∘ x) atTop (𝓝 (∫⁻ (a : α), f a ∂μ))
GOLD: intro x xl
NEG : intro n

### item 300  [UNC]
- [ ] MISLABELED?
GOAL: ⊢ (∫⁻ (a : α), (f + g) a ^ 0 ∂μ) ^ (1 / 0) ≤ |     2 ^ (1 / 0 - 1) * ((∫⁻ (a : α), f a ^ 0 ∂μ) ^ (1 / 0) + (∫⁻ (a : α), g a ^ 0 ∂μ) ^ (1 / 0))
TRUE AFTER: hp1 : 0 ≤ 1 | ⊢ 1 ≤ 2 ^ (-1) * (1 + 1)
GOLD: simp only [<a>Pi.add_apply</a>, <a>ENNReal.rpow_zero</a>, <a>MeasureTheory.lintegral_one</a>, <a>div_zero</a>, <a>zero_s
NEG : rw [<a>MeasureTheory.Measure.map_apply</a> hX hs, <a>MeasureTheory.Measure.fst_apply</a> hs, <a>MeasureTheory.Measure.ma

### item 202  [UNC]
- [ ] MISLABELED?
GOAL: hR : R ∈ Ioi r | ⊢ ‖x‖ / R ≤ gauge (closedBall 0 r) x
TRUE AFTER: hR : R ∈ Ioi r | ⊢ gauge (ball 0 R) x ≤ gauge (closedBall 0 r) x
GOLD: rw [← <a>gauge_ball</a> (hr.trans hR.out.le)]
NEG : exact ⟨⟨r, hr₀⟩, hr⟩

### item 298  [UNC]
- [ ] MISLABELED?
GOAL: hu : ThreeGPFree ↑u | ⊢ mulRothNumber (map (mulLeftEmbedding a) s) ≤ mulRothNumber s
TRUE AFTER: hu : ThreeGPFree ↑u | ⊢ mulRothNumber (map (mulLeftEmbedding a) s) ≤ mulRothNumber s
GOLD: rw [<a>Finset.subset_map_iff</a>] at hus
NEG : apply <a>Filter.limsSup_le_of_le</a> hu

### item 330  [UNC]
- [ ] MISLABELED?
GOAL: h : p.coeff n = 0 | ⊢ ↑0 = p.coeff n
TRUE AFTER: h : p.coeff n = 0 | ⊢ ↑0 = 0
GOLD: rw [h]
NEG : simp [h]

### item 204  [UNC]
- [ ] MISLABELED?
GOAL: h : b ∈ q.support | ⊢ p.totalDegree ≤ q.totalDegree
TRUE AFTER: h : b ∈ q.support | ⊢ Multiset.card (toMultiset b) ≤ q.support.sup fun m => Multiset.card (toMultiset m)
GOLD: rw [<a>MvPolynomial.totalDegree_eq</a> p, hb₂, <a>MvPolynomial.totalDegree_eq</a>]
NEG : refine ⟨fun hx => ⟨⟨x, ⟨(↑hx.unit⁻¹ : A), <a>StarSubalgebra.isUnit_coe_inv_mem</a> hS hx x.prop⟩, ?_, ?_⟩, <a>rfl</a>⟩,
