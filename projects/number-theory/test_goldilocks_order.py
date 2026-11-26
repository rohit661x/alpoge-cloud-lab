import unittest
from unittest.mock import patch

import goldilocks_order as cert


class CertificateTests(unittest.TestCase):
    def test_complete_certificate(self):
        self.assertTrue(cert.verify())

    def test_corrupt_residue(self):
        with patch.object(cert, "RESIDUES", (cert.ONE,) + cert.RESIDUES[1:]):
            self.assertFalse(cert.verify())

    def test_corrupt_prime_witness(self):
        with patch.dict(cert.LUCAS, {cert.P: (1, cert.LUCAS[cert.P][1])}):
            self.assertFalse(cert.verify())
