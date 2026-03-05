#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE_TAG="$(date +%F)"
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/valid_intersection_scenario}"

SUMO_GUI="${SUMO_GUI:-1}"
SIM_TIME="${SIM_TIME:-20}"
USE_SIONNA="${USE_SIONNA:-1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
CHECK_SIONNA_LISTENER="${CHECK_SIONNA_LISTENER:-0}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"
PHY_ONLY="${PHY_ONLY:-1}"
ALLOW_MANUAL_RX_DROP="${ALLOW_MANUAL_RX_DROP:-0}"

VEH2_EQ_DBM="${VEH2_EQ_DBM:-23}"
VEH2_TARGET_PRR="${VEH2_TARGET_PRR:-1.0}"
VEH2_RX_DROP_PHY_CAM="${VEH2_RX_DROP_PHY_CAM:-0.000000}"

VEH3_EQ_DBM="${VEH3_EQ_DBM:--30}"
VEH3_TARGET_PRR="${VEH3_TARGET_PRR:-0.02}"
VEH3_RX_DROP_PHY_CAM="${VEH3_RX_DROP_PHY_CAM:-0.923000}"
VEH4_EQ_DBM="${VEH4_EQ_DBM:-23}"
VEH4_TARGET_PRR="${VEH4_TARGET_PRR:-0.95}"
VEH4_RX_DROP_PHY_CAM="${VEH4_RX_DROP_PHY_CAM:-0.000000}"

CAM_SILENCE_DROP_INFERENCE_ENABLE="${CAM_SILENCE_DROP_INFERENCE_ENABLE:-$PHY_ONLY}"
CAM_SILENCE_FOCUS_TX_ID="${CAM_SILENCE_FOCUS_TX_ID:-2}"
CAM_SILENCE_EXPECTED_PERIOD_MS="${CAM_SILENCE_EXPECTED_PERIOD_MS:-600}"
CAM_SILENCE_TIMEOUT_S="${CAM_SILENCE_TIMEOUT_S:-0.95}"
CAM_SILENCE_BOOTSTRAP_TIME_S="${CAM_SILENCE_BOOTSTRAP_TIME_S:-2.2}"

if [[ "$PHY_ONLY" == "1" && "$ALLOW_MANUAL_RX_DROP" != "1" ]]; then
  VEH2_RX_DROP_PHY_CAM="0.0"
  VEH3_RX_DROP_PHY_CAM="0.0"
fi

PER_VEHICLE_PRR_PROFILE="${PER_VEHICLE_PRR_PROFILE:-veh2:${VEH2_RX_DROP_PHY_CAM}:${VEH2_EQ_DBM}:${VEH2_TARGET_PRR},veh3:${VEH3_RX_DROP_PHY_CAM}:${VEH3_EQ_DBM}:${VEH3_TARGET_PRR},veh4:${VEH4_RX_DROP_PHY_CAM}:${VEH4_EQ_DBM}:${VEH4_TARGET_PRR}}"

CRASH_MODE_ENABLE="${CRASH_MODE_ENABLE:-auto}"
CRASH_MODE_NO_ACTION_THRESHOLD="${CRASH_MODE_NO_ACTION_THRESHOLD:-3}"
CRASH_MODE_FORCE_SPEED_MPS="${CRASH_MODE_FORCE_SPEED_MPS:-30}"
CRASH_MODE_DURATION_S="${CRASH_MODE_DURATION_S:-3.0}"
CRASH_MODE_MIN_TIME_S="${CRASH_MODE_MIN_TIME_S:-3.8}"

PLOT="${PLOT:-0}"
EXPORT_RESULTS="${EXPORT_RESULTS:-0}"
EVENT_TIMELINE="${EVENT_TIMELINE:-1}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
COLLISION_STOPTIME_S="${COLLISION_STOPTIME_S:-1000}"
COLLISION_CAUSALITY="${COLLISION_CAUSALITY:-1}"
COLLISION_CAUSALITY_FOCUS_VEHICLE="${COLLISION_CAUSALITY_FOCUS_VEHICLE:-veh3}"

SIONNA_ARGS=""
if [[ "$USE_SIONNA" == "1" ]]; then
  SIONNA_ARGS="--sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
  if [[ "$CHECK_SIONNA_LISTENER" == "1" ]]; then
    if ! ss -lunH 2>/dev/null | awk '{print $5}' | grep -Fq ":${SIONNA_PORT}"; then
      echo "Warning: USE_SIONNA=1 but no UDP listener detected on ${SIONNA_SERVER_IP}:${SIONNA_PORT}."
      echo "         Start Sionna server first (or set USE_SIONNA=0 for non-Sionna run)."
    fi
  fi
else
  SIONNA_ARGS="--sionna=0"
fi

