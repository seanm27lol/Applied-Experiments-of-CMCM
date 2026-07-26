# V0 audit sheet S1 (8 items)
Mark [x] ONLY if the negative could be VALID (tactic reproduces the recorded after-state).

### item 160  [CONF]
- [ ] MISLABELED?
GOAL: sep : L.SeparatesPointsStrongly | ⊢ closure L = ⊤
TRUE AFTER: sep : L.SeparatesPointsStrongly | ⊢ ⊤ ≤ closure L
GOLD: rw [<a>eq_top_iff</a>]
NEG : rwa [← <a>Real.exp_lt_exp</a>, <a>Real.exp_log</a> hx, <a>Real.exp_log</a> (<a>lt_trans</a> hx h)]

### item 72  [CONF]
- [ ] MISLABELED?
GOAL: hz : z ≠ 0 | ⊢ ∃ y' z', y' < y ∧ z' < z ∧ x < y' + z'
TRUE AFTER: this : NeZero y | ⊢ ∃ y' z', y' < y ∧ z' < z ∧ x < y' + z'
GOLD: have : <a>NeZero</a> y := ⟨hy⟩
NEG : omega

### item 200  [CONF]
- [ ] MISLABELED?
GOAL: a : ℝ | ⊢ ∀ (x : ℝ), ContinuousAt (fun b => ∫ (x : ℝ) in a..b, f x ∂μ) x
TRUE AFTER: a b₀ : ℝ | ⊢ ContinuousAt (fun b => ∫ (x : ℝ) in a..b, f x ∂μ) b₀
GOLD: intro b₀
NEG : exact <a>le_of_smul_le_smul_of_pos_left</a> h <| <a>neg_pos</a>.2 ha

### item 24  [CONF]
- [ ] MISLABELED?
GOAL: hf_meas : ∀ (x : β), MeasurableSet (↑f ⁻¹' {x}) | ⊢ ∃ c, ∀ (x : α), ↑f x = c
TRUE AFTER: hf_meas : ∀ (x : β), ↑f ⁻¹' {x} = ∅ ∨ ↑f ⁻¹' {x} = univ | ⊢ ∃ c, ∀ (x : α), ↑f x = c
GOLD: simp_rw [<a>MeasurableSpace.measurableSet_bot_iff</a>] at hf_meas
NEG : simp [h]

### item 32  [CONF]
- [ ] MISLABELED?
GOAL: t : M ⊗[R] N | ⊢ t ∈ Submodule.span R {t | ∃ m n, m ⊗ₜ[R] n = t}
TRUE AFTER:     x ∈ Submodule.span R {t | ∃ m n, m ⊗ₜ[R] n = t} → |       y ∈ Submodule.span R {t | ∃ m n, m ⊗ₜ[R] n = t} → x + y ∈ Submodule.span R {t | ∃ m n, m ⊗ₜ[R] n =
GOLD: refine t.induction_on ?_ ?_ ?_
NEG : simp (config := { contextual := <a>Bool.true</a> }) [← <a>List.getElem_take</a>, <a>Nat.lt_min</a>]

### item 272  [CONF]
- [ ] MISLABELED?
GOAL: hmain : ∀ (m : ℕ) (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-↑m - 1) * x₀) (2 ^ (-↑m) * x₀) → f z = 0 | ⊢ logb 2 (2 ^ (-↑⌊-logb 2 (x / x₀)⌋₊ - 1)) ≤ logb 2 (x / x₀)
TRUE AFTER: hmain : ∀ (m : ℕ) (z : ℝ), x ≤ z → z ∈ Set.Icc (2 ^ (-↑m - 1) * x₀) (2 ^ (-↑m) * x₀) → f z = 0 | ⊢ -logb 2 (x / x₀) ≤ -↑(-↑⌊-logb 2 (x / x₀)⌋₊ - 1)
GOLD: rw [← <a>Real.rpow_intCast</a>, <a>Real.logb_rpow</a> (by norm_num) (by norm_num), ← <a>neg_le_neg_iff</a>]
NEG : congr

### item 48  [CONF]
- [ ] MISLABELED?
GOAL: hij_lt : i < j | ⊢ False
TRUE AFTER: h_succFn_eq : succFn i = i | ⊢ False
GOLD: have h_succFn_eq : <a>LinearLocallyFiniteOrder.succFn</a> i = i := <a>le_antisymm</a> hi (<a>LinearLocallyFiniteOrder.le
NEG : obtain ⟨a, rfl⟩ | ⟨hf, h⟩ := h

### item 184  [CONF]
- [ ] MISLABELED?
GOAL: y : P | ⊢ (∃ x' ∈ Ideal.span {x}, (algebraMap R P) x' = y) → ∃ z, z • (algebraMap R P) x = y
TRUE AFTER: hy' : y' ∈ Ideal.span {x} | ⊢ ∃ z, z • (algebraMap R P) x = (algebraMap R P) y'
GOLD: rintro ⟨y', hy', rfl⟩
NEG : have : i = <a>Unit.unit</a> := by simp only [<a>eq_iff_true_of_subsingleton</a>]
