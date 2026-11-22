#!/usr/bin/env bash
set -eu
cd "$(git rev-parse --show-toplevel)"
until test -f stage-replication/codespace-evidence/build-status.txt; do sleep 5; done
git pull --rebase --autostash origin resnet-followup-codespace-20261122
git push origin HEAD
test -x /tmp/stage-native/arms/common11/stage_portable
python3 -B stage-replication/pilot/codespace-pilot.py --evidence stage-replication/codespace-evidence "$@"
