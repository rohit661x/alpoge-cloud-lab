import csv
import statistics as st
import sys
from pathlib import Path
from collections import defaultdict

arms = ['G4','G3','C3','C4','C6','C8']
data = {}
for p in range(10):
    rows = list(csv.DictReader((Path(sys.argv[1])/f'process-{p}.csv').open()))
    assert len(rows) == 210
    for row in rows:
        b, f, pos = (int(row[key]) for key in ('block','f','position'))
        assert int(row['process']) == p and int(row['min_noise']) > 0
        assert arms[(p+b+6+[0,1,5,2,4,3][pos])%6] == row['arm']
        key = (p,b,f,row['arm'])
        assert key not in data
        data[key] = float(row['ms']),int(row['min_noise'])
writer=csv.writer(sys.stdout,lineterminator='\n')
writer.writerow(['f','arm','median_ms','min_process_ms','max_process_ms','paired_ratio_vs_C8','min_noise','max_noise'])
for f in (1,2,3,4,8):
    for arm in arms:
        times,ratios,noises=[],[],[]
        for p in range(10):
            obs=[data[p,b,f,arm] for b in range(6)]
            times.append(st.median(t for t,n in obs))
            ratios.append(st.median(t/data[p,b,f,'C8'][0] for b,(t,n) in enumerate(obs)))
            noises.extend(n for t,n in obs)
        writer.writerow([f,arm,*[round(v,6) for v in [st.median(times),min(times),max(times),st.median(ratios)]],min(noises),max(noises)])
