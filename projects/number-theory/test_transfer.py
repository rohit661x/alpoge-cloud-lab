import ast
import itertools
import json
import re
import subprocess
import sys
import unittest
from math import isqrt
from pathlib import Path

from gaussian_transfer import UNITS, four_square_count, image, shell_vectors, transfer


SCRIPT = Path(__file__).with_name("gaussian_transfer.py")


def hermitian(x, y):
    """Pair of integer coordinates of conjugate(x₁)y₁ + conjugate(x₂)y₂."""
    a, b, c, d = x
    e, f, g, h = y
    return a*e + b*f + c*g + d*h, a*f - b*e + c*h - d*g


class GaussianTransferTests(unittest.TestCase):
    def test_shell_against_direct_box(self):
        for m in range(1, 26):
            with self.subTest(m=m):
                radius = isqrt(m)
                box = itertools.product(range(-radius, radius + 1), repeat=4)
                direct = [v for v in box if sum(x*x for x in v) == m]
                self.assertEqual(shell_vectors(m), direct)
                self.assertEqual(four_square_count(m), len(direct))

    def test_source_unit_orbit_partition(self):
        for m in (1, 2, 4, 5, 8, 12, 25, 50):
            with self.subTest(m=m):
                result = transfer(m)
                seen = []
                for orbit in result["orbits"]:
                    a, b, c, d = orbit["representative"]
                    expected = {"1": (a, b, c, d), "i": (-b, a, -d, c),
                                "-1": (-a, -b, -c, -d), "-i": (b, -a, d, -c)}
                    self.assertEqual(orbit["unit_images"], expected)
                    self.assertEqual(orbit["stabilizer"], ["1"])
                    self.assertEqual(orbit["size"], 4)
                    seen.extend(expected.values())
                self.assertEqual(sorted(seen), result["shell"])

    def test_hermitian_pullback_on_basis(self):
        # Sesquilinearity reduces equality over the underlying Z-lattice
        # to the four pairings on its ordered basis (1,i).
        for m in (1, 5, 9, 16, 65):
            for v in shell_vectors(m):
                columns = (image(v, 1, 0), image(v, 0, 1))
                self.assertEqual([hermitian(x, y) for x in columns for y in columns],
                                 [(m, 0), (0, m), (0, -m), (m, 0)])
                self.assertEqual(image(v, 11, -7),
                                 tuple(11*x - 7*y for x, y in zip(*columns)))

    def test_includes_nonprimitive_embeddings(self):
        # Multiplication by 2 on the first Gaussian axis embeds [4].
        self.assertIn((2, 0, 0, 0), shell_vectors(4))

    def test_known_cardinalities(self):
        for m, count in [(1, 8), (2, 24), (4, 24), (5, 48), (8, 24), (9, 104)]:
            result = transfer(m)
            self.assertEqual(result["embedding_count"], count)
            self.assertEqual(result["orbit_count"], count // len(UNITS))

    def test_cli_json_and_lean_agree(self):
        command = [sys.executable, str(SCRIPT), "--norm", "5"]
        data = json.loads(subprocess.check_output(command, text=True))
        fixture = subprocess.check_output(command + ["--lean"], text=True)
        lists = {name: ast.literal_eval(rows) for name, rows in
                 re.findall(r"def (\w+) : List Point := (\[.*?\])", fixture, re.S)}
        self.assertEqual(lists["vectors"], list(map(tuple, data["shell"])))
        self.assertEqual(lists["representatives"],
                         [tuple(o["representative"]) for o in data["orbits"]])
        self.assertEqual((len(lists["vectors"]), len(lists["representatives"])), (48, 12))

    def test_invalid_norm(self):
        for invalid in (0, -1, 2.5, True):
            with self.assertRaises(ValueError):
                transfer(invalid)
        result = subprocess.run([sys.executable, str(SCRIPT), "--norm", "0"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("source norm must be a positive integer", result.stderr)


if __name__ == "__main__":
    unittest.main()
