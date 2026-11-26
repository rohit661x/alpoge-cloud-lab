# A 256-bit interval containing primes with exactly one trace root

Let H(U)=U⁹−18U⁶+54U³+27. The interval

    (2²⁵⁶ − 2¹⁴², 2²⁵⁶]

contains at least **2,716,342,439,235,134,011,632,130,820,349,336,797,735** primes for which H has exactly one root in the prime field. The integer upper bound from the same computation is 12,993,215,425,046,400,288,206,230,783,130,401,424,406. Its width is a fraction 2⁻¹¹⁴ of the upper endpoint. This is an analytic count certificate. The calculation uses the checked Dirichlet critical-line theorem and a published explicit prime-counting inequality.

## The exact prime set

Put q(t)=t³−6t−3. For p>23, H(U)=27q(U³/3−2), and H(0)≠0. When p≡1 modulo 3, multiplication by a primitive cube root of unity partitions the roots into orbits of three. When p≡2 modulo 3, U↦U³/3−2 permutes the prime field, so the root count agrees with that of q. The discriminant of q is 621=9·69. This cubic has exactly one root if and only if its Frobenius exchanges two of its three distinct roots. Its Vandermonde product changes sign precisely for an odd permutation, so this occurs if and only if 69 is a quadratic nonresidue modulo p. Write χ_D for the primitive quadratic character attached to the fundamental discriminant D. Since χ₆₉=χ₋₃χ₋₂₃ and χ₋₃(p)=−1 exactly when p≡2 modulo 3, the desired condition is

    χ₋₃(p) = −1 and χ₋₂₃(p) = +1.

This describes one element C of the four-element Galois group of B=Q(√−3,√−23). The corresponding density is 1/4. Only 3 and 23 ramify in B. Restricting the lower endpoint to at least 23 discards any exceptional reductions.

## Which formal theorem enters

The verified challenge statement LFunction_eq_zero_re places every zero in the open critical strip of every Dirichlet L-function on the critical line. Applying it to the three quadratic characters and the trivial character proves the required critical-line statement for ζ_B. Indeed abelian Artin factorization gives

    ζ_B(s) = ζ(s) L(s,χ₋₃) L(s,χ₋₂₃) L(s,χ₆₉).

All factors are holomorphic in the open critical strip. The conductor–discriminant formula gives |disc B|=3·23·69=4761, and [B:Q]=4. The deduction uses only the verified Dirichlet statement. Applying the same explicit theorem to the nonabelian normal closures for particular eligible Perrin-period classes requires additional zero bounds. The window proof and its Python implementation are mathematical deductions external to the Lean archive. [Sutherland's verification and exact challenge statements](https://math.mit.edu/~drew/grh/) · [Alpöge's announcement](https://alpo.ge/remark.pdf)

## Prime-count inequality

Let Π_C(x) count unramified rational primes at most x with Frobenius C, and let I(x)=∫₂ˣdt/log t (natural logarithm). Grenié and Molteni, Corollary 1.2, give the following for x≥2, on substituting |G|/|C|=4, n_B=4 and Δ_B=4761:

    |4Π_C(x) − I(x)| ≤ E(x),
    E(x) = √x [(1/(2π) + 3/log x) log 4761
               + 4 (log x/(8π) + 1/(4π) + 6/log x)].

This is the corollary's estimate for π_C, counting unramified primes without logarithmic weights or prime powers. Section 3.1 and Lemma 3.2 identify the critical-strip zeros used in their proof with zeros of the top field's zeta function. For 23≤a<b we have

    (b−a)/log b ≤ I(b)−I(a) ≤ (b−a)/log a.

Subtract the two endpoint inequalities, allowing errors of opposite signs; divide by four. The lower bound is the ceiling of ((b−a)/log b−E(a)−E(b))/4 and the upper bound is the floor of ((b−a)/log a+E(a)+E(b))/4, or any outward relaxation of these. [Grenié and Molteni, Corollary 1.2 and Lemma 3.2](https://sites.unimi.it/molteni/research/papers-pdf/44-molteni-An_explicit_Chebotarev_density_theorem_under_GRH.pdf)

## Numerical certificate

Run `python3 rh_trace_window.py` and `python3 -m unittest test_rh_trace_window.py` in this directory. The executable uses integers and fractions. For n=2ᵏy with 1≤y<2, it bounds log n=k log 2+log y. Set z=(y−1)/(y+1). The sum of the first 16 terms of 2Σⱼ z²ʲ⁺¹/(2j+1) is a lower bound for log y. The omitted tail is at most 2z³³/[33(1−z²)]. The case z=1/3 bounds log 2. The code rounds the resulting bounds outward to multiples of 10⁻¹² and uses the upper log for positive log terms and the lower log for inverse-log terms. Integer ceilings bound square roots. The rational 3.14 is a strict lower bound for π, for example from Machin's identity and the alternating arctangent series, π > 16(1/5−1/375)−4/239 > 3.14. Replacing π by this lower bound enlarges every error term. The final integer rounding occurs after forming lower and upper rational bounds for the count. Tests compare the modular characterization with direct polynomial evaluation for every prime between 23 and 2500 and the log enclosures with independently computed high-precision logarithms.

## Lean arithmetic check

`TraceWindowArithmetic.directed_rounding` checks the two square roots and the cleared integral and error inequalities by kernel evaluation. The common log bounds for the endpoints are 177445678223345/10¹² and 177445678223346/10¹². The upper bound for log 4761 is 8468213009195/10¹². Substitution of these constants and 314/100 for the lower bound on π gives exactly the fraction P/Q in the Lean source.

For x=a,b let iₓ=⌊1000 I(x)⌋. The analytic inequalities imply that 4000Π_C(x) is within the integer error ceiling of iₓ: flooring preserves both inequalities when the compared count and the error ceiling are integers. The difference i_b−i_a lies between the floor and ceiling of the scaled integral change. The theorem `classified_window_count` takes these endpoint and integral inequalities as hypotheses, and derives the displayed pair of integer bounds for Π_C(b)−Π_C(a). The analytic corollary, factorization of the zeta function, and logarithm-series enclosure are supplied by the written argument above. [Lean statement](../lean/TraceWindowArithmetic.lean)
