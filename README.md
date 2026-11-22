# Alpöge number-theory lab

This Python 3.8+ project lets you compute finite pieces of Alpöge’s formalization and use the Riemann hypothesis to bound the average search effort for a prime. The numerical commands use the Python standard library.

The [cubic-field study](research/RESULTS.md) certifies a norm-one generator for the Goldilocks field and compares the same trinomial over ten public fields.

The [independent audit and extensions](research/DEEP_AUDIT.md) give a degree-three cube test, its prime density, explicit roots, and the exact Perrin period over the Curve25519 base field.

## A generated operator at a 1,024-bit prime

The `cm` command builds lattice classes and their prime-index neighbor operators from a negative fundamental discriminant. Its small-prime route enumerates sublattices and checks the result by counting lattice vectors. Its large-prime route recovers the neighbors using modular square roots, so its work at this discriminant does not scale linearly with the value of the prime.

```sh
python3 zeta_prime_density.py cm chain -D -23 --primes 2 2 --through 32
python3 alpoge_cm_certificate.py verify cm_prime_1024.json
python3 zeta_prime_density.py cm certified cm_prime_1024.json
```

The included public certificate proves the primality of a particular 1,024-bit integer and supplies integers x and y satisfying 2x² + xy + 3y² = p. Its known factor of p−1 is 3^324, which exceeds √p. The witness 3 satisfies Pocklington’s criterion. To reproduce this research input, run `python3 alpoge_cm_certificate.py generate --bits 1024`. The generator is deterministic.

For discriminant −23 the three reduced forms, in the order printed, are (1,1,6), (2,−1,3), and (2,1,3). From the certificate the program derives a square root of −23 modulo p. For each class it computes the two lines that define the index-p neighbors and reduces the resulting forms. The resulting matrix has zeros on its diagonal and ones elsewhere. The three theta series have coefficients 0, 2, and 2 at index p. The normalized difference of the first two gives **−1** for the coefficient of the modular form η(τ)η(23τ) at this prime. [Binary theta series, Hecke operators, and the eta-product identity, equations (1.17)–(1.21)](https://arxiv.org/pdf/1302.2359)

The same command cross-checks the answer at the full 1,024-bit index. It counts the roots of X³−X−1 modulo p using polynomial exponentiation and a greatest common divisor. It finds zero roots. Serre’s identity gives the Fourier coefficient as the root count minus one, again −1. This second algorithm takes only p and does not see the lattice representation. [Serre, *On a theorem of Jordan*, §5.3](https://www.math.mcgill.ca/goren/SeminarOnCohomology/Serre.pdf#page=6)

This calculation uses classical imaginary quadratic ideal classes. Composing prime operators here counts paths on those classes. Constructing a rank-changing automorphic theta lift for a specific field and matching it to the hypotheses of Alpöge’s proof is a further research milestone. The prime certificate and coefficient above are independent of RH.

## Other calculations

From this folder, run:

```sh
python3 zeta_prime_density.py --bits 1024
python3 zeta_prime_density.py theta --vector vector_chain.json
python3 zeta_prime_density.py theta --gaussian 2 5
python3 zeta_prime_density.py local --prime 3 --e 1
python3 zeta_prime_density.py prime-sum --window 100 --samples 3
python3 -m unittest -v
```

| Calculation | What it gives you |
| --- | --- |
| Prime search by bit length | An estimate from Gram’s series and a separate bound on the mean number of independent, uniformly sampled odd candidates through the first prime. For 1,024 bits, the estimate is 354.74 and the enclosing interval is [354.544, 354.892]. This describes the distribution before trial division or other RSA-specific filters. |
| Vector-valued kernel chain | An exact rational evaluation of `chainOpM` on supplied class weights and linear maps. In the included example, two maps applied successively give (3, 5/4, 1). Multiplying by the common denominator 24 gives the integer vector (72, 30, 24). |
| Gaussian lattice | An exact theta-series coefficient for the standard Hermitian lattice over the Gaussian integers. At rank two there are 48 vectors of squared norm five. For constant input one, weighting by its 32 automorphisms gives this class’s contribution of 3/2. |
| Local divisibility | A specialization of the proof’s `key_minor_dvd` lemma to the ring of integers of the form a + b√p with a,b integral. It checks the input congruences and constructs an exact quotient of the resulting minor by √p. Use `local --help` for the input format. [Pinned Lean lemma](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GrowthBounds/CoarseMultiplicity/KeyMinorDvd.lean#L132-L155) |
| Prime-power window | Floating-point values of `Formalism.Sz` and `Formalism.Gz`. Each prime power contributes the logarithm of its underlying prime. The window command evaluates finitely many points between Y and Y raised to the power 3/2. |

**Where the geometric inputs come from.** In the vector example, the user supplies the finite kernels, and each matrix entry is exact. Its class data are illustrative. The Gaussian calculation constructs coefficients for one concrete lattice. Constructing the CM fields, automorphic representations, and kernels throughout Alpöge’s global tower remains outside the Python port. The published Lean export contains the proof that assembles those ingredients. [Original author’s note](https://alpo.ge/remark.pdf) · [Pinned kernel and lift definitions](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/ThetaLiftIndependence/Statement.lean) · [Pinned Hermitian theta series](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/HermitianLattices/StatementTheta.lean) · [Pinned prime sums](https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/StatementOC.lean)

**How the prime search uses RH.** The interval applies Schoenfeld’s inequality separately at the two ends of the bit range. The code encloses the intervening logarithmic integral using its endpoint slopes, rounds outwards with rational arithmetic, and divides the number of odd candidates by the resulting prime-count bounds. The inequality applies for endpoints at least 2,657. Smaller ranges use an exact sieve. The bound uses the theorem established in Lean. The example matrices and the sampled prime sums do not feed the cryptographic bit-range calculation. [Schoenfeld, Corollary 1](https://doi.org/10.1090/S0025-5718-1976-0457374-X)

**Full formal replay.** With the pinned challenge and solution exports and a trusted build of the documented `con-leche` checker, run `python3 zeta_prime_density.py verify challenge.ndjson solution.ndjson --checker /path/to/con-leche`. See `python3 zeta_prime_density.py verify --help` for the build and decompression commands. The reference setup requires roughly 70 GB of disk and 50 GB of RAM. Python verifies both export hashes and invokes the checker. A successful run prints the checker’s verdict for each of the five statements. [Reference verification procedure and downloads](https://math.mit.edu/~drew/grh/)

**Run the agent team.** Open this folder as a trusted local project in Codex. The kickoff prompt and file ownership are in [AGENTS.md](AGENTS.md). The primary model and all five role profiles are set to GPT-6.2-Astra.
