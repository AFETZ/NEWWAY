#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Natural Intersection Collision Scenario
# ─────────────────────────────────────────────────────────────────────────────
# This scenario demonstrates a V2X safety-critical intersection conflict where
# collision emerges NATURALLY from degraded channel conditions, not from
# hardcoded force-speed hacks.
#
# How it works:
#   1. Sionna + NR PHY provide realistic channel propagation
#   2. The "obstructed" vehicle has degraded rx sensitivity (equiv_tx_power_dbm)
#      which raises its NR PHY noise figure → real SINR drops → real packet loss
#   3. After enough missed CAMs, the vehicle enters "unaware mode" — it simply
#      doesn't know about the emergency vehicle and drives normally
#   4. SUMO handles collision detection naturally based on vehicle trajectories
#
# No setSpeedMode(0), no setSpeed(30), no lane-change-mode hacks.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE_TAG="$(date +%F)"
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/intersection_natural}"

# ── Simulation basics ──
SUMO_GUI="${SUMO_GUI:-1}"
SIM_TIME="${SIM_TIME:-20}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"

# ── Sionna configuration ──
USE_SIONNA="${USE_SIONNA:-1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
AUTO_START_SIONNA_SERVER="${AUTO_START_SIONNA_SERVER:-1}"
SIONNA_STARTUP_WAIT_S="${SIONNA_STARTUP_WAIT_S:-90}"

# ── Role-based vehicle profiles ──
# Instead of VEH2_*, VEH3_*, VEH4_* we define roles.
# The mapping role→vehicleId is in ONE place (below) and derived from the
# SUMO route file, not hardcoded per-parameter.

# Role: EMERGENCY — the sender on the major approach (good channel, broadcasts CAMs)
ROLE_EMERGENCY_ID="${ROLE_EMERGENCY_ID:-veh2}"
ROLE_EMERGENCY_EQ_DBM="${ROLE_EMERGENCY_EQ_DBM:-${TX_POWER_DBM}}"

# Role: OBSTRUCTED — the vehicle with degraded channel (NLOS, interference, etc.)
ROLE_OBSTRUCTED_ID="${ROLE_OBSTRUCTED_ID:-veh3}"
ROLE_OBSTRUCTED_EQ_DBM="${ROLE_OBSTRUCTED_EQ_DBM:--30}"

# Role: BYSTANDER — connected vehicle with good channel, observes but not in conflict
ROLE_BYSTANDER_ID="${ROLE_BYSTANDER_ID:-veh4}"
ROLE_BYSTANDER_EQ_DBM="${ROLE_BYSTANDER_EQ_DBM:-${TX_POWER_DBM}}"

# Derive station IDs from vehicle IDs (vehN → N)
_station_id() { echo "${1#veh}"; }
EMERGENCY_STATION_ID="$(_station_id "$ROLE_EMERGENCY_ID")"

# ── PHY-driven profiles (no manual rx_drop_prob) ──
# With USE_SIONNA=1 and PHY_ONLY=1, packet losses come from the real NR PHY
# channel model. The equiv_tx_power_dbm adjusts the receiver noise figure to
# model degraded conditions (e.g., NLOS, antenna impairment, interference).
# target_prr is informational only — it documents the EXPECTED outcome, not
# a forced value.
PHY_ONLY="${PHY_ONLY:-1}"
PER_VEHICLE_PRR_PROFILE="${ROLE_EMERGENCY_ID}:0.0:${ROLE_EMERGENCY_EQ_DBM}:1.0,${ROLE_OBSTRUCTED_ID}:0.0:${ROLE_OBSTRUCTED_EQ_DBM}:0.02,${ROLE_BYSTANDER_ID}:0.0:${ROLE_BYSTANDER_EQ_DBM}:0.95"

