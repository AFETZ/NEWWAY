#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec env MODE=sensor_good_cpm "$ROOT/experiments/cpm_perception/scripts/run.sh"
