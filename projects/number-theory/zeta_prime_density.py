#!/usr/bin/env python3
"""Estimate the work of finding a prime among uniformly random odd candidates.

Run: python3 zeta_prime_density.py --bits 1024
The bit length is for one candidate prime. Draws are independent, with
replacement, before any trial division or other filters. Requires Python 3.8+.
"""

import argparse
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from math import ceil, floor, fsum, isqrt, pi


@lru_cache(maxsize=64)
def integer_zeta(s):
    """Approximate zeta at an integer s >= 2 for use in the Gram series."""
    if s == 2:
        return pi**2 / 6
    if s == 3:
        return 1.2020569031595943  # Apéry's constant
    if s >= 54:
        return 1.0  # zeta(s) rounds to 1 in double precision.
    # The tail beyond N is at most the integral N**(1-s)/(s-1).
    limit = ceil((1e14 / (s - 1)) ** (1 / (s - 1)))
    return fsum(n ** (-s) for n in range(1, limit + 1))


def riemann_r(x):
    """Evaluate R(x) for x >= 1 using Gram's series in the active Decimal context."""
    log_x = Decimal(x).ln()
    total = Decimal(1)
    power_over_factorial = Decimal(1)
    k = 0
    while True:
        k += 1
        power_over_factorial *= log_x / k
        addend = power_over_factorial / (k * Decimal(str(integer_zeta(k + 1))))
        updated = total + addend
        if k > log_x and updated == total:
            return updated
        total = updated


def prime_probability(bits):
    """Estimate the prime fraction among odd integers with exactly this bit length."""
    if not 3 <= bits <= 16384:
        raise ValueError("bits must be between 3 and 16384")
    with localcontext() as ctx:
        ctx.prec = 28
        lower = 1 << (bits - 1)
        odd_count = lower // 2
        # Both endpoints are composite, so endpoint inclusion makes no difference.
        return (riemann_r(2 * lower) - riemann_r(lower)) / odd_count


def exact_prime_count(bits):
    """Count primes in the same interval by sieving all odd integers below 2**bits."""
    if not 3 <= bits <= 22:
        raise ValueError("the exact sieve supports 3 through 22 bits")
    upper = 1 << bits
    flags = bytearray([1]) * (upper // 2)  # index i represents 2*i + 1
    flags[0] = 0
    for p in range(3, isqrt(upper - 1) + 1, 2):
        if flags[p // 2]:
            start = p * p // 2
            size = (len(flags) - 1 - start) // p + 1
            flags[start::p] = bytes(size)
    return flags.count(1, upper // 4)


def prime_count_bounds(bits):
    """Enclose the count of primes of one bit length with exact rational arithmetic.

    For x >= 2657, Schoenfeld's Corollary 1 gives, on RH,
      |pi(x) - li(x)| < sqrt(x)*ln(x)/(8*pi).
    Apply it at BOTH endpoints. The integral of 1/ln(t) between them
    lies between the interval width times the two endpoint values.
    Reference: https://doi.org/10.1090/S0025-5718-1976-0457374-X
    """
    if not 3 <= bits <= 16384:
        raise ValueError("bits must be between 3 and 16384")
    if bits < 13:  # The lower endpoint would be below Schoenfeld's threshold.
        count = exact_prime_count(bits)
        return count, count
    lo = 1 << (bits - 1)
    hi = 2 * lo
    # Adjacent decimal endpoints enclose ln(2). Use pi > 3 and round
    # each square root up so every numerical simplification widens the bound.
    log2_lo = Fraction(6931471805599453, 10**16)
    log2_hi = Fraction(6931471805599454, 10**16)
    error = sum((isqrt(x - 1) + 1) * k * log2_hi / 24
                for x, k in ((lo, bits - 1), (hi, bits)))
    lower = ceil(lo / (bits * log2_hi) - error)
    upper = floor(lo / ((bits - 1) * log2_lo) + error)
    return max(1, lower), min(lo // 2, upper)  # Bertrand's postulate gives at least one.


def decimal_endpoint(value, digits, upper=False):
    """Print an outward-rounded fixed-point endpoint of a rational interval."""
    scale = 10 ** digits
    n = (ceil if upper else floor)(value * scale)
    return f"{n // scale}.{n % scale:0{digits}d}"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "cm":
        from alpoge_cm import main as run_cm
        return run_cm(argv[1:])
    if argv and argv[0] == "theta":
        from alpoge_theta import main as run_theta
        return run_theta(argv[1:])
    if argv and argv[0] == "prime-sum":
        from alpoge_prime_sum import main as run_sums
        return run_sums(argv[1:])
    if argv and argv[0] == "local":
        from alpoge_local import main as run_local_lemma
        return run_local_lemma(argv[1:])
    if argv and argv[0] == "verify":
        from alpoge_verify import main as run_verifier
        return run_verifier(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0],
        epilog="Proof tools: cm --help, theta --help, local --help, prime-sum --help, verify --help")
    parser.add_argument("--bits", type=int, default=1024,
                        help="bits per candidate prime, 3 to 16384 (default 1024); "
                             "includes an exact count up to 22 bits")
    args = parser.parse_args(argv)
    try:
        probability = prime_probability(args.bits)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Uniform random odd {args.bits}-bit candidates before filtering")
    print(f"Estimated probability of a prime: {probability:.6%}")
    print(f"Estimated average draws through the first prime: {1 / probability:.2f}")
    low, high = prime_count_bounds(args.bits)
    odd_count = 1 << (args.bits - 2)
    bound_name = "RH + Schoenfeld" if args.bits >= 13 else "exact sieve"
    low_draws = decimal_endpoint(Fraction(odd_count, high), 3)
    high_draws = decimal_endpoint(Fraction(odd_count, low), 3, upper=True)
    print(f"Bounds on the mean number of draws ({bound_name}): [{low_draws}, {high_draws}]")
    if args.bits <= 22:
        primes = exact_prime_count(args.bits)
        odds = 1 << (args.bits - 2)
        print(f"Exact sieve: {primes:,} primes among {odds:,} odd candidates "
              f"({primes / odds:.6%})")


if __name__ == "__main__":
    main()
