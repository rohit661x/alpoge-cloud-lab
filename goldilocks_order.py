"""Verify an exact multiplicative order certificate using Python 3.8+."""
from math import gcd, isqrt, prod

P = 18446744069414584321
N = P**2 + P + 1
FACTORS = (3, 937, 724723, 167034643597991036904547663171)
# Complete factorizations of n-1 and full-order integer witnesses modulo n.
LUCAS = {
    P: (7, {2: 32, 3: 1, 5: 1, 17: 1, 257: 1, 65537: 1}),
    FACTORS[-1]: (2, {2: 1, 3: 5, 5: 1, 5821: 1, 1039033: 1,
                        11365102077808483: 1}),
    11365102077808483: (3, {2: 1, 3: 2, 19: 1, 8627: 1, 3852010273: 1}),
}
RESIDUES = (
    (4294967295, 0, 0),
    (2296356816046148297, 7363194806461452677, 1318824000890520107),
    (10014784525102553761, 6743920291608311130, 2440758390240611205),
    (10476926443089750167, 704602827531774410, 5602663535673119219),
)
ONE = (1, 0, 0)
X = (0, 1, 0)


def prime(n):
    """Prove primality by trial division at leaves, Lucas above them."""
    if n not in LUCAS:
        if n > 4_000_000_000:
            raise ValueError("missing prime certificate")
        return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))
    a, factors = LUCAS[n]
    return (prod(q**e for q, e in factors.items()) == n-1
            and pow(a, n-1, n) == 1
            and all(prime(q) and gcd(pow(a, (n-1)//q, n)-1, n) == 1
                    for q in factors))


def mul(u, v):
    a, b, c = u
    d, e, f = v
    high = b*f+c*e
    top = c*f
    return ((a*d+high) % P, (a*e+b*d+high+top) % P,
            (a*f+b*e+c*d+top) % P)


def x_power(k):
    acc = ONE
    for bit in bin(k)[2:]:
        acc = mul(acc, acc)
        if bit == "1":
            acc = mul(acc, X)
    return acc


def verify():
    """Return True exactly when all steps of this certificate check."""
    if not prime(P) or prod(FACTORS) != N or not all(map(prime, FACTORS)):
        return False
    # A cubic is irreducible iff it has no prime-field root, equivalently
    # X^p-X is a unit in the quotient. Test its multiplication determinant.
    a, b, c = x_power(P)
    h = (a, b-1, c)
    (d, e, f), (g, i, j), (k, l, m) = (mul(h, v) for v in (ONE, X, (0, 0, 1)))
    det = d*(i*m-j*l)-e*(g*m-j*k)+f*(g*l-i*k)
    return (det % P != 0 and x_power(N) == ONE
            and all(x_power(N//q) == r and r != ONE
                    for q, r in zip(FACTORS, RESIDUES))
            and len(RESIDUES) == len(FACTORS))


if __name__ == "__main__":
    if not verify():
        raise SystemExit("certificate failed")
    print(f"Verified multiplicative order {N} at p={P}")
