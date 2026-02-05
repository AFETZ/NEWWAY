#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
PYTHONUNBUFFERED=1 python3 -u "$SCRIPT_DIR/run_sweep.py" 2>&1 | tee "$LOG_DIR/run_sweep.log"
