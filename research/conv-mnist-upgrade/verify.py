"""Verify the public files and run the archived ConvMNIST audits with stock Python."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import zipfile


STUDY = Path(__file__).resolve().parent
CHECKPOINT = "partial/two-mac-checkpoint.json"
PUBLIC_FILES = {"replay.zip", "report.html", CHECKPOINT}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def manifest(contents, expected):
    hashes = {}
    for line in contents.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match, f"Invalid SHA256SUMS entry: {line!r}")
        digest, name = match.groups()
        require(name not in hashes, f"Duplicate SHA256SUMS entry: {name}")
        hashes[name] = digest
    require(set(hashes) == expected, "SHA256SUMS coverage differs from the file list")
    return hashes


def check_digest(data, expected, name):
    require(hashlib.sha256(data).hexdigest() == expected, f"SHA-256 mismatch: {name}")


def extract_verified(archive, destination):
    members = {}
    seen_paths = set()
    for member in archive.infolist():
        name = member.orig_filename
        parts = name.split("/")
        # The kit contains ordinary files with portable ASCII names.
        require(all(re.fullmatch(r"[A-Za-z0-9_+@.-]+", part) and not part.endswith(".")
                    for part in parts), f"Invalid archive path: {name!r}")
        require(stat.S_IFMT(member.external_attr >> 16) in (0, stat.S_IFREG),
                f"Archive member is not an ordinary file: {name}")
        require(name.casefold() not in seen_paths, f"Duplicate archive path: {name}")
        seen_paths.add(name.casefold())
        members[name] = member

    hashes = manifest(archive.read("SHA256SUMS"), set(members) - {"SHA256SUMS"})
    for name, member in members.items():
        data = archive.read(member)
        if name != "SHA256SUMS":
            check_digest(data, hashes[name], name)
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)


def verify_checkpoint(checkpoint):
    prepared = checkpoint["prepared"]
    on_demand = checkpoint["on_demand"]
    excluded = checkpoint["excluded_attempts"]
    require(checkpoint["status"] == "partial", "Expected a partial two-Mac checkpoint")
    require(checkpoint["primary_latency_result"] is None, "Partial cohort has a latency result")
    smoke = checkpoint["smoke"]
    require(smoke["matching_predictions"] == smoke["queries"] == 4, "Unexpected smoke test count")
    require((prepared["verified_key_blocks"], prepared["planned_key_blocks"]) == (10, 12),
            "Unexpected number of prepared key blocks")
    queries = prepared["verified_key_blocks"] * 4 * 24  # Four policies with 24 requests each.
    require(prepared["checks"]["queries"] == prepared["checks"]["matching_predictions"] == queries,
            "Prepared queries and matching predictions must count complete blocks only")
    require((on_demand["verified_key_blocks"], on_demand["planned_key_blocks"]) == (0, 4),
            "Unexpected number of on-demand key blocks")
    require(on_demand["verified_predictions"] == 0, "Unexpected on-demand prediction count")
    counts = excluded["query_receipts_by_attempt"]
    require(isinstance(counts, list) and len(counts) == 8
            and all(type(n) is int and n >= 0 for n in counts),
            "Invalid excluded query counts")
    require(sum(counts) == excluded["total_query_receipts"] == 54,
            "Excluded attempt counts must sum to 54 uncommitted query receipts")


def main():
    require(sys.version_info >= (3, 11), "Python 3.11 or newer is required")
    hashes = manifest((STUDY / "SHA256SUMS").read_bytes(), PUBLIC_FILES)
    for name, digest in hashes.items():
        check_digest((STUDY / name).read_bytes(), digest, name)
    verify_checkpoint(json.loads((STUDY / CHECKPOINT).read_bytes()))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        with zipfile.ZipFile(STUDY / "replay.zip") as archive:
            extract_verified(archive, root)
        require((root / "report.html").read_bytes() == (STUDY / "report.html").read_bytes(),
                "Published report differs from the archived report")
        # The archived replay and its child processes use Python assertions.
        env = os.environ.copy()
        env.pop("PYTHONOPTIMIZE", None)
        subprocess.run([sys.executable, "replay.py"], cwd=root, env=env, check=True)
        (root / "outputs").mkdir()
        subprocess.run([sys.executable, "work/switchtrial/report.py"], cwd=root, env=env, check=True)
        require((root / "outputs/conv-mnist-when-to-upgrade.html").read_bytes()
                == (STUDY / "report.html").read_bytes(),
                "Report regenerated from the audited results differs from the published HTML")
    print("PASS: public files and partial two-Mac checkpoint arithmetic "
          "(10/12 prepared blocks, 960 matches, 54 excluded receipts, 0/4 on-demand blocks).")


if __name__ == "__main__":
    main()
