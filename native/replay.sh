#!/bin/sh
set -eu
# Parameters are the source checkout, its configured native build, and the version.
src=$1
build=$2
version=$3
shift 3
case "$version" in
  4.7.2) lib=libseal.a; feature=-DVECTOR_ROTATIONS ;;
  4.1.2) lib=libseal-4.1.a; feature= ;;
  *) exit 2 ;;
esac
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
c++ -O3 -DNDEBUG -std=c++17 $feature -I"$src/native/src" -I"$build/native/src" "$dir/stencil.cpp" "$build/lib/$lib" -o "$tmpdir/stencil"
"$tmpdir/stencil" "$@"
