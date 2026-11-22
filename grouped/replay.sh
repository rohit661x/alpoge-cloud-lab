#!/bin/sh
set -eu
src=$1
build=$2
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
c++ -O2 -std=c++17 -I"$src/native/src" -I"$build/native/src" "$here/grouped.cpp" "$build/lib/libseal.a" -o "$tmpdir/grouped"
"$tmpdir/grouped"
