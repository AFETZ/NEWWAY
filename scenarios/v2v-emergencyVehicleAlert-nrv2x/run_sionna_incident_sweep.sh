#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-sionna-incident-sweep-$(date +%H%M%S)}"
TX_POWERS="${TX_POWERS:-23 17 11 5}"
SIM_TIME="${SIM_TIME:-40}"
RNG_RUN="${RNG_RUN:-1}"
SUMO_GUI="${SUMO_GUI:-0}"

COMPARE_NON_SIONNA="${COMPARE_NON_SIONNA:-1}"
RUN_RETRIES="${RUN_RETRIES:-3}"
PLOT_CASE="${PLOT_CASE:-1}"

INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=1 --enableChannelRandomness=1 --channelUpdatePeriod=100 --slThresPsschRsrp=-126}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

SIONNA_PY="${SIONNA_PY:-$ROOT/.venv_sionna/bin/python}"
SIONNA_GPU="${SIONNA_GPU:-0}"
SIONNA_MI_VARIANT="${SIONNA_MI_VARIANT:-}"
SIONNA_ALLOW_LLVM_FALLBACK="${SIONNA_ALLOW_LLVM_FALLBACK:-1}"
SIONNA_SERVER_READY_TIMEOUT="${SIONNA_SERVER_READY_TIMEOUT:-300}"
SIONNA_RT_MAX_DEPTH="${SIONNA_RT_MAX_DEPTH:-2}"
SIONNA_RT_MAX_PATHS_PER_SRC="${SIONNA_RT_MAX_PATHS_PER_SRC:-256}"
SIONNA_RT_SAMPLES_PER_SRC="${SIONNA_RT_SAMPLES_PER_SRC:-512}"
SIONNA_RT_POSITION_THRESHOLD="${SIONNA_RT_POSITION_THRESHOLD:-3}"
SIONNA_RT_ANGLE_THRESHOLD="${SIONNA_RT_ANGLE_THRESHOLD:-90}"
SIONNA_PORT="${SIONNA_PORT:-8103}"
SIONNA_SERVER_IP="${SIONNA_SERVER_IP:-127.0.0.1}"
SIONNA_LOCAL_MACHINE="${SIONNA_LOCAL_MACHINE:-1}"
SIONNA_OPTIX_LIB_DIR="${SIONNA_OPTIX_LIB_DIR:-}"
SCENE_XML="${SCENE_XML:-}"

EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]] && [[ -z "$SCENE_XML" ]]; then
  SCENE_XML="$NS3_DIR/src/sionna/scenarios/SionnaCircleScenario/scene.xml"
fi
if [[ ! -x "$SIONNA_PY" ]]; then
  SIONNA_PY="python3"
fi
if [[ -z "$SIONNA_OPTIX_LIB_DIR" ]] && [[ -d "$ROOT/.optix-wsl/lib" ]]; then
  SIONNA_OPTIX_LIB_DIR="$ROOT/.optix-wsl/lib"
fi

# Auto-wire CUDA libraries from Python site-packages (tensorflow[and-cuda]) on WSL/Linux.
SIONNA_CUDA_LIBS="$("$SIONNA_PY" - <<'PY' 2>/dev/null || true
import glob
import os
import site

paths = []
for base in site.getsitepackages():
    paths.extend(glob.glob(os.path.join(base, "nvidia", "*", "lib")))

# Keep deterministic order and avoid duplicates.
seen = set()
uniq = []
for p in paths:
    if p not in seen:
        seen.add(p)
        uniq.append(p)
print(":".join(uniq))
PY
)"
if [[ -n "$SIONNA_OPTIX_LIB_DIR" ]] && [[ ! -d "$SIONNA_OPTIX_LIB_DIR" ]]; then
  echo "SIONNA_OPTIX_LIB_DIR does not exist: $SIONNA_OPTIX_LIB_DIR"
  exit 1
fi
if [[ -n "$SIONNA_CUDA_LIBS" ]]; then
  if [[ -n "$SIONNA_OPTIX_LIB_DIR" ]]; then
    export LD_LIBRARY_PATH="$SIONNA_CUDA_LIBS:$SIONNA_OPTIX_LIB_DIR:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
  else
    export LD_LIBRARY_PATH="$SIONNA_CUDA_LIBS:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
  fi
elif [[ -n "$SIONNA_OPTIX_LIB_DIR" ]]; then
  export LD_LIBRARY_PATH="$SIONNA_OPTIX_LIB_DIR:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
fi

if [[ "$SIONNA_LOCAL_MACHINE" != "0" ]] && [[ "$SIONNA_LOCAL_MACHINE" != "1" ]]; then
  echo "SIONNA_LOCAL_MACHINE must be 0 or 1 (got: $SIONNA_LOCAL_MACHINE)"
  exit 1
