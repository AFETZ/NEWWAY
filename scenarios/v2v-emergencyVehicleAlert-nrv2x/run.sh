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
SUMO_PORT="${SUMO_PORT:-}"
CSV_PREFIX="${CSV_PREFIX:-$OUT_DIR/artifacts/eva}"
NETSTATE_FILE="${NETSTATE_FILE:-$OUT_DIR/artifacts/eva-netstate.xml}"
RISK_GAP_THRESHOLD="${RISK_GAP_THRESHOLD:-2.0}"
RISK_TTC_THRESHOLD="${RISK_TTC_THRESHOLD:-1.5}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-0}"
COLLISION_OUTPUT_FILE="${COLLISION_OUTPUT_FILE:-$OUT_DIR/artifacts/eva-collision.xml}"
COLLISION_ACTION="${COLLISION_ACTION:-warn}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"
NS3_CONFIGURE_ARGS="${NS3_CONFIGURE_ARGS:---enable-examples --build-profile=optimized --disable-werror}"
NS3_REQUIRE_OPTIMIZED="${NS3_REQUIRE_OPTIMIZED:-1}"

if [[ "$OUT_DIR" != /* ]]; then
  OUT_DIR="$ROOT/$OUT_DIR"
fi
if [[ "$CSV_PREFIX" != /* ]]; then
  CSV_PREFIX="$ROOT/$CSV_PREFIX"
fi
if [[ "$NETSTATE_FILE" != /* ]]; then
  NETSTATE_FILE="$ROOT/$NETSTATE_FILE"
fi
if [[ "$COLLISION_OUTPUT_FILE" != /* ]]; then
  COLLISION_OUTPUT_FILE="$ROOT/$COLLISION_OUTPUT_FILE"
fi

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

mkdir -p "$OUT_DIR/artifacts"
mkdir -p "$(dirname "$CSV_PREFIX")"
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

rm -f "$NETSTATE_FILE"
rm -f "$COLLISION_OUTPUT_FILE"
rm -f "${CSV_PREFIX}"-veh*-CAM.csv "${CSV_PREFIX}"-veh*-MSG.csv "${CSV_PREFIX}"-veh*-CTRL.csv 2>/dev/null || true

sumo_cfg_arg=""
if [[ "$ENABLE_COLLISION_OUTPUT" == "1" ]]; then
  if [[ " $RUN_ARGS $EXTRA_ARGS " =~ --sumo-config ]]; then
    echo "Warning: ENABLE_COLLISION_OUTPUT=1 ignored because --sumo-config is already provided in RUN_ARGS/EXTRA_ARGS."
  else
    SUMO_BASE="$NS3_DIR/src/automotive/examples/sumo_files_v2v_map"
    COLLISION_CFG="$OUT_DIR/artifacts/eva-collision.sumo.cfg"
    cat > "$COLLISION_CFG" <<EOF
<configuration>
  <input>
    <net-file value="$SUMO_BASE/map.net.xml"/>
    <route-files value="$SUMO_BASE/cars.rou.xml"/>
    <additional-files value="$SUMO_BASE/rerouter.add.xml"/>
  </input>
  <time>
    <begin value="0"/>
    <end value="300"/>
    <step-length value="0.1"/>
  </time>
  <processing>
    <collision.action value="$COLLISION_ACTION"/>
    <collision.check-junctions value="true"/>
  </processing>
  <output>
    <collision-output value="$COLLISION_OUTPUT_FILE"/>
  </output>
</configuration>
EOF
    sumo_cfg_arg="--sumo-config=$COLLISION_CFG"
  fi
fi

RUN_CMD="v2v-emergencyVehicleAlert-nrv2x $RUN_ARGS --csv-log=$CSV_PREFIX --netstate-dump-file=$NETSTATE_FILE $sumo_cfg_arg"

if [[ -z "$SUMO_PORT" ]]; then
  SUMO_PORT="$((30000 + (RANDOM % 20000)))"
fi
RUN_CMD+=" --sumo-port=$SUMO_PORT"

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
  SUMO_PORT="$((30000 + (RANDOM % 20000)))"
  RUN_CMD="$(sed -E "s/--sumo-port=[0-9]+/--sumo-port=$SUMO_PORT/" <<<"$RUN_CMD")"
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

if [[ "$ENABLE_COLLISION_OUTPUT" == "1" ]] && [[ -f "$COLLISION_OUTPUT_FILE" ]]; then
  echo "Collision output: $COLLISION_OUTPUT_FILE"
fi

if [[ "$PLOT" == "1" ]]; then
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/make_plots.py" \
    --run-dir "$OUT_DIR" \
    --scenario "v2v-emergencyVehicleAlert-nrv2x"; then
    echo "Warning: plot generation failed for v2v-emergencyVehicleAlert-nrv2x"
  fi
fi

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_DIR" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for v2v-emergencyVehicleAlert-nrv2x"
  fi
fi

echo "Done: $OUT_DIR/v2v-emergencyVehicleAlert-nrv2x.log"
