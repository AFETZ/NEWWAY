#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-$ROOT/ns-3-dev}"
OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)}"
JOBS="${JOBS:-8}"
RUN_ARGS="${RUN_ARGS:---sumo-gui=0 --sim-time=20}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
PLOT="${PLOT:-1}"
RUN_RETRIES="${RUN_RETRIES:-3}"

if [[ ! -x "$NS3_DIR/ns3" ]]; then
  echo "Missing executable: $NS3_DIR/ns3"
  echo "Set NS3_DIR to your prepared ns-3-dev tree."
  exit 1
fi

mkdir -p "$OUT_DIR/artifacts"
cd "$NS3_DIR"

# Scenario appends into these files; clear them to keep run-local artifacts.
rm -f "$NS3_DIR/src/output.txt" \
  "$NS3_DIR/src/sionna/phy_with_sionna_nrv2x.csv" \
  "$NS3_DIR/src/sionna/prr_with_sionna_nrv2x.csv"

./ns3 build -j "$JOBS" v2v-cam-exchange-sionna-nrv2x

RUN_CMD="v2v-cam-exchange-sionna-nrv2x $RUN_ARGS"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

attempt=1
while true; do
  set +e
  ./ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    break
  fi
  if [[ $attempt -ge $RUN_RETRIES ]] || ! grep -q "Connection refused" "$OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log"; then
    echo "Scenario failed. See $OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log"
    exit $rc
  fi
  attempt=$((attempt + 1))
  sleep 2
done

if [[ -f "$NS3_DIR/src/output.txt" ]]; then
  cp -f "$NS3_DIR/src/output.txt" "$OUT_DIR/artifacts/v2v-cam-exchange-sionna-nrv2x_output.txt"
fi
if [[ -f "$NS3_DIR/src/sionna/phy_with_sionna_nrv2x.csv" ]]; then
  cp -f "$NS3_DIR/src/sionna/phy_with_sionna_nrv2x.csv" "$OUT_DIR/artifacts/"
fi
if [[ -f "$NS3_DIR/src/sionna/prr_with_sionna_nrv2x.csv" ]]; then
  cp -f "$NS3_DIR/src/sionna/prr_with_sionna_nrv2x.csv" "$OUT_DIR/artifacts/"
fi

if [[ "$PLOT" == "1" ]]; then
  PLOT_PY="$ROOT/.venv/bin/python"
  if [[ ! -x "$PLOT_PY" ]]; then
    PLOT_PY="python3"
  fi
  if ! "$PLOT_PY" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "v2v-cam-exchange-sionna-nrv2x"; then
    echo "Warning: plot generation failed for v2v-cam-exchange-sionna-nrv2x"
  fi
fi

echo "Done: $OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log"
