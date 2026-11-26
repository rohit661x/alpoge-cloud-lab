"""A 256-bit public transform field inside the certified trace window."""
import argparse
import json

from alpoge_cm_frobenius import cubic_root_count
from cubic_trace_criterion import H, root_count


TWO_ADICITY = 128
COFACTOR = (1 << TWO_ADICITY) - 255
P = (COFACTOR << TWO_ADICITY) + 1
WITNESS = 3
OMEGA = pow(WITNESS, COFACTOR, P)


def verify_parameters():
    """Certify primality and exact order without probabilistic prime tests."""
    radix = 1 << TWO_ADICITY
    if not (0 < COFACTOR < radix and COFACTOR % 2 == 1 and P == COFACTOR*radix+1):
        raise ArithmeticError("invalid Proth shape")
    if pow(WITNESS, (P-1)//2, P) != P-1:
        raise ArithmeticError("Proth primality witness failed")
    if pow(OMEGA, radix, P) != 1 or pow(OMEGA, radix//2, P) != P-1:
        raise ArithmeticError("root of unity order failed")
    if not (2**256-2**142 < P < 2**256 and P % 3 == 2 and pow(-23, (P-1)//2, P) == 1):
        raise ArithmeticError("prime outside the certified window or residue class")
    if cubic_root_count(P) != 0 or root_count(H,P) != 1:
        raise ArithmeticError("unexpected Perrin or trace polynomial factorization")
    # These are all larger candidates with the two congruences, including
    # even d. A failing Fermat identity proves each composite.
    excluded = []
    for d in range(3, 255, 3):
        candidate = (1 << 256) - (d << 128) + 1
        residue = pow(2, candidate - 1, candidate)
        if residue == 1:
            raise ArithmeticError("larger candidate lacks its compositeness witness")
        excluded.append([d, residue])
    return dict(prime=P, larger_composite_witnesses=excluded, cofactor=COFACTOR, proth_witness=WITNESS, two_adicity=TWO_ADICITY,
                root_of_unity=OMEGA, perrin_roots=0, trace_roots=1)


def transform(values, inverse=False):
    """Radix-two NTT over the public field, in natural coefficient order."""
    out = [v % P for v in values]
    n = len(out)
    if n == 0 or n & (n-1) or n > 1 << TWO_ADICITY:
        raise ValueError("transform length must be a supported power of two")
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            out[i], out[j] = out[j], out[i]
    width = 2
    while width <= n:
        step = pow(OMEGA, (1 << TWO_ADICITY)//width, P)
        if inverse:
            step = pow(step, -1, P)
        half = width // 2
        for start in range(0, n, width):
            w = 1
            for j in range(start, start+half):
                a, b = out[j], out[j+half] * w % P
                out[j], out[j+half] = (a+b) % P, (a-b) % P
                w = w * step % P
        width *= 2
    if inverse:
        scale = pow(n,-1,P)
        out = [x*scale % P for x in out]
    return out


def verify_convolution():
    n = 256
    a = [(i**3-11*i+2) % P for i in range(n)]
    b = [(i**2 + 17*i - 4) % P for i in range(n)]
    result = transform([x*y % P for x,y in zip(transform(a),transform(b))], inverse=True)
    direct = [sum(a[j]*b[(i-j) % n] for j in range(n)) % P for i in range(n)]
    if result != direct:
        raise ArithmeticError("transform disagrees with direct cyclic convolution")
    return n


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    report = verify_parameters()
    report["direct_convolution_length"] = verify_convolution()
    print(json.dumps(report, indent=2))
