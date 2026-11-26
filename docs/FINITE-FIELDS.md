# A test vector for Goldilocks cubic arithmetic

How do you test a field implementation at a point more than 10³⁸ steps into a recurrence? This project gives an exact answer for the cubic field defined by α³ = α + 1 over the Goldilocks prime p = 2⁶⁴ − 2³² + 1. Plonky3 implements the same field, so a developer can compare its arithmetic against a short, standalone Python verifier. [Plonky3’s field definition](https://github.com/Plonky3/Plonky3/blob/0d803737b681774186cd283b1fd2d8e493655c82/goldilocks/src/extension.rs#L65-L99)

Write a field element as a coefficient triple `(a, b, c)` for a + bα + cα². Multiplication by α sends it to `(c, a+c, b)`, with the sum reduced modulo p. Starting at `(1, 0, 0)`, the rule visits every element of the norm-one subgroup exactly once in **N = p² + p + 1** steps before repeating. For a concrete test, raise `(0, 1, 0)` to the power N/3 by repeated squaring. The expected triple is `(4294967295, 0, 0)`. [Derivation and test vectors](../research/RESULTS.md)

## Reproduce the certificate

Run this from the repository root with Python 3.8 or later. It uses only the standard library.

```sh
python3 goldilocks_order.py
```

```text
Verified multiplicative order 340282366762482138508632908526633615363 at p=18446744069414584321
```

The verifier checks primality, irreducibility of the cubic, and the complete factorization of N. It computes αᴺ = 1 and checks that α raised to N/q differs from 1 for each prime factor q of N. Any smaller order dividing N would divide at least one of those N/q values. This proves the exact period with a handful of exponentiations. The sequence is publicly computable at every index, so its period supplies no evidence of cryptographic unpredictability. [Python verifier](../goldilocks_order.py)
