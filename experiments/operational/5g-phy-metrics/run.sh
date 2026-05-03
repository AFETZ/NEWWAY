#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# 5G NR-V2X PHY Metrics Experiment — Self-contained scenario runner
#
# Usage:
#   bash scenarios/5g-phy-metrics/run.sh
#
# All knobs are configurable via environment variables.
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="$(date +%F)"
OUT_DIR="${OUT_DIR:-$HOME/NEWWAY_runs/$DATE_TAG/5g-phy-metrics}"
JOBS="${JOBS:-8}"
RUN_RETRIES="${RUN_RETRIES:-3}"

# ── Simulation parameters (override via env) ──
SIM_TIME="${SIM_TIME:-100}"
TX_POWER_DBM="${TX_POWER_DBM:-23}"
MCS="${MCS:-14}"
NUMEROLOGY="${NUMEROLOGY:-2}"
SENSING="${SENSING:-0}"
CHANNEL_RANDOMNESS="${CHANNEL_RANDOMNESS:-0}"
SUBCHANNEL_SIZE="${SUBCHANNEL_SIZE:-10}"
RESERVATION_PERIOD="${RESERVATION_PERIOD:-20}"
BANDWIDTH="${BANDWIDTH:-100}"
T1="${T1:-2}"
T2="${T2:-81}"
SUMO_GUI="${SUMO_GUI:-0}"
SUMO_CONFIG="${SUMO_CONFIG:-src/automotive/examples/sumo_files_v2v_map/map.sumo.cfg}"
SUMO_WAIT_FOR_SOCKET_S="${SUMO_WAIT_FOR_SOCKET_S:-5}"
BASELINE="${BASELINE:-150}"
SUMO_PORT="${SUMO_PORT:-}"
PLOT="${PLOT:-1}"

# Sionna parameters
USE_SIONNA="${USE_SIONNA:-0}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-0}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
AUTO_START_SIONNA_SERVER="${AUTO_START_SIONNA_SERVER:-1}"
SIONNA_STARTUP_WAIT_S="${SIONNA_STARTUP_WAIT_S:-90}"

# ns-3 build settings
NS3_DIR="${NS3_DIR:-}"
NS3_CONFIGURE_ARGS="${NS3_CONFIGURE_ARGS:---enable-examples --build-profile=optimized --disable-werror}"
NS3_REQUIRE_OPTIMIZED="${NS3_REQUIRE_OPTIMIZED:-1}"

