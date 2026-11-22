"""Enumerate isometric Z[i]-linear embeddings [m] → I₂ and their source-unit orbits.

A vector (a,b,c,d) encodes the image (a+bi,c+di) of 1. Its squared
Hermitian norm determines the pullback form, since f(s) = s f(1).
For m > 0 the image of 1 is nonzero, so the map is injective. All such
embeddings are counted, including those having nonprimitive image.
"""

import argparse
import json
from collections import defaultdict
from math import isqrt


UNITS = (("1", 1, 0), ("i", 0, 1), ("-1", -1, 0), ("-i", 0, -1))


def positive_norm(m):
    if type(m) is not int or m <= 0:
        raise ValueError("source norm must be a positive integer")


def shell_vectors(m):
    """Enumerate each ordered, signed vector with sum of four squares m."""
    positive_norm(m)
    pairs = defaultdict(list)
    bound = isqrt(m)
    for a in range(-bound, bound + 1):
        other_bound = isqrt(m - a * a)
        for b in range(-other_bound, other_bound + 1):
            pairs[a * a + b * b].append((a, b))
    return sorted(first + second
                  for weight, first_group in pairs.items()
                  for first in first_group
                  for second in pairs.get(m - weight, ()))


def image(v, real, imag):
    """Evaluate the embedding encoded by v at the Gaussian integer real+imag*i."""
    a, b, c, d = v
    return (real * a - imag * b, real * b + imag * a,
            real * c - imag * d, real * d + imag * c)


def four_square_count(m):
    """Jacobi's r₄(m) = 8 times the sum of the divisors of m not divisible by 4."""
    positive_norm(m)
    total = 0
    for d in range(1, isqrt(m) + 1):
        q, r = divmod(m, d)
        if r == 0:
            if d % 4:
                total += d
            if q != d and q % 4:
                total += q
    return 8 * total


def transfer(m):
    """Build source-unit orbits and verify coverage against the four-square count."""
    shell = shell_vectors(m)
    expected = four_square_count(m)
    shell_set = set(shell)
    if len(shell) != len(shell_set) or len(shell_set) != expected:
        raise ArithmeticError("enumeration disagrees with Jacobi's four-square count")
    covered = set()
    orbits = []
    for v in shell:
        if v in covered:
            continue
        # Precomposing f with s ↦ us takes the generator to f(u).
        images = {name: image(v, x, y) for name, x, y in UNITS}
        members = set(images.values())
        stabilizer = [name for name, w in images.items() if w == v]
        if (members & covered or not members <= shell_set or min(members) != v
                or stabilizer != ["1"] or len(members) * len(stabilizer) != len(UNITS)):
            raise ArithmeticError("source-unit orbit or stabilizer is inconsistent")
        covered.update(members)
        orbits.append({"representative": v, "unit_images": images,
                       "size": len(members), "stabilizer": stabilizer})
    if covered != shell_set or any(sum(x*x for x in v) != m for v in shell):
        raise ArithmeticError("partition does not cover precisely the expected norm shell")
    return {"norm": m, "coordinates": ["Re z1", "Im z1", "Re z2", "Im z2"],
            "action": "precomposition by source units", "units": [u[0] for u in UNITS],
            "embedding_count": len(shell), "jacobi_four_square_count": expected,
            "orbit_count": len(orbits), "shell": shell, "orbits": orbits}


def lean_fixture(data):
    """Serialize signed witnesses in the core-Lean tuple and list syntax."""
    shell = data["shell"]
    representatives = [o["representative"] for o in data["orbits"]]
    lines = ["import Std", "", "namespace GaussianData", "",
             "abbrev Point := Int × Int × Int × Int", ""]
    for name, points in (("vectors", shell), ("representatives", representatives)):
        rows = ["  (" + ", ".join(map(str, v)) + ")" for v in points]
        lines.extend([f"def {name} : List Point := [", ",\n".join(rows), "]", ""])
    return "\n".join(lines + ["end GaussianData", ""])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--norm", type=int, required=True, metavar="M",
                        help="positive integral norm of the source generator")
    parser.add_argument("--lean", action="store_true",
                        help="print the Lean module GaussianData instead of JSON")
    args = parser.parse_args(argv)
    try:
        data = transfer(args.norm)
    except ValueError as error:
        parser.error(str(error))
    if args.lean:
        print(lean_fixture(data), end="")
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
