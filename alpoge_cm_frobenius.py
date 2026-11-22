"""Count roots of X^3-X-1 modulo a prime by exact polynomial arithmetic.

For a prime p away from 23, Serre identifies this root count with 1+a_p,
where a_p is the coefficient of eta(tau) eta(23*tau). See section 5.3
of "On a theorem of Jordan", p. 434:
https://www.math.mcgill.ca/goren/SeminarOnCohomology/Serre.pdf
"""


def _product_mod_cubic(left, right, p):
    """Multiply in F_p[X]/(X^3-X-1), using ascending coefficients."""
    product = [0] * 5
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            product[i + j] += a * b
    # X^d = X^(d-2) + X^(d-3) for d >= 3 in this quotient.
    for degree in (4, 3):
        product[degree - 2] += product[degree]
        product[degree - 3] += product[degree]
    return [a % p for a in product[:3]]


def _trim(poly):
    while poly and poly[-1] == 0:
        poly.pop()
    return poly


def _remainder(dividend, divisor, p):
    remainder = dividend.copy()
    inverse = pow(divisor[-1], -1, p)
    while len(remainder) >= len(divisor):
        offset = len(remainder) - len(divisor)
        factor = remainder[-1] * inverse % p
        for j, coefficient in enumerate(divisor):
            remainder[offset + j] = (remainder[offset + j] - factor * coefficient) % p
        _trim(remainder)
    return remainder


def cubic_root_count(p):
    """Return the number of distinct roots of X^3-X-1 in F_p.

    The caller must establish that p is prime. X^p-X is the product of all
    monic linear factors over F_p, each once. Thus the gcd degree is the
    root count, even at the ramified prime 23. The calculation takes only
    O(log p) multiplications in the cubic quotient.
    """
    if type(p) is not int or p < 2:
        raise ValueError("p must be a prime integer")

    x = [0, 1, 0]
    power = [1, 0, 0]
    for bit in bin(p)[2:]:
        power = _product_mod_cubic(power, power, p)
        if bit == "1":
            power = _product_mod_cubic(power, x, p)
    power[1] = (power[1] - 1) % p

    a, b = [p - 1, p - 1, 0, 1], _trim(power)
    while b:
        a, b = b, _remainder(a, b, p)
    return len(a) - 1
