import Std

/-! Integer consequences of the RH–Schoenfeld bound for a 256-bit integer
    with 112 prescribed leading bits. The analytic endpoint inequality is an
    explicit external hypothesis of the count theorem. -/
namespace PrefixArithmetic

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def minimum : Nat := 119364572746971480821742986104065588231880
def numerator : Nat := 300 * 2^144 - 896^2 * 2^128
def denominator : Nat := 60 * 896

theorem rounding_certificate :
    (minimum - 1) * denominator ≤ numerator ∧ numerator < minimum * denominator := by
  decide

/-- The integer count n satisfies the cleared strict inequality by Schoenfeld
    at both even endpoints, RH, π > 3, and log(2) < 7/10. -/
theorem prefix_count (n : Nat) (analyticBound : numerator < n * denominator) :
    minimum ≤ n ∧ 2^143 < 94*n := by
  have hlo : minimum ≤ n := by
    by_cases h : minimum ≤ n
    · exact h
    · have hn : n ≤ minimum - 1 := by omega
      have hprod := Nat.mul_le_mul_right denominator hn
      have hle := Nat.le_trans hprod rounding_certificate.1
      omega
  exact ⟨hlo, Nat.lt_of_lt_of_le (by decide : 2^143 < 94*minimum)
    (Nat.mul_le_mul_left 94 hlo)⟩

/-- Cross-multiplication of (93/94)^8296 < 2^(-128). -/
theorem sampling_tail : (2 : Nat)^128 * 93^8296 < 94^8296 := by decide

end PrefixArithmetic
#print axioms PrefixArithmetic.rounding_certificate
#print axioms PrefixArithmetic.prefix_count
#print axioms PrefixArithmetic.sampling_tail
