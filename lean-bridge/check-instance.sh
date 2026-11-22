#!/bin/sh
set -eu
cd "$(dirname "$0")"
lib=.lake/build/lib/lean
cp ../lean/GaussianData.lean ../lean/GaussianShell.lean .
for module in Bridge GaussianData GaussianShell LinkedShell; do
  lake env lean -o "$lib/$module.olean" "$module.lean"
done
