#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE_TAG="$(date +%F)"
MODE="${MODE:-all}"

if [[ $# -gt 0 ]]; then
  MODE="$1"
fi

OUT_ROOT="${OUT_ROOT:-$HOME/NEWWAY_runs/$DATE_TAG/valid_cpm_perception_scenario}"
SUMO_GUI="${SUMO_GUI:-0}"
SIM_TIME="${SIM_TIME:-40}"
PLOT="${PLOT:-0}"
EXPORT_RESULTS="${EXPORT_RESULTS:-0}"
EVENT_TIMELINE="${EVENT_TIMELINE:-1}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
COLLISION_STOPTIME_S="${COLLISION_STOPTIME_S:-1000}"
COLLISION_CAUSALITY="${COLLISION_CAUSALITY:-1}"
COLLISION_CAUSALITY_FOCUS_VEHICLE="${COLLISION_CAUSALITY_FOCUS_VEHICLE:-veh4}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"

USE_SIONNA="${USE_SIONNA:-1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
CHECK_SIONNA_LISTENER="${CHECK_SIONNA_LISTENER:-1}"
SUMO_CONFIG="${SUMO_CONFIG:-src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow_veh4lead.sumo.cfg}"

VEH4_BAD_CPM_DROP="${VEH4_BAD_CPM_DROP:-0.995}"
SENSOR_RANGE_M="${SENSOR_RANGE_M:-30}"
SENSOR_REACTION_DISTANCE_M="${SENSOR_REACTION_DISTANCE_M:-10}"
SENSOR_REACTION_TTC_S="${SENSOR_REACTION_TTC_S:-1.0}"
SENSOR_REACTION_PERIOD_MS="${SENSOR_REACTION_PERIOD_MS:-100}"
CPM_REACTION_DISTANCE_M="${CPM_REACTION_DISTANCE_M:-200}"
CPM_REACTION_TTC_S="${CPM_REACTION_TTC_S:-30.0}"

if [[ "$USE_SIONNA" != "1" ]]; then
  echo "valid_cpm_perception_scenario is Sionna-only. Set USE_SIONNA=1." >&2
  exit 2
fi
SIONNA_ARGS="--sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
if [[ "$CHECK_SIONNA_LISTENER" == "1" ]]; then
  if ! ss -lunH 2>/dev/null | awk '{print $4}' | grep -Fq ":${SIONNA_PORT}"; then
    echo "Sionna listener not detected on ${SIONNA_SERVER_IP}:${SIONNA_PORT}." >&2
    echo "Start the server first:" >&2
    echo "  valid_cpm_perception_scenario/start_sionna_server.sh" >&2
    exit 3
  fi
fi

COMMON_ARGS="--sumo-gui=${SUMO_GUI} --sim-time=${SIM_TIME} --met-sup=1 --penetrationRate=1 \
--txPower=${TX_POWER_DBM} ${SIONNA_ARGS} \
--sumo-config=${SUMO_CONFIG} \
--incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=6 --incident-stop-duration-s=20 --incident-setstop-enable=0 \
--cam-reaction-distance-m=0 --cam-reaction-heading-deg=180 --cam-reaction-target-lane=1 \
--reaction-force-lane-change-enable=1 \
--drop-triggered-reaction-enable=0 \
--sensor-reaction-enable=1 \
--sensor-reaction-distance-m=${SENSOR_REACTION_DISTANCE_M} \
--sensor-reaction-ttc-s=${SENSOR_REACTION_TTC_S} \
--sensor-reaction-focus-vehicle-id=veh2 \
--sensor-reaction-period-ms=${SENSOR_REACTION_PERIOD_MS} \
--sensor-range-m=${SENSOR_RANGE_M} \
--rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 \
--target-loss-profile-enable=0 \
--target-loss-rx-drop-prob-cam=0 --target-loss-rx-drop-prob-cpm=0 \
--target-loss-rx-drop-prob-phy-cam=0 --target-loss-rx-drop-prob-phy-cpm=0 \
--crash-mode-enable=0"

run_mode() {
  local mode="$1"
  local mode_args="$2"
  local out_dir="$OUT_ROOT/$mode"
  local run_args="$COMMON_ARGS $mode_args"

  echo "=== MODE: $mode ==="
  PLOT="$PLOT" \
  EXPORT_RESULTS="$EXPORT_RESULTS" \
  EVENT_TIMELINE="$EVENT_TIMELINE" \
  ENABLE_COLLISION_OUTPUT="$ENABLE_COLLISION_OUTPUT" \
  COLLISION_ACTION="$COLLISION_ACTION" \
  COLLISION_STOPTIME_S="$COLLISION_STOPTIME_S" \
  COLLISION_CAUSALITY="$COLLISION_CAUSALITY" \
  COLLISION_CAUSALITY_FOCUS_VEHICLE="$COLLISION_CAUSALITY_FOCUS_VEHICLE" \
  OUT_DIR="$out_dir" \
  RUN_ARGS="$run_args" \
  "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"
}

case "$MODE" in
  all|sensor_only|sensor_good_cpm|sensor_bad_cpm)
    ;;
  *)
    echo "Invalid MODE='$MODE'. Valid values: all, sensor_only, sensor_good_cpm, sensor_bad_cpm" >&2
    exit 2
    ;;
esac

run_selected_modes() {
  local modes=("$@")

  for selected_mode in "${modes[@]}"; do
    case "$selected_mode" in
      sensor_only)
        run_mode "sensor_only" \
          "--cpm-reaction-distance-m=0 --cpm-reaction-ttc-s=0"
        ;;
      sensor_good_cpm)
        run_mode "sensor_good_cpm" \
          "--cpm-reaction-distance-m=${CPM_REACTION_DISTANCE_M} --cpm-reaction-ttc-s=${CPM_REACTION_TTC_S}"
        ;;
      sensor_bad_cpm)
        run_mode "sensor_bad_cpm" \
          "--cpm-reaction-distance-m=${CPM_REACTION_DISTANCE_M} --cpm-reaction-ttc-s=${CPM_REACTION_TTC_S} \
--target-loss-profile-enable=1 --target-loss-vehicle-id=veh4 \
--target-loss-rx-drop-prob-cam=0 --target-loss-rx-drop-prob-cpm=0 \
--target-loss-rx-drop-prob-phy-cam=0 --target-loss-rx-drop-prob-phy-cpm=${VEH4_BAD_CPM_DROP}"
        ;;
    esac
  done
}

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_MODES=()
if [[ "$MODE" == "all" ]]; then
  run_selected_modes sensor_only sensor_good_cpm sensor_bad_cpm
  SUMMARY_MODES=(sensor_only sensor_good_cpm sensor_bad_cpm)
else
  run_selected_modes "$MODE"
  SUMMARY_MODES=("$MODE")
fi

"$PY_BIN" "$ROOT/valid_cpm_perception_scenario/summarize_runs.py" \
  --runs-root "$OUT_ROOT" \
  --modes "${SUMMARY_MODES[@]}" \
  --out-dir "$OUT_ROOT/summary"

echo "VALID_CPM_PERCEPTION_SCENARIO_DONE: $OUT_ROOT"
echo "MODES: ${SUMMARY_MODES[*]}"
echo "SUMMARY_CSV: $OUT_ROOT/summary/cpm_perception_mode_summary.csv"
