"""A trace criterion for the norm-one order of a root of X^3-X-1.

Polynomial coefficients are in ascending order. Callers establish primality.
"""
import argparse
from math import isqrt

F = [-1, -1, 0, 1]
H = [27, 0, 0, 54, 0, 0, -18, 0, 0, 1]


def trim(a):
    while a and a[-1] == 0:
        a.pop()
    return a


def remainder(a, b, p):
    a = trim([c % p for c in a])
    scale = pow(b[-1], -1, p)
    while len(a) >= len(b):
        offset = len(a) - len(b)
        factor = a[-1] * scale % p
        for j, c in enumerate(b):
            a[offset + j] = (a[offset + j] - factor * c) % p
        trim(a)
    return a


def product(a, b, m, p):
    if not a or not b:
        return []
    c = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i+j] += x*y
    return remainder(c, m, p)


def root_count(m, p):
    """Return deg gcd(m, X^p-X), counting distinct base-field roots."""
    a, b = [1], [0, 1]
    n = p
    while n:
        if n & 1:
            a = product(a, b, m, p)
        b = product(b, b, m, p)
        n >>= 1
    a += [0] * max(0, 2-len(a))
    a[1] = (a[1]-1) % p
    b, a = trim(a), m
    while b:
        a, b = b, remainder(a, b, p)
    return len(a)-1


def criterion(p):
    """Return the 3-adic valuation of ord(X mod F) for an eligible prime."""
    if p < 7 or p % 3 != 1:
        raise ValueError("requires a prime congruent to 1 modulo 3")
    if root_count(F, p):
        raise ValueError("requires irreducible X^3-X-1")
    count = root_count(H, p)
    if count not in (0, 3):
        raise ArithmeticError(f"unexpected number of trace roots: {count}")
    return int(count == 0)


def brute_check(limit):
    """Compare simple enumeration, generic gcd, and cubic extension arithmetic."""
    counts = [0, 0]
    for p in range(7, limit+1, 6):
        if any(p % k == 0 for k in range(2, isqrt(p)+1)):
            continue
        if any((x**3-x-1) % p == 0 for x in range(p)):
            continue
        traces = sum((x**9-18*x**6+54*x**3+27) % p == 0 for x in range(p))
        exponent = (p*p+p+1)//3
        a, b = (1, 0, 0), (0, 1, 0)

        def multiply(left, right):
            i, j, k = left
            u, v, w = right
            return ((i*u+j*w+k*v) % p, (i*v+j*u+j*w+k*v+k*w) % p,
                    (i*w+j*v+k*u+k*w) % p)

        while exponent:
            if exponent & 1:
                a = multiply(a, b)
            b = multiply(b, b)
            exponent >>= 1
        valuation = criterion(p)
        if traces != 3*(1-valuation) or valuation != int(a != (1, 0, 0)):
            raise AssertionError((p, traces, valuation, a))
        counts[valuation] += 1
    return tuple(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prime", type=int, help="known prime p")
    group.add_argument("--check-through", type=int, help="inclusive brute-force bound")
    args = parser.parse_args()
    if args.prime is not None:
        print(criterion(args.prime))
    else:
        print("counts for valuations 0 and 1:", brute_check(args.check_through))
