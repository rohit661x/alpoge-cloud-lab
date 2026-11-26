# Prior art and fixed-panel observations

Serre’s *On a theorem of Jordan*, §5.3 and Notes §5.3, derives the root counts for this exact polynomial. For p distinct from 23, a quadratic nonresidue modulo 23 gives one root. For quadratic residues, representation by x²+xy+6y² gives three roots, while representation by 2x²+xy+3y² gives zero. The paper also relates the counts to the Fourier coefficients of η(z)η(23z) and identifies the splitting field as the Hilbert class field of Q(√−23). [Serre](https://www.math.mcgill.ca/goren/SeminarOnCohomology/Serre.pdf)

Adams and Shanks’ 1982 paper studies signatures of cubic recurrences including the Perrin sequence. Its characteristic polynomial is X³−X−1. The power sums of its three roots give initial values 3, 0, 2 and recurrence P(n)=P(n−2)+P(n−3). [Adams and Shanks](https://doi.org/10.1090/S0025-5718-1982-0658231-9)

Plonky3 implements this exact cubic extension over Goldilocks and supplies Sage code identifying 2+a as a multiplicative generator. [Goldilocks implementation](https://github.com/Plonky3/Plonky3/blob/0d803737b681774186cd283b1fd2d8e493655c82/goldilocks/src/extension.rs#L96-L106)

In the ten-field panel, the BLS12-381 scalar and Curve25519 base moduli both reduce to 8 modulo 23, but the cubic is irreducible over the first and splits completely over the second. Across the Pasta cycle it is irreducible over Pallas base and has degrees 1+2 over Vesta base. These are finite illustrations of Serre’s classification. We selected named fields for recognizability and reproducibility. The observed counts have no sampling interpretation. The registry stores unique decimal moduli with one or more primary source URLs per row.

## Search for exact precedents

Indexed web searches used the exact decimal value 340282366762482138508632908526633615363, its largest prime factor 167034643597991036904547663171, Goldilocks/Polygon/Plonky/Perrin period and norm-one terminology, and expressions for x⁹−18x⁶+54x³+27. In these results we found no publication identifying α = X mod (X³−X−1) as a generator of the Goldilocks norm-one subgroup, or giving that specific degree-nine polynomial in this setting. Plonky3’s pinned lines 96–106 explicitly use 2+α for the full multiplicative group. A separate implementation also names the Goldilocks extension. Indexing, notation changes and equivalent defining polynomials limit what this search can establish. [Goldilocks implementation by Zhenfei Zhang](https://github.com/zhenfeizhang/Goldilocks)
