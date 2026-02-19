#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-loss-sweep-$(date +%H%M%S)}"
SIM_TIME="${SIM_TIME:-40}"
LOSS_PROBS="${LOSS_PROBS:-0.0 0.3 0.6}"
BASE_RADIO_ARGS="${BASE_RADIO_ARGS:---enableSensing=0 --txPower=23 --slThresPsschRsrp=-128}"
RUN_RETRIES="${RUN_RETRIES:-3}"
PLOT="${PLOT:-1}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"

mkdir -p "$OUT_BASE"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

CASES_CSV="$OUT_BASE/cases.csv"
{
  echo "case_id,rx_drop_prob_cam,run_dir"
} > "$CASES_CSV"

for prob in $LOSS_PROBS; do
  case_id="drop_${prob//./p}"
  case_dir="$OUT_BASE/$case_id"
  run_args="--sumo-gui=0 --sim-time=$SIM_TIME --met-sup=1 --rx-drop-prob-cam=$prob --rx-drop-prob-cpm=0 $BASE_RADIO_ARGS"

  OUT_DIR="$case_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="$run_args" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT="$PLOT" \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,$prob,$case_dir" >> "$CASES_CSV"
done

SUMMARY_CSV="$OUT_BASE/loss_sweep_summary.csv"
SUMMARY_PNG="$OUT_BASE/loss_sweep_summary.png"
export CASES_CSV SUMMARY_CSV SUMMARY_PNG
"$PY_BIN" - <<'PY'
import csv
import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

cases_csv = Path(os.environ["CASES_CSV"])
summary_csv = Path(os.environ["SUMMARY_CSV"])
summary_png = Path(os.environ["SUMMARY_PNG"])

rows = []
with cases_csv.open() as f:
    reader = csv.DictReader(f)
    for case in reader:
        run_dir = Path(case["run_dir"])
        log_path = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
        log_text = log_path.read_text(errors="ignore") if log_path.exists() else ""

        m_prr = re.search(r"Average PRR:\s*([0-9.]+)", log_text)
        m_lat = re.search(r"Average latency \(ms\):\s*([0-9.]+)", log_text)
        avg_prr = float(m_prr.group(1)) if m_prr else np.nan
        avg_latency_ms = float(m_lat.group(1)) if m_lat else np.nan

        risk_csv = run_dir / "artifacts" / "collision_risk" / "collision_risk_summary.csv"
        if risk_csv.exists():
            risk_df = pd.read_csv(risk_csv)
            risk_row = risk_df.iloc[0]
            min_gap_m = pd.to_numeric(risk_row.get("min_gap_m"), errors="coerce")
            min_ttc_s = pd.to_numeric(risk_row.get("min_ttc_s"), errors="coerce")
            risky_gap_events = pd.to_numeric(risk_row.get("risky_gap_events"), errors="coerce")
            risky_ttc_events = pd.to_numeric(risk_row.get("risky_ttc_events"), errors="coerce")
        else:
            min_gap_m = np.nan
            min_ttc_s = np.nan
            risky_gap_events = np.nan
            risky_ttc_events = np.nan

        ctrl_events = 0
        for ctrl_file in sorted((run_dir / "artifacts").glob("*-CTRL.csv")):
            try:
                ctrl_events += len(pd.read_csv(ctrl_file).index)
            except Exception:
                pass

        cam_drop_app = 0
        cam_rx_ok = 0
        for msg_file in sorted((run_dir / "artifacts").glob("*-MSG.csv")):
            try:
                msg = pd.read_csv(msg_file)
            except Exception:
                continue
            if "msg_type" not in msg.columns:
                continue
            msg_type = msg["msg_type"].astype(str)
            cam_drop_app += int((msg_type == "CAM_DROP_APP").sum())
            if "rx_ok" in msg.columns:
                rx_ok = pd.to_numeric(msg["rx_ok"], errors="coerce").fillna(0)
                cam_rx_ok += int(((msg_type == "CAM") & (rx_ok > 0)).sum())

        denom = cam_drop_app + cam_rx_ok
        observed_cam_drop_ratio = float(cam_drop_app / denom) if denom > 0 else np.nan

        rows.append(
            {
                "case_id": case["case_id"],
                "rx_drop_prob_cam": float(case["rx_drop_prob_cam"]),
                "avg_prr": avg_prr,
                "avg_latency_ms": avg_latency_ms,
                "min_gap_m": min_gap_m,
                "min_ttc_s": min_ttc_s,
                "risky_gap_events": risky_gap_events,
                "risky_ttc_events": risky_ttc_events,
                "control_actions": ctrl_events,
                "cam_drop_app_events": cam_drop_app,
                "cam_rx_ok_events": cam_rx_ok,
                "observed_cam_drop_ratio": observed_cam_drop_ratio,
                "run_dir": str(run_dir),
            }
        )

summary = pd.DataFrame(rows).sort_values("rx_drop_prob_cam")
summary.to_csv(summary_csv, index=False)

fig, ax = plt.subplots(2, 2, figsize=(10, 7))
x = summary["rx_drop_prob_cam"].to_numpy()

ax[0, 0].plot(x, summary["avg_prr"], marker="o", label="Average PRR")
if "observed_cam_drop_ratio" in summary:
    ax[0, 0].plot(x, summary["observed_cam_drop_ratio"], marker="s", label="Observed CAM drop ratio")
ax[0, 0].set_xlabel("Injected CAM drop probability")
ax[0, 0].set_ylabel("Ratio")
ax[0, 0].set_ylim(0, 1.05)
ax[0, 0].grid(alpha=0.3)
ax[0, 0].legend()

ax[0, 1].plot(x, summary["avg_latency_ms"], marker="o", color="#ff7f0e")
ax[0, 1].set_xlabel("Injected CAM drop probability")
ax[0, 1].set_ylabel("Average latency [ms]")
ax[0, 1].grid(alpha=0.3)

ax[1, 0].plot(x, summary["risky_ttc_events"], marker="o", label="Risky TTC events")
ax[1, 0].plot(x, summary["risky_gap_events"], marker="s", label="Risky gap events")
ax[1, 0].set_xlabel("Injected CAM drop probability")
ax[1, 0].set_ylabel("Events")
ax[1, 0].grid(alpha=0.3)
ax[1, 0].legend()

ax[1, 1].plot(x, summary["control_actions"], marker="o", label="Control actions")
ax[1, 1].plot(x, summary["min_ttc_s"], marker="s", label="Min TTC [s]")
ax[1, 1].set_xlabel("Injected CAM drop probability")
ax[1, 1].grid(alpha=0.3)
ax[1, 1].legend()

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)

print(summary_csv)
print(summary_png)
PY

echo "Sweep done:"
echo "  $SUMMARY_CSV"
echo "  $SUMMARY_PNG"
