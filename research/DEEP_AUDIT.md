# Independent audit of the Goldilocks result and extensions

The original Goldilocks claim survives a separate computation. Raising the Perrin companion matrix on the state (3,0,2) verifies the same exact period as the norm-one order certificate. In both checks the full exponent returns the initial state and every quotient by a prime factor fails to do so. PARI/GP provides a third route using its own finite-field order routine.

## The cubic test and its frequency

Let p≡1 mod 3 be prime with X³−X−1 irreducible modulo p. Write α for one of its roots. The norm-one subgroup of the cubic extension has size N=p²+p+1. To decide whether α is a cube in that subgroup, test whether t³−6t−3 has a root over the base field. Three roots mean yes and zero mean no. Computing a single gcd with tᵖ−t suffices.

The proportion of eligible primes giving a cube is exactly **one third in the limit**. The absolute density among rational primes is **1/18**. The same one-third law holds among eligible primes in every compatible fixed arithmetic progression. In particular, requiring a fixed power of two to divide p−1 retains both 1/3 among eligible primes and 1/18 among the primes in that progression. This covers an additional arithmetic constraint used to support radix-two number-theoretic transforms.

The proof encodes the nine assignments of cube roots of product one as nine points of an affine plane over the field of three elements. Grouping them by common multiplication by a cube root of unity gives three classes, indexed by the roots of the smaller cubic. Exactly six of the 18 eligible Frobenius actions fix an assignment. Chebotarev's theorem gives the natural density. The general algebraic and density arguments are written proofs; the Lean file verifies the finite fixed-point counts. [Proof of the cubic criterion, Galois group, and progression result](DENSITY.md)

The degree-nine number field and its order-108 Galois group are already catalogued, as is the cubic resolvent field. Publication priority for the specific norm-one criterion, density application, and public-field order certificates remains open. [LMFDB degree-nine field](https://www.lmfdb.org/NumberField/9.3.6466042647.1) · [LMFDB cubic field](https://www.lmfdb.org/NumberField/3.3.621.1)

The exhaustive count through one million is **4,369 cube cases and 8,708 noncube cases** among 13,077 eligible primes. The distinction between the finite count and the limiting density follows from the proof above. Primes up to 10,000 were well within the range of earlier Perrin period calculations. [Prior-art audit](PRIOR_AUDIT.md)

## Exact period over a second public field

Over the Curve25519 base prime p=2²⁵⁵−19, all three roots of X³−X−1 lie in the base field. In increasing order of residue, they have orders p−1, (p−1)/3, and (p−1)/2. The first is a primitive element. The scalar Perrin recurrence consequently has period **2²⁵⁵−20**, attaining the largest possible period in this separable split case. The verification covers arithmetic in the public base field. [Root values, prime certificates and period proof](CURVE25519_PERIOD.md)

## Constructing cube roots and reproducing the checks

The constructor returns all three norm-one cube roots for the Pallas and BLS12-381 base fields and an empty list for Goldilocks and the BLS12-381 scalar field. For a positive case, write m=N/3. The first root returned is α raised to the inverse of 3 modulo m. The other two are its multiples by the nontrivial cube roots of unity. Each output is checked by cubing, checking norm one, and computing its trace.

From the project root:

```sh
python3 -m unittest discover -v
python3 matrix_periods.py
python3 cubic_lift.py 151
gp -q -f research/pari_audit.gp > pari-rows.jsonl
python3 galois_census.py pari-rows.jsonl
```

The last two commands require PARI/GP with its galdata package. They independently obtain the Galois groups of two degree-nine polynomials, rediscover the Curve25519 roots and orders, and factor the three polynomials at every unramified prime through one million. A Python sieve checks the list of primes and compares each record with the permutation model; at every eligible prime it checks the cube decision by exponentiation in the extension. The cloud evidence includes the prime-by-prime records, the joint counts and the named-field lifts. The research articles and code specify all exceptions. These results are independent of the Riemann hypothesis. The exact orders over the BLS12-381 fields remain open in this investigation.
