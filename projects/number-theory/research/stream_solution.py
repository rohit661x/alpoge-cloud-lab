"""Check both hashes of the MIT solution from a single compressed stdin stream.

curl --fail --location https://math.mit.edu/~drew/grh/solution.ndjson.zst |
    python3 stream_solution.py
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
import sys

COMPRESSED = (7699933588, "61a8938ad5f5e57397c1c0e3b954916af546d9004ade01c3555744a681b05381")
RAW = (61570595788, "5ea74b912147c5c93cc2b6d70cc727cf908df2f62ac6a20480a3fa02f6be244e")

def consume(source, destination=None):
    h = hashlib.sha256()
    size = 0
    try:
        for block in iter(lambda: source.read(4 << 20), b""):
            h.update(block)
            size += len(block)
            if destination is not None:
                destination.write(block)
    finally:
        if destination is not None:
            destination.close()
    return size, h.hexdigest()

def verify(source):
    with subprocess.Popen(["zstd", "-qdc", "--long=30"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE) as proc:
        with ThreadPoolExecutor(max_workers=1) as io:
            written = io.submit(consume, source, proc.stdin)
            raw = consume(proc.stdout)
            proc.stdout.close()
            code = proc.wait()
            compressed = written.result()
    if code or raw != RAW or compressed != COMPRESSED:
        raise ValueError(f"solution stream mismatch: zstd={code}, compressed={compressed}, raw={raw}")
    return {"export": "solution", "compressed_bytes": compressed[0],
            "compressed_sha256": compressed[1], "raw_bytes": raw[0],
            "raw_sha256": raw[1], "local_kernel_replay": False}

if __name__ == "__main__":
    print(json.dumps(verify(sys.stdin.buffer), indent=2))
