import unittest

from alpoge_cm_frobenius import cubic_root_count
from cubic_crypto_lab import cm_coefficient, walk
from cubic_trace_criterion import brute_check, criterion
import goldilocks_order as gold


class CryptoLabTests(unittest.TestCase):
    def test_walk_wraps_and_random_access_agrees(self):
        for start in (0, gold.N - 2, (1 << 300) + 1):
            for i, point in walk(start, 6):
                self.assertEqual(point, gold.x_power(i))
        self.assertEqual(list(walk(0, 0)), [])
        with self.assertRaises(ValueError):
            list(walk(-1, 1))

    def test_perrin_trace_and_recurrence(self):
        points = [u for _, u in walk(0, 32)]
        traces = [(3*a + 2*c) % gold.P for a, _, c in points]
        self.assertEqual(traces[:3], [3, 0, 2])
        self.assertEqual(traces[3:], [(a+b) % gold.P for a, b in zip(traces, traces[1:])][:29])

    def test_trace_branches(self):
        self.assertEqual(criterion(13), 1)
        self.assertEqual(criterion(151), 0)
        self.assertEqual(brute_check(2000), (17, 32))

    def test_cm_factorization_types(self):
        for p in (5, 13, 59, gold.P):
            self.assertEqual(cm_coefficient(p), cubic_root_count(p) - 1)
