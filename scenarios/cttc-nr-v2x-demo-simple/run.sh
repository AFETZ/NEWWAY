#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)}"
JOBS="${JOBS:-8}"
SIM_TAG="${SIM_TAG:-run$(date +%Y%m%d-%H%M%S)-cttc}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
PLOT="${PLOT:-1}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"

mkdir -p "$OUT_DIR/artifacts"
cd "$NS3_DIR"

if [[ "$EUID" -eq 0 ]]; then
  NS3_USER_OVERRIDE="${NS3_USER_OVERRIDE:-ns3}"
  run_ns3() { USER="$NS3_USER_OVERRIDE" ./ns3 "$@"; }
else
  run_ns3() { ./ns3 "$@"; }
fi

if ! run_ns3 show config 2>/dev/null \
  | sed -r 's/\x1B\[[0-9;]*[mK]//g' \
  | grep -Eq 'Examples[[:space:]]*:[[:space:]]*ON'; then
  run_ns3 configure --enable-examples
fi

run_ns3 build -j "$JOBS" cttc-nr-v2x-demo-simple

RUN_CMD="cttc-nr-v2x-demo-simple --simTag=$SIM_TAG"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

run_ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/cttc-nr-v2x-demo-simple.log" 2>&1

DB_FILE="$NS3_DIR/${SIM_TAG}-nr-v2x-simple-demo.db"
if [[ -f "$DB_FILE" ]]; then
  cp -f "$DB_FILE" "$OUT_DIR/artifacts/"
fi

if [[ "$PLOT" == "1" ]]; then
  PLOT_PY="$ROOT/.venv/bin/python"
  if [[ ! -x "$PLOT_PY" ]]; then
    PLOT_PY="python3"
  fi
  if ! "$PLOT_PY" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "cttc-nr-v2x-demo-simple"; then
    echo "Warning: plot generation failed for cttc-nr-v2x-demo-simple"
  fi
fi

echo "Done: $OUT_DIR/cttc-nr-v2x-demo-simple.log"
