#!/usr/bin/env python3
"""Exact quadratic-ring specialization of Alpöge's local divisibility lemma.

Run: python3 alpoge_local.py --prime 3 --e 1
For other data pass a JSON file with --input. Keys: p, e, u, u_prime, M,
N_prime, c. A scalar may be an integer or [a,b] denoting a + b*sqrt(p).
Rows are indexed from zero. The demonstration generates a two-row instance.

Lean: Formalism.MainNotions.ColumnSystems.Pf.key_minor_dvd, used by kW_ord.
https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/SharpRestriction/GrowthBounds/CoarseMultiplicity/KeyMinorDvd.lean
"""

import argparse
import json
from math import isqrt
from pathlib import Path


def scalar(value):
    if type(value) is int:
        return value, 0
    if (isinstance(value, (list, tuple)) and len(value) == 2
            and all(type(c) is int for c in value)):
        return tuple(value)
    raise ValueError("ring entries must be integers or pairs of integers [a,b]")


def multiply(x, y, p):
    a, b = x
    c, d = y
    return a * c + p * b * d, a * d + b * c


def power(value, n, p):
    result = (1, 0)
    while n:
        if n % 2:
            result = multiply(result, value, p)
        n //= 2
        if n:
            value = multiply(value, value, p)
    return result


def row_column(row, matrix, col, p):
    a = b = 0
    for val, matrix_row in zip(row, matrix):
        c, d = multiply(val, matrix_row[col], p)
        a += c
        b += d
    return a, b


def minor_witness(p, e, u, u_prime, M, N_prime, c):
    """Check the hypotheses and return the exact minor and its quotient by sqrt(p)."""
    if type(p) is not int or p < 2 or any(p % d == 0 for d in range(2, isqrt(p) + 1)):
        raise ValueError("p must be prime")
    if type(e) is not int or e < 0:
        raise ValueError("e must be a nonnegative integer")
    if not all(isinstance(arr, (list, tuple)) for arr in (u, u_prime, M, N_prime)):
        raise ValueError("expected two rows and two square matrices")
    size = len(u)
    if not size or len(u_prime) != size or len(M) != size or len(N_prime) != size:
        raise ValueError("both row lengths and both matrix dimensions must agree")
    if type(c) is not int or not 0 <= c < size:
        raise ValueError("column c is out of range")
    u, u_prime = list(map(scalar, u)), list(map(scalar, u_prime))
    # sqrt(p) divides a+b*sqrt(p) exactly when p divides a.
    if any(x[0] % p for row in (u, u_prime) for x in row[1:]):
        raise ValueError("sqrt(p) must divide both rows at all indices greater than zero")

    def square(matrix):
        if any(not isinstance(row, (list, tuple)) or len(row) != size for row in matrix):
            raise ValueError("expected a square matrix for each row transform")
        return [list(map(scalar, row)) for row in matrix]

    M, N_prime = square(M), square(N_prime)
    for i in range(size):
        for j in range(size):
            a, b = M[i][j]
            r, s = N_prime[i][j]
            # Modulo p, w^2=0. For e>0 Frobenius sends a+b*w to a.
            if (a - r) % p or ((b if e == 0 else 0) - s) % p:
                raise ValueError(f"entrywise congruence fails at [{i},{j}]")
    q = p**e
    v0 = power(row_column(u, M, 0, p), q, p)
    vc = power(row_column(u, M, c, p), q, p)
    left = multiply(row_column(u_prime, N_prime, c, p), v0, p)
    right = multiply(row_column(u_prime, N_prime, 0, p), vc, p)
    minor = (left[0] - right[0], left[1] - right[1])
    quotient = (minor[1], minor[0] // p)
    if multiply((0, 1), quotient, p) != minor:
        raise ArithmeticError("the computed quotient does not reconstruct the minor")
    return minor, quotient


def demo(p, e):
    # Upper triangular constant terms have determinant one mod p. Several entries
    # have nonzero irrational parts, and N' includes explicit multiples of p.
    M = [[(1, 1), (1, -1)], [(0, 1), (1, 2)]]
    N = [[(a + p * (i + 1), (b if e == 0 else 0) + p * j)
          for j, (a, b) in enumerate(row)] for i, row in enumerate(M)]
    return dict(p=p, e=e, u=[(1, 1), (0, 1)], u_prime=[(1, 0), (0, 1)],
                M=M, N_prime=N, c=1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, help="JSON instance of key_minor_dvd")
    parser.add_argument("--prime", type=int, help="demo prime (default 3)")
    parser.add_argument("--e", type=int, help="demo exponent index (default 1)")
    args = parser.parse_args(argv)
    try:
        if args.input is not None:
            if args.prime is not None or args.e is not None:
                parser.error("--prime and --e apply only to the built-in demo")
            data = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or set(data) != {"p", "e", "u", "u_prime", "M", "N_prime", "c"}:
                raise ValueError("expected an object with p, e, u, u_prime, M, N_prime, c")
        else:
            data = demo(3 if args.prime is None else args.prime, 1 if args.e is None else args.e)
        p, e = data["p"], data["e"]
        # CLI emits full decimal integers. Keep interactive examples tractable.
        if (type(p) is not int or type(e) is not int or not 2 <= p <= 1_000_000
                or not 0 <= e <= 12 or p**e > 4096):
            raise ValueError("the CLI supports 2 <= p <= 1000000 and 0 <= e with p**e <= 4096")
        minor, quotient = minor_witness(**data)
        print(f"In Z[w] with w^2 = {p}, coefficient pairs [a,b] denote a + b*w.")
        for name, pair in (("minor", minor), ("quotient by w", quotient)):
            try:
                a, b = map(str, pair)
            except ValueError:  # Python's decimal digit limit; hex stays exact.
                a, b = map(hex, pair)
            print(f"{name} = [{a}, {b}]")
        print("Verified w * quotient = minor exactly.")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
