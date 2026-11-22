import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
app, output = map(Path, sys.argv[1:])
output.mkdir()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for entry in json.loads((ROOT / 'draw.json').read_text())['images']:
    image = entry['image']
    photo = ROOT / 'fixtures' / (image + '.jpg')
    assert sha(photo) == entry['sha256']
    work = output / image
    work.mkdir()
    subprocess.run(['./pack', photo, work / 'input.f64'], check=True)
    for profile, degree in [(2,200), (3,119)]:
        subprocess.run(['./reference', app / 'weights', work / 'input.f64', str(degree), work / str(profile)], check=True)
        assert len(list((work / str(profile)).glob('*.f64'))) == 14
(output / 'SHA256.json').write_text(json.dumps({str(f.relative_to(output)):sha(f) for f in sorted(output.rglob('*.f64'))}, indent=2))
