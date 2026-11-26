import unittest
from galois_census import cycles, group_weights, primes_through


class CensusTests(unittest.TestCase):
    def test_group_and_eligible_fibers(self):
        weights = group_weights()
        self.assertEqual(sum(weights.values()), 108)
        self.assertEqual(len(weights), 11)
        eligible = [(q, h, n) for (r, f, q, h), n in weights.items() if r == 1 and f == (3,)]
        self.assertEqual(sorted(eligible), [((1,1,1), (1,1,1,3,3), 6), ((3,), (3,3,3), 12)])

    def test_unramified_primes(self):
        self.assertEqual(list(primes_through(25)), [2, 5, 7, 11, 13, 17, 19])
        with self.assertRaises(ValueError):
            cycles((0, 0))
