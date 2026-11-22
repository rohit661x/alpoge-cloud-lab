"""Verify every first-stage weight, image and source against the pinned git tree."""
from pathlib import Path
import argparse
import subprocess
import hashlib
import csv

ap=argparse.ArgumentParser()
ap.add_argument("checkout",type=Path)
ap.add_argument("manifest",type=Path)
a=ap.parse_args()
pin="c818bd3519794191dfcf78c252bc209ee30e3e4a"
required=["inputs/luis.png","src/main.cpp","src/FHEController.cpp","src/FHEController.h","src/Utils.h","src/stb_image.h"]
prefixes=["conv1bn1"]+[f"layer{n}-conv{j}bn{j}" for n in (1,2,3) for j in (1,2)]
for prefix in prefixes:
    required.append(f"weights/{prefix}-bias.bin")
    required.extend(f"weights/{prefix}-ch{ch}-k{i}.bin" for ch in range(16) for i in range(1,10))
listing=subprocess.check_output(["git","-C",str(a.checkout),"ls-tree","-r","--full-tree",pin],text=True)
blobs={f:meta.split()[2] for meta,f in (line.split("\t",1) for line in listing.splitlines())}
with a.manifest.open("w",newline="") as output:
    writer=csv.writer(output);writer.writerow(["path","published_git_blob","bytes","sha256"])
    for f in sorted(required):
        b=(a.checkout/f).read_bytes()
        git_hash=hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()
        if git_hash!=blobs[f]: raise ValueError(f)
        writer.writerow([f,blobs[f],len(b),hashlib.sha256(b).hexdigest()])
print(f"{len(required)} source, image and weight files matched. {len(prefixes)*145} weight files.")
