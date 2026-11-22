# Number-theory project

Open this directory as a trusted local Codex project. It contains the Python programs and a hidden `.codex/` directory with the project settings and agent definitions. A new local chat reads the project configuration. Use `gpt-6.2-astra` for the primary session and every delegated role. If the client cannot use the requested model, report the blocker before dispatch.

## Kickoff

Paste this into a new project chat, replacing the bracketed text with the actual task.

> Lead the number-theory team on [specific change or question]. Delegate planning to orchestrator, dispatch the applicable specialists in parallel, and have independent_reviewer check the integrated result. Run the affected commands and report the exact calculation, observed checks, and any proof replay still pending.

## Coordination

1. **Plan.** The primary session gives `orchestrator` the user request and asks for a short plan with the mathematical claim, affected files, dependencies and acceptance checks. The primary session dispatches workers so clients with one level of delegation can use the same workflow.
2. **Implement.** Give `lean_provenance` ownership of `alpoge_verify.py` and `alpoge_local.py`, including the source mapping for each local-ring hypothesis. Give `theta_implementation` ownership of `alpoge_theta.py` and `vector_chain.json`. Give `prime_numerics` ownership of `alpoge_prime_sum.py` and `zeta_prime_density.py`. Delegate only work relevant to the request. Agree on ownership of any additional files before concurrent edits. Send the verified declaration and hypotheses to each worker whose calculation depends on them.
3. **Review.** Collect paths changed, commands, results and assumptions from each worker. Run `independent_reviewer` against the integrated files. Have the original owner address each reproducible finding and rerun the affected checks.
4. **Verify and deliver.** The primary session runs the affected entry points from this directory and records evidence for each claim. Separate exact finite values, floating-point estimates, source-level correspondence and actual checker results. Identify missing inputs explicitly.

## Reproducible checks

- The theta specialist owns the CM form and neighbor modules. The prime specialist owns the public prime certificate. For a change at their boundary, have the independent reviewer check both the representation and the resulting operator. The orchestrator integrates them through `alpoge_cm.py`.
- `python3 zeta_prime_density.py cm certified cm_prime_1024.json` verifies the bundled prime certificate and gives representation counts [0, 2, 2] and the eta-product coefficient −1. `python3 zeta_prime_density.py cm chain -D -23 --primes 2 2 --through 32` checks repeated applications against direct lattice counts.

- `python3 -m unittest -v` runs the project regression suite.
- `python3 zeta_prime_density.py theta --vector vector_chain.json` returns the exact vector (3, 5/4, 1). The denominator product 24 scales the vector to (72, 30, 24).
- `python3 zeta_prime_density.py local --prime 3 --e 1` verifies the minor in ℤ[√3]. Multiplying its quotient 9280 + 5319√3 by √3 gives 15957 + 9280√3.
- `python3 alpoge_theta.py --gaussian 2 1` counts eight vectors of norm one. The standard lattice has automorphism order 32 and contributes the exact coefficient 1/4 with input form one.
- `printf '%s\n' '{"input":[2,3],"steps":[{"stabilizers":[2,3],"kernel":[[1],[4]]}]}' | python3 alpoge_theta.py -` gives 5. Scaling by the product of weight denominator LCMs yields 30.
- `python3 alpoge_prime_sum.py 4` gives Sz(4) = log(2) + log(3)/3. Include nearby noninteger scales when changing the inclusive prime-power cutoff.
- `python3 zeta_prime_density.py --bits 8` compares the estimate with the exact count of 23 primes among 64 odd eight-bit candidates.
- `python3 alpoge_verify.py --help` lists the export and checker prerequisites. To run a full replay with prepared inputs, use `python3 alpoge_verify.py /path/to/challenge.ndjson /path/to/solution.ndjson --checker /path/to/con-leche`. Report a local proof replay only after the pinned exports pass the manifest checks and the checker accepts all required declarations. Distinguish published replay evidence from the result of this run.

Custom role definitions and model precedence follow the [Codex subagent configuration guide](https://learn.chatgpt.com/docs/agent-configuration/subagents).
