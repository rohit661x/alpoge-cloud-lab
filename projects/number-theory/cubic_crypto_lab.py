"""Reproduce the public-field survey or walk the Goldilocks norm-one subgroup."""

import argparse
import json
from pathlib import Path

from alpoge_cm_certificate import verify_certificate
from alpoge_cm_forms import reduced_forms
from alpoge_cm_hecke import hecke_matrix_from_root
from cubic_study import power, study
from cubic_trace_criterion import H, brute_check, root_count
import goldilocks_order as gold


ROOT = Path(__file__).resolve().parent


def sqrt_mod(value, p):
    """Tonelli-Shanks for a nonzero square over a known odd prime field."""
    value %= p
    if not value or pow(value, (p - 1) // 2, p) != 1:
        raise ValueError("expected a nonzero quadratic residue")
    odd, k = p - 1, 0
    while odd % 2 == 0:
        odd //= 2
        k += 1
    nonresidue = 2
    while pow(nonresidue, (p - 1) // 2, p) == 1:
        nonresidue += 1
    c = pow(nonresidue, odd, p)
    t = pow(value, odd, p)
    r = pow(value, (odd + 1) // 2, p)
    while t != 1:
        i, u = 0, t
        while u != 1:
            u = u * u % p
            i += 1
        b = pow(c, 1 << (k - i - 1), p)
        c = b * b % p
        r = r * b % p
        t = t * c % p
        k = i
    if r * r % p != value:
        raise ArithmeticError("modular square root failed")
    return r


def cm_coefficient(p):
    """Compute a_p at D=-23 independently of polynomial factorization."""
    if pow(-23, (p - 1) // 2, p) == p - 1:
        return 0  # Inert primes give no index-p neighbors.
    forms = reduced_forms(-23)
    matrix = hecke_matrix_from_root(forms, p, sqrt_mod(-23, p))
    principal = forms.index((1, 1, 6))
    other = forms.index((2, -1, 3))
    # Only the principal class represents 1, twice. The theta difference is halved.
    return matrix[principal][principal] - matrix[other][principal]


def examine(record):
    p = int(record["modulus"])
    result = study(p)
    ap = cm_coefficient(p)
    if ap + 1 != result["gcd_degree"]:
        raise ArithmeticError("CM Hecke coefficient disagrees with polynomial gcd")
    result.update(id=record["id"], label=record["label"], eta_coefficient=ap)
    if result["factor_degrees"] == (3,) and p % 3 == 1:
        count = root_count(H, p)
        n = p * p + p + 1
        witness = power((0, 1, 0), n // 3, p)
        if (count, witness == (1, 0, 0)) not in ((0, False), (3, True)):
            raise ArithmeticError("trace criterion disagrees with cubic exponentiation")
        result.update(trace_polynomial_roots=count, norm_one_cube=(count == 3),
                      alpha_to_n_over_three=witness)
    return result


def field_survey(brute_bound=2000):
    records = json.loads((ROOT / "research/public_fields.json").read_text())
    certificate = json.loads((ROOT / "cm_prime_1024.json").read_text())
    verify_certificate(certificate)
    lab_record = dict(id="lab1024", label="Lab certified 1,024-bit prime",
                      modulus=str(certificate["n"]))
    if not gold.verify():
        raise ArithmeticError("Goldilocks exact-order certificate failed")
    counts = brute_check(brute_bound)
    return dict(public_panel=[examine(r) for r in records],
                certified_lab_field=examine(lab_record),
                goldilocks_norm_one_order=gold.N,
                goldilocks_order_factors=gold.FACTORS,
                small_prime_check=dict(through=brute_bound, cube=counts[0], noncube=counts[1]))


def walk(start, count):
    """Produce consecutive powers of X, indexed cyclically from the identity."""
    if start < 0 or count < 0:
        raise ValueError("start and count must be nonnegative")
    index = start % gold.N
    a, b, c = gold.x_power(index)
    for _ in range(count):
        yield index, (a, b, c)
        total = a + c
        a, b, c = c, total - gold.P if total >= gold.P else total, b
        index = (index + 1) % gold.N


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    survey = modes.add_parser("survey", help="emit the checked field panel and small-prime counts")
    survey.add_argument("--through", type=int, default=2000, help="inclusive exhaustive prime bound")
    step = modes.add_parser("walk", help="stream index and coefficient triple as JSON lines")
    step.add_argument("--start", type=int, default=0)
    step.add_argument("--count", type=int, default=8)
    args = parser.parse_args()
    if args.mode == "survey":
        if args.through < 7:
            parser.error("choose an inclusive bound of at least 7")
        print(json.dumps(field_survey(args.through), indent=2))
    else:
        if args.start < 0 or args.count < 0:
            parser.error("start and count must be nonnegative")
        for index, point in walk(args.start, args.count):
            print(json.dumps({"index": index, "point": point}))


if __name__ == "__main__":
    main()
