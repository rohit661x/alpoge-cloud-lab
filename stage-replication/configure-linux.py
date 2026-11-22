"""Emit the shared trial driver's configuration for a Linux build on a provisioned host."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("build", type=Path, help="output directory of build.sh")
parser.add_argument("replication", type=Path, help="shared directory containing trial.py, draw.json and fixtures")
parser.add_argument("output", type=Path, help="private working and results directory")
parser.add_argument("--threads", type=int, default=6)
args = parser.parse_args()
build = args.build.resolve()
paths = dict(init=build/"harness/stage_native", old8=build/"arms/old8/stage_ninth",
             new8=build/"arms/parents/stage_ninth", old9=build/"arms/old9/stage_ninth",
             new9=build/"arms/parents/stage_ninth", common11=build/"arms/common11/stage_portable",
             pack=build/"pack", reference=build/"reference", weights=build/"app/weights",
             fixtures=args.replication.resolve()/"fixtures")
for path in paths.values():
    if not path.exists():
        parser.error(f"Missing build or fixture path {path}")
if args.threads < 1:
    parser.error("threads must be positive")
config = {key:str(value) for key,value in paths.items()}
config.update(output=str(args.output.resolve()), threads=args.threads, environment={"LD_LIBRARY_PATH":str(build/"install/lib")})
print(json.dumps(config, indent=2))
