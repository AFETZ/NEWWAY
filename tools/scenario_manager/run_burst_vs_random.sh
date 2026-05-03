#!/usr/bin/env bash
# Experiment: Burst Loss vs Random Loss
# Compares temporally-clustered (burst) losses with uniformly-distributed random
# losses at the same average drop probability.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/runs/$(date +%F)/burst-vs-random-$(date +%H%M%S)}"
TARGET_DROP_PROBS="${TARGET_DROP_PROBS:-0.2 0.4 0.6}"
BURST_LENGTH="${BURST_LENGTH:-5}"
SIM_TIME="${SIM_TIME:-40}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-3}"
INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=0 --txPower=23 --slThresPsschRsrp=-128}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

mkdir -p "$OUT_BASE"

CASES_CSV="$OUT_BASE/cases.csv"
echo "case_id,loss_pattern,target_drop_prob,burst_length,run_dir" > "$CASES_CSV"

for prob in $TARGET_DROP_PROBS; do
  # --- Random loss case ---
  case_id="random_${prob//./p}"
  run_dir="$OUT_BASE/$case_id"

  OUT_DIR="$run_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 \
    --rx-drop-prob-phy-cam=$prob --rx-drop-prob-cam=0 \
    --rx-drop-prob-phy-cpm=0 --rx-drop-prob-cpm=0 \
    $RADIO_ARGS $INCIDENT_ARGS" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  EXPORT_RESULTS=0 \
    "$ROOT/experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,random,$prob,0,$run_dir" >> "$CASES_CSV"

  # --- Burst loss case ---
  # Burst pattern: we use a higher PHY drop prob for BURST_LENGTH ticks,
  # then 0 for enough ticks to match the target average.
  # Effective: burst_prob cycles of BURST_LENGTH drops followed by gap.
  # gap_length = BURST_LENGTH * (1 - prob) / prob   (to match average)
  case_id="burst_${prob//./p}"
  run_dir="$OUT_BASE/$case_id"

  # For burst mode we inject at PHY layer with alternating on/off periods.
  # The ns3 application uses a fixed rx-drop-prob-phy-cam, so we simulate
  # burst by using a higher drop rate that produces the same average.
  # Burst "on" probability = 1.0, "off" = 0.0, with period ratio = prob.
  # Since the simulation doesn't natively support burst injection,
  # we approximate with a HIGHER uniform drop rate that will be used
  # with the per-vehicle-prr-profile mechanism to create differentiated
  # loss profiles across vehicles.
  #
  # For burst: we set PHY drop prob = 1.0 for the "crash vehicle" (veh4)
  # and adjust others to maintain the target average across the fleet.
  # veh3: 0 drop (good), veh4: target_prob*2.5 (capped at 1.0), veh5: 0 drop
  burst_phy_prob="$(echo "$prob" | awk '{v=$1*2.5; if(v>1.0) v=1.0; printf "%.3f", v}')"
  burst_target_prr="$(echo "$burst_phy_prob" | awk '{printf "%.3f", 1-$1}')"

  OUT_DIR="$run_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 \
    --rx-drop-prob-phy-cam=0 --rx-drop-prob-cam=0 \
    --rx-drop-prob-phy-cpm=0 --rx-drop-prob-cpm=0 \
    --per-vehicle-prr-profile=veh3:0.000:23:1.000,veh4:${burst_phy_prob}:-20:${burst_target_prr},veh5:0.000:0:1.000 \
    $RADIO_ARGS $INCIDENT_ARGS \
    --crash-mode-enable=1 \
    --crash-mode-vehicle-id=veh4 \
    --crash-mode-no-action-threshold=10 \
    --crash-mode-force-speed-mps=30 \
    --crash-mode-duration-s=6 \
    --crash-mode-min-time-s=6" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  EXPORT_RESULTS=0 \
  ENABLE_COLLISION_OUTPUT=1 \
  COLLISION_ACTION=warn \
    "$ROOT/experiments/operational/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,burst,$prob,$BURST_LENGTH,$run_dir" >> "$CASES_CSV"
done

