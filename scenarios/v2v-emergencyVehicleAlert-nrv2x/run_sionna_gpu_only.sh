#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-short-sionna-gpu-only-tx23-$(date +%H%M%S)}"
TX_POWERS="${TX_POWERS:-23}"
SIM_TIME="${SIM_TIME:-15}"
RNG_RUN="${RNG_RUN:-1}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-1}"
PLOT_CASE="${PLOT_CASE:-1}"

INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=5 --incident-stop-duration-s=8}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=0 --enableChannelRandomness=0 --channelUpdatePeriod=500 --slThresPsschRsrp=-128 --sumo-updates=0.1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

SIONNA_PY="${SIONNA_PY:-$ROOT/.venv_sionna/bin/python}"
SIONNA_GPU="${SIONNA_GPU:-1}"
SIONNA_ALLOW_LLVM_FALLBACK="${SIONNA_ALLOW_LLVM_FALLBACK:-0}"
SIONNA_SERVER_READY_TIMEOUT="${SIONNA_SERVER_READY_TIMEOUT:-2400}"
SIONNA_OPTIX_LIB_DIR="${SIONNA_OPTIX_LIB_DIR:-$ROOT/.optix-wsl/lib}"
SIONNA_RT_SAMPLES_PER_SRC="${SIONNA_RT_SAMPLES_PER_SRC:-512}"
SIONNA_RT_MAX_PATHS_PER_SRC="${SIONNA_RT_MAX_PATHS_PER_SRC:-256}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
KILL_EXISTING_SIONNA="${KILL_EXISTING_SIONNA:-1}"

if ss -lunH 2>/dev/null | awk '{print $5}' | grep -Eq "127\\.0\\.0\\.1:${SIONNA_PORT}$|0\\.0\\.0\\.0:${SIONNA_PORT}$|\\*:${SIONNA_PORT}$"; then
  if [[ "$KILL_EXISTING_SIONNA" == "1" ]]; then
    echo "Port ${SIONNA_PORT} is busy. Stopping previous sionna_v1_server_script.py ..."
    pkill -f sionna_v1_server_script.py || true
    sleep 1
  else
    echo "Port ${SIONNA_PORT} is busy. Set KILL_EXISTING_SIONNA=1 or choose another SIONNA_PORT."
    exit 1
  fi
fi

OUT_BASE="$OUT_BASE" \
TX_POWERS="$TX_POWERS" \
SIM_TIME="$SIM_TIME" \
RNG_RUN="$RNG_RUN" \
SUMO_GUI="$SUMO_GUI" \
COMPARE_NON_SIONNA=0 \
RUN_RETRIES="$RUN_RETRIES" \
PLOT_CASE="$PLOT_CASE" \
INCIDENT_ARGS="$INCIDENT_ARGS" \
RADIO_ARGS="$RADIO_ARGS" \
EXTRA_ARGS="$EXTRA_ARGS" \
SIONNA_PY="$SIONNA_PY" \
SIONNA_GPU="$SIONNA_GPU" \
SIONNA_ALLOW_LLVM_FALLBACK="$SIONNA_ALLOW_LLVM_FALLBACK" \
SIONNA_SERVER_READY_TIMEOUT="$SIONNA_SERVER_READY_TIMEOUT" \
SIONNA_OPTIX_LIB_DIR="$SIONNA_OPTIX_LIB_DIR" \
SIONNA_RT_SAMPLES_PER_SRC="$SIONNA_RT_SAMPLES_PER_SRC" \
SIONNA_RT_MAX_PATHS_PER_SRC="$SIONNA_RT_MAX_PATHS_PER_SRC" \
SIONNA_PORT="$SIONNA_PORT" \
  bash "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run_sionna_incident_sweep.sh"

echo "Done: $OUT_BASE"
