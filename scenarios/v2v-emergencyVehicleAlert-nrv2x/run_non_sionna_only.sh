#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-short-non-sionna-tx23-$(date +%H%M%S)}"
SIM_TIME="${SIM_TIME:-15}"
TX_POWER="${TX_POWER:-23}"
RNG_RUN="${RNG_RUN:-1}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-1}"
PLOT="${PLOT:-1}"

INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=5 --incident-stop-duration-s=8}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=0 --enableChannelRandomness=0 --channelUpdatePeriod=500 --slThresPsschRsrp=-128 --sumo-updates=0.1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 --RngRun=$RNG_RUN --txPower=$TX_POWER --sionna=0 --rx-drop-prob-cam=0 --rx-drop-prob-cpm=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 $INCIDENT_ARGS $RADIO_ARGS $EXTRA_ARGS"

OUT_DIR="$OUT_DIR" \
RUN_RETRIES="$RUN_RETRIES" \
PLOT="$PLOT" \
RUN_ARGS="$RUN_ARGS" \
  bash "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

echo "Done: $OUT_DIR"
