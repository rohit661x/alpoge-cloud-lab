"""Exact arithmetic for positive definite integral binary quadratic forms.

A triple (a,b,c) denotes a*x^2 + b*x*y + c*y^2. Classes use proper
equivalence (changes of variables in SL(2,Z)).
"""

from math import gcd, isqrt


def _is_negative_fundamental(D):
    if type(D) is not int or D >= 0:
        return False
    if D % 4 == 1:
        radicand = D
    elif D % 4 == 0 and (D // 4) % 4 in (2, 3):
        radicand = D // 4
    else:
        return False
    magnitude = -radicand
    # The residue conditions already exclude a factor of 4 in radicand.
    return all(magnitude % (d * d) for d in range(3, isqrt(magnitude) + 1, 2))


def reduced_forms(D):
    """List one primitive reduced triple per proper class at fundamental D < 0.

    Reduced triples have |b| <= a <= c, with b >= 0 if |b| = a or a = c.
    Hence |D| = 4ac - b^2 >= 3a^2. Once a and b are fixed, D determines c.
    """
    if not _is_negative_fundamental(D):
        raise ValueError("D must be a negative fundamental discriminant")
    forms = []
    for a in range(1, isqrt(-D // 3) + 1):
        # Both signs occur for interior forms. On the edge |b| = a use +a.
        first_b = 1 - a
        first_b += (D - first_b) % 2
        for b in range(first_b, a + 1, 2):
            c, remainder = divmod(b * b - D, 4 * a)
            if remainder or c < a or (c == a and b < 0):
                continue
            if gcd(gcd(a, b), c) == 1:
                forms.append((a, b, c))
    return tuple(forms)


def reduce_representation(form, vector=(1, 0)):
    """Reduce a primitive form and transport an integer vector to its new basis.

    If (R,w) is returned then R(w) equals form(vector). Each change of
    basis has determinant one, so a primitive input vector stays primitive.
    """
    if (not isinstance(form, (tuple, list)) or len(form) != 3
            or any(type(v) is not int for v in form)):
        raise ValueError("a form must be an integer triple (a,b,c)")
    a, b, c = form
    if a <= 0 or b * b >= 4 * a * c:
        raise ValueError("the form must be positive definite")
    if gcd(gcd(a, b), c) != 1:
        raise ValueError("the form must be primitive")
    if (not isinstance(vector, (tuple, list)) or len(vector) != 2
            or any(type(v) is not int for v in vector)):
        raise ValueError("a vector must be an integer pair (x,y)")
    x, y = vector
    while True:
        # Q(x+k*y,y) makes -a < b <= a, including the +a convention.
        k = (a - b) // (2 * a)
        c += k * (b + a * k)
        b += 2 * a * k
        x -= k * y
        if a < c or (a == c and b >= 0):
            return (a, b, c), (x, y)
        # Q(-y,x) decreases a or, when a=c, fixes the sign of b.
        a, b, c = c, -b, a
        x, y = y, -x


def reduce_form(form):
    """Return the canonical properly equivalent representative of a primitive form."""
    return reduce_representation(form)[0]


def theta_coefficients(form, limit):
    """Count all signed, ordered lattice vectors of each norm from 0 to limit.

    Reduction preserves all multiplicities. With d = 4ac-b^2 > 0, the
    identity 4aQ(x,y) = (2ax+by)^2 + d*y^2 bounds |y| and then gives
    the exact closed interval of x for each y. All endpoints use integer
    square roots and directed integer division.
    """
    if type(limit) is not int or limit < 0:
        raise ValueError("limit must be a nonnegative integer")
    a, b, c = reduce_form(form)
    d = 4 * a * c - b * b
    budget = 4 * a * limit
    max_y = isqrt(budget // d)
    counts = [0] * (limit + 1)
    for y in range(-max_y, max_y + 1):
        radius = isqrt(budget - d * y * y)
        by = b * y
        xmin = -((radius + by) // (2 * a))
        xmax = (radius - by) // (2 * a)
        for x in range(xmin, xmax + 1):
            counts[a * x * x + by * x + c * y * y] += 1
    return counts
