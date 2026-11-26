"""Prime Hecke matrices on proper classes of imaginary quadratic norm forms."""

from math import isqrt

from alpoge_cm_forms import reduce_form, reduced_forms


def splitting_symbol(D, p):
    """Return the Kronecker symbol (D/p) for a prime p, including p=2."""
    if type(D) is not int:
        raise ValueError("D must be an integer")
    if type(p) is not int or p < 2:
        raise ValueError("p must be a prime integer")
    if p == 2:
        if D % 2 == 0:
            return 0
        return 1 if D % 8 in (1, 7) else -1
    if p % 2 == 0 or any(p % q == 0 for q in range(3, isqrt(p) + 1, 2)):
        raise ValueError("p must be a prime integer")
    residue = pow(D % p, (p - 1) // 2, p)
    return -1 if residue == p - 1 else residue


def _class_columns(forms):
    forms = tuple(tuple(form) for form in forms)
    if not forms:
        raise ValueError("supply the complete basis of reduced forms")
    if any(len(form) != 3 or any(type(t) is not int for t in form) for form in forms):
        raise ValueError("a form must be an integer triple (a,b,c)")
    a, b, c = forms[0]
    D = b * b - 4 * a * c
    columns = {form: j for j, form in enumerate(forms)}
    if len(columns) != len(forms) or set(columns) != set(reduced_forms(D)):
        raise ValueError("supply each reduced form of the discriminant exactly once")
    return D, columns


def _finite_roots(a, b, c, p, root):
    if root is None:
        for k in range(p):
            if ((a * k + b) * k + c) % p == 0:
                yield k
    elif a % p:
        inverse = pow(2 * a, -1, p)
        yield ((-b + root) * inverse) % p
        if root:
            yield ((-b - root) * inverse) % p
    elif b % p:
        yield (-c * pow(b, -1, p)) % p
    # When p divides a and b, primitivity forces p not to divide c.


def _matrix(columns, p, degree, root=None):
    matrix = []
    for a, b, c in columns:
        row = [0] * len(columns)
        # The preimage of [k:1] has oriented basis (p,0), (k,1).
        for k in _finite_roots(a, b, c, p, root):
            value = (a * k + b) * k + c
            neighbor = reduce_form((p * a, 2 * a * k + b, value // p))
            row[columns[neighbor]] += 1
        # The preimage of [1:0] has oriented basis (1,0), (0,p).
        if a % p == 0:
            neighbor = reduce_form((a // p, b, p * c))
            row[columns[neighbor]] += 1
        if sum(row) != degree:
            raise ArithmeticError("isotropic line count disagrees with the splitting symbol")
        matrix.append(row)
    return matrix


def hecke_matrix(forms, p):
    """Return the integer matrix in the supplied order of all reduced classes.

    Row i counts the index-p sublattices of form i on which Q/p is integral,
    grouped by its reduced class j. For theta coefficients r_i(n) this gives
    sum_j A[i][j] r_j(n) = r_i(p*n) + (D/p) r_i(n/p), with a zero term
    at nonintegral n/p. A vector of norm p*n with nonzero reduction lies on
    one isotropic line. A vector divisible by p lies on all 1+(D/p) such lines.
    """
    D, columns = _class_columns(forms)
    return _matrix(columns, p, 1 + splitting_symbol(D, p))


def hecke_matrix_from_root(forms, p, root):
    """Compute the Hecke matrix from a square root of D modulo an odd prime p.

    The caller must establish primality of p. The supplied root is checked,
    then each row uses at most two isotropic lines obtained by field arithmetic.
    Either sign of the root gives the same matrix. A zero root gives the
    ramified operator with one line per class.
    """
    if type(p) is not int or p < 3 or p % 2 == 0:
        raise ValueError("p must be an odd prime")
    if type(root) is not int:
        raise ValueError("root must be an integer")
    D, columns = _class_columns(forms)
    root %= p
    if root * root % p != D % p:
        raise ValueError("root must square to the discriminant modulo p")
    return _matrix(columns, p, 1 if root == 0 else 2, root)