fi
if [[ "$SIONNA_LOCAL_MACHINE" == "0" ]] && [[ -z "$SIONNA_SERVER_IP" ]]; then
  echo "SIONNA_SERVER_IP must be set when SIONNA_LOCAL_MACHINE=0"
  exit 1
fi
if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]]; then
  if [[ ! -f "$NS3_DIR/src/sionna/sionna_v1_server_script.py" ]]; then
    echo "Missing Sionna server script: $NS3_DIR/src/sionna/sionna_v1_server_script.py"
    exit 1
  fi
  if [[ ! -f "$SCENE_XML" ]]; then
    echo "Missing Sionna scene XML: $SCENE_XML"
    exit 1
  fi
fi

mkdir -p "$OUT_BASE"

if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]]; then
  echo "[1/4] Checking Sionna runtime dependencies..."
  if ! "$SIONNA_PY" - <<'PY'
import importlib.util
mods = ("tensorflow", "sionna", "mitsuba", "grpc")
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print("MISSING:", ",".join(missing))
    raise SystemExit(1)
print("OK")
PY
  then
    echo "Sionna stack is missing. Required modules: tensorflow, sionna, mitsuba, grpc."
    echo "Try:"
    echo "  python3 -m venv .venv_sionna"
    echo "  .venv_sionna/bin/pip install --upgrade pip"
    echo "  .venv_sionna/bin/pip install tensorflow-cpu sionna mitsuba grpcio"
    exit 1
  fi
else
  echo "[1/4] Remote Sionna mode enabled: skipping local python dependency checks."
fi

SIONNA_PID=""
cleanup() {
  if [[ -n "$SIONNA_PID" ]] && kill -0 "$SIONNA_PID" >/dev/null 2>&1; then
    kill "$SIONNA_PID" >/dev/null 2>&1 || true
    wait "$SIONNA_PID" >/dev/null 2>&1 || true
  fi
}

start_sionna_server() {
  local variant="$1"
  : > "$OUT_BASE/sionna_server.log"
  local gpu_arg="$SIONNA_GPU"
  if [[ "$variant" == "llvm_ad_mono_polarized" ]]; then
    gpu_arg=0
  fi
  local cmd=(
    "$SIONNA_PY" "$NS3_DIR/src/sionna/sionna_v1_server_script.py"
    --path-to-xml-scenario "$SCENE_XML"
    --local-machine
    --port "$SIONNA_PORT"
    --gpu "$gpu_arg"
    --max-depth "$SIONNA_RT_MAX_DEPTH"
    --max-num-paths-per-src "$SIONNA_RT_MAX_PATHS_PER_SRC"
    --samples-per-src "$SIONNA_RT_SAMPLES_PER_SRC"
    --position-threshold "$SIONNA_RT_POSITION_THRESHOLD"
    --angle-threshold "$SIONNA_RT_ANGLE_THRESHOLD"
  )
  if [[ -n "$variant" ]]; then
    PYTHONUNBUFFERED=1 SIONNA_MI_VARIANT="$variant" "${cmd[@]}" > "$OUT_BASE/sionna_server.log" 2>&1 &
  else
    PYTHONUNBUFFERED=1 "${cmd[@]}" > "$OUT_BASE/sionna_server.log" 2>&1 &
  fi
  SIONNA_PID=$!
  local waited=0
  while [[ "$waited" -lt "$SIONNA_SERVER_READY_TIMEOUT" ]]; do
    # With redirected logs, stdout can be buffered; socket bind is a reliable readiness signal.
    if ss -lunH 2>/dev/null | awk '{print $5}' | grep -Eq "127\\.0\\.0\\.1:${SIONNA_PORT}$|0\\.0\\.0\\.0:${SIONNA_PORT}$|\\*:${SIONNA_PORT}$"; then
      return 0
    fi
    if grep -q "Setup complete." "$OUT_BASE/sionna_server.log"; then
      return 0
    fi
    if grep -Eiq "could not initialize optix|optixqueryfunctiontable|jit_optix_api_init|jit_optix_check|optix_error|error creating rtx context" "$OUT_BASE/sionna_server.log"; then
      if kill -0 "$SIONNA_PID" >/dev/null 2>&1; then
        kill "$SIONNA_PID" >/dev/null 2>&1 || true
      fi
      wait "$SIONNA_PID" >/dev/null 2>&1 || true
      return 2
    fi
    if ! kill -0 "$SIONNA_PID" >/dev/null 2>&1; then
      wait "$SIONNA_PID" >/dev/null 2>&1 || true
      return 1
    fi
    sleep 1
    waited=$((waited + 1))
  done

  if kill -0 "$SIONNA_PID" >/dev/null 2>&1; then
    kill "$SIONNA_PID" >/dev/null 2>&1 || true
    wait "$SIONNA_PID" >/dev/null 2>&1 || true
  fi
  return 3
}

