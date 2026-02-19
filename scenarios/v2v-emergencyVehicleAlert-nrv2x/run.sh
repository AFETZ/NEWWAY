#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)}"
JOBS="${JOBS:-8}"
RUN_ARGS="${RUN_ARGS:---sumo-gui=0 --sim-time=40 --met-sup=1}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
PLOT="${PLOT:-1}"
RUN_RETRIES="${RUN_RETRIES:-3}"
CSV_PREFIX="${CSV_PREFIX:-$OUT_DIR/artifacts/eva}"
NETSTATE_FILE="${NETSTATE_FILE:-$OUT_DIR/artifacts/eva-netstate.xml}"
RISK_GAP_THRESHOLD="${RISK_GAP_THRESHOLD:-2.0}"
RISK_TTC_THRESHOLD="${RISK_TTC_THRESHOLD:-1.5}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"

mkdir -p "$OUT_DIR/artifacts"
mkdir -p "$(dirname "$CSV_PREFIX")"
cd "$NS3_DIR"

if [[ "$EUID" -eq 0 ]]; then
  NS3_USER_OVERRIDE="${NS3_USER_OVERRIDE:-ns3}"
  run_ns3() { USER="$NS3_USER_OVERRIDE" ./ns3 "$@"; }
else
  run_ns3() { ./ns3 "$@"; }
fi

if ! run_ns3 show config 2>/dev/null \
  | sed -r 's/\x1B\[[0-9;]*[mK]//g' \
  | grep -Eq 'Examples[[:space:]]*:[[:space:]]*ON'; then
  run_ns3 configure --enable-examples
fi

run_ns3 build -j "$JOBS" v2v-emergencyVehicleAlert-nrv2x

rm -f "$NETSTATE_FILE"
rm -f "${CSV_PREFIX}"-veh*-CAM.csv "${CSV_PREFIX}"-veh*-MSG.csv "${CSV_PREFIX}"-veh*-CTRL.csv 2>/dev/null || true

RUN_CMD="v2v-emergencyVehicleAlert-nrv2x $RUN_ARGS --csv-log=$CSV_PREFIX --netstate-dump-file=$NETSTATE_FILE"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

attempt=1
while true; do
  set +e
  run_ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    break
  fi
  if [[ $attempt -ge $RUN_RETRIES ]] || ! grep -q "Connection refused" "$OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log"; then
    echo "Scenario failed. See $OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log"
    exit $rc
  fi
  attempt=$((attempt + 1))
  sleep 2
done

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

if [[ -f "$NETSTATE_FILE" ]]; then
  "$PY_BIN" "$ROOT/analysis/scenario_runs/analyze_netstate_collision_risk.py" \
    --netstate "$NETSTATE_FILE" \
    --out-dir "$OUT_DIR/artifacts/collision_risk" \
    --gap-threshold-m "$RISK_GAP_THRESHOLD" \
    --ttc-threshold-s "$RISK_TTC_THRESHOLD"
else
  echo "Warning: netstate file not found, collision risk analysis skipped: $NETSTATE_FILE"
fi

if [[ "$PLOT" == "1" ]]; then
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "v2v-emergencyVehicleAlert-nrv2x"; then
    echo "Warning: plot generation failed for v2v-emergencyVehicleAlert-nrv2x"
  fi
fi

echo "Done: $OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log"
