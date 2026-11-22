from array import array
from pathlib import Path
from zipfile import ZipFile
import math
with ZipFile('mac-refs.zip') as ref:
    names=sorted(ref.namelist()); assert len(names)==42
    peak=0
    for name in names:
        apple=array('d'); apple.frombytes(ref.read(name))
        other=array('d'); other.frombytes((Path('work')/name).read_bytes())
        assert len(apple)==len(other)==16384
        assert all(math.isfinite(a) and math.isfinite(b) for a,b in zip(apple,other))
        err=max(abs(a-b) for a,b in zip(apple,other)); assert err<5e-10,(name,err)
        print(name, f'{err:.12g}')
        peak=max(peak,err)
print('Verified',len(names)*16384,'reference values. Largest cross-platform absolute difference:',format(peak,'.12g'))
