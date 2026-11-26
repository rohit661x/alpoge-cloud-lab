"""Generate and check Hecke operators from imaginary quadratic lattice classes."""

import argparse
import json
from math import prod
from pathlib import Path

from alpoge_cm_forms import reduced_forms, theta_coefficients
from alpoge_cm_hecke import hecke_matrix, splitting_symbol


def cm_chain(discriminant, primes, through):
    """Compare each operator and their ordered product with theta coefficients."""
    if type(discriminant) is not int or not -10000 <= discriminant <= -3:
        raise ValueError("the class enumeration demo supports -10000 <= D <= -3")
    if type(through) is not int or through < 1:
        raise ValueError("choose a positive final coefficient")
    primes = tuple(primes)
    if not 1 <= len(primes) <= 12 or any(type(p) is not int or not 2 <= p <= 4096 for p in primes):
        raise ValueError("supply 1 to 12 prime indices, each between 2 and 4096")
    forms = reduced_forms(discriminant)
    cutoff = through * prod(primes)
    # Direct representation counting is the independent check. Limit its table size.
    if len(forms) * (cutoff + 1) > 1_000_000:
        raise ValueError("direct theta check exceeds one million coefficients; reduce --through or the indices")
    h = len(forms)
    original = [theta_coefficients(form, cutoff) for form in forms]
    matrices = {p: hecke_matrix(forms, p) for p in set(primes)}
    chain = [[int(i == j) for j in range(h)] for i in range(h)]
    checks = 0
    for p in primes:
        matrix = matrices[p]
        symbol = splitting_symbol(discriminant, p)
        for i, row in enumerate(matrix):
            for n in range(through + 1):
                rhs = original[i][p*n] + (symbol * original[i][n//p] if n % p == 0 else 0)
                if sum(m * series[n] for m, series in zip(row, original)) != rhs:
                    raise ArithmeticError(f"neighbor identity failed for p={p}, class={i}, n={n}")
                checks += 1
        chain = [[sum(a*b for a, b in zip(row, col)) for col in zip(*matrix)] for row in chain]

    # Independently apply the Hecke q-expansion rule on the source series.
    transformed = original
    for p in reversed(primes):
        symbol = splitting_symbol(discriminant, p)
        cutoff //= p
        transformed = [
            [series[p*n] + (symbol * series[n//p] if n % p == 0 else 0)
             for n in range(cutoff + 1)] for series in transformed
        ]
    for i, row in enumerate(chain):
        for n in range(through + 1):
            if sum(m * series[n] for m, series in zip(row, original)) != transformed[i][n]:
                raise ArithmeticError(f"chain identity failed for class={i}, n={n}")
            checks += 1
    return {"discriminant": discriminant, "forms": forms, "indices": primes,
            "operator_product": chain, "checked_through": through, "equalities_checked": checks}


def certified_operator(certificate):
    """Recover both split directions from a proved norm representation."""
    from alpoge_cm_certificate import verify_certificate
    from alpoge_cm_frobenius import cubic_root_count
    from alpoge_cm_hecke import hecke_matrix_from_root
    verify_certificate(certificate)
    p = certificate["n"]
    D = certificate["discriminant"]
    a, b, _ = certificate["form"]
    x, y = certificate["vector"]
    # (2ax+by)^2 - D*y^2 = 4a*p. The nonprincipal representation here
    # has 0 < |y| < p, so its inverse in the prime field exists.
    root = (2*a*x + b*y) * pow(y, -1, p) % p
    forms = reduced_forms(D)
    matrix = hecke_matrix_from_root(forms, p, root)
    # The coefficient of q in T_p theta_Q is r_Q(p).
    first = [theta_coefficients(form, 1)[1] for form in forms]
    r_p = [sum(m*c for m, c in zip(row, first)) for row in matrix]
    principal = forms.index((1, 1, 6))
    other = forms.index((2, -1, 3))
    # For D=-23 the normalized theta difference is eta(tau) eta(23*tau).
    coefficient, remainder = divmod(r_p[principal] - r_p[other], 2)
    if remainder:
        raise ArithmeticError("nonintegral normalized theta difference")
    # Serre, On a theorem of Jordan §5.3: roots of X^3-X-1 mod p = a_p + 1.
    # This second calculation uses only the prime, independent of class forms.
    roots = cubic_root_count(p)
    if roots != coefficient + 1:
        raise ArithmeticError("independent cubic root count disagrees with the theta coefficient")
    return {"prime_bits": p.bit_length(), "discriminant": D, "forms": forms,
            "operator": matrix, "representations_of_prime": r_p,
            "eta_tau_eta_23tau_coefficient_at_prime": coefficient,
            "roots_of_X3_minus_X_minus_1_mod_prime": roots}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    chain = modes.add_parser("chain", help="generate neighbor matrices and verify their product")
    chain.add_argument("--discriminant", "-D", type=int, default=-23)
    chain.add_argument("--primes", nargs="+", type=int, default=[2, 2])
    chain.add_argument("--through", type=int, default=32)
    certified = modes.add_parser("certified", help="compute the exact operator at a certified large prime")
    certified.add_argument("file", type=Path, help="a discriminant -23 CM prime certificate")
    args = parser.parse_args(argv)
    try:
        if args.mode == "chain":
            report = cm_chain(args.discriminant, args.primes, args.through)
        else:
            report = certified_operator(json.loads(args.file.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
