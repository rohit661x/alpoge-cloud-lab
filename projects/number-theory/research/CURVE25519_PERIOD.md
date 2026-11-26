# A primitive cubic root and the exact Perrin period modulo 2²⁵⁵ − 19

Let p = 2²⁵⁵ − 19. The polynomial X³ − X − 1 has three distinct roots in Fₚ. In increasing order of their least nonnegative residues, they generate subgroups of indices 1, 3, and 2, respectively. Thus the first root is a primitive element of Fₚ. This is arithmetic of the base field used by Curve25519. [RFC 7748, §4.1](https://www.rfc-editor.org/rfc/rfc7748.html#section-4.1)

| Root modulo p | Exact multiplicative order |
|---|---|
| 14535863002999908821470556791477736972039661322948065771707477577742314888008 | p − 1 |
| 45980055862320150516043228587377395813021437899593394500348496167731510246271 | (p − 1)/3 |
| 55276170371996136086057199629832775068208885443099103767401610262439304505619 | (p − 1)/2 |

The Perrin sequence starts with (3,0,2) and satisfies P(n+3) = P(n+1) + P(n). Its exact period modulo p is **2²⁵⁵ − 20**. For any n ≥ 0, P(n) is the sum of the n-th powers of the three roots. This follows by checking the first three power sums using the cubic coefficients, then applying the common recurrence. A period d must satisfy Σ rⁿ(rᵈ−1) = 0 for n = 0, 1, 2. The Vandermonde matrix is invertible since the roots are distinct. Therefore each rᵈ = 1, so the period is the least common multiple of the three displayed orders. Fermat's theorem bounds the period by p−1 for any separable split cubic with nonzero roots. This example attains that bound.

## Integer certificates

The complete factorization of p−1 is 2² × 3 × 65147 × Q, where

    Q = 74058212732561358302231226437062788676166966415465897661863160754340907.

For each root and displayed order d, the verifier checks the cubic equation, rᵈ = 1, and r raised to d/q differs from 1 for every prime divisor q of d. Pocklington certificates establish primality of p and Q recursively, with deterministic trial division for leaves. Each Pocklington step finds prime powers in n−1 with product F > √n and verifies the Fermat and gcd conditions for every certified prime dividing F. The Curve25519 chain uses prime divisors from Bernstein's Appendix B. [Daniel J. Bernstein, *Curve25519: new Diffie-Hellman speed records*](https://cr.yp.to/ecdh/curve25519-20051115.pdf)

A second verification raises the companion matrix to d = p−1 and d/q by integer matrix squaring on three consecutive sequence values. The initial triple returns at d and at none of the prime-divisor quotients. Invertibility of the update (determinant 1) guarantees pure periodicity. Equality of the triple implies equality of the full future by the recurrence. This calculation also reproduces the Goldilocks period p′²+p′+1 for p′ = 2⁶⁴−2³²+1, independently of arithmetic in the cubic quotient. The eigenvalue and matrix computations share only primality and the integer factorization.

From the directory containing the verifier, run:

```sh
python3 matrix_periods.py
python3 -m unittest -v test_matrix_periods
```

The JSON output records exact integers, including every proper-divisor state. Use an arbitrary-precision JSON reader. The independent PARI/GP census script also rediscovers all three roots and their multiplicative orders from the defining polynomial. These computations establish the stated finite-field identities. Publication priority has not been established.
