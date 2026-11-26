import Std

/-! Arithmetic witnesses for the Proth prime and the generator of its
2-primary subgroup. The general Proth criterion is applied in the text. -/
namespace TransformPrime

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def p : Nat := 115792089237316195423570985008687907766497981100801255856297059112812235718657
def k : Nat := 2^128 - 255
def omega : Nat := 48833969589503083022509012172934626663844146844705684658994622419314871942659

theorem proth_shape :
    p = k * 2^128 + 1 ∧ 0 < k ∧ k < 2^128 ∧ k % 2 = 1 := by decide

theorem in_window : 2^256 - 2^142 < p ∧ p < 2^256 := by decide

/-- Binary powering returns zero on exhausted fuel with a nonzero exponent. -/
def loop : Nat → Nat → Nat → Nat → Nat
  | 0, e, _, acc => if e = 0 then acc else 0
  | fuel + 1, e, base, acc =>
      if e = 0 then acc
      else loop fuel (e / 2) (base * base % p)
        (if e % 2 = 1 then acc * base % p else acc)

def power (a e : Nat) : Nat := loop 256 e a 1

theorem proth_witness : power 3 ((p - 1) / 2) = p - 1 := by decide
theorem root_value : power 3 k = omega := by decide
theorem root_half_order : power omega (2^127) = p - 1 := by decide
theorem root_full_order : power omega (2^128) = 1 := by decide

end TransformPrime

#print axioms TransformPrime.proth_shape
#print axioms TransformPrime.in_window
#print axioms TransformPrime.proth_witness
#print axioms TransformPrime.root_value
#print axioms TransformPrime.root_half_order
#print axioms TransformPrime.root_full_order
