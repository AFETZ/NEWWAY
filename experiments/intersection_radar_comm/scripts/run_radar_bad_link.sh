#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT/experiments/intersection_radar_comm/scripts/run.sh" radar_bad_link "$@"
