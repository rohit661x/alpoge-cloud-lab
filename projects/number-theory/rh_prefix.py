"""RH-conditional lower bound for every binary prefix of a given bit length."""
from fractions import Fraction
from math import isqrt


def prefix_bound(bits=256, suffix_bits=144):
    """Lower-bound primes for *every* leading prefix with this suffix width."""
    if type(bits) is not int or type(suffix_bits) is not int or not (13 <= bits and 1 <= suffix_bits < bits):
        raise ValueError("requires bits >= 13 and 1 <= suffix_bits < bits")
    width = 1 << suffix_bits
    upper = 1 << bits
    log_upper = Fraction(7 * bits, 10)
    sqrt_upper = isqrt(upper - 1) + 1
    raw = width / log_upper - sqrt_upper * log_upper / 12
    return max(0, raw.numerator // raw.denominator + 1)


if __name__ == "__main__":
    count = prefix_bound()
    print("RH-conditional lower count per 112-bit leading prefix:", count)
    print("Upper bound on mean independent odd draws:", Fraction(2**143, count))
