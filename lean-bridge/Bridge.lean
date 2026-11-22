import Formalism.ThetaLiftIndependence.ThetaOrbitSums.OrbitSum

/-! The four units of ℤ[i] act on embeddings of the Hermitian line with Gram
matrix [5] into the standard Gaussian plane. An embedding is determined by the
image of 1, a vector of norm five. Its four integer coordinates lie in [-2, 2].
The action below is multiplication by 1, i, -1, -i in that order. -/

namespace GaussianTransfer

set_option maxRecDepth 100000
set_option maxHeartbeats 0

abbrev FourUnits := Multiplicative (Fin 4)
abbrev GaussianCoordinate := Fin 5 × Fin 5

def centered (a : Fin 5) : ℤ := (a.val : ℤ) - 2

def norm (z : GaussianCoordinate) : ℤ :=
  centered z.1 ^ 2 + centered z.2 ^ 2

def turn (u : FourUnits) (z : GaussianCoordinate) : GaussianCoordinate :=
  match (Multiplicative.toAdd u).val with
  | 0 => z
  | 1 => (z.2.rev, z.1)
  | 2 => (z.1.rev, z.2.rev)
  | _ => (z.2, z.1.rev)

theorem centered_rev : ∀ a : Fin 5, centered a.rev = -centered a := by decide

private theorem turn_one : ∀ z, turn 1 z = z := by decide

private theorem turn_mul :
    ∀ (u v : FourUnits) (z : GaussianCoordinate), turn (u * v) z = turn u (turn v z) := by
  decide

private theorem turn_norm : ∀ u z, norm (turn u z) = norm z := by decide

abbrev NormFiveShell :=
  {v : GaussianCoordinate × GaussianCoordinate // norm v.1 + norm v.2 = 5}

theorem centered_injective : Function.Injective centered := by
  intro a b h
  apply Fin.ext
  unfold centered at h
  omega

private theorem centered_of_square_le {a : ℤ} (h : a ^ 2 ≤ 5) :
    ∃ x : Fin 5, centered x = a := by
  have hlo : -2 ≤ a := by
    by_contra! contra
    have : a ≤ -3 := by omega
    nlinarith [sq_nonneg (a + 3)]
  have hhi : a ≤ 2 := by
    by_contra! contra
    have : 3 ≤ a := by omega
    nlinarith [sq_nonneg (a - 3)]
  refine ⟨⟨(a + 2).toNat, by omega⟩, ?_⟩
  unfold centered
  dsimp
  omega

/-- Every integral vector of squared norm five occurs in the finite shell. -/
theorem covers_integer_shell (a b c d : ℤ) (h : a ^ 2 + b ^ 2 + (c ^ 2 + d ^ 2) = 5) :
    ∃ v : NormFiveShell, centered v.val.1.1 = a ∧ centered v.val.1.2 = b ∧
      centered v.val.2.1 = c ∧ centered v.val.2.2 = d := by
  obtain ⟨x, hx⟩ := centered_of_square_le (a := a) (by
    nlinarith [sq_nonneg b, sq_nonneg c, sq_nonneg d])
  obtain ⟨y, hy⟩ := centered_of_square_le (a := b) (by
    nlinarith [sq_nonneg a, sq_nonneg c, sq_nonneg d])
  obtain ⟨z, hz⟩ := centered_of_square_le (a := c) (by
    nlinarith [sq_nonneg a, sq_nonneg b, sq_nonneg d])
  obtain ⟨w, hw⟩ := centered_of_square_le (a := d) (by
    nlinarith [sq_nonneg a, sq_nonneg b, sq_nonneg c])
  refine ⟨⟨((x, y), (z, w)), ?_⟩, hx, hy, hz, hw⟩
  change (centered x ^ 2 + centered y ^ 2) + (centered z ^ 2 + centered w ^ 2) = 5
  simpa only [hx, hy, hz, hw] using h

instance : MulAction FourUnits NormFiveShell where
  smul u v := ⟨(turn u v.val.1, turn u v.val.2), by
    change norm (turn u v.val.1) + norm (turn u v.val.2) = 5
    rw [turn_norm, turn_norm]
    exact v.property⟩
  one_smul v := Subtype.ext (Prod.ext (turn_one _) (turn_one _))
  mul_smul u v x := Subtype.ext (Prod.ext (turn_mul u v _) (turn_mul u v _))

theorem four_units_card : Fintype.card FourUnits = 4 := by decide
theorem norm_five_card : Fintype.card NormFiveShell = 48 := by decide

private theorem fixed_coordinates :
    ∀ (u : FourUnits) (z w : GaussianCoordinate), norm z + norm w = 5 →
      turn u z = z → turn u w = w → u = 1 := by decide

theorem free_on_norm_five (u : FourUnits) (v : NormFiveShell) (h : u • v = v) : u = 1 :=
  fixed_coordinates u v.val.1 v.val.2 v.property
    (congrArg (fun p : NormFiveShell => p.val.1) h)
    (congrArg (fun p : NormFiveShell => p.val.2) h)

theorem stabilizer_card_one (v : NormFiveShell) :
    Nat.card (MulAction.stabilizer FourUnits v) = 1 := by
  apply Nat.card_eq_one_iff_unique.mpr
  refine ⟨⟨?_⟩, ⟨1⟩⟩
  intro a b
  apply Subtype.ext
  exact (free_on_norm_five a.val v (MulAction.mem_stabilizer_iff.mp a.property)).trans
    (free_on_norm_five b.val v (MulAction.mem_stabilizer_iff.mp b.property)).symm

/-- The actual archive theorem specialized to this finite representation shell. -/
theorem norm_five_orbit_mass :
    (∑ᶠ o : MulAction.orbitRel.Quotient FourUnits NormFiveShell,
      (Nat.card (MulAction.stabilizer FourUnits (Quotient.out o)) : ℚ)⁻¹ * 1) = 12 := by
  classical
  have orbit_identity := Formalism.ThetaLiftIndependence.orbitSum
    FourUnits NormFiveShell ℚ (fun _ => (1 : ℚ)) (fun _ _ => rfl)
  rw [← orbit_identity]
  simp [four_units_card, norm_five_card]
  <;> norm_num

theorem norm_five_orbit_count :
    Nat.card (MulAction.orbitRel.Quotient FourUnits NormFiveShell) = 12 := by
  classical
  letI := Fintype.ofFinite (MulAction.orbitRel.Quotient FourUnits NormFiveShell)
  have h := norm_five_orbit_mass
  simp only [stabilizer_card_one, Nat.cast_one, inv_one, mul_one, finsum_eq_sum_of_fintype,
    Finset.sum_const, Finset.card_univ, nsmul_eq_mul] at h
  rw [Nat.card_eq_fintype_card]
  exact_mod_cast h

end GaussianTransfer

#print axioms GaussianTransfer.norm_five_orbit_mass
#print axioms GaussianTransfer.norm_five_orbit_count
