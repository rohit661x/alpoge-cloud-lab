# Rohit’s research lab

I use this workspace to investigate questions that can be answered with a proof, a reproducible experiment, or both. The first projects grew out of computational number theory and encrypted inference. Each entry below links to the evidence and says what you can check for yourself.

| Project | Question and result | Start here |
| --- | --- | --- |
| Rotation-key latency | When should an encrypted classifier upload two extra keys? A request-12 payoff observed on one Mac did not reproduce on a physical client/server pair. | [Standalone study, timings and replay](https://github.com/rohit661x/rotation-key-latency) |
| Finite-field certificates | How do you test arithmetic more than 10³⁸ steps into a recurrence? An exact order certificate gives a known-answer test for a cubic field used in Plonky3. | [Worked example](projects/number-theory/docs/FINITE-FIELDS.md) |
| Computational number theory | Which finite calculations can we check directly? A 1,024-bit prime certificate, quadratic-form computations and a Gaussian lattice example connect executable checks to precise statements. | [Code, examples and formal checks](projects/number-theory/) |

## Try one result

From a clone of this lab, with Python 3.11+ and no dependencies:

```sh
cd projects/number-theory
python3 goldilocks_order.py
```

The expected order is `340282366762482138508632908526633615363`. The verifier checks the prime factors and rules out every proper divisor that could be the order; it does not enumerate the cycle.

## Continue the work

I keep exploratory code with its question under [projects/](projects/). When a study has its own audience, evidence and replay, it can graduate to a separate repository. [Starting a study](docs/START-A-STUDY.md) gives the short brief I use to decide what is worth testing. The [artifact guide](docs/ARTIFACTS.md) explains citation, reuse and where older links point.

Replications, counterexamples and earlier references are useful contributions. [Open an issue](https://github.com/rohit661x/research-lab/issues/new) with the project, exact claim, and enough detail to check it. Findings here have different statuses; a passing test or public release is not peer review.