if [[ "$CRASH_MODE_ENABLE" == "auto" ]]; then
  if awk "BEGIN { exit !(${VEH3_TARGET_PRR} < 0.2) }"; then
    CRASH_MODE_ENABLE="1"
  else
    CRASH_MODE_ENABLE="0"
  fi
fi

CRASH_MODE_ARGS=""
if [[ "$CRASH_MODE_ENABLE" == "1" ]]; then
  CRASH_MODE_ARGS="--crash-mode-enable=1 --crash-mode-vehicle-id=veh3 --crash-mode-no-action-threshold=${CRASH_MODE_NO_ACTION_THRESHOLD} \
--crash-mode-force-speed-mps=${CRASH_MODE_FORCE_SPEED_MPS} --crash-mode-duration-s=${CRASH_MODE_DURATION_S} --crash-mode-min-time-s=${CRASH_MODE_MIN_TIME_S}"
else
  CRASH_MODE_ARGS="--crash-mode-enable=0"
fi

BASE_RUN_ARGS="--sumo-gui=${SUMO_GUI} --sim-time=${SIM_TIME} --met-sup=1 --penetrationRate=1 \
--txPower=${TX_POWER_DBM} ${SIONNA_ARGS} \
--sumo-config=src/automotive/examples/sumo_files_v2i_map/map_intersection_priority.sumo.cfg \
--incident-enable=0 \
--cam-reaction-distance-m=90 --cam-reaction-heading-deg=130 \
--cam-reaction-target-lane=0 --cam-reaction-speed-factor-target-lane=0.10 \
--cam-reaction-speed-factor-other-lane=1.0 --cam-reaction-action-duration-s=2.5 \
--reaction-force-lane-change-enable=0 \
--cpm-reaction-distance-m=0 --cpm-reaction-ttc-s=0 \
--drop-triggered-reaction-enable=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 \
--target-loss-profile-enable=0 --target-loss-vehicle-id=veh3 \
--target-loss-rx-drop-prob-phy-cam=0.0 --target-loss-rx-drop-prob-phy-cpm=0.0 \
--per-vehicle-prr-profile=${PER_VEHICLE_PRR_PROFILE} \
--cam-silence-drop-inference-enable=${CAM_SILENCE_DROP_INFERENCE_ENABLE} \
--cam-silence-focus-tx-id=${CAM_SILENCE_FOCUS_TX_ID} \
--cam-silence-expected-period-ms=${CAM_SILENCE_EXPECTED_PERIOD_MS} \
--cam-silence-timeout-s=${CAM_SILENCE_TIMEOUT_S} \
--cam-silence-bootstrap-time-s=${CAM_SILENCE_BOOTSTRAP_TIME_S} \
${CRASH_MODE_ARGS}"

EXTRA_RUN_ARGS="${EXTRA_RUN_ARGS:-}"
RUN_ARGS_FINAL="$BASE_RUN_ARGS"
if [[ -n "$EXTRA_RUN_ARGS" ]]; then
  RUN_ARGS_FINAL+=" $EXTRA_RUN_ARGS"
fi

PLOT="$PLOT" \
EXPORT_RESULTS="$EXPORT_RESULTS" \
EVENT_TIMELINE="$EVENT_TIMELINE" \
ENABLE_COLLISION_OUTPUT="$ENABLE_COLLISION_OUTPUT" \
COLLISION_ACTION="$COLLISION_ACTION" \
COLLISION_STOPTIME_S="$COLLISION_STOPTIME_S" \
COLLISION_CAUSALITY="$COLLISION_CAUSALITY" \
COLLISION_CAUSALITY_FOCUS_VEHICLE="$COLLISION_CAUSALITY_FOCUS_VEHICLE" \
OUT_DIR="$OUT_DIR" \
RUN_ARGS="$RUN_ARGS_FINAL" \
"$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_DIR/artifacts/intersection_summary.csv"
"$PY_BIN" "$ROOT/analysis/scenario_runs/build_intersection_scenario_summary.py" \
  --run-dir "$OUT_DIR" \
  --out-csv "$SUMMARY_CSV" \
  --focus-vehicle "veh3" \
  --tx-id "2"

echo "VALID_INTERSECTION_SCENARIO_DONE: $OUT_DIR"
echo "SIONNA_MODE: $USE_SIONNA (server=${SIONNA_SERVER_IP}, local_machine=${SIONNA_LOCAL_MACHINE})"
echo "PHY_ONLY: $PHY_ONLY (manual_rx_drop_allowed=${ALLOW_MANUAL_RX_DROP})"
echo "CRASH_MODE_ENABLE: $CRASH_MODE_ENABLE"
echo "PER_VEHICLE_PRR_PROFILE: $PER_VEHICLE_PRR_PROFILE"
echo "SUMMARY_CSV: $SUMMARY_CSV"
