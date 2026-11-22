"""Run a benchmark process on a Linux VM with cgroup-aware capacity admission."""
import os
from pathlib import Path
import signal
import subprocess
import time

CG = Path('/sys/fs/cgroup')
MIB = 1024**2

def values(path, delimiter=None):
    return {str(k).rstrip(':'): int(v.split()[0]) for k, v in
            (line.split(delimiter, 1) for line in path.read_text().splitlines())}

def memory():
    host = values(Path('/proc/meminfo'), ':')
    available = host['MemAvailable'] * 1024
    swap = (host['SwapTotal'] - host['SwapFree']) * 1024
    if (CG/'memory.current').exists():
        maximum = (CG/'memory.max').read_text().strip()
        if maximum != 'max':
            usage = int((CG/'memory.current').read_text())
            stat = values(CG/'memory.stat', ' ')
            reclaimable = max(0, stat['file'] - stat.get('shmem', 0) - stat.get('unevictable', 0))
            available = min(available, int(maximum) - usage + reclaimable)
        if (CG/'memory.swap.current').exists():
            swap = max(swap, int((CG/'memory.swap.current').read_text()))
    return available, swap

def run(command, log, cwd, env, estimate, journal):
    available, swap0 = memory()
    reserve = 640 * MIB
    record = dict(command=str(command[0]), estimate_bytes=estimate, available_before=available, swap_before=swap0)
    if available < estimate + reserve:
        journal(dict(record, status='admission-rejected'))
        raise RuntimeError(f'capacity admission: {available} available; {estimate} estimate plus {reserve} reserve')
    minimum, maximum_rss, maximum_threads = available, 0, 0
    start = time.monotonic()
    with log.open('w') as stream:
        process = subprocess.Popen(list(map(str, command)), cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        reason = None
        try:
            while process.poll() is None:
                available, swap = memory()
                minimum = min(minimum, available)
                try:
                    for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
                        if line.startswith('Threads:'):
                            maximum_threads = max(maximum_threads, int(line.split()[1]))
                        if line.startswith('VmRSS:'):
                            maximum_rss = max(maximum_rss, int(line.split()[1]) * 1024)
                except FileNotFoundError:
                    pass
                if available < reserve or swap > swap0:
                    reason = f'physical reserve or swap threshold crossed: available={available} swap={swap}'
                    os.killpg(process.pid, signal.SIGKILL)
                    break
                time.sleep(.5)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            rc = process.wait()
        journal(dict(record, status='complete' if rc==0 and reason is None else 'terminated', returncode=rc, reason=reason,
                     minimum_available=minimum, max_sampled_rss=maximum_rss, max_process_threads=maximum_threads, swap_after=memory()[1], seconds=time.monotonic()-start))
        if rc or reason:
            raise RuntimeError(f'process exit {rc} {reason or ""}, see {log}')