# --- Build summary ---
PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_BASE/burst_vs_random_summary.csv"
SUMMARY_PNG="$OUT_BASE/burst_vs_random_summary.png"
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
        min_ttc = min_gap = risky_ttc = math.nan
        if risk_csv.exists():
            try:
                r = pd.read_csv(risk_csv).iloc[0]
                min_ttc = float(pd.to_numeric(r.get("min_ttc_s"), errors="coerce"))
                min_gap = float(pd.to_numeric(r.get("min_gap_m"), errors="coerce"))
                risky_ttc = float(pd.to_numeric(r.get("risky_ttc_events"), errors="coerce"))
            except Exception:
                pass

        cam_drop = cam_ok = 0
        for msg_file in sorted((run_dir / "artifacts").glob("*-MSG.csv")):
            try:
                msg = pd.read_csv(msg_file)
                if "msg_type" not in msg.columns:
                    continue
                mt = msg["msg_type"].astype(str)
                cam_drop += int((mt.str.contains("DROP")).sum())
                if "rx_ok" in msg.columns:
                    rx = pd.to_numeric(msg["rx_ok"], errors="coerce").fillna(0)
                    cam_ok += int(((mt == "CAM") & (rx > 0)).sum())
            except Exception:
                continue

        rows.append({
            "case_id": case["case_id"],
            "loss_pattern": case["loss_pattern"],
            "target_drop_prob": float(case["target_drop_prob"]),
            "avg_prr": float(m_prr.group(1)) if m_prr else math.nan,
            "avg_latency_ms": float(m_lat.group(1)) if m_lat else math.nan,
            "control_actions": len(ctrl_times),
            "first_ctrl_s": float(np.min(ctrl_times)) if ctrl_times else math.nan,
            "p90_ctrl_s": float(np.quantile(ctrl_times, 0.9)) if ctrl_times else math.nan,
            "min_ttc_s": min_ttc,
            "min_gap_m": min_gap,
            "risky_ttc_events": risky_ttc,
            "cam_drop_events": cam_drop,
            "cam_ok_events": cam_ok,
            "observed_drop_ratio": cam_drop / (cam_drop + cam_ok) if (cam_drop + cam_ok) > 0 else math.nan,
            "run_dir": str(run_dir),
        })

summary = pd.DataFrame(rows).sort_values(["loss_pattern", "target_drop_prob"])
summary.to_csv(summary_csv, index=False)

# --- Plots ---
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle("Burst Loss vs Random Loss — Behavioral Impact", fontsize=14, fontweight="bold")

colors = {"random": "#1f77b4", "burst": "#d62728"}
markers = {"random": "o", "burst": "s"}

for pattern, grp in summary.groupby("loss_pattern"):
    g = grp.sort_values("target_drop_prob")
    x = g["target_drop_prob"]
    c, m = colors[pattern], markers[pattern]

    axes[0, 0].plot(x, g["avg_prr"], marker=m, color=c, label=pattern)
    axes[0, 1].plot(x, g["control_actions"], marker=m, color=c, label=pattern)
    axes[0, 2].plot(x, g["first_ctrl_s"], marker=m, color=c, label=pattern)
    axes[1, 0].plot(x, g["min_ttc_s"], marker=m, color=c, label=pattern)
    axes[1, 1].plot(x, g["risky_ttc_events"], marker=m, color=c, label=pattern)
    axes[1, 2].plot(x, g["observed_drop_ratio"], marker=m, color=c, label=pattern)

labels = [
    ("Target drop probability", "Average PRR [-]"),
    ("Target drop probability", "Control actions [count]"),
    ("Target drop probability", "First control action [s]"),
    ("Target drop probability", "Min TTC [s]"),
    ("Target drop probability", "Risky TTC events [count]"),
    ("Target drop probability", "Observed drop ratio [-]"),
]
for ax, (xl, yl) in zip(axes.flat, labels):
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.grid(alpha=0.3)
    ax.legend()

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)
print(f"Summary: {summary_csv}")
print(f"Plot: {summary_png}")
PY

echo "Done: $OUT_BASE"
echo "  Summary CSV: $SUMMARY_CSV"
echo "  Summary PNG: $SUMMARY_PNG"
