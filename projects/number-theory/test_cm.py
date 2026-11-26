"""CM operator tests, including independent q-product and certificate checks."""

import json
from pathlib import Path
import unittest

from alpoge_cm import certified_operator, cm_chain
from alpoge_cm_certificate import verify_certificate
from alpoge_cm_forms import reduced_forms, theta_coefficients
from alpoge_cm_frobenius import cubic_root_count
from alpoge_cm_hecke import hecke_matrix, hecke_matrix_from_root


class CMTests(unittest.TestCase):
    def test_ramified_and_inert(self):
        self.assertEqual(hecke_matrix(reduced_forms(-20), 2), [[0, 1], [1, 0]])
        self.assertEqual(hecke_matrix(reduced_forms(-23), 5), [[0]*3 for _ in range(3)])

    def test_repeated_prime_counts_paths(self):
        chain = cm_chain(-23, [2, 2], 32)
        self.assertEqual(chain["operator_product"], [[2, 1, 1], [1, 2, 1], [1, 1, 2]])

    def test_modular_roots_vs_enumeration(self):
        for D in (-3, -4, -20, -23, -71, -84):
            basis = reduced_forms(D)
            for p in (3, 5, 7, 11, 13):
                for root in range(p):
                    if (root*root - D) % p == 0:
                        self.assertEqual(hecke_matrix_from_root(basis, p, root), hecke_matrix(basis, p))

    def test_level_23_eta_product(self):
        # q * product_{k >= 1} (1-q^k)(1-q^(23k)), truncated through q^128.
        limit = 128
        coeffs = [0, 1] + [0]*(limit - 1)
        for factor in (1, 23):
            for step in range(factor, limit + 1, factor):
                for n in range(limit, step - 1, -1):
                    coeffs[n] -= coeffs[n - step]
        principal = theta_coefficients((1, 1, 6), limit)
        other = theta_coefficients((2, -1, 3), limit)
        self.assertEqual([2*c for c in coeffs], [a-b for a, b in zip(principal, other)])

    def test_public_certificate_and_tampering(self):
        path = Path(__file__).with_name("cm_prime_1024.json")
        record = json.loads(path.read_text(encoding="utf-8"))
        report = certified_operator(record)
        self.assertEqual(report["representations_of_prime"], [0, 2, 2])
        self.assertEqual(report["eta_tau_eta_23tau_coefficient_at_prime"], -1)
        self.assertEqual(report["roots_of_X3_minus_X_minus_1_mod_prime"], 0)
        for damaged in (dict(record, n=record["n"] - 2),
                        dict(record, witness=record["n"] - 1),
                        dict(record, vector=[record["vector"][0] + 1, record["vector"][1]])):
            with self.assertRaises(ValueError):
                verify_certificate(damaged)

    def test_polynomial_root_count(self):
        for p in (2, 3, 5, 7, 11, 13, 17, 19, 59):
            self.assertEqual(cubic_root_count(p), sum((x**3 - x - 1) % p == 0 for x in range(p)))


if __name__ == "__main__":
    unittest.main()
