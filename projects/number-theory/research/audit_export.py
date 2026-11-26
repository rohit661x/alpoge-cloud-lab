"""Inspect the published challenge, or hash the published solution without unpacking to disk.

Usage: python3 audit_export.py challenge challenge.ndjson.zst con-leche-compare.log
       python3 audit_export.py solution solution.ndjson.zst
"""
import argparse
from contextlib import nullcontext
import hashlib
import json
import subprocess
from pathlib import Path

EXPORTS = {
    "challenge": ("c24ef99dab3556a52c7fb886e03cf22a242f3b96f82ae4cc40539e5d2f678ac6",
                  350862311, "bd484ac9886a96f26b1d9a7a59ebd45b7a70d102c015d4f31f9302bbdd6ab2b9"),
    "solution": ("61a8938ad5f5e57397c1c0e3b954916af546d9004ade01c3555744a681b05381",
                 61570595788, "5ea74b912147c5c93cc2b6d70cc727cf908df2f62ac6a20480a3fa02f6be244e"),
}
LOG_SHA = "5a068bf55f24904eea9f05eda947c63d43bdee3c6ab0490e43943a3bd9af1f6e"
TARGETS = {"riemannHypothesis", "riemannZeta_eq_zero_re", "LFunction_ne_zero_of_half_lt_re",
           "LFunction_eq_zero_re", "LFunction_eq_zero_re_of_isPrimitive"}
LEAN = "819816b2e0a3bf405af45ae5c7af2491d8f5bee6"

def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()

def inspect_targets(stream, h, background):
    """Connect anonymous-root strings to declaration name IDs in actual NDJSON."""
    name_ids = {}
    axioms = {}
    metadata = None
    sizes = 0
    needles = [s.encode() for s in TARGETS]
    for line in stream:
        retain = True
        sizes += len(line)
        h.update(line)
        if line.startswith(b'{"meta":'):
            metadata = json.loads(line)["meta"]
        elif line.startswith(b'{"in":') and any(s in line for s in needles):
            record = json.loads(line)
            s = record.get("str", {})
            if s.get("str") in TARGETS and s.get("pre") == 0:
                name_ids[record["in"]] = s["str"]
        elif line.startswith(b'{"thm":'):
            record = json.loads(line)["thm"]
            name = name_ids.get(record["name"])
            if name:
                if name in axioms or record["all"] != [record["name"]] or record["levelParams"]:
                    raise ValueError(f"unexpected declaration: {name}")
                axioms[name] = {k: record[k] for k in ("name", "type", "value")}
                retain = False
        if retain and background is not None:
            background.write(line)
    if set(axioms) != TARGETS or metadata["lean"]["githash"] != LEAN:
        raise ValueError("challenge target or metadata mismatch")
    return sizes, {"lean_export": metadata, "challenge_theorem_records": axioms}

def audit(kind, path, log, background=None):
    compressed, expected_size, expected_raw = EXPORTS[kind]
    if digest_file(path) != compressed:
        raise ValueError("compressed export SHA-256 mismatch")
    h = hashlib.sha256()
    extra = {}
    window = 27 if kind == "challenge" else 30
    with subprocess.Popen(["zstd", "-qdc", f"--long={window}", "--", str(path)],
                          stdout=subprocess.PIPE) as z:
        try:
            if kind == "challenge":
                with (background.open("xb") if background else nullcontext()) as bg:
                    size, extra = inspect_targets(z.stdout, h, bg)
            else:
                size = 0
                for block in iter(lambda: z.stdout.read(4 << 20), b""):
                    size += len(block)
                    h.update(block)
        finally:
            z.stdout.close()
        if z.wait() != 0:
            raise ValueError("zstd decompression failed")
    if size != expected_size or h.hexdigest() != expected_raw:
        raise ValueError("raw export digest or length mismatch")
    if background:
        extra["challenge_background_sha256"] = digest_file(background)
    if log:
        if digest_file(log) != LOG_SHA:
            raise ValueError("published comparison log digest mismatch")
        lines = {s.strip() for s in log.read_text().splitlines()}
        verdicts = {f"con-leche: theorem {s} justified by the solution" for s in TARGETS}
        if not verdicts.issubset(lines) or "Exit status: 0" not in lines:
            raise ValueError("incomplete published comparison log")
        extra["published_comparison_log_sha256"] = LOG_SHA
    return {"export": kind, "compressed_bytes": path.stat().st_size,
            "compressed_sha256": compressed, "raw_bytes": size, "raw_sha256": expected_raw,
            "local_kernel_replay": False, **extra}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=EXPORTS)
    parser.add_argument("archive", type=Path)
    parser.add_argument("published_comparison_log", nargs="?", type=Path)
    parser.add_argument("--write-background", type=Path,
                        help="write challenge records other than the five target theorem records")
    args = parser.parse_args()
    if args.write_background and args.kind != "challenge":
        parser.error("--write-background requires a challenge")
    print(json.dumps(audit(args.kind, args.archive, args.published_comparison_log,
                           args.write_background),
                     indent=2, sort_keys=True))
