import GaussianData

/-! The finite certificate for the Gaussian norm-five shell. Each tuple gives the
two Gaussian coordinates of the generator image, in real/imaginary order.
All finite identities below are checked by kernel reduction with `decide`. -/

namespace GaussianShell

open GaussianData

/-- Hermitian squared norm in the standard rank-two lattice. -/
def normSq (v : Point) : Nat :=
  let (a,b,c,d) := v
  a.natAbs * a.natAbs + b.natAbs * b.natAbs +
    c.natAbs * c.natAbs + d.natAbs * d.natAbs

/-- Gaussian coordinates for the map taking the source generator to `v`. -/
def image (v : Point) (s : Int × Int) : Point :=
  let (a,b,c,d) := v
  (s.1*a - s.2*b, s.1*b + s.2*a, s.1*c - s.2*d, s.1*d + s.2*c)

/-- Squared norm with integer-valued coordinates. -/
def integerNorm (v : Point) : Int :=
  let (a,b,c,d) := v
  a*a + b*b + c*c + d*d

private theorem cast_abs_square (a : Int) :
    ((a.natAbs * a.natAbs : Nat) : Int) = a*a := by
  cases a <;> simp [Int.natAbs, Int.negSucc_eq]

theorem integerNorm_eq (v : Point) : (normSq v : Int) = integerNorm v := by
  obtain ⟨a,b,c,d⟩ := v
  simp [normSq, integerNorm, Int.natCast_add, cast_abs_square]

abbrev Gaussian := Int × Int

def mul (s t : Gaussian) : Gaussian :=
  (s.1*t.1 - s.2*t.2, s.1*t.2 + s.2*t.1)

/-- The rank-one standard Hermitian form, conjugate-linear in the first argument. -/
def scalarPair (s t : Gaussian) : Gaussian :=
  (s.1*t.1 + s.2*t.2, s.1*t.2 - s.2*t.1)

def pair (u v : Point) : Gaussian :=
  let (a,b,c,d) := u
  let (e,f,g,h) := v
  (a*e + b*f + c*g + d*h, a*f - b*e + c*h - d*g)

theorem image_generator (v : Point) : image v (1,0) = v := by
  obtain ⟨a,b,c,d⟩ := v
  simp [image]

theorem image_scalar (v : Point) (s t : Gaussian) :
    image v (mul s t) = image (image v t) s := by
  obtain ⟨a,b,c,d⟩ := v
  simp [image, mul]
  grind

theorem image_add (v : Point) (s t : Gaussian) :
    image v (s.1 + t.1, s.2 + t.2) =
      (let (a,b,c,d) := image v s
       let (e,f,g,h) := image v t
       (a+e,b+f,c+g,d+h)) := by
  obtain ⟨a,b,c,d⟩ := v
  simp [image]
  grind

/-- Scalar-linearity determines every map out of the rank-one source by its generator. -/
theorem determined_by_generator (F : Gaussian → Point)
    (h : ∀ s t, F (mul s t) = image (F t) s) : F = image (F (1,0)) := by
  funext s
  simpa [mul] using h s (1,0)

/-- Pullback of the entire Hermitian pairing, including its imaginary part. -/
theorem pullback (v : Point) (s t : Gaussian) :
    pair (image v s) (image v t) =
      (integerNorm v * (scalarPair s t).1, integerNorm v * (scalarPair s t).2) := by
  obtain ⟨a,b,c,d⟩ := v
  simp [pair, image, integerNorm, scalarPair]
  grind

theorem image_injective_at_five (v : Point) (hv : normSq v = 5) :
    ∀ s t, image v s = image v t → s = t := by
  intro s t h
  have hweight : integerNorm v = 5 := (integerNorm_eq v).symm.trans (congrArg Int.ofNat hv)
  have heq := congrArg (pair (image v (1,0))) h
  rw [pullback, pullback, hweight] at heq
  have hx := congrArg Prod.fst heq
  have hy := congrArg Prod.snd heq
  simp [scalarPair] at hx hy
  apply Prod.ext <;> omega

/-- Precomposition by multiplication by i on the source. -/
def rotate (v : Point) : Point :=
  let (a,b,c,d) := v
  (-b, a, -d, c)

theorem source_i_action (v : Point) : image v (0, 1) = rotate v := by
  obtain ⟨a,b,c,d⟩ := v
  simp [image, rotate]

def orbit (v : Point) : List Point :=
  [v, rotate v, rotate (rotate v), rotate (rotate (rotate v))]

theorem fourth_rotation (v : Point) : rotate (rotate (rotate (rotate v))) = v := by
  obtain ⟨a,b,c,d⟩ := v
  simp [rotate]

def coordinates : List Int := [-2, -1, 0, 1, 2]

def box : List Point := do
  let a ← coordinates
  let b ← coordinates
  let c ← coordinates
  let d ← coordinates
  pure (a,b,c,d)

private theorem small_of_square_le_five (n : Nat) (h : n * n ≤ 5) : n ≤ 2 := by
  by_cases hsmall : n ≤ 2
  · exact hsmall
  · have hthree : 3 ≤ n := by omega
    have hbound := Nat.mul_le_mul hthree hthree
    omega

