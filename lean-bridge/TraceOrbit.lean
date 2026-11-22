import Formalism.ThetaLiftIndependence.ThetaOrbitSums.OrbitSum

/-! Apply the archived orbit-sum identity to the nine cube-root assignments.
    A pair (i,j) denotes the triple (i,j,-i-j) over F₃. -/
namespace PerrinTraceOrbit

set_option maxHeartbeats 0
set_option maxRecDepth 100000

abbrev Assignment := Fin 3 × Fin 3
abbrev Scalars := Multiplicative (Fin 3)

def scale (a : Scalars) (x : Assignment) : Assignment :=
  (a.toAdd + x.1, a.toAdd + x.2)

private theorem scale_one : ∀ x, scale 1 x = x := by decide
private theorem scale_mul : ∀ (a b : Scalars) x,
    scale (a * b) x = scale a (scale b x) := by decide

local instance : MulAction Scalars Assignment where
  smul := scale
  one_smul := scale_one
  mul_smul := scale_mul

/-- The two cyclic coordinate permutations, followed by a translation. -/
def frobenius (forward : Bool) (t x : Assignment) : Assignment :=
  let z := -(x.1 + x.2)
  if forward then (t.1 + x.2, t.2 + z) else (t.1 + z, t.2 + x.1)

def weight (forward : Bool) (t x : Assignment) : ℚ :=
  if frobenius forward t x = x then 1 else 0

private theorem weight_invariant :
    ∀ (f : Bool) (t : Assignment) (a : Scalars) (x : Assignment),
      weight f t (a • x) = weight f t x := by decide

private def natWeight (f : Bool) (t x : Assignment) : Nat :=
  if frobenius f t x = x then 1 else 0

private theorem nat_sum : ∀ (f : Bool) (t : Assignment),
    (∑ x : Assignment, natWeight f t x) = (if t.1 = t.2 then 3 else 0) := by decide

private theorem weight_eq_cast (f : Bool) (t x : Assignment) :
    weight f t x = (natWeight f t x : ℚ) := by
  by_cases h : frobenius f t x = x <;> simp [natWeight, weight, h]

theorem plain_sum (f : Bool) (t : Assignment) :
    (∑ x : Assignment, weight f t x) = (if t.1 = t.2 then 3 else 0) := by
  simp only [weight_eq_cast, ← Nat.cast_sum, nat_sum]
  by_cases h : t.1 = t.2 <;> norm_num [h]

theorem fixed_orbit_mass (f : Bool) (t : Assignment) :
    (∑ᶠ o : MulAction.orbitRel.Quotient Scalars Assignment,
      (Nat.card (MulAction.stabilizer Scalars (Quotient.out o)) : ℚ)⁻¹ *
        weight f t (Quotient.out o)) = (if t.1 = t.2 then 1 else 0) := by
  classical
  have h := Formalism.ThetaLiftIndependence.orbitSum
    Scalars Assignment ℚ (weight f t) (weight_invariant f t)
  rw [← h, plain_sum]
  have hcard : Fintype.card Scalars = 3 := by decide
  rw [hcard]
  by_cases ht : t.1 = t.2 <;> norm_num [ht]

end PerrinTraceOrbit

#print axioms PerrinTraceOrbit.fixed_orbit_mass
