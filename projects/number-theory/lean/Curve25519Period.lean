import Std

/-! Fixed arithmetic witnesses for three roots of X³ − X − 1 over the
Curve25519 base field. The Python verifier supplies the Pocklington proofs
and the independent Perrin companion-matrix calculation. -/
namespace Curve25519Period

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def p : Nat := 2^255 - 19
def n : Nat := p - 1
def q : Nat := 74058212732561358302231226437062788676166966415465897661863160754340907
def a : Nat := 14535863002999908821470556791477736972039661322948065771707477577742314888008
def b : Nat := 45980055862320150516043228587377395813021437899593394500348496167731510246271
def c : Nat := 55276170371996136086057199629832775068208885443099103767401610262439304505619

theorem factor_product : n = 2^2 * 3 * 65147 * q := by decide
theorem bit_bound : n < 2^255 := by decide
theorem representatives : 0 < a ∧ a < b ∧ b < c ∧ c < p := by decide
theorem cubic_roots :
    a^3 % p = (a+1) % p ∧ b^3 % p = (b+1) % p ∧ c^3 % p = (c+1) % p := by decide

/-- Square and multiply from the least significant bit. A nonzero residual
exponent at fuel exhaustion returns 0, so a truncated full power cannot pass. -/
def powerLoop : Nat → Nat → Nat → Nat → Nat
  | 0, e, _, acc => if e = 0 then acc else 0
  | fuel + 1, e, base, acc =>
    if e = 0 then acc
    else powerLoop fuel (e / 2) (base * base % p)
           (if e % 2 = 1 then acc * base % p else acc)

def modPow (r e : Nat) : Nat := powerLoop 255 e r 1

/-- Every divisor test has exponent at most d, whose bit bound is checked. -/
def checkOrder (r d : Nat) (primes : List Nat) : Bool :=
  decide (d < 2^255) && (modPow r d == 1) &&
    primes.all (fun l => (d % l == 0) && !(modPow r (d/l) == 1))

theorem first_witnesses : checkOrder a n [2, 3, 65147, q] = true := by decide
theorem second_witnesses : checkOrder b (n/3) [2, 65147, q] = true := by decide
theorem third_witnesses : checkOrder c (n/2) [2, 3, 65147, q] = true := by decide

end Curve25519Period

#print axioms Curve25519Period.factor_product
#print axioms Curve25519Period.bit_bound
#print axioms Curve25519Period.representatives
#print axioms Curve25519Period.cubic_roots
#print axioms Curve25519Period.first_witnesses
#print axioms Curve25519Period.second_witnesses
#print axioms Curve25519Period.third_witnesses
