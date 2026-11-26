# Prime completions of a fixed 112-bit prefix

Fix any 112-bit prefix beginning in 1. Among the 256-bit integers with those leading bits, at least **119364572746971480821742986104065588231880** are prime, assuming the Riemann hypothesis for the ordinary zeta function. This holds individually for each of the 2^111 prefixes, including the all-ones prefix immediately below 2^256.

The connection to Alpöge’s announced theorem is through its ordinary Riemann hypothesis conclusion. Substituting that conclusion into Schoenfeld’s Corollary 1 gives the analytic inequality used here. The integer certificate checks the specialization and rounding. [Lean community verification report](https://leanprover-community.github.io/blog/posts/riemann-hypothesis/) · [Schoenfeld, Corollary 1, equation (6.18)](https://doi.org/10.1090/S0025-5718-1976-0457374-X)

## Proof

Write W = 2^144. A prefix with integer value j determines the interval [A,B), where A = jW and B = A + W. Both endpoints are even and composite, so its prime count is C = π(B) − π(A). Both exceed 2657. Under RH, Schoenfeld bounds the absolute difference between π(x) and li(x) by √x log(x)/(8π) at each endpoint. The integral of 1/log(t) from A to B is at least W/log(B).

Throughout the interval √x ≤ 2^128 and log(x) < L = 896/5. Indeed log(2) < 7/10, since the exponential series through its positive cubic term at 7/10 already exceeds 2. Using π > 3 to bound both errors gives

    C > W/L − 2^128 L/12 = (300 · 2^144 − 896² · 2^128)/(60 · 896).

The count is an integer, so rounding the displayed rational down and adding one gives the stated lower bound K. The verifier checks (K−1)d ≤ n < Kd with the numerator n and denominator d displayed above.

## Search budget

There are 2^143 odd candidates per prefix. Since 94K > 2^143, each independent uniform odd draw with replacement succeeds with probability strictly greater than 1/94. Thus the mean number of draws through the first prime is below 94. The probability of no prime in 8296 draws is below (93/94)^8296 < 2^(−128), where the final inequality is checked by integer exponentiation. Success denotes actual primality. This budget counts candidate draws before sieving and assumes that the primality decision is correct.

Run `python3 rh_prefix.py` and `python3 -m unittest discover -v` in this directory. The tests independently check the cleared integer inequalities and compare the generalization with exact sieve counts in smaller prefix intervals.
