#!/bin/sh
set -eu
cd "$(dirname "$0")"
integration=${SEAL_INTEGRATION:-../../../allocator-next/integration}
src=${SEAL_SOURCE_DIR:-$integration/SEAL-current}
build=${SEAL_BUILD_DIR:-$integration/build-v4.7.2/seal-build}
"${CXX:-c++}" -std=c++17 -O3 -DNDEBUG -pthread -I"$src/native/src" -I"$build/native/src" load.cpp "$build/lib/libseal.a" -o load
echo 'process,round,position,route,format,keys,bytes,load_ns' > results.tmp
for process in 1 2 3 4 5 6 7 8 9 10; do
    ./load "$process" >> results.tmp
done
mv results.tmp results.csv
