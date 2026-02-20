#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/rssi-safety-sweep-$(date +%H%M%S)}"
TX_POWERS="${TX_POWERS:-23 17 11}"
RNG_RUN="${RNG_RUN:-1}"

SIM_TIME_CAM="${SIM_TIME_CAM:-20}"
SIM_TIME_EVA="${SIM_TIME_EVA:-40}"
SUMO_GUI="${SUMO_GUI:-0}"

EVA_INCIDENT_ARGS="${EVA_INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
EVA_RADIO_ARGS="${EVA_RADIO_ARGS:---enableSensing=1 --enableChannelRandomness=1 --channelUpdatePeriod=100 --slThresPsschRsrp=-126}"
CAM_EXTRA_ARGS="${CAM_EXTRA_ARGS:-}"
EVA_EXTRA_ARGS="${EVA_EXTRA_ARGS:-}"

RUN_RETRIES="${RUN_RETRIES:-3}"
ENABLE_COLLISION_OUTPUT="${ENABLE_COLLISION_OUTPUT:-1}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"

mkdir -p "$OUT_BASE"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_BASE/rssi_safety_summary.csv"
{
  echo "tx_power_dbm,cam_mean_rssi_dbm,cam_p10_rssi_dbm,cam_mean_snr_db,cam_avg_prr,eva_avg_prr,eva_avg_latency_ms,eva_control_actions,eva_first_control_action_s,eva_p90_control_action_s,eva_min_ttc_s,eva_min_gap_m,cam_run_dir,eva_run_dir"
} > "$SUMMARY_CSV"

for tx in $TX_POWERS; do
  tag="tx_${tx//./p}"
  cam_dir="$OUT_BASE/$tag/cam"
  eva_dir="$OUT_BASE/$tag/eva"

  echo "[tx=$tx] Running CAM benchmark for RSSI/PRR..."
  OUT_DIR="$cam_dir" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME_CAM --sionna=0 --tx-power=$tx --RngRun=$RNG_RUN $CAM_EXTRA_ARGS" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  EXPORT_RESULTS=0 \
    "$ROOT/scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh"

  echo "[tx=$tx] Running EVA incident scenario for safety metrics..."
  OUT_DIR="$eva_dir" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME_EVA --met-sup=1 --RngRun=$RNG_RUN --txPower=$tx --rx-drop-prob-cam=0 --rx-drop-prob-cpm=0 $EVA_INCIDENT_ARGS $EVA_RADIO_ARGS $EVA_EXTRA_ARGS" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  ENABLE_COLLISION_OUTPUT="$ENABLE_COLLISION_OUTPUT" \
  EXPORT_RESULTS=0 \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  export TX_DBM="$tx" CAM_DIR="$cam_dir" EVA_DIR="$eva_dir"
  row="$("$PY_BIN" - <<'PY'
import math
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

tx = float(os.environ["TX_DBM"])
cam_dir = Path(os.environ["CAM_DIR"])
eva_dir = Path(os.environ["EVA_DIR"])

cam_mean_rssi = math.nan
cam_p10_rssi = math.nan
cam_mean_snr = math.nan
cam_avg_prr = math.nan

phy_csv = cam_dir / "artifacts" / "phy_with_sionna_nrv2x.csv"
if phy_csv.exists():
    try:
        phy = pd.read_csv(phy_csv)
        if "rssi" in phy.columns:
            rssi = pd.to_numeric(phy["rssi"], errors="coerce").dropna()
            if not rssi.empty:
                cam_mean_rssi = float(rssi.mean())
                cam_p10_rssi = float(rssi.quantile(0.1))
        if "snr" in phy.columns:
            snr = pd.to_numeric(phy["snr"], errors="coerce").dropna()
            if not snr.empty:
                cam_mean_snr = float(snr.mean())
    except Exception:
        pass

cam_out = cam_dir / "artifacts" / "v2v-cam-exchange-sionna-nrv2x_output.txt"
if cam_out.exists():
    txt = cam_out.read_text(errors="ignore")
    m = re.search(r"Average PRR:\s*([0-9.]+)", txt)
    if m:
        cam_avg_prr = float(m.group(1))

eva_avg_prr = math.nan
eva_avg_latency = math.nan
eva_control_actions = 0.0
eva_first_ctrl = math.nan
eva_p90_ctrl = math.nan
eva_min_ttc = math.nan
eva_min_gap = math.nan

