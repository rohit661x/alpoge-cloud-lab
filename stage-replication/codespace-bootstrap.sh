#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
mkdir -p stage-replication/codespace-evidence
e=stage-replication/codespace-evidence
{
  date -u
  uname -sm
  lscpu | grep -E 'Architecture|CPU\(s\)|Model name|Hypervisor'
  nproc
  for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.swap.max; do
    test ! -f "$f" || { echo "$f"; cat "$f"; }
  done
  grep -E 'MemTotal|MemAvailable|SwapTotal' /proc/meminfo
  df -B1 . /tmp
  df -T . /tmp
} | tee "$e/capacity.txt"
git add "$e/capacity.txt"
git commit -qm 'Record private Codespace capacity' && git push origin HEAD || true
sudo apt-get -qq update
sudo DEBIAN_FRONTEND=noninteractive apt-get -qq install -y cmake g++-12 libgomp1 git
export CC=gcc-12 CXX=g++-12 BUILD_JOBS=2
bash stage-replication/build.sh /tmp/stage-native >"$e/build.log" 2>&1 || {
  tail -35 "$e/build.log" >"$e/build-status.txt"
  git add "$e/build-status.txt" && git commit -qm 'Record failed native compile' && git push origin HEAD
  exit 1
}
{
  date -u
  sha256sum /tmp/stage-native/{harness/stage_native,arms/old8/stage_ninth,arms/old9/stage_ninth,arms/parents/stage_ninth,arms/common11/stage_portable,pack,reference}
  df -B1 . /tmp
} >"$e/build-status.txt"
git add "$e/build-status.txt"
git commit -qm 'Record working private Linux benchmark binaries' && git push origin HEAD
