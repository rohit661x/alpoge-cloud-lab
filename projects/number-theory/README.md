# Computational number theory

This project combines exact finite-field arithmetic, computations on quadratic forms and limited checks related to a pinned external Lean formalization. The finite-field certificates do not depend on the Riemann hypothesis.

Run these commands **from this directory**, with Python 3.11+ and its standard library:

| Check | Command | What to look for |
| --- | --- | --- |
| Goldilocks order | `python3 goldilocks_order.py` | Exact subgroup order, independently checkable by testing its prime divisors. [Worked example](docs/FINITE-FIELDS.md) |
| Prime certificate | `python3 alpoge_cm_certificate.py verify cm_prime_1024.json` | Checks primality and the supplied quadratic-form representation for this particular integer. |
| Finite examples and regression suite | `bash cloud-setup.sh python` | Runs the Python suite and compares generated Gaussian data with the committed input. |

[Number-theory examples](docs/NUMBER-THEORY.md) · [Cubic-field results and prior art](research/RESULTS.md) · [Independent audit](research/DEEP_AUDIT.md) · [Lean bridge and optional dependencies](CLOUD.md)

A finite arithmetic witness, a local Lean specialization and a full replay of an external proof are different checks. The quick commands above perform only the finite checks. Original inputs and their provenance are retained under [inputs/](inputs/); none of these commands generates a production cryptographic key.
