"""Construct norm-one cube roots of X modulo X^3-X-1 for a verified prime.

Coordinates and polynomial coefficients are in ascending degree order.
"""
import argparse
import json

from cubic_study import power
from cubic_trace_criterion import F, root_count

Q = [-3, -6, 0, 1]
ALPHA = (0, 1, 0)
ONE = (1, 0, 0)


def _unity_root(p):
    for candidate in range(2, p):
        zeta = pow(candidate, (p - 1) // 3, p)
        if zeta != 1 and (zeta*zeta + zeta + 1) % p == 0:
            return zeta
    raise ArithmeticError("failed to find a primitive cube root of unity")


def cubic_lift(p):
    """Return the three lifts, their traces, and gcd(H,U^p-U), or empty lifts.

    Caller establishes primality. The first lift is canonical in the subgroup
    of order (p²+p+1)/3. The auxiliary cubic independently checks existence.
    """
    if type(p) is not int or p < 7 or p % 3 != 1:
        raise ValueError("expected a verified prime congruent to 1 modulo 3")
    if root_count(F, p):
        raise ValueError("requires irreducible X^3-X-1")
    order = p*p + p + 1
    m = order // 3
    character = power(ALPHA, m, p)
    count = root_count(Q, p)
    if character[1:] != (0, 0) or pow(character[0], 3, p) != 1:
        raise ArithmeticError("invalid norm-one cubic character")
    if count != (3 if character == ONE else 0):
        raise ArithmeticError("auxiliary cubic and norm-one character disagree")
    report = dict(p=p, q_root_count=count, character=character[0],
                  roots=(), traces=(), trace_gcd=(1,))
    if not count:
        return report

    beta = power(ALPHA, pow(3, -1, m), p)
    zeta = _unity_root(p)
    roots = tuple(tuple(k*v % p for v in beta) for k in (1, zeta, zeta*zeta % p))
    traces = tuple((3*a + 2*c) % p for a, _, c in roots)
    if any(power(r, 3, p) != ALPHA or power(r, order, p) != ONE for r in roots):
        raise ArithmeticError("invalid norm-one cube roots")
    if len(set(traces)) != 3 or power(beta, m, p) != ONE:
        raise ArithmeticError("invalid canonical lift or repeated traces")
    report.update(roots=roots, traces=traces, trace_gcd=((-traces[0]**3) % p, 0, 0, 1))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("p", type=int, help="independently verified prime")
    args = parser.parse_args()
    try:
        print(json.dumps(cubic_lift(args.p)))
    except ValueError as exc:
        parser.error(str(exc))
