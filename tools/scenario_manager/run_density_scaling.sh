#!/usr/bin/env bash
# Experiment: Vehicle Density Impact on V2X Safety
# Sweeps the number of transmitting vehicles (3 / 5 / 8) to measure how
# Mode 2 channel congestion degrades PRR and safety metrics.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/runs/$(date +%F)/density-scaling-$(date +%H%M%S)}"
DENSITIES="${DENSITIES:-3 5 8}"
SIM_TIME="${SIM_TIME:-40}"
TX_POWER="${TX_POWER:-23}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-3}"
INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

mkdir -p "$OUT_BASE"

CASES_CSV="$OUT_BASE/cases.csv"
echo "case_id,num_vehicles,density_label,sumo_config,run_dir" > "$CASES_CSV"

for n in $DENSITIES; do
  case "$n" in
    3|light|threeflow)
      density_level="3"
      density_label="light"
      sumo_config="src/automotive/examples/sumo_files_v2v_map/map_incident_threeflow.sumo.cfg"
      ;;
    5|medium|platoon)
      density_level="5"
      density_label="medium"
      sumo_config="src/automotive/examples/sumo_files_v2v_map/map_incident_platoon.sumo.cfg"
      ;;
    8|dense)
      density_level="8"
      density_label="dense"
      sumo_config="src/automotive/examples/sumo_files_v2v_map/map_incident_dense.sumo.cfg"
      ;;
    *)
      echo "Unsupported density preset '$n'. Use 3 5 8 (or light medium dense)." >&2
      exit 1
      ;;
  esac

  case_id="density_${density_level}_${density_label}"
  run_dir="$OUT_BASE/$case_id"

  OUT_DIR="$run_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 \
    --txPower=$TX_POWER \
    --sumo-config=$sumo_config \
    --rx-drop-prob-phy-cam=0 --rx-drop-prob-cam=0 \
    --rx-drop-prob-phy-cpm=0 --rx-drop-prob-cpm=0 \
    --enableSensing=1 --enableChannelRandomness=1 --channelUpdatePeriod=100 \
    --slThresPsschRsrp=-126 \
    $INCIDENT_ARGS" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  EXPORT_RESULTS=0 \
  ENABLE_COLLISION_OUTPUT=1 \
  COLLISION_ACTION=warn \
    "$ROOT/experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,$density_level,$density_label,$sumo_config,$run_dir" >> "$CASES_CSV"
done

# --- Build summary ---
PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_BASE/density_scaling_summary.csv"
SUMMARY_PNG="$OUT_BASE/density_scaling_summary.png"
export CASES_CSV SUMMARY_CSV SUMMARY_PNG
"$PY_BIN" - <<'PY'
import csv, math, os, re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

cases_csv = Path(os.environ["CASES_CSV"])
summary_csv = Path(os.environ["SUMMARY_CSV"])
summary_png = Path(os.environ["SUMMARY_PNG"])

