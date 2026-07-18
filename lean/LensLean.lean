/-
LensLean: the categorical layer of reverse-mode automatic differentiation,
kernel-checked, in core Lean 4 (no Mathlib, no dependencies).

Context. TorchLean (lean-dojo/TorchLean, arXiv:2602.22631) gives neural
networks executable semantics in Lean 4, with autograd correctness proved
against Mathlib's `fderiv` and a tape-based runtime. What it does not
contain (checked against the source, July 2026) is the categorical layer
worked out on paper by Fong-Spivak-Tuyeras, Elliott, and
Cruttwell-Gavranovic-Ghani-Wilson-Zanasi: reverse-mode differentiation
organizes into a category of LENSES whose composition law is the chain
rule's wiring, with a strict symmetric monoidal structure given by
running lenses in parallel. This file supplies that layer, then uses it:
a compositional reverse-mode engine built from six primitive lenses
trains a linear model by gradient descent inside the same file as the
proofs, with a finite-difference evaluation as an executable witness
that the compositional backward pass computes the true gradient.

The punchline: every structural theorem below is proved by `rfl`.
Associativity of the chain rule's wiring, the identity laws, the
interchange law, symmetry: all definitional. The category was already
there; we are letting the kernel say so.

Where this would slot in TorchLean: NN/Proofs/Autograd/Categorical.lean,
depended on via `require TorchLean from git ".../TorchLean.git" @ "main"`.
-/

namespace LensLean

/-- A lens `A <-> B`: a forward pass and a backward pass. `bwd` takes the
ORIGINAL input and a cotangent at the output, and returns a cotangent at
the input. This is the shape of reverse-mode AD, and of the parametric
lenses of categorical deep learning. -/
structure Lens (A B : Type) where
  fwd : A → B
  bwd : A → B → A

variable {A B C D E G : Type}

/-- Identity lens: pass forward, pass back. -/
def lid (A : Type) : Lens A A :=
  ⟨fun a => a, fun _ db => db⟩

/-- Composition: forwards compose forwards; backwards compose BACKWARDS
through the remembered input. This is the chain rule as plumbing. -/
def comp (g : Lens B C) (f : Lens A B) : Lens A C :=
  ⟨fun a => g.fwd (f.fwd a),
   fun a dc => f.bwd a (g.bwd (f.fwd a) dc)⟩

/-- Parallel (monoidal) product: run two lenses side by side. -/
def par (f : Lens A B) (g : Lens C D) : Lens (A × C) (B × D) :=
  ⟨fun ac => (f.fwd ac.1, g.fwd ac.2),
   fun ac bd => (f.bwd ac.1 bd.1, g.bwd ac.2 bd.2)⟩

/-- Symmetry: the braiding, which squares to the identity. -/
def swap (A B : Type) : Lens (A × B) (B × A) :=
  ⟨fun ab => (ab.2, ab.1), fun _ dba => (dba.2, dba.1)⟩

/-! ## The category laws: all definitional. -/

theorem comp_assoc (h : Lens C D) (g : Lens B C) (f : Lens A B) :
    comp (comp h g) f = comp h (comp g f) := rfl

theorem id_comp (f : Lens A B) : comp (lid B) f = f := rfl

theorem comp_id (f : Lens A B) : comp f (lid A) = f := rfl

/-! ## The strict symmetric monoidal structure: also definitional. -/

theorem interchange (g₁ : Lens B C) (f₁ : Lens A B)
    (g₂ : Lens E G) (f₂ : Lens D E) :
    par (comp g₁ f₁) (comp g₂ f₂) = comp (par g₁ g₂) (par f₁ f₂) := rfl

theorem par_id (A B : Type) : par (lid A) (lid B) = lid (A × B) := rfl

theorem swap_swap (A B : Type) :
    comp (swap B A) (swap A B) = lid (A × B) := rfl

theorem swap_natural (f : Lens A B) (g : Lens C D) :
    comp (swap B D) (par f g) = comp (par g f) (swap A C) := rfl

/-! ## The chain rule for scalar linear maps, over any associative
commutative multiplication. Note the twist: because the backward pass
composes in REVERSE, proving `mulBy a ∘ mulBy b = mulBy (a*b)` as a lens
equation needs commutativity, not just associativity. Reverse mode is a
transpose; the scalar chain rule secretly uses that scalars commute. -/

def mulBy {R : Type} [Mul R] (c : R) : Lens R R :=
  ⟨fun x => c * x, fun _ d => c * d⟩

