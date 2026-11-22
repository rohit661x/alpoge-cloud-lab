"""Validate exact balanced design and emit paired, seed-level summaries as CSV."""
import csv
import itertools
import pathlib
import statistics
import sys

median = statistics.median
seeds = [370817, 842771, 1301081]
shapes = list(itertools.product(["baby", "koala"], [4, 8], [4096, 65536], ["2222", "44", "242"]))
methods = ["shared", "native", "once", "every"]
observations = {}
for seed in seeds:
    with (pathlib.Path(sys.argv[1]) / f"seed-{seed}.csv").open() as f:
        for r in csv.DictReader(f):
            shape = r["field"], int(r["degree"]), int(r["items"]), r["schedule"]
            k = seed, shape, int(r["round"]), r["method"]
            assert k not in observations and shape in shapes and int(r["seed"]) == seed
            repeats, elapsed, position = map(int, (r["repeats"], r["total_ns"], r["position"]))
            assert repeats == 65536 // shape[2] and elapsed > 0
            observations[k] = elapsed / repeats, position
assert len(observations) == 3*24*8*4
out = csv.writer(sys.stdout, lineterminator="\n")
out.writerow(["field", "degree", "items", "schedule", "ratio", *seeds, "median"])
for shape in shapes:
    for seed in seeds:
        for i in range(1, 9):
            assert sorted(observations[seed, shape, i, m][1] for m in methods) == list(range(4))
        for method in methods:
            for block in [1, 5]:
                assert sorted(observations[seed, shape, i, method][1] for i in range(block,block+4)) == list(range(4))
    for a,b in [("once","shared"),("every","shared"),("every","once"),("native","shared")]:
        ratios = [median(observations[s,shape,i,a][0] / observations[s,shape,i,b][0] for i in range(1,9)) for s in seeds]
        out.writerow([*shape, f"{a}/{b}", *(f"{v:.6f}" for v in [*ratios,median(ratios)])])
