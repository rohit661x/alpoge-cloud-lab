#!/usr/bin/env bash
set -u
f=stage-replication/codespace-evidence/termination-diagnostics.txt
{
  date -u
  uptime
  ps -Ao pid,comm,rss --sort=-rss | head -18
  grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo
  for m in /sys/fs/cgroup/memory.events /sys/fs/cgroup/memory.pressure /proc/pressure/memory; do test ! -r "$m" || { echo "$m"; cat "$m"; }; done
  pgrep -a -x earlyoom || true
  sudo dmesg | grep -Ei 'earlyoom|oom.kill|out.of.memory|killed process' | tail -12 || true
  command -v journalctl >/dev/null && sudo journalctl --since '25 min ago' --no-pager | grep -Ei 'earlyoom|out.of.memory|oom.kill|killed process|stage_ninth' | tail -25 || true
  df -B1 /tmp
} >"$f" 2>&1
git add "$f" && git commit -qm 'Preserve post-termination Linux memory diagnostics' && git push origin HEAD