theorem mulBy_comp {R : Type} [Mul R]
    (assoc : ∀ x y z : R, x * (y * z) = (x * y) * z)
    (comm : ∀ x y : R, x * y = y * x)
    (a b : R) :
    comp (mulBy a) (mulBy b) = mulBy (a * b) := by
  have hf : (fun x : R => a * (b * x)) = fun x => (a * b) * x :=
    funext fun x => assoc a b x
  have hb : (fun (_ : R) (d : R) => b * (a * d)) = fun _ d => (a * b) * d :=
    funext fun _ => funext fun d =>
      (assoc b a d).trans (congrArg (fun y => y * d) (comm b a))
  show Lens.mk (fun x : R => a * (b * x)) (fun _ d => b * (a * d)) =
       Lens.mk (fun x : R => (a * b) * x) (fun _ d => (a * b) * d)
  rw [hf, hb]

/-- Sanity instantiation at `Nat`, core lemmas only. -/
example : comp (mulBy 3) (mulBy 4) = mulBy (12 : Nat) :=
  mulBy_comp (fun x y z => (Nat.mul_assoc x y z).symm) Nat.mul_comm 3 4

/-! ## Executable: a compositional reverse-mode engine on `Float`,
training y = w*x + b by gradient descent, in the same file as the
proofs. Six primitive lenses; everything else is `comp` and `par`. -/

abbrev F := Float

def dup : Lens F (F × F) := ⟨fun x => (x, x), fun _ d => d.1 + d.2⟩

def addL : Lens (F × F) F := ⟨fun p => p.1 + p.2, fun _ d => (d, d)⟩

def mulL : Lens (F × F) F :=
  ⟨fun p => p.1 * p.2, fun p d => (d * p.2, d * p.1)⟩

def scale (c : F) : Lens F F := ⟨fun x => c * x, fun _ d => c * d⟩

def subConst (t : F) : Lens F F := ⟨fun x => x - t, fun _ d => d⟩

def square : Lens F F := comp mulL dup

/-- Fan a parameter pair out to two consumers; the backward pass ADDS
cotangents. The sum rule appears exactly where sharing appears. -/
def dupP : Lens (F × F) ((F × F) × (F × F)) :=
  ⟨fun p => (p, p), fun _ d => (d.1.1 + d.2.1, d.1.2 + d.2.2)⟩

/-- Loss of one sample (x, t), as a lens from parameters (w, b):
(w, b) ↦ ((w*x + b) - t)^2. Built entirely by composition. -/
def sampleLoss (x t : F) : Lens (F × F) F :=
  comp square (comp (subConst t) (comp addL (par (scale x) (lid F))))

/-- Total loss over a batch: still just one lens. -/
def batchLoss : List (F × F) → Lens (F × F) F
  | [] => ⟨fun _ => 0.0, fun _ _ => (0.0, 0.0)⟩
  | (x, t) :: rest =>
      comp addL (comp (par (sampleLoss x t) (batchLoss rest)) dupP)

/-- One gradient-descent step. The gradient is literally `L.bwd p 1.0`:
push the unit cotangent back through the composite. -/
def gradStep (L : Lens (F × F) F) (lr : F) (p : F × F) : F × F :=
  let g := L.bwd p 1.0
  (p.1 - lr * g.1, p.2 - lr * g.2)

def train (L : Lens (F × F) F) (lr : F) : Nat → F × F → F × F
  | 0, p => p
  | n + 1, p => train L lr n (gradStep L lr p)

/-- Data drawn from y = 3x + 1. -/
def data : List (F × F) := [(0.0, 1.0), (1.0, 4.0), (2.0, 7.0), (3.0, 10.0)]

def L : Lens (F × F) F := batchLoss data

/-- Central finite differences: the independent numerical witness. -/
def fdGrad (f : F × F → F) (p : F × F) : F × F :=
  let h := 1e-6
  ((f (p.1 + h, p.2) - f (p.1 - h, p.2)) / (2 * h),
   (f (p.1, p.2 + h) - f (p.1, p.2 - h)) / (2 * h))

#eval L.fwd (0.0, 0.0)                      -- initial loss at (w,b) = (0,0)
#eval train L 0.02 400 (0.0, 0.0)           -- learned (w, b): expect near (3, 1)
#eval L.fwd (train L 0.02 400 (0.0, 0.0))   -- final loss: expect near 0
#eval L.bwd (0.3, -0.2) 1.0                 -- compositional gradient at a test point
#eval fdGrad L.fwd (0.3, -0.2)              -- finite-difference witness: must match

end LensLean
