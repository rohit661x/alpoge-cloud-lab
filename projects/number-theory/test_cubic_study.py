import unittest
from itertools import product
from math import isqrt

from cubic_study import apply_frobenius, multiply, power, study


class CubicStudyTests(unittest.TestCase):
    def test_small_prime_oracle(self):
        for p in range(3, 500, 2):
            if p == 23 or any(p % d == 0 for d in range(2, isqrt(p)+1)):
                continue
            with self.subTest(p=p):
                report = study(p)
                count = sum((x**3-x-1) % p == 0 for x in range(p))
                self.assertEqual(report['gcd_degree'], count)
                self.assertEqual(report['factor_degrees'].count(1), count)
                if count == 0:
                    self.assertEqual(power((0, 1, 0), report['x_order_divides'], p),
                                     (1, 0, 0))

    def test_frobenius_all_elements(self):
        for p in (3, 13):
            matrix = study(p)['frobenius_matrix']
            for element in product(range(p), repeat=3):
                expected = (1, 0, 0)
                for _ in range(p):
                    expected = multiply(expected, element, p)
                self.assertEqual(apply_frobenius(matrix, element, p), expected)

    def test_domain(self):
        for invalid in (True, 1, 2, 4, 23, -3, 3.0):
            with self.assertRaises(ValueError):
                study(invalid)
