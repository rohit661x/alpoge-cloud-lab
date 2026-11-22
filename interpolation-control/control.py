"""Run the prospectively specified local control, or audit its saved timings."""
import argparse
import csv
import hashlib
import io
import itertools
import os
from pathlib import Path
import random
from statistics import median
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
RC_HASH = "b9cc4562f5d72cca25163fcf9688d326a9b35c7a84fa0b2b941b2b3038c794ad"
GRID = list(itertools.product(("BabyBear", "KoalaBear"), (4, 8), (2, 8, 128)))
COLUMNS = "block,field,degree,factor,pair,first,early_ns,late_ns"


def schedule(block):
    order_rng = random.Random(0x4F52444552 + block)
    data_rng = random.Random(0x44415441 + block)
    cases = []
    for field, degree, factor in GRID:
        orders = list("EEEELLLL")
        order_rng.shuffle(orders)
        cases.append((block, field, degree, factor, data_rng.randrange(1, 2**64), "".join(orders)))
    order_rng.shuffle(cases)
    return cases


def run(archive, out):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != RC_HASH:
        raise ValueError("Wrong release-candidate ZIP")
    if out.exists():
        raise FileExistsError(f"Choose a fresh output path: {out}")
    with TemporaryDirectory() as tmp:
        crate = Path(tmp) / "linear"
        prefix = "plonky3-basis-public-rc/linear/"
        members = ("Cargo.toml", "Cargo.lock", "basis/Cargo.toml", "basis/src/lib.rs")
        with ZipFile(archive) as source:
            for member in members:
                target = crate / member
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read(prefix + member))
        (crate / "src").mkdir()
        (crate / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        # An explicit target directory locates the binary unambiguously.
        env = dict(os.environ, CARGO_TARGET_DIR=str(crate / "target"), RUSTFLAGS="")
        subprocess.run(["cargo", "build", "--locked", "--release"], cwd=crate, env=env, check=True)
        measurements = [COLUMNS]
        for block in range(1, 13):
            plan = "".join(" ".join(map(str, row)) + "\n" for row in schedule(block))
            completed = subprocess.run([str(crate / "target/release/linear-frontier")],
                                       input=plan, capture_output=True, text=True)
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr)
            measurements.extend(completed.stdout.splitlines())
        result = "\n".join(measurements) + "\n"
        summarize(result)
        with out.open("x") as f:
            f.write(result)


def summarize(data):
    rows = list(csv.DictReader(io.StringIO(data)))
    expected = [(str(block), field, str(degree), str(factor), str(pair), first)
                for block in range(1, 13)
                for _, field, degree, factor, _, orders in schedule(block)
                for pair, first in enumerate(orders)]
    observed = [tuple(row[k] for k in COLUMNS.split(",")[:6]) for row in rows]
    if observed != expected:
        raise ValueError("Rows differ from the frozen process, case, or pair schedule")
    if any(min(int(r["early_ns"]), int(r["late_ns"])) <= 0 for r in rows):
        raise ValueError("Timing outside the supported positive range")
    print("field,degree,factor,median_early_over_late,min_block,max_block,blocks_above_one,"
          "median_early_first,median_late_first")
    for field, degree, factor in GRID:
        case = [r for r in rows if (r["field"], int(r["degree"]), int(r["factor"])) ==
                (field, degree, factor)]
        def per_block(order):
            return [median(int(r["early_ns"]) / int(r["late_ns"]) for r in case
                           if int(r["block"]) == block and r["first"] in order)
                    for block in range(1, 13)]
        pooled = per_block("EL")
        print(f"{field},{degree},{factor},{median(pooled):.5f},{min(pooled):.5f},"
              f"{max(pooled):.5f},{sum(x > 1 for x in pooled)},"
              f"{median(per_block('E')):.5f},{median(per_block('L')):.5f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    replay = actions.add_parser("run")
    replay.add_argument("archive", type=Path)
    replay.add_argument("out", type=Path)
    check = actions.add_parser("summarize")
    check.add_argument("csv", type=Path)
    args = parser.parse_args()
    if args.action == "run":
        run(args.archive, args.out)
    else:
        summarize(args.csv.read_text())


if __name__ == "__main__":
    main()
