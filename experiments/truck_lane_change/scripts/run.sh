#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DATE_TAG="$(date +%F)"
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/truck_lane_change}"
SUMO_GUI="${SUMO_GUI:-1}"
SIM_TIME="${SIM_TIME:-40}"
USE_SIONNA="${USE_SIONNA:-1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
CHECK_SIONNA_LISTENER="${CHECK_SIONNA_LISTENER:-0}"
AUTO_START_SIONNA_SERVER="${AUTO_START_SIONNA_SERVER:-1}"
SIONNA_STARTUP_WAIT_S="${SIONNA_STARTUP_WAIT_S:-90}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"

VEH3_EQ_DBM="${VEH3_EQ_DBM:-23}"
VEH3_TARGET_PRR="${VEH3_TARGET_PRR:-0.95}"
VEH3_RX_DROP_PHY_CAM="${VEH3_RX_DROP_PHY_CAM:-0.050000}"
VEH4_EQ_DBM="${VEH4_EQ_DBM:--20}"
VEH4_TARGET_PRR="${VEH4_TARGET_PRR:-0.077}"
VEH4_RX_DROP_PHY_CAM="${VEH4_RX_DROP_PHY_CAM:-0.923000}"
VEH5_EQ_DBM="${VEH5_EQ_DBM:-0}"
VEH5_TARGET_PRR="${VEH5_TARGET_PRR:-0.693}"
VEH5_RX_DROP_PHY_CAM="${VEH5_RX_DROP_PHY_CAM:-0.307000}"
PER_VEHICLE_PRR_PROFILE="${PER_VEHICLE_PRR_PROFILE:-veh3:${VEH3_RX_DROP_PHY_CAM}:${VEH3_EQ_DBM}:${VEH3_TARGET_PRR},veh4:${VEH4_RX_DROP_PHY_CAM}:${VEH4_EQ_DBM}:${VEH4_TARGET_PRR},veh5:${VEH5_RX_DROP_PHY_CAM}:${VEH5_EQ_DBM}:${VEH5_TARGET_PRR}}"

PLOT="${PLOT:-0}"
EXPORT_RESULTS="${EXPORT_RESULTS:-0}"
EVENT_TIMELINE="${EVENT_TIMELINE:-1}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
COLLISION_STOPTIME_S="${COLLISION_STOPTIME_S:-1000}"
COLLISION_CAUSALITY="${COLLISION_CAUSALITY:-1}"
COLLISION_CAUSALITY_FOCUS_VEHICLE="${COLLISION_CAUSALITY_FOCUS_VEHICLE:-veh4}"
CRASH_MODE_ENABLE="${CRASH_MODE_ENABLE:-auto}"
CRASH_MODE_NO_ACTION_THRESHOLD="${CRASH_MODE_NO_ACTION_THRESHOLD:-10}"
CRASH_MODE_FORCE_SPEED_MPS="${CRASH_MODE_FORCE_SPEED_MPS:-30}"
CRASH_MODE_DURATION_S="${CRASH_MODE_DURATION_S:-6}"
CRASH_MODE_MIN_TIME_S="${CRASH_MODE_MIN_TIME_S:-6}"

has_local_sionna_listener() {
  ss -lunH 2>/dev/null | awk '{print $4}' | grep -Fq ":${SIONNA_PORT}"
}

SIONNA_ARGS=""
if [[ "$USE_SIONNA" == "1" ]]; then
  SIONNA_SERVER_LOG="${SIONNA_SERVER_LOG:-$OUT_DIR/sionna_server.log}"
  SIONNA_START_SCRIPT="${SIONNA_START_SCRIPT:-$ROOT/experiments/truck_lane_change/scripts/start_sionna_server.sh}"
  if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]] && ! has_local_sionna_listener; then
    if [[ "$AUTO_START_SIONNA_SERVER" == "1" ]]; then
      if [[ ! -x "$SIONNA_START_SCRIPT" ]]; then
        echo "Error: local Sionna start script not found: $SIONNA_START_SCRIPT" >&2
        exit 1
      fi
      mkdir -p "$(dirname "$SIONNA_SERVER_LOG")"
      echo "No local Sionna listener on UDP ${SIONNA_PORT}; starting server..." >&2
      (
        cd "$ROOT"
        nohup "$SIONNA_START_SCRIPT" >"$SIONNA_SERVER_LOG" 2>&1 &
      )
      for _ in $(seq 1 "$SIONNA_STARTUP_WAIT_S"); do
        if has_local_sionna_listener; then
          break
        fi
        sleep 1
      done
    fi

    if ! has_local_sionna_listener; then
      echo "Error: USE_SIONNA=1 but no local UDP listener detected on ${SIONNA_SERVER_IP}:${SIONNA_PORT}." >&2
      echo "Start Sionna first with:" >&2
      echo "  bash experiments/truck_lane_change/scripts/start_sionna_server.sh" >&2
      echo "Or run without Sionna:" >&2
      echo "  USE_SIONNA=0 bash experiments/truck_lane_change/scripts/run.sh" >&2
      exit 1
    fi
  fi

  SIONNA_ARGS="--sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
  if [[ "$CHECK_SIONNA_LISTENER" == "1" ]]; then
    if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]] && ! has_local_sionna_listener; then
      echo "Warning: USE_SIONNA=1 but no UDP listener detected on ${SIONNA_SERVER_IP}:${SIONNA_PORT}."
      echo "         Start Sionna server first (or set USE_SIONNA=0 for non-Sionna run)."
    fi
  fi
