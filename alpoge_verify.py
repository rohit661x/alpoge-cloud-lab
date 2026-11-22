#!/usr/bin/env python3
"""Replay Alpöge's exported Lean proof against the independent Mathlib challenge.

Get the two exports from https://math.mit.edu/~drew/grh/ and unpack them:
  zstd -d --long=27 challenge.ndjson.zst
  zstd -d --long=30 solution.ndjson.zst

The published comparison used con-leche at commit 5dc36dc1 (Lean v4.36.0):
  git clone https://github.com/leanprover/con-leche
  cd con-leche
  git checkout 5dc36dc1
  lake build con-leche

Pass the path to that trusted binary using --checker, or add it to PATH.
Allow roughly 70 GB of disk and 50 GB of RAM for the published setup.
The wrapper verifies both unpacked exports against Sutherland's SHA-256
manifest, then delegates kernel replay and statement comparison to con-leche.
The Python wrapper does not download files or build the checker.
"""

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess


# https://math.mit.edu/~drew/grh/SHA256SUMS (21 November 2026)
CHALLENGE = (350862970, "bd484ac9886a96f26b1d9a7a59ebd45b7a70d102c015d4f31f9302bbdd6ab2b9")
SOLUTION = (61570595788, "5ea74b912147c5c93cc2b6d70cc727cf908df2f62ac6a20480a3fa02f6be244e")
THEOREMS = (
    "riemannHypothesis",
    "riemannZeta_eq_zero_re",
    "LFunction_ne_zero_of_half_lt_re",
    "LFunction_eq_zero_re",
    "LFunction_eq_zero_re_of_isPrimitive",
)


def check_export(path, expected):
    """Check a regular, uncompressed export, using bounded memory."""
    size, sha256 = expected
    if not path.is_file():
        raise ValueError(f"Missing export file: {path}")
    if path.stat().st_size != size:
        raise ValueError(f"Expected an unpacked export of {size:,} bytes: {path}")
    digest = hashlib.sha256()
    print(f"Hashing {path.name} ({size:,} bytes)", flush=True)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != sha256:
        raise ValueError(f"SHA-256 mismatch for {path}")


def replay(checker, challenge, solution):
    """Run comparison and require the theorem acknowledgments in the pinned CLI."""
    lines_needed = {f"con-leche: theorem {t} justified by the solution" for t in THEOREMS}
    # The checker writes progress and verdicts on the same combined stream.
    command = [checker, "--compare", str(challenge), str(solution)]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, errors="replace") as process:
        for line in process.stdout:
            print(line, end="", flush=True)
            lines_needed.discard(line.rstrip())
        status = process.wait()
    if status:
        raise ValueError(f"con-leche ended with status {status}; replay did not pass")
    if lines_needed:
        raise ValueError("Incomplete checker verdict; expected confirmation of all five theorems")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("challenge", type=Path, help="unpacked challenge.ndjson")
    parser.add_argument("solution", type=Path, help="unpacked solution.ndjson")
    parser.add_argument("--checker", default="con-leche",
                        help="trusted con-leche executable built at commit 5dc36dc1")
    args = parser.parse_args(argv)
    checker = shutil.which(args.checker)
    if not checker:
        parser.error(f"Missing checker '{args.checker}'. See --help for the build instructions.")
    try:
        challenge = args.challenge.resolve()
        solution = args.solution.resolve()
        check_export(challenge, CHALLENGE)
        check_export(solution, SOLUTION)
        replay(checker, challenge, solution)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Replay failed: {exc}\n")
    print("con-leche accepted all five theorems against the pinned challenge.")


if __name__ == "__main__":
    main()
