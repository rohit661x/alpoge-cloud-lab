# A one-addition walk through the Goldilocks norm-one subgroup

Let p = 2⁶⁴ − 2³² + 1 and let α be the residue of X in the field Fₚ[X]/(X³−X−1). The element α generates the kernel of the norm to Fₚ. Its exact order is

    N = p² + p + 1 = 340282366762482138508632908526633615363
      = 3 × 937 × 724723 × 167034643597991036904547663171.

Multiplying a field element a+bα+cα² by α sends its coefficients to (c, a+c, b), reduced modulo p. Starting from (1,0,0), this one-addition update visits every norm-one element once before repeating. Binary exponentiation gives the state at any index. This provides deterministic test vectors for arithmetic in the same cubic quotient used by Plonky3. Plonky3 documents 2+α as a generator of the full multiplicative group. [Pinned Plonky3 implementation](https://github.com/Plonky3/Plonky3/blob/0d803737b681774186cd283b1fd2d8e493655c82/goldilocks/src/extension.rs#L96-L106)

## How the order was proved

The standalone Python verifier proves primality of p and each factor of N using integer witnesses and trial division at the leaves. It checks that Xᵖ−X acts invertibly in the cubic quotient, which proves irreducibility. It verifies αᴺ=1 and α raised to N/q differs from 1 for every prime q dividing N. Those conditions prove exact order. In particular α raised to N/3 is the base-field element 4294967295. The Lean file separately evaluates the factor product, the full power, and each prime-divisor witness by kernel reduction. The primality proof and irreducibility test run in Python. The arguments use finite-field arithmetic and hold independently of RH.

The same N is the exact period of the scalar Perrin sequence modulo p. For the coefficient vector of αⁿ, three consecutive field traces are obtained by multiplying by the matrix with rows (3,0,2), (0,2,3), and (2,3,2). Their determinant is −23, nonzero modulo p. Thus those three traces determine the state, while the traces themselves start 3,0,2 and satisfy P(n+3)=P(n+1)+P(n). A period of the scalar output must be a period of the state. This period and the public recurrence establish no unpredictability or protocol security claim. [Adams and Shanks on cubic recurrences](https://doi.org/10.1090/S0025-5718-1982-0658231-9)

## A trace criterion across public fields

For primes p ≡ 1 modulo 3 where the cubic is irreducible, α is a cube in the norm-one subgroup exactly when U⁹−18U⁶+54U³+27 has a root in Fₚ. In that case the polynomial has exactly three roots. Otherwise it has zero and 3 divides the order of α. The [derivation](TRACE_CRITERION.md) uses the traces of a norm-one cube root and its inverse. The classifier computes the degree of a polynomial gcd. A second algorithm checks it by exponentiation in the cubic extension.

| Base field | Degrees of factors of X³−X−1 | Norm-one cube test |
|---|---|---|
| Goldilocks | 3 | No |
| Pallas base / Vesta scalar | 3 | Yes |
| BLS12-381 base | 3 | Yes |
| BLS12-381 scalar | 3 | No |
| Curve448 | 3 | Cube map bijective since p ≡ 2 mod 3 |
| BabyBear, Vesta base / Pallas scalar, BN254 base, BN254 scalar | 1 + 2 | Reducible cubic |
| Curve25519 | 1 + 1 + 1 | Reducible cubic |
| Lab certified 1,024-bit prime (separate fixture) | 3 | No |

The ten public field moduli come from the [source registry](public_fields.json). At each modulus and at the lab prime, the lab independently computed the discriminant −23 theta coefficient and the cubic factorization; the root count always equalled the coefficient plus one, as in Serre’s formula. Across all 204 eligible primes through 10,000, direct evaluation, polynomial gcd, and cubic exponentiation agreed: 67 cube cases and 137 noncube cases. This finite census makes no density prediction. [Serre, §5.3](https://www.math.mcgill.ca/goren/SeminarOnCohomology/Serre.pdf)

We found prior work on the cubic, the field implementation, and the Perrin recurrence. The exact Goldilocks order certificate and trace criterion are findings of this investigation. Publication priority remains open. [Prior-art search](PRIOR_ART.md)

## Reproduction

From the extracted project root, using Python 3.8 or later:

```sh
python3 goldilocks_order.py
python3 cubic_crypto_lab.py walk --start 0 --count 8
python3 cubic_crypto_lab.py survey --through 10000
python3 -m unittest discover -v
```

The survey emits JSON with exact integer literals. Read it using an arbitrary-precision integer parser such as Python’s json module. GitHub Actions repeats these commands and runs the fixed arithmetic witnesses in Lean 4.33.1. With that version on PATH, run `lean lean/GoldilocksOrder.lean`. The cloud workflow also replays the previous Gaussian lattice checks.
