# Gaussian embedding check

The starting project is preserved in `inputs/alpoge-lab.zip`, SHA-256 `0a64dd290eaae88fe5a82115867e5dcec69d650b9bc6a08438388497e75fa922`. The cloud workflow unpacks and tests that archive before running the new work.

Run `bash cloud-setup.sh python` to reproduce the Python calculation and generate the signed coordinates. Run `bash cloud-setup.sh core` for the Lean certificate and `bash cloud-setup.sh bridge` for the application of the pinned archive lemma. Each stage includes the earlier checks. The installer uses a matching Lean 4.33.1 on PATH or downloads the matching official release into the project. It needs Python 3.8+, bash, curl, tar, and zstd. The bridge also requires Git, network access to the pinned Mathlib dependencies and cache, and space for compiled Mathlib.

The source lattice is the Gaussian line with Hermitian form [5]. A linear map into the standard Gaussian plane is determined by the image v of 1. Its pullback Hermitian form is [5] exactly when the sum of the four squared integer coordinates of v is 5. Source units identify the maps with images v, iv, −v and −iv. The expected counts are 48 embeddings and 12 orbits. This convention quotients only by source units.

The core Lean file checks the Python-generated lists. The archive bridge applies the finite orbit-sum theorem to a separately defined norm-five shell. This proves a finite identity used in the formalization. The construction of the global automorphic theta kernel requires further geometric data.
