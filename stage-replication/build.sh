#!/usr/bin/env bash
set -euo pipefail
base=$(cd "$(dirname "$0")" && pwd)
dst=$(mkdir -p "$1" && cd "$1" && pwd)
fetch() {
  if [[ ! -d "$3/.git" ]]; then
    git init -q "$3"
    git -C "$3" fetch -q --depth 1 "$1" "$2"
    git -C "$3" checkout -q --detach FETCH_HEAD
  fi
  test "$(git -C "$3" rev-parse HEAD)" = "$2"
}
fetch https://github.com/lorenzorovida/LowMemoryFHEResNet20.git c818bd3519794191dfcf78c252bc209ee30e3e4a "$dst/app"
fetch https://github.com/openfheorg/openfhe-development.git a7415334b8fc033501809d9547be92fb90228c0a "$dst/openfhe"
git -C "$dst/openfhe" submodule update --init --depth 1 third-party/cereal
cmake -S "$dst/openfhe" -B "$dst/libbuild" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$dst/install" -DBUILD_UNITTESTS=OFF -DBUILD_BENCHMARKS=OFF -DBUILD_EXAMPLES=OFF -DGIT_SUBMOD_AUTO=OFF -DWITH_OPENMP=ON
cmake --build "$dst/libbuild" --parallel "${BUILD_JOBS:-2}"
cmake --install "$dst/libbuild"
for project in harness arms/old8 arms/old9 arms/parents arms/common11; do
  cmake -S "$base/$project" -B "$dst/$project" -DCMAKE_PREFIX_PATH="$dst/install" -DAPP="$dst/app" -DPLANS="$base/plans" -DCMAKE_BUILD_TYPE=Release
  cmake --build "$dst/$project" --parallel "${BUILD_JOBS:-2}"
done
"${CXX:-c++}" -std=c++17 -O3 "$base/reference.cpp" -o "$dst/reference"
"${CXX:-c++}" -std=c++17 -O3 -I"$dst/app/src" "$base/pack.cpp" -o "$dst/pack"