else
  SIONNA_ARGS="--sionna=0"
fi

if [[ "$CRASH_MODE_ENABLE" == "auto" ]]; then
  if awk "BEGIN { exit !(${VEH4_TARGET_PRR} < 0.2) }"; then
    CRASH_MODE_ENABLE="1"
  else
    CRASH_MODE_ENABLE="0"
  fi
fi

CRASH_MODE_ARGS=""
if [[ "$CRASH_MODE_ENABLE" == "1" ]]; then
  CRASH_MODE_ARGS="--crash-mode-enable=1 --crash-mode-vehicle-id=veh4 --crash-mode-no-action-threshold=${CRASH_MODE_NO_ACTION_THRESHOLD} \
--crash-mode-force-speed-mps=${CRASH_MODE_FORCE_SPEED_MPS} --crash-mode-duration-s=${CRASH_MODE_DURATION_S} --crash-mode-min-time-s=${CRASH_MODE_MIN_TIME_S}"
else
  CRASH_MODE_ARGS="--crash-mode-enable=0"
fi

BASE_RUN_ARGS="--sumo-gui=${SUMO_GUI} --sim-time=${SIM_TIME} --met-sup=1 --penetrationRate=1 \
--txPower=${TX_POWER_DBM} ${SIONNA_ARGS} \
--sumo-config=src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow.sumo.cfg \
--incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=6 --incident-stop-duration-s=20 --incident-setstop-enable=0 \
--cam-reaction-target-lane=1 --cam-reaction-distance-m=22 --reaction-force-lane-change-enable=1 \
--cpm-reaction-distance-m=0 --cpm-reaction-ttc-s=0 \
--drop-triggered-reaction-enable=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 \
--target-loss-profile-enable=0 --target-loss-vehicle-id=veh4 \
--target-loss-rx-drop-prob-phy-cam=0.0 --target-loss-rx-drop-prob-phy-cpm=0.0 \
--per-vehicle-prr-profile=${PER_VEHICLE_PRR_PROFILE} \
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
"$ROOT/experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

STORY_OUT_DIR="${STORY_OUT_DIR:-$OUT_DIR/artifacts/valid_scenario_story}"
"$PY_BIN" "$ROOT/tools/plots/build_valid_scenario_story_plots.py" \
  --run-dir "$OUT_DIR" \
  --out-dir "$STORY_OUT_DIR"

INTUITIVE_OUT_DIR="${INTUITIVE_OUT_DIR:-$OUT_DIR/artifacts/valid_scenario_intuitive}"
"$PY_BIN" "$ROOT/tools/plots/build_valid_scenario_intuitive_plots.py" \
  --run-dir "$OUT_DIR" \
  --out-dir "$INTUITIVE_OUT_DIR"

echo "VALID_SCENARIO_DONE: $OUT_DIR"
echo "SIONNA_MODE: $USE_SIONNA (server=${SIONNA_SERVER_IP}, local_machine=${SIONNA_LOCAL_MACHINE})"
echo "CRASH_MODE_ENABLE: $CRASH_MODE_ENABLE"
echo "PER_VEHICLE_PRR_PROFILE: $PER_VEHICLE_PRR_PROFILE"
echo "STORY_PLOTS: $STORY_OUT_DIR"
echo "INTUITIVE_PLOTS: $INTUITIVE_OUT_DIR"
