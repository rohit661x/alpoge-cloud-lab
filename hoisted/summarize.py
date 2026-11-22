import csv
import statistics as st
import sys
from pathlib import Path

root = Path(sys.argv[1])
timed = {i: [] for i in range(4)}
noise = {i: set() for i in range(4)}
ratios = []
for process in range(16):
    lines=(root/f'process-{process}.csv').read_text().splitlines()
    assert len(lines)==26
    keys=list(csv.DictReader(lines[:5]))
    assert [(int(r['keys']),int(r['depth']),int(r['sources'])) for r in keys]==[(3,3,4),(4,2,3),(6,2,2),(8,1,1)]
    rows=list(csv.DictReader(lines[5:]))
    assert len(rows)==20
    for b in range(-1,4):
        assert sorted(int(r['route']) for r in rows if int(r['block'])==b)==list(range(4))
    for route in range(4):
        relevant=[r for r in rows if int(r['block'])>=0 and int(r['route'])==route]
        assert {int(r['position']) for r in relevant}==set(range(4))
        timed[route].append(st.median(float(r['time_ms']) for r in relevant))
        noise[route].update(int(r['output_noise_bits']) for r in relevant)
    ratios.append(timed[0][-1]/timed[3][-1])
print('route,median_of_process_medians_ms,min_process_median_ms,max_process_median_ms,min_noise,max_noise')
for route, values in timed.items():
    print(route,st.median(values),min(values),max(values),min(noise[route]),max(noise[route]),sep=',')
print('three_over_eight_paired_process_median_ratio',st.median(ratios),min(ratios),max(ratios),sep=',')
