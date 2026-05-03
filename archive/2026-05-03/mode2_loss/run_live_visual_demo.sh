#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

POINT_ID="${1:-live_tx23}"
OUT_DIR="${2:-$SCRIPT_DIR/data/live/$POINT_ID}"

SIM_TIME="${SIM_TIME:-45}"
TX_POWER="${TX_POWER:-23}"
MCS="${MCS:-14}"
ENABLE_SENSING="${ENABLE_SENSING:-False}"
SL_THRES_PSSCH_RSRP="${SL_THRES_PSSCH_RSRP:--128}"
ENABLE_CHANNEL_RANDOMNESS="${ENABLE_CHANNEL_RANDOMNESS:-False}"
CHANNEL_UPDATE_PERIOD="${CHANNEL_UPDATE_PERIOD:-500}"
PENETRATION_RATE="${PENETRATION_RATE:-0.7}"
SUMO_UPDATES="${SUMO_UPDATES:-0.01}"
RNG_RUN="${RNG_RUN:-1}"

RESULTS_DIR="$OUT_DIR/results"
FIGURES_DIR="$OUT_DIR/figures"
NETSTATE_FILE="$OUT_DIR/sumo_netstate.xml"

mkdir -p "$OUT_DIR" "$RESULTS_DIR" "$FIGURES_DIR"

echo "Live demo output directory: $OUT_DIR"
echo "Open the live web visualizer while simulation is running: http://localhost:8080"

python3 "$SCRIPT_DIR/run_one.py" \
  --point-id "$POINT_ID" \
  --out-dir "$OUT_DIR" \
  --scenario v2v-emergencyVehicleAlert-nrv2x \
  --sim-time "$SIM_TIME" \
  --rng-run "$RNG_RUN" \
  --sumo-gui 1 \
  --vehicle-visualizer 1 \
  --sumo-updates "$SUMO_UPDATES" \
  --penetrationRate "$PENETRATION_RATE" \
  --txPower "$TX_POWER" \
  --mcs "$MCS" \
  --enableSensing "$ENABLE_SENSING" \
  --slThresPsschRsrp "$SL_THRES_PSSCH_RSRP" \
  --enableChannelRandomness "$ENABLE_CHANNEL_RANDOMNESS" \
  --channelUpdatePeriod "$CHANNEL_UPDATE_PERIOD" \
  --netstate-dump-file "$NETSTATE_FILE"

python3 "$SCRIPT_DIR/analyze_csv.py" --input "$OUT_DIR" --out "$RESULTS_DIR"
python3 "$SCRIPT_DIR/make_plots.py" --input "$RESULTS_DIR" --out "$FIGURES_DIR"

echo "Simulation finished."
echo "Run log: $OUT_DIR/run.log"
echo "Metadata: $OUT_DIR/metadata.json"
echo "SUMO netstate dump: $NETSTATE_FILE"
echo "Plots: $FIGURES_DIR"