if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]]; then
  echo "[2/4] Starting Sionna server..."
  start_rc=0
  start_sionna_server "$SIONNA_MI_VARIANT" || start_rc=$?

  if [[ "$start_rc" -ne 0 ]]; then
    if [[ "$SIONNA_ALLOW_LLVM_FALLBACK" == "1" ]] && [[ "$start_rc" -eq 2 ]]; then
      echo "Sionna server failed with OptiX initialization. Retrying with SIONNA_MI_VARIANT=llvm_ad_mono_polarized."
      if ! start_sionna_server "llvm_ad_mono_polarized"; then
        echo "Sionna server failed even after LLVM fallback. See $OUT_BASE/sionna_server.log"
        exit 1
      fi
    else
      if [[ "$start_rc" -eq 3 ]]; then
        echo "Sionna server did not become ready within ${SIONNA_SERVER_READY_TIMEOUT}s. See $OUT_BASE/sionna_server.log"
      fi
      echo "Sionna server failed to start. See $OUT_BASE/sionna_server.log"
      exit 1
    fi
  fi
  trap cleanup EXIT
else
  echo "[2/4] Remote Sionna mode: expecting server at ${SIONNA_SERVER_IP}:${SIONNA_PORT}"
  echo "       Ensure UDP/${SIONNA_PORT} is reachable from this host."
fi

CASES_CSV="$OUT_BASE/cases.csv"
{
  echo "tx_power_dbm,backend,run_dir"
} > "$CASES_CSV"

echo "[3/4] Running incident sweep..."
for tx in $TX_POWERS; do
  if [[ "$COMPARE_NON_SIONNA" == "1" ]]; then
    run_dir="$OUT_BASE/tx_${tx}/non_sionna"
    args="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 --RngRun=$RNG_RUN --txPower=$tx --sionna=0 --rx-drop-prob-cam=0 --rx-drop-prob-cpm=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 $INCIDENT_ARGS $RADIO_ARGS $EXTRA_ARGS"
    OUT_DIR="$run_dir" \
    NS3_DIR="$NS3_DIR" \
    RUN_ARGS="$args" \
    RUN_RETRIES="$RUN_RETRIES" \
    PLOT="$PLOT_CASE" \
    EXPORT_RESULTS=0 \
      "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"
    echo "$tx,non_sionna,$run_dir" >> "$CASES_CSV"
  fi

  run_dir="$OUT_BASE/tx_${tx}/sionna"
  args="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 --RngRun=$RNG_RUN --txPower=$tx --sionna=1 --sionna-local-machine=$SIONNA_LOCAL_MACHINE --sionna-server-ip=$SIONNA_SERVER_IP --rx-drop-prob-cam=0 --rx-drop-prob-cpm=0 --rx-drop-prob-phy-cam=0 --rx-drop-prob-phy-cpm=0 $INCIDENT_ARGS $RADIO_ARGS $EXTRA_ARGS"
  OUT_DIR="$run_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="$args" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT="$PLOT_CASE" \
  EXPORT_RESULTS=0 \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"
  echo "$tx,sionna,$run_dir" >> "$CASES_CSV"
done

if [[ "$SIONNA_LOCAL_MACHINE" == "1" ]]; then
  cleanup
  trap - EXIT
fi

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

echo "[4/4] Building summary and plots..."
SUMMARY_CSV="$OUT_BASE/sionna_incident_summary.csv"
SUMMARY_PNG="$OUT_BASE/sionna_incident_summary.png"
export CASES_CSV SUMMARY_CSV SUMMARY_PNG
"$PY_BIN" - <<'PY'
import csv
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os

cases_csv = Path(os.environ["CASES_CSV"]).resolve()
summary_csv = Path(os.environ["SUMMARY_CSV"]).resolve()
summary_png = Path(os.environ["SUMMARY_PNG"]).resolve()

