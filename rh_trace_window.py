"""Certify prime counts for exactly one root of the Perrin trace polynomial."""

import argparse
from fractions import Fraction as F
from math import ceil, floor, isqrt


def atanh_log_bounds(z, terms=16):
    """Enclose log((1+z)/(1-z)) for 0 <= z <= 1/3."""
    if not 0 <= z <= F(1, 3) or terms < 1:
        raise ValueError("series requires 0 <= z <= 1/3 and positive terms")
    power = z
    total = F(0)
    for j in range(terms):
        total += 2 * power / (2 * j + 1)
        power *= z * z
    return total, total + 2 * power / ((2 * terms + 1) * (1 - z * z))


def log_bounds(n):
    """Return exact rational outward enclosures for log(n), n >= 1."""
    if n < 1:
        raise ValueError("logarithm requires a positive integer")
    k = n.bit_length() - 1
    base = 1 << k
    lo2, hi2 = atanh_log_bounds(F(1, 3))
    lo, hi = atanh_log_bounds(F(n - base, n + base))
    scale = 10**12
    return F(floor((k * lo2 + lo) * scale), scale), F(ceil((k * hi2 + hi) * scale), scale)


def normalized_error(x):
    """Upper bound on |4*pi_C(x) - integral_2^x dt/log(t)|."""
    if x < 2:
        raise ValueError("the prime-count bound requires x >= 2")
    low, high = log_bounds(x)
    _, log_disc = log_bounds(4761)
    pi_low = F(314, 100)
    root = isqrt(x)
    if root * root < x:
        root += 1
    return root * ((1 / (2 * pi_low) + 3 / low) * log_disc
                   + 4 * (high / (8 * pi_low) + 1 / (4 * pi_low) + 6 / low))


def certify(a, b):
    """Bounds on the count in (a,b], for integers b > a >= 23."""
    if not 23 <= a < b:
        raise ValueError("endpoints must satisfy 23 <= a < b")
    log_a_low, _ = log_bounds(a)
    _, log_b_high = log_bounds(b)
    errors = normalized_error(a) + normalized_error(b)
    width = b - a
    lower = max(0, ceil((width / log_b_high - errors) / 4))
    upper = min(width, floor((width / log_a_low + errors) / 4))
    return lower, upper


if __name__ == "__main__":
    b = 2**256
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lower", type=int, default=b - 2**142)
    parser.add_argument("--upper", type=int, default=b)
    args = parser.parse_args()
    low, high = certify(args.lower, args.upper)
    print(f"interval ({args.lower}, {args.upper}]")
    print(f"width {args.upper - args.lower}")
    print(f"certified count [{low}, {high}]")
