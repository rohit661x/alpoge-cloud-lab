# A 256-bit public field in the certified trace window

Set s=2¹²⁸, k=s−255 and p=ks+1=2²⁵⁶−255·2¹²⁸+1. This p lies strictly between 2²⁵⁶−2¹⁴² and 2²⁵⁶. It is a prime where the trace polynomial H has exactly one root and the Perrin cubic X³−X−1 is irreducible. Its multiplicative group has a primitive 2¹²⁸-th root ω=3ᵏ mod p. The lab supplies a radix-two number-theoretic transform (NTT) over this field.

The primality proof uses a single exact congruence. The modular power 3^((p−1)/2) equals −1. For any prime divisor r of p, the order of 3 modulo r divides p−1 but does not divide (p−1)/2. Since k is odd, that order is divisible by 2¹²⁸. Thus r≥2¹²⁸+1>√p, proving p prime. The same power identity gives ω^(2¹²⁷)=−1, so ω has exact order 2¹²⁸. Polynomial gcds with Xᵖ−X verify both root counts independently of the analytic argument.

The prime is the **largest** below 2²⁵⁶ satisfying p≡1 modulo 2¹²⁸ and p≡2 modulo 3. Every larger candidate must equal 2²⁵⁶−d·2¹²⁸+1 for d in {3,6,…,252}. The verifier checks that each of these 84 integers fails the base-2 Fermat identity, proving each composite. The cloud evidence lists all 84 residues.

The example is selected by trying odd d divisible by 3 in p=(2¹²⁸−d)2¹²⁸+1 and screening for the specified field properties. Its exact certificates stand independently of the population bound. The interval theorem counts the one-root primes; the high two-adicity and the irreducible Perrin cubic are additional properties proved for this individual example. The NTT implementation targets reproducible arithmetic tests. No timing or protocol-security result is claimed.

Run `python3 ntt_fixture.py` to check the certificates and a 256-point cyclic convolution against schoolbook multiplication. Import `transform` from `ntt_fixture` to run the forward and inverse transforms. The cloud suite also checks the output against the defining Fourier sum for small lengths.