rows = []
with cases_csv.open() as f:
    for case in csv.DictReader(f):
        run_dir = Path(case["run_dir"])
        log_path = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
        txt = log_path.read_text(errors="ignore") if log_path.exists() else ""

        m_prr = re.search(r"Average PRR:\s*([0-9.]+)", txt)
        m_lat = re.search(r"Average latency \(ms\):\s*([0-9.]+)", txt)

        ctrl_times = []
        for ctrl_file in sorted((run_dir / "artifacts").glob("*-CTRL.csv")):
            try:
                df = pd.read_csv(ctrl_file)
                if "time_s" in df.columns:
                    t = pd.to_numeric(df["time_s"], errors="coerce").dropna()
                    ctrl_times.extend(t.tolist())
            except Exception:
                continue

        risk_csv = run_dir / "artifacts" / "collision_risk" / "collision_risk_summary.csv"
        min_ttc = min_gap = risky_ttc = risky_gap = math.nan
        if risk_csv.exists():
            try:
                r = pd.read_csv(risk_csv).iloc[0]
                min_ttc = float(pd.to_numeric(r.get("min_ttc_s"), errors="coerce"))
                min_gap = float(pd.to_numeric(r.get("min_gap_m"), errors="coerce"))
                risky_ttc = float(pd.to_numeric(r.get("risky_ttc_events"), errors="coerce"))
                risky_gap = float(pd.to_numeric(r.get("risky_gap_events"), errors="coerce"))
            except Exception:
                pass

        cam_total = cam_ok = 0
        for msg_file in sorted((run_dir / "artifacts").glob("*-MSG.csv")):
            try:
                msg = pd.read_csv(msg_file)
                if "msg_type" not in msg.columns:
                    continue
                mt = msg["msg_type"].astype(str)
                cam_total += len(mt)
                if "rx_ok" in msg.columns:
                    rx = pd.to_numeric(msg["rx_ok"], errors="coerce").fillna(0)
                    cam_ok += int(((mt == "CAM") & (rx > 0)).sum())
            except Exception:
                continue

        rows.append({
            "num_vehicles": int(case["num_vehicles"]),
            "density_label": case["density_label"],
            "sumo_config": case["sumo_config"],
            "avg_prr": float(m_prr.group(1)) if m_prr else math.nan,
            "avg_latency_ms": float(m_lat.group(1)) if m_lat else math.nan,
            "control_actions": len(ctrl_times),
            "first_ctrl_s": float(np.min(ctrl_times)) if ctrl_times else math.nan,
            "p90_ctrl_s": float(np.quantile(ctrl_times, 0.9)) if ctrl_times else math.nan,
            "min_ttc_s": min_ttc,
            "min_gap_m": min_gap,
            "risky_ttc_events": risky_ttc,
            "risky_gap_events": risky_gap,
            "total_cam_events": cam_total,
            "cam_ok_events": cam_ok,
            "run_dir": str(run_dir),
        })

summary = pd.DataFrame(rows).sort_values("num_vehicles")
summary.to_csv(summary_csv, index=False)

# --- Plots ---
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("Vehicle Density Impact on V2X Safety", fontsize=14, fontweight="bold")
x = summary["num_vehicles"]

axes[0, 0].bar(x, summary["avg_prr"], color="#1f77b4", width=0.8)
axes[0, 0].set_ylabel("Average PRR [-]")
axes[0, 0].set_ylim(0, 1.05)

axes[0, 1].bar(x, summary["avg_latency_ms"], color="#ff7f0e", width=0.8)
axes[0, 1].set_ylabel("Average latency [ms]")

axes[0, 2].bar(x, summary["control_actions"], color="#2ca02c", width=0.8)
axes[0, 2].set_ylabel("Control actions [count]")

axes[1, 0].bar(x, summary["min_ttc_s"], color="#d62728", width=0.8)
axes[1, 0].set_ylabel("Min TTC [s]")
axes[1, 0].axhline(y=3.0, color="black", linestyle="--", alpha=0.5, label="TTC=3s threshold")
axes[1, 0].legend()

axes[1, 1].bar(x - 0.2, summary["risky_ttc_events"], width=0.4, label="Risky TTC", color="#9467bd")
axes[1, 1].bar(x + 0.2, summary["risky_gap_events"], width=0.4, label="Risky gap", color="#8c564b")
axes[1, 1].set_ylabel("Risky events [count]")
axes[1, 1].legend()

axes[1, 2].bar(x, summary["total_cam_events"], color="#e377c2", width=0.8)
axes[1, 2].set_ylabel("Total CAM events [count]")

for ax in axes.flat:
    ax.set_xlabel("Number of vehicles")
    ax.grid(alpha=0.3, axis="y")
    ax.set_xticks(x)

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)
print(f"Summary: {summary_csv}")
print(f"Plot: {summary_png}")
PY

echo "Done: $OUT_BASE"
echo "  Summary CSV: $SUMMARY_CSV"
echo "  Summary PNG: $SUMMARY_PNG"
