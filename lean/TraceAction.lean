import Std

/-! Finite fixed-point counts for the two cyclic coordinate permutations and
    nine translations. The arithmetic interpretation of this action is separate. -/
namespace TraceAction

set_option maxRecDepth 10000
set_option maxHeartbeats 0

structure Point where
  a : Nat
  b : Nat
  c : Nat
  deriving DecidableEq, BEq

/-- Representatives in {0,1,2} of the plane a+b+c=0 modulo 3. -/
def points : List Point :=
  (List.range 3).flatMap fun a =>
    (List.range 3).map fun b => ⟨a, b, (6-a-b) % 3⟩

def lifts : List (Bool × Point) :=
  [false, true].flatMap fun direction => points.map fun t => (direction, t)

def act (g : Bool × Point) (x : Point) : Point :=
  let y : Point := if g.1 then ⟨x.b,x.c,x.a⟩ else ⟨x.c,x.a,x.b⟩
  let t := g.2
  ⟨(y.a+t.a) % 3, (y.b+t.b) % 3, (y.c+t.c) % 3⟩

/-- b-a labels the three cosets modulo the diagonal. -/
def coset (x : Point) : Nat := (x.b + 3 - x.a) % 3

def fixedPoints (g : Bool × Point) : Nat :=
  (points.filter fun x => act g x == x).length

def fixedCosets (g : Bool × Point) : Nat :=
  ((List.range 3).filter fun k =>
    let representative : Point := ⟨0,k,(3-k) % 3⟩
    coset (act g representative) == k).length

theorem invariant_plane :
    lifts.all (fun g => points.all (fun x => points.contains (act g x))) = true := by decide

theorem action_descends :
    lifts.all (fun g => points.all (fun x => points.all (fun y =>
      coset x != coset y || coset (act g x) == coset (act g y)))) = true := by decide

theorem eligible_lifts : lifts.length = 18 := by decide

theorem six_with_fixed_point :
    (lifts.filter fun g => fixedPoints g > 0).length = 6 := by decide

theorem twelve_without_fixed_point :
    (lifts.filter fun g => fixedPoints g == 0).length = 12 := by decide

theorem same_fixed_counts :
    lifts.all (fun g => fixedPoints g == fixedCosets g &&
      (fixedPoints g == 3 || fixedPoints g == 0)) = true := by decide

end TraceAction
#print axioms TraceAction.invariant_plane
#print axioms TraceAction.action_descends
#print axioms TraceAction.eligible_lifts
#print axioms TraceAction.six_with_fixed_point
#print axioms TraceAction.twelve_without_fixed_point
#print axioms TraceAction.same_fixed_counts