# ── V2X awareness: junction yield ──
# Non-emergency vehicles start WITHOUT junction right-of-way awareness
# (SUMO speedMode bit 3 = off). The first received CAM from the emergency
# vehicle grants awareness (bit 3 = on).
# Result: channel quality ALONE determines whether vehicles collide.
#   - Good channel → CAM arrives → vehicle yields → safe pass
#   - Bad channel  → CAM lost   → vehicle doesn't know → collision
# No counters, no thresholds, no timers.
V2X_AWARENESS_JUNCTION="${V2X_AWARENESS_JUNCTION:-1}"

# ── CAM silence inference ──
CAM_SILENCE_DROP_INFERENCE_ENABLE="${CAM_SILENCE_DROP_INFERENCE_ENABLE:-${PHY_ONLY}}"
CAM_SILENCE_FOCUS_TX_ID="${CAM_SILENCE_FOCUS_TX_ID:-${EMERGENCY_STATION_ID}}"
CAM_SILENCE_EXPECTED_PERIOD_MS="${CAM_SILENCE_EXPECTED_PERIOD_MS:-600}"
CAM_SILENCE_TIMEOUT_S="${CAM_SILENCE_TIMEOUT_S:-0.95}"
CAM_SILENCE_BOOTSTRAP_TIME_S="${CAM_SILENCE_BOOTSTRAP_TIME_S:-2.2}"

# ── Collision detection ──
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
COLLISION_STOPTIME_S="${COLLISION_STOPTIME_S:-1000}"
COLLISION_CAUSALITY="${COLLISION_CAUSALITY:-1}"
COLLISION_CAUSALITY_FOCUS_VEHICLE="${COLLISION_CAUSALITY_FOCUS_VEHICLE:-${ROLE_OBSTRUCTED_ID}}"
EVENT_TIMELINE="${EVENT_TIMELINE:-1}"
PLOT="${PLOT:-0}"
EXPORT_RESULTS="${EXPORT_RESULTS:-0}"

# ── Sionna server management ──
has_local_sionna_listener() {
  ss -lunH 2>/dev/null | awk '{print $4}' | grep -Fq ":${SIONNA_PORT}"
}

SIONNA_ARGS=""
if [[ "$USE_SIONNA" == "1" ]]; then
  SIONNA_SERVER_LOG="${SIONNA_SERVER_LOG:-$OUT_DIR/sionna_server.log}"
  SIONNA_START_SCRIPT="${SIONNA_START_SCRIPT:-$ROOT/valid_intersection_scenario/start_sionna_server.sh}"
  if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]] && ! has_local_sionna_listener; then
    if [[ "$AUTO_START_SIONNA_SERVER" == "1" ]]; then
      if [[ ! -x "$SIONNA_START_SCRIPT" ]]; then
        echo "Error: Sionna start script not found: $SIONNA_START_SCRIPT" >&2
        exit 1
      fi
      mkdir -p "$(dirname "$SIONNA_SERVER_LOG")"
      echo "Starting Sionna server on UDP ${SIONNA_PORT}..." >&2
      ( cd "$ROOT" && nohup "$SIONNA_START_SCRIPT" >"$SIONNA_SERVER_LOG" 2>&1 & )
      for _ in $(seq 1 "$SIONNA_STARTUP_WAIT_S"); do
        has_local_sionna_listener && break
        sleep 1
      done
    fi
    if ! has_local_sionna_listener; then
      echo "Error: USE_SIONNA=1 but no UDP listener on ${SIONNA_SERVER_IP}:${SIONNA_PORT}." >&2
      echo "Start Sionna first or set USE_SIONNA=0." >&2
      exit 1
    fi
  fi
  SIONNA_ARGS="--sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
else
  SIONNA_ARGS="--sionna=0"
fi

