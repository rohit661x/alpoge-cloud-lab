import Std

/-! Exact arithmetic specialization for the one-root trace window near 2^256.
    The analytic endpoint bounds and the real logarithm enclosures are external. -/
namespace TraceWindowArithmetic

def a : Nat := 2^256 - 2^142
def b : Nat := 2^256
def scale : Nat := 10^12
-- Common directed log enclosures for the endpoints, in units of 10^-12.
def logLo : Nat := 177445678223345
def logHi : Nat := 177445678223346
def logDiscHi : Nat := 8468213009195

-- P/Q is the normalized error coefficient using pi >= 314/100.
def P : Nat :=
  400*logLo*logDiscHi + 7536*scale*logDiscHi + 400*logHi*logLo
    + 800*scale*logLo + 60288*scale^2
def Q : Nat := 2512*scale*logLo

def rootA : Nat := 340282366920938463463374607431768203264
def rootB : Nat := 2^128
def errorA : Nat := 10276872985811222010751394186904997314029214
def errorB : Nat := 10276872985811222010751394186904997561435932
def mainLo : Nat := 31419115728562980068031311655207342066405049
def mainHi : Nat := 31419115728563157131322134758711610822161920

/-- Integer square roots, directed integral bounds, and endpoint error ceilings.
    These are kernel-decided arithmetic, independent of analytic hypotheses. -/
theorem directed_rounding :
    0 < logLo ∧ 0 < logHi ∧ 0 < Q ∧
    (rootA-1)^2 < a ∧ a ≤ rootA^2 ∧ rootB^2 = b ∧
    mainLo*logHi ≤ 1000*(b-a)*scale ∧
    1000*(b-a)*scale ≤ mainHi*logLo ∧
    1000*rootA*P ≤ errorA*Q ∧ 1000*rootB*P ≤ errorB*Q := by decide

/-- pa,pb are the Chebotarev prime counts at a,b and n their difference.
    ia,ib model the floors of 1000 times the corresponding logarithmic integrals.
    Four endpoint inequalities allow both signs for the two independent errors. -/
theorem classified_window_count (pa pb ia ib n : Nat)
    (countDiff : pb = pa + n)
    (atALower : ia ≤ 4000*pa + errorA) (atAUpper : 4000*pa ≤ ia + errorA)
    (atBLower : ib ≤ 4000*pb + errorB) (atBUpper : 4000*pb ≤ ib + errorB)
    (integralLower : ia + mainLo ≤ ib) (integralUpper : ib ≤ ia + mainHi) :
    2716342439235134011632130820349336797735 ≤ n ∧
      n ≤ 12993215425046400288206230783130401424406 := by
  unfold errorA at atALower atAUpper
  unfold errorB at atBLower atBUpper
  unfold mainLo at integralLower
  unfold mainHi at integralUpper
  omega

end TraceWindowArithmetic
#print axioms TraceWindowArithmetic.directed_rounding
#print axioms TraceWindowArithmetic.classified_window_count
