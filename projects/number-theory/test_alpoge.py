"""Reproducible checks for the numerical ports. Run python3 -m unittest -v."""

import itertools
import json
import math
import unittest
from fractions import Fraction
from pathlib import Path

from alpoge_local import demo, minor_witness
from alpoge_prime_sum import prime_sums
from alpoge_theta import chain_op, gaussian_contribution, module_chain
from zeta_prime_density import exact_prime_count, prime_count_bounds


class AlpogeTests(unittest.TestCase):
    def test_schoenfeld_count_bounds_vs_sieve(self):
        for bits in range(3, 23):
            with self.subTest(bits=bits):
                lower, upper = prime_count_bounds(bits)
                exact = exact_prime_count(bits)
                self.assertLessEqual(lower, exact)
                self.assertLessEqual(exact, upper)
                if bits < 13:
                    self.assertEqual(lower, upper)

    def test_prime_power_contribution(self):
        # At x=5 the n=4 term uses log(2). At x=4 it has zero weight.
        for x in [4, 4.5, 5]:
            expected = (math.log(2) * (x / 2 - 1) + math.log(3) * (x / 3 - 1)
                        + math.log(2) * (x / 4 - 1))
            self.assertAlmostEqual(prime_sums(x).sz, expected)

    def test_gaussian_coefficients(self):
        vectors = itertools.product(range(-2, 3), repeat=4)
        count = sum(sum(t*t for t in v) == 5 for v in vectors)
        actual = gaussian_contribution(2, 5)
        self.assertEqual(actual["coefficient"], count)
        self.assertEqual(Fraction(actual["weighted_coefficient"]), Fraction(count, 32))

    def test_vector_chain(self):
        example = json.loads(Path(__file__).with_name("vector_chain.json").read_text())
        values, scale, applies = module_chain(example["input"], example["steps"])
        # After step 1 the two scalar classes have values 3 and 1.
        # Their weighted contributions to the last class are
        # (3, 3/2, 0) and (0, -1/4, 1).
        self.assertEqual(values, ((3, Fraction(5, 4), 1),))
        self.assertTrue(applies)
        self.assertEqual(scale, 24)

    def test_divisibility_witness(self):
        example = demo(3, 1)
        minor, quotient = minor_witness(**example)
        self.assertEqual(minor, (15957, 9280))
        self.assertEqual((3 * quotient[1], quotient[0]), minor)
        example["N_prime"][0][0] = 0
        with self.assertRaisesRegex(ValueError, "congruence fails"):
            minor_witness(**example)

    def test_integrality_is_about_hypotheses(self):
        result = chain_op([1, 1], [{"weights": [1, 1], "kernel": [["1/2"], ["1/2"]]}])
        self.assertEqual(result.values, (1,))
        self.assertFalse(result.chain_int_applies)
        _, _, applies = module_chain([[1], [1]], [{
            "weights": [1, 1], "blocks": [[[["1/2"]]], [[["1/2"]]]]}])
        self.assertFalse(applies)


if __name__ == "__main__":
    unittest.main()
