#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env MODE=sensor_only "$ROOT/valid_cpm_perception_scenario/run.sh"
