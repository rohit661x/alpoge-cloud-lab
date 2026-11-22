import csv
from pathlib import Path
from statistics import median

out = Path(__file__).resolve().parent / 'results'
cases = {}
for seed in (1021, 4111, 7963):
    with (out / f'seed-{seed}.csv').open() as stream:
        for row in csv.DictReader(stream):
            case = (row['field'], int(row['degree']), int(row['inputs']), int(row['outputs']))
            key = (seed, int(row['sample']), int(row['mode']))
            assert seed == int(row['seed'])
            values = cases.setdefault(case, {})
            assert key not in values
            values[key] = int(row['ns'])
assert len(cases) == 16
with (out/'summary.csv').open('w') as stream:
    writer = csv.writer(stream)
    writer.writerow(['field','degree','inputs','outputs','native_us','early_us','late_us','fused_early_us','fused_late_us','fused_native_us','early_over_late','fused_early_over_late','fused_early_over_late_min_seed','fused_early_over_late_max_seed','fused_late_over_native'])
    for case, v in sorted(cases.items()):
        assert len(v) == 3*6*6
        seeds = [1021,4111,7963]
        def speed(a,b):
            return [median(v[s,i,a]/v[s,i,b] for i in range(6)) for s in seeds]
        times = [median(median(v[s,i,mode] for i in range(6)) for s in seeds)/1000 for mode in range(6)]
        ratios = speed(3,4)
        writer.writerow([*case,*[round(t,4) for t in times],round(median(speed(1,2)),5),round(median(ratios),5),round(min(ratios),5),round(max(ratios),5),round(median(speed(4,5)),5)])
