import unittest

from ntt_fixture import OMEGA, P, TWO_ADICITY, transform, verify_convolution, verify_parameters


class TransformTests(unittest.TestCase):
    def test_certificate(self):
        self.assertEqual(verify_parameters()["prime"].bit_length(), 256)
        self.assertEqual(verify_convolution(), 256)

    def test_transform_agrees_with_definition(self):
        for n in (1, 2, 4, 16, 32):
            values = [i**2-10 for i in range(n)]
            root = pow(OMEGA, (1 << TWO_ADICITY)//n, P)
            expected = [sum(v*pow(root, i*j, P) for j,v in enumerate(values)) % P
                        for i in range(n)]
            self.assertEqual(transform(values), expected)
            self.assertEqual(transform(expected,inverse=True), [v%P for v in values])
        for values in ([], [1,2,3]):
            with self.assertRaises(ValueError):
                transform(values)
