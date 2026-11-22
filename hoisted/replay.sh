#!/bin/sh
set -eu
src=$1
build=$2
out=$3
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$out"
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
c++ -O3 -DNDEBUG -std=c++17 -I"$src/native/src" -I"$build/native/src" "$dir/stencil.cpp" "$build/lib/libseal.a" -o "$tmpdir/stencil"
for idx in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    "$tmpdir/stencil" "$idx" > "$out/process-$idx.csv"
done
python3 "$dir/summarize.py" "$out"
