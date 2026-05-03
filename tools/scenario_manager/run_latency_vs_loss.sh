#!/usr/bin/env bash
# Experiment: Latency vs Loss Trade-off
# Sweeps PHY-level loss probability (with delay=0) and then channel delay
# (with loss=0) to compare which impairment affects safety more.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/latency-vs-loss-$(date +%H%M%S)}"
LOSS_PROBS="${LOSS_PROBS:-0.0 0.2 0.4}"
T1_DELAYS="${T1_DELAYS:-${EXTRA_DELAYS_MS:-2 8 16}}"
SIM_TIME="${SIM_TIME:-40}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-3}"
INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=0 --txPower=23 --slThresPsschRsrp=-128}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
"$ROOT/scripts/sync-overlay-into-bootstrap-ns3.sh" --root "$ROOT" --ns3-dir "$NS3_DIR"

mkdir -p "$OUT_BASE"

CASES_CSV="$OUT_BASE/cases.csv"
echo "case_id,impairment,loss_prob,t1_delay,run_dir" > "$CASES_CSV"

# --- Loss sweep (delay=0) ---
for prob in $LOSS_PROBS; do
  case_id="loss_${prob//./p}"
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
  ENABLE_COLLISION_OUTPUT=1 \
  COLLISION_ACTION=warn \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,loss,$prob,0,$run_dir" >> "$CASES_CSV"
done

# --- Delay-proxy sweep (loss=0) ---
for t1 in $T1_DELAYS; do
  case_id="delay_t1_${t1}"
  run_dir="$OUT_BASE/$case_id"

  # The EVA scenario supports the NR sidelink processing-delay proxy `t1`.
  OUT_DIR="$run_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="--sumo-gui=$SUMO_GUI --sim-time=$SIM_TIME --met-sup=1 \
    --rx-drop-prob-phy-cam=0 --rx-drop-prob-cam=0 \
    --rx-drop-prob-phy-cpm=0 --rx-drop-prob-cpm=0 \
    --t1=$t1 \
    $RADIO_ARGS $INCIDENT_ARGS" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT=0 \
  EXPORT_RESULTS=0 \
  ENABLE_COLLISION_OUTPUT=1 \
  COLLISION_ACTION=warn \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,delay,0,$t1,$run_dir" >> "$CASES_CSV"
done

# --- Build summary ---
PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

SUMMARY_CSV="$OUT_BASE/latency_vs_loss_summary.csv"
SUMMARY_PNG="$OUT_BASE/latency_vs_loss_summary.png"
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

        rows.append({
            "case_id": case["case_id"],
            "impairment": case["impairment"],
            "loss_prob": float(case["loss_prob"]),
            "t1_delay": float(case["t1_delay"]),
            "avg_prr": float(m_prr.group(1)) if m_prr else math.nan,
            "avg_latency_ms": float(m_lat.group(1)) if m_lat else math.nan,
            "control_actions": len(ctrl_times),
            "first_ctrl_s": float(np.min(ctrl_times)) if ctrl_times else math.nan,
            "p90_ctrl_s": float(np.quantile(ctrl_times, 0.9)) if ctrl_times else math.nan,
            "min_ttc_s": min_ttc,
            "min_gap_m": min_gap,
            "risky_ttc_events": risky_ttc,
            "run_dir": str(run_dir),
        })

summary = pd.DataFrame(rows)
summary.to_csv(summary_csv, index=False)

# --- Plots: side by side comparison ---
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Latency vs Loss Trade-off — Impact on V2X Safety", fontsize=14, fontweight="bold")

loss_df = summary[summary["impairment"] == "loss"].sort_values("loss_prob")
delay_df = summary[summary["impairment"] == "delay"].sort_values("t1_delay")

# Row 1: Loss sweep
if not loss_df.empty:
    x_loss = loss_df["loss_prob"]
    axes[0, 0].plot(x_loss, loss_df["avg_prr"], "o-", color="#1f77b4")
    axes[0, 0].set_xlabel("PHY loss probability")
    axes[0, 0].set_ylabel("Average PRR [-]")
    axes[0, 0].set_ylim(0, 1.05)
    axes[0, 0].set_title("Loss sweep: PRR")

    axes[0, 1].plot(x_loss, loss_df["control_actions"], "o-", color="#2ca02c")
    axes[0, 1].set_xlabel("PHY loss probability")
    axes[0, 1].set_ylabel("Control actions")
    axes[0, 1].set_title("Loss sweep: Control actions")

    axes[0, 2].plot(x_loss, loss_df["first_ctrl_s"], "o-", color="#d62728", label="First action")
    axes[0, 2].plot(x_loss, loss_df["min_ttc_s"], "s--", color="#9467bd", label="Min TTC")
    axes[0, 2].set_xlabel("PHY loss probability")
    axes[0, 2].set_ylabel("Time [s]")
    axes[0, 2].set_title("Loss sweep: Timing & Safety")
    axes[0, 2].legend()

# Row 2: Delay sweep
if not delay_df.empty:
    x_delay = delay_df["t1_delay"]
    axes[1, 0].plot(x_delay, delay_df["avg_latency_ms"], "o-", color="#ff7f0e")
    axes[1, 0].set_xlabel("T1 delay [slots]")
    axes[1, 0].set_ylabel("Measured latency [ms]")
    axes[1, 0].set_title("Delay sweep: Latency")

    axes[1, 1].plot(x_delay, delay_df["control_actions"], "o-", color="#2ca02c")
    axes[1, 1].set_xlabel("T1 delay [slots]")
    axes[1, 1].set_ylabel("Control actions")
    axes[1, 1].set_title("Delay sweep: Control actions")

    axes[1, 2].plot(x_delay, delay_df["first_ctrl_s"], "o-", color="#d62728", label="First action")
    axes[1, 2].plot(x_delay, delay_df["min_ttc_s"], "s--", color="#9467bd", label="Min TTC")
    axes[1, 2].set_xlabel("T1 delay [slots]")
    axes[1, 2].set_ylabel("Time [s]")
    axes[1, 2].set_title("Delay sweep: Timing & Safety")
    axes[1, 2].legend()

for ax in axes.flat:
    ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)
print(f"Summary: {summary_csv}")
print(f"Plot: {summary_png}")
PY

echo "Done: $OUT_BASE"
echo "  Summary CSV: $SUMMARY_CSV"
echo "  Summary PNG: $SUMMARY_PNG"
