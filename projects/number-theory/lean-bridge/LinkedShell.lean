import Bridge
import GaussianShell

/-! Identify the shell used to specialize the archive orbit identity with the
signed vectors emitted by Python, including the action of the generator i. -/

namespace LinkedShell

open GaussianTransfer GaussianData

def toPoint (v : NormFiveShell) : Point :=
  (centered v.val.1.1, centered v.val.1.2, centered v.val.2.1, centered v.val.2.2)

theorem toPoint_mem (v : NormFiveShell) : toPoint v ∈ vectors := by
  apply (GaussianShell.mem_vectors_iff _).2
  have hw : GaussianShell.integerNorm (toPoint v) = 5 := by
    simpa only [GaussianShell.integerNorm, toPoint, GaussianTransfer.norm, pow_two, add_assoc]
      using v.property
  have hcast := (GaussianShell.integerNorm_eq (toPoint v)).trans hw
  omega

theorem toPoint_injective : Function.Injective toPoint := by
  intro v w h
  apply Subtype.ext
  apply Prod.ext
  · exact Prod.ext (centered_injective (congrArg Prod.fst h))
      (centered_injective (congrArg (fun p : Point => p.2.1) h))
  · exact Prod.ext (centered_injective (congrArg (fun p : Point => p.2.2.1) h))
      (centered_injective (congrArg (fun p : Point => p.2.2.2) h))

theorem mem_vectors_iff_preimage (p : Point) : p ∈ vectors ↔ ∃ v, toPoint v = p := by
  constructor
  · obtain ⟨a,b,c,d⟩ := p
    intro h
    have hn := (GaussianShell.mem_vectors_iff _).1 h
    have hw : GaussianShell.integerNorm (a,b,c,d) = 5 :=
      (GaussianShell.integerNorm_eq (a,b,c,d)).symm.trans (congrArg Int.ofNat hn)
    obtain ⟨v, ha, hb, hc, hd⟩ := covers_integer_shell a b c d (by
      simpa only [GaussianShell.integerNorm, pow_two, add_assoc] using hw)
    exact ⟨v, by simp only [toPoint, ha, hb, hc, hd]⟩
  · rintro ⟨v, rfl⟩
    exact toPoint_mem v

/-- A bijection onto the specific list-membership subtype. -/
noncomputable def shellEquiv : NormFiveShell ≃ {p : Point // p ∈ vectors} :=
  Equiv.ofBijective (fun v => ⟨toPoint v, toPoint_mem v⟩)
    ⟨fun _ _ h => toPoint_injective (congrArg Subtype.val h), by
      intro p
      obtain ⟨v, hv⟩ := (mem_vectors_iff_preimage p.val).1 p.property
      exact ⟨v, Subtype.ext hv⟩⟩

/-- The generator of the archive action is precomposition by the Gaussian unit i. -/
theorem maps_generator (v : NormFiveShell) :
    toPoint (Multiplicative.ofAdd (1 : Fin 4) • v) = GaussianShell.rotate (toPoint v) := by
  change (centered v.val.1.2.rev, centered v.val.1.1,
      centered v.val.2.2.rev, centered v.val.2.1) = _
  simp only [toPoint, GaussianShell.rotate, centered_rev]

end LinkedShell

#print axioms LinkedShell.shellEquiv
#print axioms LinkedShell.maps_generator
