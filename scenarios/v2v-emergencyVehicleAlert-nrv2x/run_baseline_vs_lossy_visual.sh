#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-baseline-lossy-$(date +%H%M%S)}"
SIM_TIME="${SIM_TIME:-45}"
SUMO_GUI="${SUMO_GUI:-0}"
RNG_RUN="${RNG_RUN:-1}"

BASE_DROP_CAM="${BASE_DROP_CAM:-0.0}"
LOSSY_DROP_CAM="${LOSSY_DROP_CAM:-0.8}"
BASE_DROP_CPM="${BASE_DROP_CPM:-0.0}"
LOSSY_DROP_CPM="${LOSSY_DROP_CPM:-0.0}"
BASE_DROP_PHY_CAM="${BASE_DROP_PHY_CAM:-0.0}"
LOSSY_DROP_PHY_CAM="${LOSSY_DROP_PHY_CAM:-0.0}"
BASE_DROP_PHY_CPM="${BASE_DROP_PHY_CPM:-0.0}"
LOSSY_DROP_PHY_CPM="${LOSSY_DROP_PHY_CPM:-0.0}"

BASE_TX_POWER="${BASE_TX_POWER:-23}"
LOSSY_TX_POWER="${LOSSY_TX_POWER:-$BASE_TX_POWER}"

INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
BASE_RADIO_ARGS="${BASE_RADIO_ARGS:---enableSensing=1 --enableChannelRandomness=1 --channelUpdatePeriod=100 --slThresPsschRsrp=-126}"
LOSSY_RADIO_ARGS="${LOSSY_RADIO_ARGS:-$BASE_RADIO_ARGS}"
COMMON_EXTRA_ARGS="${COMMON_EXTRA_ARGS:-}"

RUN_RETRIES="${RUN_RETRIES:-3}"
PLOT_CASE="${PLOT_CASE:-1}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"
BASELINE_LABEL="${BASELINE_LABEL:-baseline}"
LOSSY_LABEL="${LOSSY_LABEL:-lossy}"

mkdir -p "$OUT_BASE"
BASE_DIR="$OUT_BASE/$BASELINE_LABEL"
LOSS_DIR="$OUT_BASE/$LOSSY_LABEL"
CMP_DIR="$OUT_BASE/comparison"

base_args="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 --RngRun=$RNG_RUN --txPower=$BASE_TX_POWER --rx-drop-prob-cam=$BASE_DROP_CAM --rx-drop-prob-cpm=$BASE_DROP_CPM --rx-drop-prob-phy-cam=$BASE_DROP_PHY_CAM --rx-drop-prob-phy-cpm=$BASE_DROP_PHY_CPM $INCIDENT_ARGS $BASE_RADIO_ARGS $COMMON_EXTRA_ARGS"
lossy_args="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 --RngRun=$RNG_RUN --txPower=$LOSSY_TX_POWER --rx-drop-prob-cam=$LOSSY_DROP_CAM --rx-drop-prob-cpm=$LOSSY_DROP_CPM --rx-drop-prob-phy-cam=$LOSSY_DROP_PHY_CAM --rx-drop-prob-phy-cpm=$LOSSY_DROP_PHY_CPM $INCIDENT_ARGS $LOSSY_RADIO_ARGS $COMMON_EXTRA_ARGS"

echo "[1/3] Running baseline case..."
OUT_DIR="$BASE_DIR" \
RUN_ARGS="$base_args" \
RUN_RETRIES="$RUN_RETRIES" \
PLOT="$PLOT_CASE" \
ENABLE_COLLISION_OUTPUT="$ENABLE_COLLISION_OUTPUT" \
EXPORT_RESULTS="$EXPORT_RESULTS" \
EXPORT_ROOT="$EXPORT_ROOT" \
EXPORT_INCLUDE_RAW_CSV="$EXPORT_INCLUDE_RAW_CSV" \
  "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

echo "[2/3] Running lossy case..."
OUT_DIR="$LOSS_DIR" \
RUN_ARGS="$lossy_args" \
RUN_RETRIES="$RUN_RETRIES" \
PLOT="$PLOT_CASE" \
ENABLE_COLLISION_OUTPUT="$ENABLE_COLLISION_OUTPUT" \
EXPORT_RESULTS="$EXPORT_RESULTS" \
EXPORT_ROOT="$EXPORT_ROOT" \
EXPORT_INCLUDE_RAW_CSV="$EXPORT_INCLUDE_RAW_CSV" \
  "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

echo "[3/3] Building baseline-vs-lossy comparison timeline..."
"$PY_BIN" "$ROOT/analysis/scenario_runs/compare_incident_baseline_loss.py" \
  --baseline-dir "$BASE_DIR" \
  --lossy-dir "$LOSS_DIR" \
  --out-dir "$CMP_DIR" \
  --baseline-label "$BASELINE_LABEL" \
  --lossy-label "$LOSSY_LABEL"

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_BASE" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for baseline-vs-lossy run"
  fi
fi

echo "Done:"
echo "  baseline: $BASE_DIR"
echo "  lossy:    $LOSS_DIR"
echo "  compare:  $CMP_DIR"
