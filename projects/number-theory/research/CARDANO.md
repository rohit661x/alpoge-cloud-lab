# A cubic-residue test using the classical Perrin signature

Suppose p≡1 mod 3 is a prime for which X³−X−1 is irreducible. The discriminant −23 is a nonzero square in Fₚ because Frobenius permutes the three roots cyclically and therefore fixes their Vandermonde product. Take either square root d of −23 in Fₚ. Write A(n) for the Perrin sequence (A(0),A(1),A(2))=(3,0,2). Each of the following is equivalent:

1. The order of a root α of X³−X−1 is prime to 3.
2. The cubic q(t)=t³−6t−3 splits in Fₚ.
3. The scalar γ=(3+d)/2 in Fₚ satisfies γ^((p−1)/3)=1.
4. The classic I-signature entry D=A(p−1) mod p satisfies D^((p−1)/3)=1.

For the equivalence of the first two statements, see the nine-choice Frobenius proof. For the remaining steps set γ′=(3−d)/2; then γ+γ′=3 and γγ′=8. For r³=γ in the algebraic closure, t=r+2/r satisfies t³−6t=γ+γ′. This gives a Frobenius-equivariant bijection from the three choices of r to the three q-roots: if r+2/r=s+2/s then r=s or rs=2, the latter forcing γ²=8 and γ=γ′, impossible since d≠0. A fixed t is therefore equivalent to an r∈Fₚ. Since Fₚ contains the cube roots of unity, one fixed point gives all three. The cyclic group Fₚ× gives the displayed powering test. Changing the orientation of d replaces γ by 8/γ and preserves cubic residuosity.

Adams and Shanks, equations (13) and (13a), identify the two middle entries of the I signature as D and −3−D, where D=A(p−1) and D²+3D+8=0 in Fₚ. Consequently D equals −γ or −γ′. The scalar −1 is a cube and γγ′=8 is a cube, proving the final equivalence, also for the opposite middle entry. This tests the 3-part alone. The excluded primes 2, 3 and 23 all fail p≡1 mod 3. No additional exceptional eligible primes occur. [Original paper](https://doi.org/10.1090/S0025-5718-1982-0658231-9)

The indexed search also included Perrin I-signatures with cubic residue, order and period terminology. In the original paper we verified equations (13), (13a), (32), (150) and Appendix I. Its examples already include both outcomes at eligible primes, with 151 designated I/21 and 163 designated I/3 (the denominator is the index in p²+p+1). We found no statement in the inspected sources identifying cubic residuosity of D with this 3-part. This is a bounded search and does not establish priority.
