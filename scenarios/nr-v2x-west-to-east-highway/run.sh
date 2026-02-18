#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-$ROOT/ns-3-dev}"
OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)}"
JOBS="${JOBS:-8}"
SIM_TAG="${SIM_TAG:-run$(date +%Y%m%d-%H%M%S)-highway}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
PLOT="${PLOT:-1}"

if [[ ! -x "$NS3_DIR/ns3" ]]; then
  echo "Missing executable: $NS3_DIR/ns3"
  echo "Set NS3_DIR to your prepared ns-3-dev tree."
  exit 1
fi

mkdir -p "$OUT_DIR/artifacts"
cd "$NS3_DIR"

./ns3 build -j "$JOBS" nr-v2x-west-to-east-highway

RUN_CMD="nr-v2x-west-to-east-highway --simTag=$SIM_TAG"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

./ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/nr-v2x-west-to-east-highway.log" 2>&1

DB_FILE="$NS3_DIR/${SIM_TAG}-nr-v2x-west-to-east-highway.db"
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
    --scenario "nr-v2x-west-to-east-highway"; then
    echo "Warning: plot generation failed for nr-v2x-west-to-east-highway"
  fi
fi

echo "Done: $OUT_DIR/nr-v2x-west-to-east-highway.log"
