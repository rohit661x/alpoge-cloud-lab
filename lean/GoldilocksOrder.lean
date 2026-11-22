import Std

/-! Fixed arithmetic witnesses in the quotient by X³ − X − 1.
    Run with: lean GoldilocksOrder.lean -/

namespace GoldilocksOrder

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def p : Nat := 18446744069414584321
def n : Nat := p * p + p + 1

structure Cubic where
  a : Nat
  b : Nat
  c : Nat
  deriving DecidableEq

def one : Cubic := ⟨1, 0, 0⟩
def alpha : Cubic := ⟨0, 1, 0⟩

/-- Multiply coefficient triples, replacing X³ by X+1 and X⁴ by X²+X. -/
def mul (u v : Cubic) : Cubic :=
  let d3 := u.b * v.c + u.c * v.b
  let d4 := u.c * v.c
  ⟨(u.a * v.a + d3) % p,
   (u.a * v.b + u.b * v.a + d3 + d4) % p,
   (u.a * v.c + u.b * v.b + u.c * v.a + d4) % p⟩

/-- Process low bits first; fuel bounds the number of squarings. -/
def powerLoop : Nat → Nat → Cubic → Cubic → Cubic
  | 0, _, _, acc => acc
  | fuel + 1, e, base, acc =>
      if e = 0 then acc
      else powerLoop fuel (e / 2) (mul base base)
             (if e % 2 = 1 then mul acc base else acc)

def alphaPower (e : Nat) : Cubic := powerLoop 128 e alpha one

theorem bit_bound : n < 2 ^ 128 := by decide

theorem factor_product :
    n = 3 * 937 * 724723 * 167034643597991036904547663171 := by decide

theorem full_exponent : alphaPower n = one := by decide

theorem third_witness :
    alphaPower (n / 3) = ⟨4294967295, 0, 0⟩ := by decide

theorem at_three : alphaPower (n / 3) ≠ one := by
  rw [third_witness]
  decide

theorem at_937 : alphaPower (n / 937) ≠ one := by decide

theorem at_724723 : alphaPower (n / 724723) ≠ one := by decide

theorem at_large_factor :
    alphaPower (n / 167034643597991036904547663171) ≠ one := by decide

end GoldilocksOrder
#print axioms GoldilocksOrder.factor_product
#print axioms GoldilocksOrder.full_exponent
#print axioms GoldilocksOrder.at_three
#print axioms GoldilocksOrder.at_937
#print axioms GoldilocksOrder.at_724723
#print axioms GoldilocksOrder.at_large_factor
#print axioms GoldilocksOrder.third_witness
