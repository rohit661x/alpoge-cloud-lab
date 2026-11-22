#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# Give the disconnected editor time to release background extension processes.
sleep 150
python3 -B stage-replication/pilot/codespace-pilot.py --profile 3 --image-index 0 --key 1 --attempt 2 --timed-rounds 5 --evidence stage-replication/codespace-evidence