eva_log = eva_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
if eva_log.exists():
    txt = eva_log.read_text(errors="ignore")
    m = re.search(r"Average PRR:\s*([0-9.]+)", txt)
    if m:
        eva_avg_prr = float(m.group(1))
    m = re.search(r"Average latency \(ms\):\s*([0-9.]+)", txt)
    if m:
        eva_avg_latency = float(m.group(1))

ctrl_times = []
for ctrl_file in sorted((eva_dir / "artifacts").glob("*-CTRL.csv")):
    try:
        df = pd.read_csv(ctrl_file)
    except Exception:
        continue
    if df.empty or "time_s" not in df.columns:
        continue
    t = pd.to_numeric(df["time_s"], errors="coerce").dropna()
    if not t.empty:
        ctrl_times.extend(t.to_list())

if ctrl_times:
    arr = np.array(ctrl_times, dtype=float)
    eva_control_actions = float(len(arr))
    eva_first_ctrl = float(arr.min())
    eva_p90_ctrl = float(np.quantile(arr, 0.9))

risk_csv = eva_dir / "artifacts" / "collision_risk" / "collision_risk_summary.csv"
if risk_csv.exists():
    try:
        risk = pd.read_csv(risk_csv)
        if not risk.empty:
            row = risk.iloc[0]
            eva_min_ttc = float(pd.to_numeric(row.get("min_ttc_s"), errors="coerce"))
            eva_min_gap = float(pd.to_numeric(row.get("min_gap_m"), errors="coerce"))
    except Exception:
        pass

vals = [
    tx,
    cam_mean_rssi,
    cam_p10_rssi,
    cam_mean_snr,
    cam_avg_prr,
    eva_avg_prr,
    eva_avg_latency,
    eva_control_actions,
    eva_first_ctrl,
    eva_p90_ctrl,
    eva_min_ttc,
    eva_min_gap,
    str(cam_dir),
    str(eva_dir),
]

def f(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return ""
    return str(v)

print(",".join(f(v) for v in vals))
PY
)"
  echo "$row" >> "$SUMMARY_CSV"
done

PLOT_PNG="$OUT_BASE/rssi_safety_summary.png"
export SUMMARY_CSV PLOT_PNG
"$PY_BIN" - <<'PY'
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

summary = pd.read_csv(Path(os.environ["SUMMARY_CSV"]))
summary = summary.sort_values("tx_power_dbm")

fig, ax = plt.subplots(2, 2, figsize=(11, 8))

ax[0, 0].plot(summary["tx_power_dbm"], summary["cam_mean_rssi_dbm"], marker="o")
ax[0, 0].set_xlabel("TX power [dBm]")
ax[0, 0].set_ylabel("Mean RSSI [dBm]")
ax[0, 0].grid(alpha=0.3)

ax[0, 1].plot(summary["cam_mean_rssi_dbm"], summary["cam_avg_prr"], marker="o", label="CAM PRR")
ax[0, 1].plot(summary["cam_mean_rssi_dbm"], summary["eva_avg_prr"], marker="s", label="EVA PRR")
ax[0, 1].set_xlabel("Mean RSSI [dBm]")
ax[0, 1].set_ylabel("PRR [-]")
ax[0, 1].set_ylim(0, 1.05)
ax[0, 1].grid(alpha=0.3)
ax[0, 1].legend()

ax[1, 0].plot(summary["cam_mean_rssi_dbm"], summary["eva_control_actions"], marker="o")
ax[1, 0].set_xlabel("Mean RSSI [dBm]")
ax[1, 0].set_ylabel("Control actions [count]")
ax[1, 0].grid(alpha=0.3)

ax[1, 1].plot(summary["cam_mean_rssi_dbm"], summary["eva_first_control_action_s"], marker="o", label="First control action")
ax[1, 1].plot(summary["cam_mean_rssi_dbm"], summary["eva_p90_control_action_s"], marker="s", label="P90 control action")
ax[1, 1].set_xlabel("Mean RSSI [dBm]")
ax[1, 1].set_ylabel("Control action time [s]")
ax[1, 1].grid(alpha=0.3)
ax[1, 1].legend()

fig.tight_layout()
fig.savefig(Path(os.environ["PLOT_PNG"]), dpi=150)
plt.close(fig)

print(Path(os.environ["SUMMARY_CSV"]))
print(Path(os.environ["PLOT_PNG"]))
PY

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_BASE" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for RSSI safety sweep"
  fi
fi

echo "Done:"
echo "  $SUMMARY_CSV"
echo "  $PLOT_PNG"
