"""Compare the nine-point affine action with independently factored polynomials."""
import argparse
import gzip
import json
from collections import Counter
from itertools import permutations, product
from math import isqrt
from pathlib import Path

from cubic_crypto_lab import sqrt_mod
from cubic_lift import cardano_character
from cubic_study import power
from matrix_periods import CURVE, GOLD, ROOTS


def cycles(image):
    """Cycle lengths of a permutation of 0,...,len(image)-1."""
    remaining = set(range(len(image)))
    lengths = []
    while remaining:
        first = next(iter(remaining))
        i = first
        size = 0
        while i in remaining:
            remaining.remove(i)
            size += 1
            i = image[i]
        if i != first:
            raise ValueError("map is not a permutation")
        lengths.append(size)
    return tuple(sorted(lengths))


def group_weights():
    """Enumerate AGL actions of the 108 elements on f, q and H roots."""
    points = [(a, b, (-a-b) % 3) for a, b in product(range(3), repeat=2)]
    point_index = {v: i for i, v in enumerate(points)}
    weights = Counter()
    actions = set()
    for perm in permutations(range(3)):
        for sign in (1, -1):
            for shift in points:
                image = tuple(point_index[tuple((c + sign*v[j]) % 3
                                          for c, j in zip(shift, perm))] for v in points)
                # The class modulo the diagonal is the difference of the first
                # two entries. Compute the induced permutation from all nine points.
                quotient = {}
                for v, target in zip(points, image):
                    w = points[target]
                    source_class = (v[0] - v[1]) % 3
                    target_class = (w[0] - w[1]) % 3
                    if quotient.setdefault(source_class, target_class) != target_class:
                        raise ArithmeticError("action does not descend to the quotient")
                q_cycles = cycles(tuple(quotient[i] for i in range(3)))
                weights[sign % 3, cycles(perm), q_cycles, cycles(image)] += 1
                actions.add(image)
    if len(actions) != 108:
        raise ArithmeticError("affine group action is not faithful")
    return weights


def primes_through(bound):
    sieve = bytearray(b"\x01") * (bound + 1)
    for d in range(2, isqrt(bound) + 1):
        if sieve[d]:
            sieve[d*d::d] = bytes((bound-d*d)//d+1)
    return (n for n in range(2, bound+1) if sieve[n] and n not in (3, 23))


def check_file(path, bound):
    theoretical = group_weights()
    actual = Counter()
    eligible = cubes = 0
    ntt_counts = {k: Counter() for k in (1, 4, 8, 12)}
    with (gzip.open if path.suffix == ".gz" else open)(path, "rt", encoding="utf-8") as stream:
        marker, meta = json.loads(next(stream))
        h_order, h_transitive_id, radical_order, disc_f, disc_q, order, roots, root_orders = meta
        if (marker, h_order, radical_order, disc_f, disc_q, order) != (
                "metadata", 108, 108, -23, 621, GOLD**2 + GOLD + 1):
            raise ValueError("PARI disagrees with the number fields or Goldilocks certificate")
        if list(zip(roots, root_orders)) != [(r, (CURVE - 1)//index) for r, index in ROOTS]:
            raise ValueError("PARI disagrees with the Curve25519 root orders")
        for expected in primes_through(bound):
            p, f, q, h = json.loads(next(stream))
            key = (p % 3, tuple(f), tuple(q), tuple(h))
            if p != expected or key not in theoretical:
                raise ValueError(f"unexpected prime or Frobenius action at {p}: {key}")
            if p > 23 and (h.count(1) == 1) != (p % 3 == 2 and pow(-23,(p-1)//2,p) == 1):
                raise ValueError(f"biquadratic class disagrees with the one-root condition at {p}")
            actual[key] += 1
            ntt_classes = [k for k in ntt_counts if p % (1 << k) == 1]
            for k in ntt_classes:
                ntt_counts[k]["primes"] += 1
            if p % 3 == 1 and f == [3]:
                eligible += 1
                is_cube = power((0, 1, 0), (p*p+p+1)//3, p) == (1, 0, 0)
                scalar = cardano_character(p, sqrt_mod(-23, p))
                if (scalar == 1) != is_cube:
                    raise ValueError(f"scalar cubic-residue test disagrees at {p}")
                if (q.count(1), h.count(1)) != ((3, 3) if is_cube else (0, 0)):
                    raise ValueError(f"degree-three, degree-nine and exponent tests disagree at {p}")
                cubes += int(is_cube)
                for k in ntt_classes:
                    ntt_counts[k]["eligible"] += 1
                    ntt_counts[k]["cubes"] += int(is_cube)
        if json.loads(next(stream)) != ["complete", bound] or stream.read().strip():
            raise ValueError("unexpected PARI record count or incomplete census")
    return dict(bound=bound, excluded_ramified_primes=[3, 23], checked_primes=sum(actual.values()),
                eligible=eligible, cubes=cubes, noncubes=eligible-cubes,
                primes_one_mod_power_of_two=ntt_counts,
                h_galois_group_order=h_order, h_transitive_group=h_transitive_id,
                radical_galois_group_order=radical_order, actions=[
                    dict(p_mod_3=k[0], f=k[1], q=k[2], h=k[3],
                         group_elements=theoretical[k], primes=actual[k])
                    for k in sorted(theoretical)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pari_output", type=Path)
    parser.add_argument("--bound", type=int, default=1_000_000)
    args = parser.parse_args()
    print(json.dumps(check_file(args.pari_output, args.bound), indent=2))
