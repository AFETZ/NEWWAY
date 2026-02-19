#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_DIR="${OUT_DIR:-$ROOT/analysis/scenario_runs/$(date +%F)}"
JOBS="${JOBS:-8}"
RUN_ARGS="${RUN_ARGS:---sumo-gui=0 --sim-time=20}"
EXTRA_ARGS="${EXTRA_ARGS:-}"
PLOT="${PLOT:-1}"
RUN_RETRIES="${RUN_RETRIES:-3}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"
NS3_CONFIGURE_ARGS="${NS3_CONFIGURE_ARGS:---enable-examples --build-profile=optimized --disable-werror}"
NS3_REQUIRE_OPTIMIZED="${NS3_REQUIRE_OPTIMIZED:-1}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

mkdir -p "$OUT_DIR/artifacts"
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

# Scenario appends into these files; clear them to keep run-local artifacts.
rm -f "$NS3_DIR/src/output.txt" \
  "$NS3_DIR/src/sionna/phy_with_sionna_nrv2x.csv" \
  "$NS3_DIR/src/sionna/prr_with_sionna_nrv2x.csv"

run_ns3 build -j "$JOBS" v2v-cam-exchange-sionna-nrv2x

RUN_CMD="v2v-cam-exchange-sionna-nrv2x $RUN_ARGS"
if [[ -n "$EXTRA_ARGS" ]]; then
  RUN_CMD+=" $EXTRA_ARGS"
fi

attempt=1
while true; do
  set +e
  run_ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log" 2>&1
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

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

if [[ "$PLOT" == "1" ]]; then
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "v2v-cam-exchange-sionna-nrv2x"; then
    echo "Warning: plot generation failed for v2v-cam-exchange-sionna-nrv2x"
  fi
fi

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_DIR" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for v2v-cam-exchange-sionna-nrv2x"
  fi
fi

echo "Done: $OUT_DIR/v2v-cam-exchange-sionna-nrv2x.log"