rows = []
with cases_csv.open() as f:
    for case in csv.DictReader(f):
        run_dir = Path(case["run_dir"])
        log_path = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
        txt = log_path.read_text(errors="ignore") if log_path.exists() else ""

        m_prr = re.search(r"Average PRR:\s*([0-9.]+)", txt)
        m_lat = re.search(r"Average latency \(ms\):\s*([0-9.]+)", txt)
        avg_prr = float(m_prr.group(1)) if m_prr else math.nan
        avg_latency_ms = float(m_lat.group(1)) if m_lat else math.nan

        ctrl_times = []
        for ctrl_file in sorted((run_dir / "artifacts").glob("*-CTRL.csv")):
            try:
                df = pd.read_csv(ctrl_file, usecols=["time_s"])
            except Exception:
                continue
            t = pd.to_numeric(df["time_s"], errors="coerce").dropna()
            if not t.empty:
                ctrl_times.extend(t.to_list())
        if ctrl_times:
            ctrl_arr = np.array(ctrl_times, dtype=float)
            control_actions = float(len(ctrl_arr))
            first_ctrl = float(np.min(ctrl_arr))
            p90_ctrl = float(np.quantile(ctrl_arr, 0.9))
        else:
            control_actions = 0.0
            first_ctrl = math.nan
            p90_ctrl = math.nan

        risk_summary = run_dir / "artifacts" / "collision_risk" / "collision_risk_summary.csv"
        min_gap_m = math.nan
        min_ttc_s = math.nan
        risky_gap_events = math.nan
        risky_ttc_events = math.nan
        if risk_summary.exists():
            try:
                risk = pd.read_csv(risk_summary)
                if not risk.empty:
                    r = risk.iloc[0]
                    min_gap_m = float(pd.to_numeric(r.get("min_gap_m"), errors="coerce"))
                    min_ttc_s = float(pd.to_numeric(r.get("min_ttc_s"), errors="coerce"))
                    risky_gap_events = float(pd.to_numeric(r.get("risky_gap_events"), errors="coerce"))
                    risky_ttc_events = float(pd.to_numeric(r.get("risky_ttc_events"), errors="coerce"))
            except Exception:
                pass

        rows.append(
            {
                "tx_power_dbm": float(case["tx_power_dbm"]),
                "backend": case["backend"],
                "avg_prr": avg_prr,
                "avg_latency_ms": avg_latency_ms,
                "control_actions": control_actions,
                "first_control_action_s": first_ctrl,
                "p90_control_action_s": p90_ctrl,
                "min_gap_m": min_gap_m,
                "min_ttc_s": min_ttc_s,
                "risky_gap_events": risky_gap_events,
                "risky_ttc_events": risky_ttc_events,
                "run_dir": str(run_dir),
            }
        )

summary = pd.DataFrame(rows).sort_values(["backend", "tx_power_dbm"])
summary.to_csv(summary_csv, index=False)

fig, ax = plt.subplots(2, 2, figsize=(12, 8))
for backend, grp in summary.groupby("backend"):
    g = grp.sort_values("tx_power_dbm")
    ax[0, 0].plot(g["tx_power_dbm"], g["avg_prr"], marker="o", label=backend)
    ax[0, 1].plot(g["tx_power_dbm"], g["avg_latency_ms"], marker="o", label=backend)
    ax[1, 0].plot(g["tx_power_dbm"], g["control_actions"], marker="o", label=backend)
    ax[1, 1].plot(g["tx_power_dbm"], g["min_ttc_s"], marker="o", label=f"{backend} min TTC")

ax[0, 0].set_xlabel("TX power [dBm]")
ax[0, 0].set_ylabel("Average PRR [-]")
ax[0, 0].set_ylim(0, 1.05)
ax[0, 0].grid(alpha=0.3)
ax[0, 0].legend()

ax[0, 1].set_xlabel("TX power [dBm]")
ax[0, 1].set_ylabel("Average latency [ms]")
ax[0, 1].grid(alpha=0.3)
ax[0, 1].legend()

ax[1, 0].set_xlabel("TX power [dBm]")
ax[1, 0].set_ylabel("Control actions [count]")
ax[1, 0].grid(alpha=0.3)
ax[1, 0].legend()

ax2 = ax[1, 1].twinx()
for backend, grp in summary.groupby("backend"):
    g = grp.sort_values("tx_power_dbm")
    ax2.plot(g["tx_power_dbm"], g["min_gap_m"], marker="s", linestyle="--", label=f"{backend} min gap")

ax[1, 1].set_xlabel("TX power [dBm]")
ax[1, 1].set_ylabel("Min TTC [s]")
ax2.set_ylabel("Min gap [m]")
ax[1, 1].grid(alpha=0.3)
h1, l1 = ax[1, 1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax[1, 1].legend(h1 + h2, l1 + l2, loc="best")

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)

print(summary_csv)
print(summary_png)
PY

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_BASE" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for Sionna incident sweep"
  fi
fi

echo "Done:"
echo "  $SUMMARY_CSV"
echo "  $SUMMARY_PNG"
