#!/usr/bin/env python3
"""Evaluate a finite chain of weighted kernels using exact rational arithmetic.

Usage: python3 alpoge_theta.py chain.json   (use - to read standard input)
Example: {"input":[2,3],"steps":[{"stabilizers":[2,3],"kernel":[[1],[4]]}]}
Built-in lattice example: python3 alpoge_theta.py --gaussian 2 5
Vector-valued chain: python3 alpoge_theta.py --vector vector_chain.json

Each kernel row corresponds to a source class and each column to a target.
Provide either source stabilizer orders or explicit source weights. Use
integers and quoted fractions such as "2/3". An empty list of steps returns
the input. For an empty source, target_size specifies the number of outputs.

This specializes kerOp, chainOp and ChainInt to rational scalars and the
integer subring. For stabilizers it evaluates the finite class sum used by
thetaLiftAMF, given the kernel values and class data. The Gaussian mode
constructs the theta series of one standard lattice via orthogonal direct
sums. The full automorphic tower requires additional geometric data.
Source (archive commit 40e56ba):
https://github.com/leanprover-community/riemann-hypothesis/blob/40e56bab026552e089d7afcfeff08d2defb9c005/src/Formalism/ThetaLiftIndependence/Statement.lean
"""

import argparse
import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from math import factorial, gcd, isqrt


def _vector(items, label):
    if not isinstance(items, (list, tuple)):
        raise ValueError(f"{label} must be an array")
    result = []
    for value in items:
        if type(value) not in (int, str, Fraction):
            raise ValueError(f"{label}: use integers or quoted fractions")
        try:
            result.append(Fraction(value))
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"{label}: invalid rational {value!r}") from exc
    return tuple(result)


@dataclass(frozen=True)
class ChainResult:
    values: tuple
    denominator_product: int
    chain_int_applies: bool

    @property
    def scaled_values(self):
        return tuple(value * self.denominator_product for value in self.values)


def chain_op(values, steps):
    """Apply the supplied steps and check the integer hypotheses of ChainInt.

    For step j, D_j is the LCM of denominators of its weights. The theorem
    gives integer outputs after scaling by the product of D_j if the initial
    vector and all kernels are integral. Integrality of an output alone is
    insufficient to establish these hypotheses.
    """
    values = _vector(values, "input")
    if not isinstance(steps, (list, tuple)):
        raise ValueError("steps must be an array")
    integral = all(value.denominator == 1 for value in values)
    product = 1
    for j, step in enumerate(steps, 1):
        label = f"step {j}"
        if not isinstance(step, dict):
            raise ValueError(f"{label} must be an object")
        if ("weights" in step) == ("stabilizers" in step):
            raise ValueError(f"{label} requires exactly one of weights or stabilizers")
        if "stabilizers" in step:
            orders = step["stabilizers"]
            if not isinstance(orders, (list, tuple)) or any(
                    type(n) is not int or n < 1 for n in orders):
                raise ValueError(f"{label} stabilizers must be positive integer orders")
            weights = tuple(Fraction(1, n) for n in orders)
        else:
            weights = _vector(step["weights"], f"{label} weights")
        if len(weights) != len(values):
            raise ValueError(f"{label} needs one weight per source")
        rows = step.get("kernel")
        if not isinstance(rows, (list, tuple)) or len(rows) != len(values):
            raise ValueError(f"{label} kernel needs one row per source")
        kernel = tuple(_vector(row, f"{label} kernel row {i}")
                       for i, row in enumerate(rows, 1))
        width = step.get("target_size", len(kernel[0]) if kernel else 0)
        if type(width) is not int or width < 0 or any(len(row) != width for row in kernel):
            raise ValueError(f"{label} kernel rows must match the target dimension")

        scale = 1
        for weight in weights:
            d = weight.denominator
            scale = scale // gcd(scale, d) * d
        product *= scale
        integral = integral and all(x.denominator == 1 for row in kernel for x in row)
        weighted = tuple(w * f for w, f in zip(weights, values))
        values = tuple(sum((c * row[col] for c, row in zip(weighted, kernel)), Fraction())
                       for col in range(width))
    return ChainResult(values, product, integral)


