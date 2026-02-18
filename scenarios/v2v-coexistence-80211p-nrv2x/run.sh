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
if [[ ! -x "$NS3_DIR/switch_ms-van3t-interference.sh" ]]; then
  echo "Missing script: $NS3_DIR/switch_ms-van3t-interference.sh"
  exit 1
fi

mkdir -p "$OUT_DIR/artifacts"
cd "$NS3_DIR"

cleanup() {
  ./switch_ms-van3t-interference.sh off >/dev/null 2>&1 || true
}
trap cleanup EXIT

./switch_ms-van3t-interference.sh on
./ns3 build -j "$JOBS" v2v-coexistence-80211p-nrv2x

# Scenario appends into these files; clear them to keep run-local artifacts.
rm -f "$NS3_DIR/src/prr_latency_ns3_coexistence_11p.csv" \
  "$NS3_DIR/src/prr_latency_ns3_coexistence_nrv2x.csv" \
  "$NS3_DIR/src/sinr_ni.csv"

RUN_CMD="v2v-coexistence-80211p-nrv2x $RUN_ARGS"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

attempt=1
while true; do
  set +e
  ./ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/v2v-coexistence-80211p-nrv2x.log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    break
  fi
  if [[ $attempt -ge $RUN_RETRIES ]] || ! grep -q "Connection refused" "$OUT_DIR/v2v-coexistence-80211p-nrv2x.log"; then
    echo "Scenario failed. See $OUT_DIR/v2v-coexistence-80211p-nrv2x.log"
    exit $rc
  fi
  attempt=$((attempt + 1))
  sleep 2
done

for f in \
  "$NS3_DIR/src/prr_latency_ns3_coexistence_11p.csv" \
  "$NS3_DIR/src/prr_latency_ns3_coexistence_nrv2x.csv" \
  "$NS3_DIR/src/sinr_ni.csv"
do
  if [[ -f "$f" ]]; then
    cp -f "$f" "$OUT_DIR/artifacts/"
  fi
done

if [[ "$PLOT" == "1" ]]; then
  PLOT_PY="$ROOT/.venv/bin/python"
  if [[ ! -x "$PLOT_PY" ]]; then
    PLOT_PY="python3"
  fi
  if ! "$PLOT_PY" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "v2v-coexistence-80211p-nrv2x"; then
    echo "Warning: plot generation failed for v2v-coexistence-80211p-nrv2x"
  fi
fi

echo "Done: $OUT_DIR/v2v-coexistence-80211p-nrv2x.log"
