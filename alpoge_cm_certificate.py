"""Deterministic public split-prime fixtures at discriminant -23.

Each certificate proves primality by a single-prime-factor Pocklington
argument and exhibits the prime as the value of a nonprincipal reduced form.
The verifier uses only Python's standard library. The generator additionally
uses the project's exact change-of-basis routine. All JSON numbers are exact
integers and require a reader with arbitrary-precision integer support.
"""

import argparse
import json
from math import gcd, isqrt
from pathlib import Path


SCHEMA = "alpoge-cm-prime-v1"
MIN_BITS = 32
MAX_BITS = 2048
NONPRINCIPAL = ((2, -1, 3), (2, 1, 3))


def _check_bits(bits):
    if type(bits) is not int or not MIN_BITS <= bits <= MAX_BITS:
        raise ValueError("bits must be an integer from 32 through 2048")


def verify_certificate(record):
    """Raise ValueError on invalid input, returning None for a verified record.

    For each prime divisor r of n, the order of the witness modulo r divides
    n-1 and does not divide (n-1)/3. Its 3-part therefore contains 3**m,
    so r >= 3**m+1 > sqrt(n), proving n prime.
    """
    fields = {"schema", "bits", "n", "k", "m", "witness", "discriminant", "form", "vector"}
    if not isinstance(record, dict) or set(record) != fields or record["schema"] != SCHEMA:
        raise ValueError("unrecognized certificate schema or fields")
    for key in ("bits", "n", "k", "m", "witness", "discriminant"):
        if type(record[key]) is not int:
            raise ValueError("{} must be an integer".format(key))
    bits, n, k, m = (record[key] for key in ("bits", "n", "k", "m"))
    _check_bits(bits)
    if n <= 0 or n.bit_length() != bits or not 0 < k < n or k % 2 != 1 or not 0 < m < bits:
        raise ValueError("invalid prime size, cofactor, or exponent")
    factor = 3 ** m
    if n != 2 * k * factor + 1 or factor * factor <= n:
        raise ValueError("invalid Pocklington factorization or size bound")
    witness = record["witness"]
    if not 1 < witness < n:
        raise ValueError("witness must be strictly between 1 and n")
    if pow(witness, n - 1, n) != 1 or gcd(pow(witness, (n - 1) // 3, n) - 1, n) != 1:
        raise ValueError("Pocklington witness failed")

    # Quadratic reciprocity gives (-23/n) = (n/23). The reduced forms
    # of discriminant -23 have a <= sqrt(23/3), leaving just the principal
    # (1,1,6) and the two distinct proper classes (2,+/-1,3).
    if record["discriminant"] != -23 or pow(n, 11, 23) != 1:
        raise ValueError("prime must split at discriminant -23")
    for key, length in (("form", 3), ("vector", 2)):
        value = record[key]
        if not isinstance(value, list) or len(value) != length or any(type(t) is not int for t in value):
            raise ValueError("{} has an invalid shape or component".format(key))
    a, b, c = record["form"]
    if (a, b, c) not in NONPRINCIPAL:
        raise ValueError("form must be a reduced nonprincipal form at -23")
    x, y = record["vector"]
    if a * x * x + b * x * y + c * y * y != n:
        raise ValueError("quadratic form at the supplied vector differs from n")


def _find_witness(n):
    """Return a proof witness or skip the candidate after a bounded search."""
    for base in range(2, 65):
        residue = pow(base, (n - 1) // 3, n)
        if pow(residue, 3, n) != 1:
            return None
        if gcd(residue - 1, n) == 1:
            return base
    return None


def example_certificate(bits):
    """Find a public fixture of exactly the requested size in ascending k order."""
    _check_bits(bits)
    from alpoge_cm_forms import reduce_representation

    upper = 1 << bits
    factor, m = 1, 0
    while factor * factor < upper:
        factor *= 3
        m += 1
    stride = 2 * factor
    lower = upper // 2
    k = (lower - 1 + stride - 1) // stride
    k |= 1
    small_primes = [p for p in range(5, 1000, 2)
                    if all(p % d for d in range(3, isqrt(p) + 1, 2))]
    for k in range(k, (upper - 2) // stride + 1, 2):
        n = stride * k + 1
        if pow(n, 11, 23) != 1 or any(n % p == 0 for p in small_primes):
            continue
        witness = _find_witness(n)
        if witness is None:
            continue
        # n = 3 (mod 4), so the exponent produces a square root of -23.
        # Use the odd lift to get b*b = -23 (mod 4*n).
        root = pow(-23, (n + 1) // 4, n)
        b = root if root % 2 else n - root
        c, remainder = divmod(b * b + 23, 4 * n)
        if remainder:
            raise ArithmeticError("square root did not give an integral form")
        form, vector = reduce_representation((n, b, c))
        if form not in NONPRINCIPAL:
            continue
        record = {"schema": SCHEMA, "bits": bits, "n": n, "k": k, "m": m,
                  "witness": witness, "discriminant": -23,
                  "form": list(form), "vector": list(vector)}
        verify_certificate(record)
        return record
    raise ValueError("no admissible fixture found for this bit length")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="print an exact public fixture as JSON")
    generate.add_argument("--bits", type=int, default=1024)
    verify = commands.add_parser("verify", help="verify an existing JSON certificate")
    verify.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "generate":
            print(json.dumps(example_certificate(args.bits), indent=2))
        else:
            record = json.loads(args.file.read_text(encoding="utf-8"))
            verify_certificate(record)
            print("Verified {}-bit prime and nonprincipal representation at D = -23.".format(record["bits"]))
    except (OSError, ValueError) as error:
        parser.exit(1, "Certificate error: {}\n".format(error))


if __name__ == "__main__":
    main()
