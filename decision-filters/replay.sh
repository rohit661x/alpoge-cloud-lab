#!/bin/sh
set -eu
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
src=$1
build=$2
out=$3
mkdir -p "$out"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
c++ -O3 -DNDEBUG -std=c++17 -I"$src/native/src" -I"$build/native/src" "$dir/filters.cpp" "$build/lib/libseal.a" -o "$tmp/filters"
for i in 0 1 2 3 4 5 6 7 8 9; do "$tmp/filters" "$i" > "$out/process-$i.csv"; done
python3 "$dir/summarize.py" "$out"
