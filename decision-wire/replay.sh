#!/bin/sh
set -eu
cd "$(dirname "$0")"
integration=${SEAL_INTEGRATION:-../../../allocator-next/integration}
src=${SEAL_SOURCE_DIR:-$integration/SEAL-current}
build=${SEAL_BUILD_DIR:-$integration/build-v4.7.2/seal-build}
"${CXX:-c++}" -std=c++17 -O2 -pthread -I"$src/native/src" -I"$build/native/src" wire.cpp "$build/lib/libseal.a" -o wire
./wire "${1:-blobs}" > results.tmp
mv results.tmp results.csv