# ── Resolve output directory ──
if [[ "$OUT_DIR" != /* ]]; then
  OUT_DIR="$ROOT/$OUT_DIR"
fi
mkdir -p "$OUT_DIR/artifacts" "$OUT_DIR/plots"

CSV_PREFIX="$OUT_DIR/artifacts/phy-metrics"

# ── Bootstrap ns-3 ──
NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

cd "$NS3_DIR"

if [[ "$EUID" -eq 0 ]]; then
  NS3_USER_OVERRIDE="${NS3_USER_OVERRIDE:-ns3}"
  run_ns3() { USER="$NS3_USER_OVERRIDE" ./ns3 "$@"; }
else
  run_ns3() { ./ns3 "$@"; }
fi

# ── Configure if needed ──
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

# ── Build ──
echo "Building v2v-5g-phy-metrics-experiment..."
run_ns3 build -j "$JOBS" v2v-5g-phy-metrics-experiment

# ── Clean old outputs ──
rm -f "$CSV_PREFIX"-*.csv "$CSV_PREFIX"-summary.txt 2>/dev/null || true

# ── Construct run command ──
RUN_CMD="v2v-5g-phy-metrics-experiment"
RUN_CMD+=" --sim-time=$SIM_TIME"
RUN_CMD+=" --tx-power=$TX_POWER_DBM"
RUN_CMD+=" --mcs=$MCS"
RUN_CMD+=" --numerology=$NUMEROLOGY"
RUN_CMD+=" --sensing=$SENSING"
RUN_CMD+=" --channel-randomness=$CHANNEL_RANDOMNESS"
RUN_CMD+=" --subchannel-size=$SUBCHANNEL_SIZE"
RUN_CMD+=" --reservation-period=$RESERVATION_PERIOD"
RUN_CMD+=" --bandwidth=$BANDWIDTH"
RUN_CMD+=" --t1=$T1"
RUN_CMD+=" --t2=$T2"
RUN_CMD+=" --sumo-gui=$SUMO_GUI"
RUN_CMD+=" --sumo-config=$SUMO_CONFIG"
RUN_CMD+=" --sumo-wait-for-socket-s=$SUMO_WAIT_FOR_SOCKET_S"
RUN_CMD+=" --baseline=$BASELINE"
RUN_CMD+=" --out-prefix=$CSV_PREFIX"

# ── Sionna setup ──
has_local_sionna_listener() {
  ss -lunH 2>/dev/null | awk '{print $4}' | grep -Fq ":${SIONNA_PORT}"
}

SIONNA_ARGS=""
if [[ "$USE_SIONNA" == "1" ]]; then
  if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]] && ! has_local_sionna_listener; then
    if [[ "$AUTO_START_SIONNA_SERVER" == "1" ]]; then
      SIONNA_START_SCRIPT="${SIONNA_START_SCRIPT:-$ROOT/scenarios/5g-phy-metrics/start_sionna_server.sh}"
      if [[ -x "$SIONNA_START_SCRIPT" ]]; then
        SIONNA_SERVER_LOG="$OUT_DIR/sionna_server.log"
        echo "No local Sionna listener on UDP ${SIONNA_PORT}; starting server..."
        ( cd "$ROOT" && nohup "$SIONNA_START_SCRIPT" >"$SIONNA_SERVER_LOG" 2>&1 & )
        for _ in $(seq 1 "$SIONNA_STARTUP_WAIT_S"); do
          has_local_sionna_listener && break
          sleep 1
        done
      fi
    fi
    if ! has_local_sionna_listener; then
      echo "Warning: USE_SIONNA=1 but no Sionna listener on ${SIONNA_SERVER_IP}:${SIONNA_PORT}"
      echo "Continuing without Sionna..."
      USE_SIONNA=0
    fi
  fi
fi

if [[ "$USE_SIONNA" == "1" ]]; then
  RUN_CMD+=" --sionna=1 --sionna-local-machine=${SIONNA_LOCAL_MACHINE} --sionna-server-ip=${SIONNA_SERVER_IP} --sionna-verbose=${SIONNA_VERBOSE}"
fi

# Random SUMO port if not specified
if [[ -z "$SUMO_PORT" ]]; then
  SUMO_PORT="$((30000 + (RANDOM % 20000)))"
fi
RUN_CMD+=" --sumo-port=$SUMO_PORT"

# ── Run simulation ──
echo "Running: $RUN_CMD"
echo "Output:  $OUT_DIR"

attempt=1
while true; do
  set +e
  run_ns3 run --no-build "$RUN_CMD" > "$OUT_DIR/experiment.log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    break
  fi
  if [[ $attempt -ge $RUN_RETRIES ]] || ! grep -q "Connection refused" "$OUT_DIR/experiment.log"; then
    break
  fi
  SUMO_PORT="$((30000 + (RANDOM % 20000)))"
  RUN_CMD="$(sed -E "s/--sumo-port=[0-9]+/--sumo-port=$SUMO_PORT/" <<<"$RUN_CMD")"
  attempt=$((attempt + 1))
  sleep 2
done

if [[ $rc -ne 0 ]]; then
  echo "ERROR: simulation failed (exit code $rc). See $OUT_DIR/experiment.log"
  tail -20 "$OUT_DIR/experiment.log"
  exit $rc
fi

echo "Simulation completed successfully."

# ── Collect artifacts ──
echo ""
echo "Artifacts in $OUT_DIR/artifacts/:"
ls -lh "$OUT_DIR/artifacts/" 2>/dev/null || true

# ── Plot ──
if [[ "$PLOT" == "1" ]]; then
  PY_BIN="$ROOT/.venv/bin/python"
  if [[ ! -x "$PY_BIN" ]]; then
    PY_BIN="python3"
  fi

  echo ""
  echo "Generating plots..."
  if "$PY_BIN" "$ROOT/analysis/plot_5g_phy_metrics.py" \
      --prefix "$CSV_PREFIX" \
      --out-dir "$OUT_DIR/plots"; then
    echo "Plots saved to $OUT_DIR/plots/"
  else
    echo "Warning: plot generation failed (non-fatal)"
  fi
fi

# ── Print summary ──
echo ""
echo "════════════════════════════════════════"
echo "5G PHY Metrics Experiment — Done"
echo "════════════════════════════════════════"
echo "OUT_DIR:     $OUT_DIR"
echo "MCS=$MCS  NUMEROLOGY=$NUMEROLOGY  TX_POWER=${TX_POWER_DBM}dBm  SENSING=$SENSING  SIONNA=$USE_SIONNA"
if [[ -f "$CSV_PREFIX-summary.txt" ]]; then
  echo ""
  cat "$CSV_PREFIX-summary.txt"
fi