private theorem in_coordinates (x : Int) (h : x.natAbs * x.natAbs ≤ 5) :
    x ∈ coordinates := by
  have hsmall := small_of_square_le_five x.natAbs h
  cases x with
  | ofNat n =>
    simp [coordinates, Int.natAbs] at * <;> omega
  | negSucc n =>
    simp [coordinates, Int.natAbs] at * <;> omega

/-- This bound quantifies over the whole integer lattice. -/
theorem norm_five_in_box (v : Point) (h : normSq v = 5) : v ∈ box := by
  obtain ⟨a,b,c,d⟩ := v
  change a.natAbs * a.natAbs + b.natAbs * b.natAbs +
    c.natAbs * c.natAbs + d.natAbs * d.natAbs = 5 at h
  have ha := in_coordinates a (by omega)
  have hb := in_coordinates b (by omega)
  have hc := in_coordinates c (by omega)
  have hd := in_coordinates d (by omega)
  exact List.mem_flatMap.mpr ⟨a, ha, List.mem_flatMap.mpr ⟨b, hb,
    List.mem_flatMap.mpr ⟨c, hc, List.mem_flatMap.mpr ⟨d, hd, by simp⟩⟩⟩⟩

set_option maxRecDepth 100000
set_option maxHeartbeats 4000000

theorem filtered_box : box.filter (fun v => normSq v == 5) = vectors := by decide

/-- The generated vectors comprise the full shell, with no bound in the conclusion. -/
theorem mem_vectors_iff (v : Point) : v ∈ vectors ↔ normSq v = 5 := by
  rw [← filtered_box, List.mem_filter]
  simp only [beq_iff_eq]
  exact ⟨And.right, fun h => ⟨norm_five_in_box v h, h⟩⟩

/-- Exactly the maps in the generated shell are scalar-linear and preserve the
Hermitian form of the source [5]. Scalar-linearity forces the map's formula,
which is additive by `image_add` and injective by `image_injective_at_five`. -/
theorem embedding_classification (F : Gaussian → Point) :
    ((∀ s t, F (mul s t) = image (F t) s) ∧
     (∀ s t, pair (F s) (F t) = (5*(scalarPair s t).1, 5*(scalarPair s t).2))) ↔
      ∃ v ∈ vectors, F = image v := by
  constructor
  · rintro ⟨hscalar, hpair⟩
    refine ⟨F (1,0), (mem_vectors_iff _).2 ?_, determined_by_generator F hscalar⟩
    have hp := congrArg Prod.fst (hpair (1,0) (1,0))
    have hd (v : Point) : (pair v v).1 = integerNorm v := by
      obtain ⟨a,b,c,d⟩ := v
      rfl
    rw [hd] at hp
    have hw : integerNorm (F (1,0)) = 5 := by simpa [scalarPair] using hp
    have hcast := (integerNorm_eq (F (1,0))).trans hw
    omega
  · rintro ⟨v, hv, rfl⟩
    have hnorm := (mem_vectors_iff v).1 hv
    have hweight : integerNorm v = 5 := (integerNorm_eq v).symm.trans (congrArg Int.ofNat hnorm)
    exact ⟨image_scalar v, fun s t => by rw [pullback, hweight]⟩

theorem image_unique (v w : Point) (h : image v = image w) : v = w := by
  simpa only [image_generator] using congrFun h (1,0)

theorem vector_count : vectors.length = 48 := by decide
theorem vectors_nodup : vectors.Nodup := by decide
theorem representative_count : representatives.length = 12 := by decide
theorem representatives_nodup : representatives.Nodup := by decide
theorem representatives_norm : ∀ v ∈ representatives, normSq v = 5 := by decide
theorem free_orbits : ∀ v ∈ representatives, (orbit v).Nodup := by decide
theorem free_on_full_shell (v : Point) (h : normSq v = 5) : (orbit v).Nodup := by
  have hfree : ∀ w ∈ vectors, (orbit w).Nodup := by decide
  exact hfree v ((mem_vectors_iff v).2 h)

/-- Distinct entries across the entire expansion certify disjointness as well as freeness. -/
theorem orbit_partition_nodup : (representatives.flatMap orbit).Nodup := by decide

private theorem all_vectors_covered : ∀ v ∈ vectors, v ∈ representatives.flatMap orbit := by decide
private theorem all_expanded_in_shell : ∀ v ∈ representatives.flatMap orbit, v ∈ vectors := by decide

theorem mem_orbit_partition_iff (v : Point) :
    (∃ r ∈ representatives, v ∈ orbit r) ↔ normSq v = 5 := by
  rw [← List.mem_flatMap, ← mem_vectors_iff]
  exact ⟨all_expanded_in_shell v, all_vectors_covered v⟩

end GaussianShell

#print axioms GaussianShell.embedding_classification
#print axioms GaussianShell.mem_orbit_partition_iff
#print axioms GaussianShell.orbit_partition_nodup
