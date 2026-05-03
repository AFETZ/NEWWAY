#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="$(date +%F)"
TIME_TAG="$(date +%H%M%S)"

OUT_DIR="${OUT_DIR:-$ROOT/raw_experiments/runs/$DATE_TAG/truck_lane_change_5glena_raw-$TIME_TAG}"
SUMO_GUI="${SUMO_GUI:-0}"
SIM_TIME="${SIM_TIME:-40}"
USE_SIONNA="${USE_SIONNA:-0}"
ENABLE_MSVAN3T_CSV="${ENABLE_MSVAN3T_CSV:-1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
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

ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
COLLISION_CHECK_JUNCTIONS="${COLLISION_CHECK_JUNCTIONS:-1}"
COLLISION_STOPTIME_S="${COLLISION_STOPTIME_S:-1000}"
SUMO_PORT="${SUMO_PORT:-}"
EXTRA_RUN_ARGS="${EXTRA_RUN_ARGS:-}"
SIM_TAG="${SIM_TAG:-truck_lane_change_5glena_raw}"

NS3_DIR="${NS3_DIR:-}"
JOBS="${JOBS:-8}"
NS3_CONFIGURE_ARGS="${NS3_CONFIGURE_ARGS:---enable-examples --build-profile=optimized --disable-werror}"
NS3_REQUIRE_OPTIMIZED="${NS3_REQUIRE_OPTIMIZED:-1}"

NETSTATE_FILE="$OUT_DIR/eva-netstate.xml"
COLLISION_OUTPUT_FILE="$OUT_DIR/eva-collision.xml"
RUN_LOG="$OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log"
CSV_PREFIX="$OUT_DIR/eva"
OFFICIAL_SQLITE_DB="$OUT_DIR/${SIM_TAG}-v2v-emergencyVehicleAlert-nrv2x.db"

mkdir -p "$OUT_DIR"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

cd "$NS3_DIR"

if [[ "$EUID" -eq 0 ]]; then
  NS3_USER_OVERRIDE="${NS3_USER_OVERRIDE:-ns3}"
  run_ns3() { USER="$NS3_USER_OVERRIDE" ./ns3 "$@"; }
else
  run_ns3() { ./ns3 "$@"; }
fi

CONFIG_STATE="$(run_ns3 show config 2>/dev/null | sed -r 's/\x1B\[[0-9;]*[mK]//g' || true)"
need_configure=0
if ! grep -Eq 'Examples[[:space:]]*:[[:space:]]*ON' <<<"$CONFIG_STATE"; then
  need_configure=1
fi
if [[ "$NS3_REQUIRE_OPTIMIZED" == "1" ]] && ! grep -Eq 'Build profile[[:space:]]*:[[:space:]]*optimized' <<<"$CONFIG_STATE"; then
  need_configure=1
fi
if [[ "$need_configure" -eq 1 ]]; then
  read -r -a configure_args <<< "$NS3_CONFIGURE_ARGS"
  run_ns3 configure "${configure_args[@]}"
fi

run_ns3 build -j "$JOBS" v2v-emergencyVehicleAlert-nrv2x

rm -f "$NETSTATE_FILE" "$COLLISION_OUTPUT_FILE" "$RUN_LOG" "$OFFICIAL_SQLITE_DB"
rm -f "${CSV_PREFIX}"-veh*-CAM.csv "${CSV_PREFIX}"-veh*-MSG.csv "${CSV_PREFIX}"-veh*-CTRL.csv "${CSV_PREFIX}"-veh*-PROFILE.csv "${CSV_PREFIX}"-veh*-PHY.csv 2>/dev/null || true

if [[ -z "$SUMO_PORT" ]]; then
  SUMO_PORT="$((30000 + (RANDOM % 20000)))"
fi

if [[ "$USE_SIONNA" == "1" ]]; then
  SIONNA_ARGS="--sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
else
  SIONNA_ARGS="--sionna=0"
fi

CRASH_MODE_ENABLE="1"
if awk "BEGIN { exit !(${VEH4_TARGET_PRR} >= 0.2) }"; then
  CRASH_MODE_ENABLE="0"
fi

if [[ "$CRASH_MODE_ENABLE" == "1" ]]; then
  CRASH_MODE_ARGS="--crash-mode-enable=1 --crash-mode-vehicle-id=veh4 --crash-mode-no-action-threshold=10 --crash-mode-force-speed-mps=30 --crash-mode-duration-s=6 --crash-mode-min-time-s=6"