# ── Build ns-3 run arguments ──
# Channel quality → CAM delivery → awareness → behavior.  No crash-mode, no unaware-mode.
RUN_ARGS_FINAL="--sumo-gui=${SUMO_GUI} --sim-time=${SIM_TIME} --met-sup=1 --penetrationRate=1 \
--txPower=${TX_POWER_DBM} ${SIONNA_ARGS} \
--sumo-config=src/automotive/examples/sumo_files_v2i_map/map_intersection_priority.sumo.cfg \
--incident-enable=0 \
--cam-reaction-distance-m=90 --cam-reaction-heading-deg=130 \
--cam-reaction-target-lane=0 --cam-reaction-speed-factor-target-lane=0.10 \
--cam-reaction-speed-factor-other-lane=1.0 --cam-reaction-action-duration-s=2.5 \
--reaction-force-lane-change-enable=0 \
--cpm-reaction-distance-m=0 --cpm-reaction-ttc-s=0 \
--drop-triggered-reaction-enable=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 \
--target-loss-profile-enable=0 \
--per-vehicle-prr-profile=${PER_VEHICLE_PRR_PROFILE} \
--cam-silence-drop-inference-enable=${CAM_SILENCE_DROP_INFERENCE_ENABLE} \
--cam-silence-focus-tx-id=${CAM_SILENCE_FOCUS_TX_ID} \
--cam-silence-expected-period-ms=${CAM_SILENCE_EXPECTED_PERIOD_MS} \
--cam-silence-timeout-s=${CAM_SILENCE_TIMEOUT_S} \
--cam-silence-bootstrap-time-s=${CAM_SILENCE_BOOTSTRAP_TIME_S} \
--crash-mode-enable=0 \
--v2x-awareness-junction=${V2X_AWARENESS_JUNCTION}"

EXTRA_RUN_ARGS="${EXTRA_RUN_ARGS:-}"
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

# ── Post-processing ──
PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_DIR/artifacts/intersection_summary.csv"
if [[ -x "$ROOT/analysis/scenario_runs/build_intersection_scenario_summary.py" ]] || \
   [[ -f "$ROOT/analysis/scenario_runs/build_intersection_scenario_summary.py" ]]; then
  "$PY_BIN" "$ROOT/analysis/scenario_runs/build_intersection_scenario_summary.py" \
    --run-dir "$OUT_DIR" \
    --out-csv "$SUMMARY_CSV" \
    --focus-vehicle "${ROLE_OBSTRUCTED_ID}" \
    --tx-id "${EMERGENCY_STATION_ID}"
fi

# ── Collision causality timeline visualization ──
VISUALIZE="${VISUALIZE:-1}"
if [[ "$VISUALIZE" == "1" ]]; then
  LANG_FLAG="${VIS_LANG:-ru}"
  "$PY_BIN" "$ROOT/hardwork/visualize_collision_causality.py" \
    --run-dir "$OUT_DIR" \
    --focus-vehicle "${ROLE_OBSTRUCTED_ID}" \
    --tx-id "${EMERGENCY_STATION_ID}" \
    --lang "$LANG_FLAG" || echo "Warning: visualization failed (matplotlib may not be installed)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "  NATURAL INTERSECTION SCENARIO COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo "  Output:        $OUT_DIR"
echo "  Sionna:        $USE_SIONNA (server=${SIONNA_SERVER_IP})"
echo "  PHY-driven:    PHY_ONLY=$PHY_ONLY (no manual rx_drop_prob)"
echo "  Crash mode:    DISABLED"
echo "  V2X awareness: junction=${V2X_AWARENESS_JUNCTION} (no counters, no thresholds)"
echo "  Roles:"
echo "    emergency:   ${ROLE_EMERGENCY_ID} (eq_dbm=${ROLE_EMERGENCY_EQ_DBM})"
echo "    obstructed:  ${ROLE_OBSTRUCTED_ID} (eq_dbm=${ROLE_OBSTRUCTED_EQ_DBM})"
echo "    bystander:   ${ROLE_BYSTANDER_ID} (eq_dbm=${ROLE_BYSTANDER_EQ_DBM})"
echo "═══════════════════════════════════════════════════════════════════"
