"""Regression and invalid-certificate checks for the companion-matrix audit."""
import unittest

from matrix_periods import (
    CURVE, CURVE_FACTORS, GOLD, INITIAL, ROOTS, audit, prime, snapshot,
    validate_roots, verify,
)


class PeriodTests(unittest.TestCase):
    def test_certificates(self):
        self.assertEqual(audit()["curve25519"]["exact_period"], CURVE-1)

    def test_wrong_root_index_and_duplicate(self):
        wrong_index = ((ROOTS[0][0], 2), *ROOTS[1:])
        for bad in (wrong_index, (ROOTS[0], ROOTS[0], ROOTS[2]),
                    ((1, 1), *ROOTS[1:])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_roots(bad)

    def test_invalid_order_and_composite_factor(self):
        for bad in ({**CURVE_FACTORS, 2: 1}, {**CURVE_FACTORS, 2: 3}, {4: 1}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verify(CURVE, bad)
        self.assertFalse(prime(2**64-1))

    def test_sequence_and_spectral_evaluation(self):
        for p in (CURVE, GOLD):
            state = INITIAL
            for n in range(40):
                self.assertEqual(snapshot(n,p), state)
                state = (state[1], state[2], (state[0]+state[1]) % p)
        for n in (0, 1, 2, 3, CURVE//9, CURVE-1):
            self.assertEqual(snapshot(n,CURVE)[0],
                             sum(pow(r,n,CURVE) for r,_ in ROOTS) % CURVE)


if __name__ == "__main__":
    unittest.main()