else
  CRASH_MODE_ARGS="--crash-mode-enable=0"
fi

sumo_collision_args=""
if [[ -n "$COLLISION_ACTION" ]]; then
  sumo_collision_args+=" --sumo-collision-action=${COLLISION_ACTION}"
  sumo_collision_args+=" --sumo-collision-check-junctions=${COLLISION_CHECK_JUNCTIONS}"
fi
if [[ "$ENABLE_COLLISION_OUTPUT" == "1" ]]; then
  sumo_collision_args+=" --sumo-collision-output=${COLLISION_OUTPUT_FILE}"
fi
if [[ -n "$COLLISION_STOPTIME_S" ]]; then
  sumo_collision_args+=" --sumo-collision-stoptime-s=${COLLISION_STOPTIME_S}"
fi

csv_args=""
if [[ "$ENABLE_MSVAN3T_CSV" == "1" ]]; then
  csv_args="--csv-log=${CSV_PREFIX}"
fi

RUN_CMD="v2v-emergencyVehicleAlert-nrv2x \
--sumo-gui=${SUMO_GUI} \
--sim-time=${SIM_TIME} \
--met-sup=1 \
--penetrationRate=1 \
--txPower=${TX_POWER_DBM} \
${SIONNA_ARGS} \
--sumo-config=src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow.sumo.cfg \
--incident-enable=1 \
--incident-vehicle-id=veh2 \
--incident-time-s=6 \
--incident-stop-duration-s=20 \
--incident-setstop-enable=0 \
--cam-reaction-target-lane=1 \
--cam-reaction-distance-m=22 \
--reaction-force-lane-change-enable=1 \
--cpm-reaction-distance-m=0 \
--cpm-reaction-ttc-s=0 \
--drop-triggered-reaction-enable=0 \
--rx-drop-prob-phy-cam=0 \
--rx-drop-prob-phy-cpm=0 \
--target-loss-profile-enable=0 \
--target-loss-vehicle-id=veh4 \
--target-loss-rx-drop-prob-phy-cam=0.0 \
--target-loss-rx-drop-prob-phy-cpm=0.0 \
--per-vehicle-prr-profile=${PER_VEHICLE_PRR_PROFILE} \
${CRASH_MODE_ARGS} \
--enable-official-sqlite=1 \
--simTag=${SIM_TAG} \
--outputDir=${OUT_DIR} \
${csv_args} \
--netstate-dump-file=${NETSTATE_FILE} \
--sumo-port=${SUMO_PORT} \
${sumo_collision_args}"

if [[ -n "$EXTRA_RUN_ARGS" ]]; then
  RUN_CMD+=" ${EXTRA_RUN_ARGS}"
fi

echo "Running raw-only lane-change scenario..."
echo "OUT_DIR: $OUT_DIR"
echo "USE_SIONNA: $USE_SIONNA"
echo "SUMO_GUI: $SUMO_GUI"
echo "ENABLE_MSVAN3T_CSV: $ENABLE_MSVAN3T_CSV"

set +e
run_ns3 run --no-build "$RUN_CMD" > "$RUN_LOG" 2>&1
rc=$?
set -e

if [[ $rc -ne 0 ]]; then
  echo "Scenario failed. See $RUN_LOG" >&2
  tail -n 40 "$RUN_LOG" >&2 || true
  exit $rc
fi

echo "Raw run completed."
echo "$RUN_LOG"
if [[ -f "$OFFICIAL_SQLITE_DB" ]]; then
  echo "$OFFICIAL_SQLITE_DB"
fi
find "$OUT_DIR" -maxdepth 1 -type f \
  \( -name 'eva-veh*-CAM.csv' -o -name 'eva-veh*-MSG.csv' -o -name 'eva-veh*-CTRL.csv' -o -name 'eva-veh*-PROFILE.csv' -o -name 'eva-veh*-PHY.csv' \) \
  | sort || true
if [[ -f "$NETSTATE_FILE" ]]; then
  echo "$NETSTATE_FILE"
fi
if [[ -f "$COLLISION_OUTPUT_FILE" ]]; then
  echo "$COLLISION_OUTPUT_FILE"
fi
