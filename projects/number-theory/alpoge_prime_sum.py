#!/usr/bin/env python3
"""Evaluate the untwisted prime sums in Alpöge's Lean development.

Formalism.Sz(x) = sum over p^k <= x of log(p) * (x/p^k - 1).
Formalism.Gz(x) = Sz(x) - x*log(x) + (1 + Euler's constant)*x.
Reference: https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/StatementOC.lean#L11-L13

Run with a scale, e.g. 1000, or --window 100 to sample [100, 1000].
All displayed values are floating-point approximations.
"""

import argparse
import math
from typing import NamedTuple


EULER_GAMMA = 0.577215664901532860606512090082402431
MAX_SCALE = 10_000_000  # The direct method sieves through the largest scale.


class PrimeSums(NamedTuple):
    x: float
    sz: float
    gz: float


def _odd_prime_flags(limit):
    # Index i denotes 2*i + 1.
    flags = bytearray([1]) * ((limit + 1) // 2)
    flags[0] = 0
    for p in range(3, math.isqrt(limit) + 1, 2):
        if flags[p // 2]:
            start = p * p // 2
            flags[start::p] = bytes((len(flags) - 1 - start) // p + 1)
    return flags


def _primes(lo, hi, flags):
    if lo <= 2 <= hi:
        yield 2
    for p in range(max(3, lo | 1), hi + 1, 2):
        if flags[p // 2]:
            yield p


def _evaluate_scales(scales):
    # Split S(x) into x * sum(Lambda(n)/n) - sum(Lambda(n)). Each sampled
    # scale adds only the prime powers since the preceding scale.
    limit = math.floor(scales[-1])
    flags = _odd_prime_flags(limit)
    higher_powers = []
    for p in _primes(2, math.isqrt(limit), flags):
        power = p * p
        while power <= limit:
            higher_powers.append((power, math.log(p)))
            power *= p

    def terms(lo, hi):
        for p in _primes(lo, hi, flags):
            yield p, math.log(p)
        for n, log_p in higher_powers:
            if lo <= n <= hi:
                yield n, log_p

    slope_parts, intercept_parts = [], []
    rows = []
    lo = 2
    for x in scales:
        hi = math.floor(x)
        slope_parts.append(math.fsum(v / n for n, v in terms(lo, hi)))
        intercept_parts.append(math.fsum(v for n, v in terms(lo, hi)))
        sz = x * math.fsum(slope_parts) - math.fsum(intercept_parts)
        gz = math.fsum((sz, -x * math.log(x), (1 + EULER_GAMMA) * x))
        rows.append(PrimeSums(x, sz, gz))
        lo = hi + 1
    return rows


def _validate_scale(x):
    if not 1 <= x <= MAX_SCALE:
        raise ValueError(f"direct sieve requires a finite scale from 1 to {MAX_SCALE:,}")


def prime_sums(x):
    """Return (x, Sz(x), Gz(x)) including every prime power up to floor(x)."""
    _validate_scale(x)
    return _evaluate_scales([x])[0]


def window_samples(start, samples=9):
    """Sample [start, start**(3/2)] at geometrically spaced scales, endpoints included."""
    _validate_scale(start)
    stop = start ** 1.5
    _validate_scale(stop)
    if not 2 <= samples <= 1000:
        raise ValueError("choose 2 through 1000 sample points")
    if start == stop:
        return [prime_sums(start)]
    scales = [start * (stop / start) ** (i / (samples - 1)) for i in range(samples - 1)]
    return _evaluate_scales(scales + [stop])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("x", type=float, nargs="?", help="scale of the prime-power sum")
    mode.add_argument("--window", type=float, metavar="Y", help="sample the window [Y, Y^(3/2)]")
    parser.add_argument("--samples", type=int, help="number of window samples (default 9)")
    args = parser.parse_args(argv)
    if args.x is not None and args.samples is not None:
        parser.error("--samples requires --window")
    try:
        if args.window is None:
            rows = [prime_sums(args.x)]
        else:
            rows = window_samples(args.window, 9 if args.samples is None else args.samples)
    except ValueError as exc:
        parser.error(str(exc))
    print("             x             Sz(x)             Gz(x)")
    for x, sz, gz in rows:
        print(f"{x:14.7g} {sz:17.8f} {gz:17.8f}")


if __name__ == "__main__":
    main()
