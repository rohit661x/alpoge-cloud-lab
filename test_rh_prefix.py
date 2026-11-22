import unittest
from math import isqrt

from rh_prefix import prefix_bound


class PrefixTests(unittest.TestCase):
    def test_256_bit_integer_certificate(self):
        count = prefix_bound()
        self.assertEqual(count, 119364572746971480821742986104065588231880)
        # W/(896/5) - 2^128*(896/5)/12, cleared of denominators.
        numerator = 300 * 2**144 - 896**2 * 2**128
        denominator = 60 * 896
        self.assertLessEqual((count-1)*denominator, numerator)
        self.assertLess(numerator, count*denominator)
        self.assertGreater(94*count, 2**143)
        self.assertLess(2**128 * 93**8296, 94**8296)

    def test_smaller_intervals_by_sieve(self):
        bits = 17
        limit = 2**bits
        prime = bytearray([1]) * limit
        for p in range(2, isqrt(limit-1)+1):
            if prime[p]:
                prime[p*p::p] = bytes((limit-1-p*p)//p+1)
        for suffix in (10, 13, 14, 15, 16):
            width = 2**suffix
            for start in range(limit//2, limit, width):
                self.assertLessEqual(prefix_bound(bits, suffix), sum(prime[start:start+width]))

    def test_domain(self):
        for args in ((12, 5), (256, True), (13, 13), (13, 0)):
            with self.assertRaises(ValueError):
                prefix_bound(*args)
