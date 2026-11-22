import unittest
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import isqrt

from rh_trace_window import certify, log_bounds


class TraceWindowTests(unittest.TestCase):
    def test_default_bounds(self):
        self.assertEqual(certify(2**256 - 2**142, 2**256), (
            2716342439235134011632130820349336797735,
            12993215425046400288206230783130401424406,
        ))

    def test_log_enclosures(self):
        with localcontext() as ctx:
            ctx.prec = 100
            for x in (1, 2, 23, 4761, 2**64 - 1, 2**256 - 2**142, 2**256):
                lo, hi = log_bounds(x)
                actual = F(Decimal(x).ln())
                self.assertLessEqual(lo, actual)
                self.assertLessEqual(actual, hi)

    def test_congruence_and_small_counts(self):
        count = 0
        for p in range(24, 2500):
            if any(p % d == 0 for d in range(2, isqrt(p) + 1)):
                continue
            roots = sum((pow(t, 9, p) - 18 * pow(t, 6, p)
                         + 54 * pow(t, 3, p) + 27) % p == 0 for t in range(p))
            self.assertEqual(roots == 1, p % 3 == 2 and pow(-23, (p - 1)//2, p) == 1)
            count += roots == 1
        lo, hi = certify(23, 2499)
        self.assertLessEqual(lo, count)
        self.assertLessEqual(count, hi)

    def test_edges(self):
        for endpoints in ((22, 23), (23, 23), (41, 25)):
            with self.assertRaises(ValueError):
                certify(*endpoints)


if __name__ == "__main__":
    unittest.main()
