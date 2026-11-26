import unittest
from math import isqrt

from cubic_lift import cubic_lift
from cubic_trace_criterion import F, H, remainder, root_count


class LiftTests(unittest.TestCase):
    def test_all_eligible_primes_through_1000(self):
        for p in range(7, 1001, 6):
            if any(p % d == 0 for d in range(2, isqrt(p)+1)) or root_count(F, p):
                continue
            with self.subTest(p=p):
                result = cubic_lift(p)
                traces = {u for u in range(p) if (u**9-18*u**6+54*u**3+27) % p == 0}
                self.assertEqual(set(result['traces']), traces)
                self.assertEqual(len(result['roots']), len(traces))
                self.assertEqual(sum((y**3-6*y-3) % p == 0 for y in range(p)),
                                 result['q_root_count'])
                self.assertEqual(remainder(H, result['trace_gcd'], p), [])

    def test_public_fields(self):
        fields = [
            (2**64-2**32+1, 0),
            (28948022309329048855892746252171976963363056481941560715954676764349967630337, 3),
            (4002409555221667393417789825735904156556882819939007885332058136124031650490837864442687629129015664037894272559787, 3),
        ]
        for p, expected in fields:
            with self.subTest(p=p):
                result = cubic_lift(p)
                self.assertEqual(len(result['roots']), expected)
                self.assertEqual(root_count(H, p), expected)
                self.assertEqual(remainder(H, result['trace_gcd'], p), [])

    def test_invalid_domain(self):
        for p in (True, 3, 5, 23, 7):
            with self.subTest(p=p), self.assertRaises(ValueError):
                cubic_lift(p)
