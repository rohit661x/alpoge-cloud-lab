#!/usr/bin/env bash
# Reproduce the standard-library Python and Lean checks from an extracted ZIP.
set -euo pipefail
cd "$(dirname "$0")"
project_dir="$PWD"
build_dir="$project_dir/.alpoge-build"
stage=${1:-core}
case "$stage" in python|core|bridge) ;; *) echo "Usage: bash cloud-setup.sh [python|core|bridge]" >&2; exit 2 ;; esac
mkdir -p "$build_dir"
python3 -B -m unittest discover -s . -v
python3 -B zeta_prime_density.py cm certified cm_prime_1024.json > "$build_dir/cm-verified.json"
python3 -B gaussian_transfer.py --norm 5 > "$build_dir/norm-five.json"
python3 -B gaussian_transfer.py --norm 5 --lean > "$build_dir/GaussianData.lean"
cmp "$build_dir/GaussianData.lean" lean/GaussianData.lean
if [[ "$stage" == python ]]; then exit 0; fi

matches_lean() {
  command -v lean >/dev/null && lean --version | grep -Eq 'version 4\.33\.1([ ,(-]|$)'
}
if ! matches_lean; then
  case "$(uname -s)/$(uname -m)" in
    Linux/x86_64) platform=linux; digest=890afd185370f85666025b883914ab4f4b339136f8c96167b69cfb62aecaf235 ;;
    Linux/aarch64) platform=linux_aarch64; digest=f7353a8b2a8741c84558523e450556f9a1c45e3cafcf54399ce68c6a24c55f07 ;;
    Darwin/arm64) platform=darwin_aarch64; digest=88c45aad985b5d2a8d925fe10bd1296bd35f66f408480ab182d3facccd065a9d ;;
    Darwin/x86_64) platform=darwin; digest=93c475c1600360df35471bf6ed1c7fe118d7fb42be6915ead67724f7ad58dfaf ;;
    *) echo "Supply Lean 4.33.1 on PATH for this platform." >&2; exit 1 ;;
  esac
  distribution=lean-4.33.1-$platform
  export PATH="$build_dir/$distribution/bin:$PATH"
  if ! matches_lean; then
    for cmd in curl zstd tar; do command -v "$cmd" >/dev/null || { echo "Install $cmd and retry." >&2; exit 1; }; done
    archive="$build_dir/$distribution.tar.zst"
    url="https://github.com/leanprover/lean4/releases/download/v4.33.1/$distribution.tar.zst"
    curl -fL --retry 3 -C - "$url" -o "$archive"
    python3 - "$archive" "$digest" <<'PY'
import hashlib
from pathlib import Path
import sys
path, expected = sys.argv[1:]
digest = hashlib.sha256()
with Path(path).open("rb") as handle:
    for block in iter(lambda: handle.read(2**20), b""):
        digest.update(block)
if digest.hexdigest() != expected:
    raise SystemExit("Lean release checksum mismatch: discard the partial download and retry.")
PY
    zstd -dc "$archive" | tar -xf - -C "$build_dir"
    matches_lean
  fi
fi
lean --version
cd "$build_dir"
cp "$project_dir/lean/GaussianShell.lean" .
lean -o GaussianData.olean GaussianData.lean
LEAN_PATH="$build_dir" lean -o GaussianShell.olean GaussianShell.lean
echo "Lean checked the generated Gaussian shell."
if [[ "$stage" == bridge ]]; then
  cd "$project_dir/lean-bridge"
  python3 -B fetch_archive.py
  export MATHLIB_CACHE_DIR="$build_dir/mathlib-cache"
  python3 -B shallow_deps.py
  lake exe cache get Mathlib
  lake build Formalism.ThetaLiftIndependence.ThetaOrbitSums.OrbitSum
  sh check-instance.sh
  echo "Lean checked the specialization of the archive's orbitSum theorem."
fi
