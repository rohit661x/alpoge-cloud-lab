"""Verify the public files and run the archived ConvMNIST audits with stock Python."""

import csv
import hashlib
import json
import os
from pathlib import Path
import random
import re
import stat
from statistics import mean, quantiles
import subprocess
import sys
import tempfile
import zipfile


STUDY = Path(__file__).resolve().parent
CHECKPOINT = "partial/two-mac-checkpoint.json"
TWO_MAC_RESULTS = "two-mac/results.json"
TWO_MAC_PREFIXES = "two-mac/prepared-prefixes.csv"
PUBLIC_FILES = {"replay.zip", "report.html", CHECKPOINT, TWO_MAC_RESULTS, TWO_MAC_PREFIXES}


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


def verify_two_mac_results():
    results = json.loads((STUDY / TWO_MAC_RESULTS).read_bytes())
    prepared = results["prepared"]
    arms = ("adaptive", "fixed17", "fixed18", "fixed19")
    with (STUDY / TWO_MAC_PREFIXES).open(newline="") as f:
        rows = [{name: int(value) for name, value in row.items()} for row in csv.DictReader(f)]
    require([row["block"] for row in rows] == list(range(1, 13)), "Prepared block coverage")
    require(prepared["verified_blocks"] == prepared["planned_blocks"] == len(rows),
            "Prepared completion count")
    predictions = len(rows) * len(arms) * 24
    require(prepared["matching_predictions"] == prepared["queries"] == predictions
            and prepared["checked_logits"] == 10 * predictions and prepared["distinct_images"] == 8,
            "Prepared correctness totals")

    def check_ms(observed, published):
        require(abs(observed - published) <= 0.000001, "Two-Mac latency mismatch")

    scores = {arm: [] for arm in arms}
    recovery = {12: [], 24: []}
    for row in rows:
        for arm in arms:
            q5, q24 = row[f"{arm}_q5_ns"], row[f"{arm}_q24_ns"]
            require(0 < q5 < q24, "Prepared endpoints out of order")
            scores[arm].append((4 * q5 + q24) / 5_000_000)  # 80% stop at five, 20% at 24.
        for arm in ("adaptive", "fixed17"):
            require(row[f"{arm}_q5_ns"] < row[f"{arm}_q12_ns"] < row[f"{arm}_q24_ns"],
                    "Request 12 endpoint out of order")
        for q in recovery:
            upgrade = row[f"adaptive_q{q}_ns"] - row["adaptive_q5_ns"]
            stay = row[f"fixed17_q{q}_ns"] - row["fixed17_q5_ns"]
            recovery[q].append((upgrade - stay) / 1_000_000)

    for arm in arms:
        check_ms(mean(scores[arm]), prepared["weighted_mean_ms"][arm])
    best = min(arms[1:], key=lambda arm: mean(scores[arm]))
    require(best == prepared["fastest_fixed"], "Fastest fixed policy mismatch")
    check_ms(mean(scores["adaptive"]) - mean(scores[best]), prepared["adaptive_minus_fastest_fixed_ms"])

    def check_interval(draws, published):
        cutoffs = quantiles(draws, n=40, method="inclusive")
        check_ms(cutoffs[0], published[0])
        check_ms(cutoffs[-1], published[1])

    # Preserve the original seeds and sampling methods for both reported analyses.
    primary_rng = random.Random(240605)
    recovery_rng = random.Random(251126)
    primary_draws = []
    recovery_draws = {q: [] for q in recovery}
    indices = range(len(rows))
    deltas = [[a - f for a, f in zip(scores["adaptive"], scores[arm], strict=True)] for arm in arms[1:]]
    for _ in range(20_000):
        sample = [primary_rng.randrange(len(rows)) for _ in indices]
        # The fastest fixed policy has the largest adaptive-minus-fixed difference.
        primary_draws.append(max(sum(delta[i] for i in sample) for delta in deltas) / len(rows))
        sample = recovery_rng.choices(indices, k=len(rows))
        for q, values in recovery.items():
            recovery_draws[q].append(sum(values[i] for i in sample) / len(rows))
    check_interval(primary_draws, prepared["primary_paired_bootstrap_95_ms"])
    for q, values in recovery.items():
        outcome = prepared["after_request_5_adaptive_minus_fixed17"][str(q)]
        check_ms(mean(values), outcome["mean_ms"])
        require(sum(v < 0 for v in values) == outcome["blocks_faster"], "Faster block count")
        check_interval(recovery_draws[q], outcome["paired_bootstrap_95_ms"])

    partial = results["on_demand"]
    require(partial["status"] == "partial" and partial["primary_latency_result"] is None
            and (partial["committed_blocks"], partial["planned_blocks"]) == (2, 4)
            and partial["query_receipts_per_committed_block"] == [96, 96]
            and partial["excluded_query_receipts_by_incomplete_attempt"] == [15],
            "On-demand snapshot totals")


def main():
    require(sys.version_info >= (3, 11), "Python 3.11 or newer is required")
    hashes = manifest((STUDY / "SHA256SUMS").read_bytes(), PUBLIC_FILES)
    for name, digest in hashes.items():
        check_digest((STUDY / name).read_bytes(), digest, name)
    verify_checkpoint(json.loads((STUDY / CHECKPOINT).read_bytes()))
    verify_two_mac_results()
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
    print("PASS: single-Mac replay and historical checkpoint. Two-Mac prepared results "
          "recomputed from 12 blocks, including the paired intervals. "
          "On-demand snapshot counts checked (2/4 blocks, 192 committed receipts).")


if __name__ == "__main__":
    main()