def module_chain(vectors, steps):
    """chainOpM over rational coordinate spaces, with their integer lattices.

    Input is a list of nonempty, equal-length vectors, one per source class.
    blocks[i][j] is the linear map from class i to class j. Each map is a
    matrix with target coordinates as rows and source coordinates as columns.
    Each level has at least one class. Return vectors grouped by target class
    along with the ChainIntM denominator and the integer-lattice check.
    """
    if not isinstance(vectors, (list, tuple)) or not vectors:
        raise ValueError("provide at least one source vector")
    vectors = tuple(_vector(v, "input vector") for v in vectors)
    dim = len(vectors[0])
    if not dim or any(len(v) != dim for v in vectors):
        raise ValueError("vectors must have the same positive dimension")
    if not isinstance(steps, (list, tuple)):
        raise ValueError("steps must be an array")
    classes = len(vectors)
    values = tuple(x for v in vectors for x in v)
    scale = 1
    applies = all(x.denominator == 1 for x in values)
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("expected a step object")
        matrices = step.get("blocks")
        if not isinstance(matrices, list) or len(matrices) != classes:
            raise ValueError("blocks must have one row per source class")
        if not all(isinstance(row, list) and row for row in matrices):
            raise ValueError("each block row needs at least one target")
        targets = len(matrices[0])
        if any(len(row) != targets for row in matrices):
            raise ValueError("ragged block rows")
        first = matrices[0][0]
        if not isinstance(first, list) or not first:
            raise ValueError("expected a matrix with positive target dimension")
        next_dim = len(first)
        keys = [k for k in ("stabilizers", "weights") if k in step]
        if len(keys) != 1:
            raise ValueError("a step requires weights or stabilizers")
        key = keys[0]
        masses = step[key]
        if not isinstance(masses, list) or len(masses) != classes:
            raise ValueError("expected one weight or stabilizer per source class")
        # Expand each class into its coordinates. Repeating a weight leaves
        # its denominator LCM unchanged. Integer matrix entries are exactly
        # the lattice-preserving condition for the standard coordinate bases.
        flat_kernel = []
        for row in matrices:
            maps = []
            for block in row:
                if not isinstance(block, list) or len(block) != next_dim:
                    raise ValueError("inconsistent target dimension")
                matrix = [_vector(r, "matrix row") for r in block]
                if any(len(r) != dim for r in matrix):
                    raise ValueError("inconsistent source dimension")
                maps.append(matrix)
            for s in range(dim):
                flat_kernel.append([r[s] for matrix in maps for r in matrix])
        integral_maps = all(x.denominator == 1 for row in flat_kernel for x in row)
        repeated = [w for w in masses for _ in range(dim)]
        result = chain_op(values, [{key: repeated, "kernel": flat_kernel}])
        values = result.values
        scale *= result.denominator_product
        applies = applies and integral_maps
        dim, classes = next_dim, targets
    grouped = tuple(values[i:i + dim] for i in range(0, len(values), dim))
    return grouped, scale, applies


def gaussian_theta_coefficients(rank, degree):
    """Return a_0,...,a_degree of the standard Hermitian lattice Z[i]^rank.

    With q = exp(2*pi*i*tau), a_n counts vectors of squared norm n. The
    trace from Q(i) to Q doubles the squared norm in the exponent of thetaL.
    An orthogonal direct sum multiplies series. Convolution here implements
    that coefficient transfer through degree n using exact integers.
    """
    if type(rank) is not int or rank < 1 or type(degree) is not int or degree < 0:
        raise ValueError("Gaussian rank must be a positive integer and degree a nonnegative integer")
    one_coordinate = [0] * (degree + 1)
    for x in range(isqrt(degree) + 1):
        x_sq = x * x
        x_signs = 1 if x == 0 else 2
        for y in range(isqrt(degree - x_sq) + 1):
            y_signs = 1 if y == 0 else 2
            one_coordinate[x_sq + y * y] += x_signs * y_signs
    coefficients = one_coordinate
    supported = [(index, count) for index, count in enumerate(one_coordinate) if count]
    for _ in range(1, rank):
        result = [0] * (degree + 1)
        for shift, count in supported:
            for i in range(degree - shift + 1):
                result[i + shift] += coefficients[i] * count
        coefficients = result
    return coefficients


def gaussian_contribution(rank, degree):
    """Return one lattice's contribution to the coefficient, with input form f=1.

    Each column of an integral unitary automorphism has norm one, so its
    sole nonzero coordinate is a Gaussian unit. Orthogonality forces a
    permutation of the coordinate axes. Thus |Aut(L)| = 4^rank * rank!.
    """
    count = gaussian_theta_coefficients(rank, degree)[degree]
    order = 4 ** rank * factorial(rank)
    return {"lattice": f"standard Z[i]^{rank}", "degree": degree, "coefficient": count,
            "automorphism_order": order, "lattice_weight": str(Fraction(1, order)),
            "weighted_coefficient": str(Fraction(count, order))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("file", nargs="?", help="JSON input file, or - for standard input")
    mode.add_argument("--vector", metavar="FILE", help="vector-valued chain JSON or - for stdin")
    mode.add_argument("--gaussian", nargs=2, metavar=("RANK", "DEGREE"), type=int,
                      help="compute one exact theta coefficient and its class-weighted contribution")
    args = parser.parse_args(argv)
    try:
        if args.gaussian is not None:
            print(json.dumps(gaussian_contribution(*args.gaussian), indent=2))
            return
        path = args.vector if args.vector is not None else args.file
        if path == "-":
            data = json.load(sys.stdin)
        else:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        if not isinstance(data, dict) or "input" not in data or "steps" not in data:
            raise ValueError("supply an object with input and steps")
        if args.vector is not None:
            vectors, scale, applies = module_chain(data["input"], data["steps"])
            print(json.dumps({"vectors": [[str(x) for x in v] for v in vectors],
                              "denominator_product": scale, "chain_int_m_applies": applies,
                              "scaled_vectors": [[str(x * scale) for x in v] for v in vectors]},
                             indent=2))
            return
        result = chain_op(data["input"], data["steps"])
    except (ValueError, OSError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")
    print(json.dumps({"values": [str(v) for v in result.values],
                      "denominator_product": result.denominator_product,
                      "chain_int_applies": result.chain_int_applies,
                      "scaled_values": [str(v) for v in result.scaled_values]}, indent=2))


if __name__ == "__main__":
    main()
