#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 fetch_archive.py
case "$(lean --version)" in
  *"version 4.33.1,"*) ;;
  *) echo "This archive requires Lean 4.33.1." >&2; exit 1 ;;
esac
export MATHLIB_CACHE_DIR="${MATHLIB_CACHE_DIR:-$(pwd)/.lake/mathlib-cache}"
python3 -B shallow_deps.py
lake exe cache get Mathlib
lake build Formalism.ThetaLiftIndependence.ThetaOrbitSums.OrbitSum
sh check-instance.sh
