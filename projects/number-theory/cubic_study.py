"""Study X^3-X-1 over a caller-verified odd prime other than 23.

Coordinates are (constant, linear, quadratic). Matrices act on columns.
Requires alpoge_cm_frobenius on the Python path.
"""
from alpoge_cm_frobenius import _product_mod_cubic, cubic_root_count


def multiply(left, right, p):
    """Multiply two three-coordinate elements in the cubic quotient."""
    if len(left) != 3 or len(right) != 3:
        raise ValueError("expected three coefficients per element")
    return tuple(_product_mod_cubic(left, right, p))


def power(element, exponent, p):
    """Raise an element to a nonnegative integer exponent."""
    if type(exponent) is not int or exponent < 0:
        raise ValueError("expected a nonnegative integer exponent")
    result = (1, 0, 0)
    for bit in bin(exponent)[2:]:
        result = multiply(result, result, p)
        if bit == "1":
            result = multiply(result, element, p)
    return result


def apply_frobenius(matrix, element, p):
    """Apply a precomputed row-major Frobenius matrix to one element."""
    if len(element) != 3 or len(matrix) != 3 or any(len(r) != 3 for r in matrix):
        raise ValueError("expected a 3 by 3 matrix and three coordinates")
    return tuple(sum(x*y for x, y in zip(row, element)) % p for row in matrix)


def determinant(rows):
    (a,b,c), (d,e,f), (g,h,i) = rows
    return a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)


def study(p):
    """Classify the cubic. The caller must independently establish primality."""
    if type(p) is not int or p < 3 or p % 2 == 0 or p == 23:
        raise ValueError("expected a verified odd prime other than 23")
    roots = cubic_root_count(p)
    degrees = {0: (3,), 1: (1, 2), 3: (1, 1, 1)}.get(roots)
    euler = pow(-23, (p-1)//2, p)
    sign = -1 if euler == p-1 else euler
    if degrees is None or sign != (-1 if roots == 1 else 1):
        raise ArithmeticError("inconsistent gcd degree and discriminant character")
    report = dict(p=p, gcd_degree=roots, factor_degrees=degrees,
                  discriminant_character=sign)
    if roots:
        return report
    x = (0, 1, 0)
    xp = power(x, p, p)
    matrix = tuple(zip((1, 0, 0), xp, multiply(xp, xp, p)))
    # For p != 3, x and x^p are independent: if x^p=kx then the
    # cubic relation forces k^3=k=1, contradicting irreducibility.
    # They span the trace-zero plane; translating x by 1 gives a
    # normal generator (the three conjugates sum to 3).
    # In characteristic 3 the element x^2 has nonzero trace (2).
    generator = (0, 0, 1) if p == 3 else (1, 1, 0)
    second = apply_frobenius(matrix, generator, p)
    third = apply_frobenius(matrix, second, p)
    basis = (generator, second, third)
    if determinant(basis) % p == 0 or apply_frobenius(matrix, third, p) != generator:
        raise ArithmeticError("failed Frobenius normal basis verification")
    # Norm(x)=1, hence x has order dividing p^2+p+1 < p^3-1.
    report.update(frobenius_matrix=matrix, normal_basis=basis,
                  x_order_divides=p*p+p+1, x_is_primitive=False)
    return report


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("p", type=int, help="independently verified odd prime other than 23")
    print(json.dumps(study(parser.parse_args().p)))
