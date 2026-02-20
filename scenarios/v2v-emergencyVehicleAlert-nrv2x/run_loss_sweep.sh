#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-loss-sweep-$(date +%H%M%S)}"
SIM_TIME="${SIM_TIME:-40}"
LOSS_PROBS="${LOSS_PROBS:-0.0 0.3 0.6}"
DROP_LAYER="${DROP_LAYER:-app}" # app | phy | both
BASE_RADIO_ARGS="${BASE_RADIO_ARGS:---enableSensing=0 --txPower=23 --slThresPsschRsrp=-128}"
INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
RUN_RETRIES="${RUN_RETRIES:-3}"
PLOT="${PLOT:-1}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"

mkdir -p "$OUT_BASE"

PY_BIN="$ROOT/.venv/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

CASES_CSV="$OUT_BASE/cases.csv"
{
  echo "case_id,drop_layer,configured_drop_prob,rx_drop_prob_cam,rx_drop_prob_phy_cam,run_dir"
} > "$CASES_CSV"

for prob in $LOSS_PROBS; do
  case_id="drop_${prob//./p}"
  case_dir="$OUT_BASE/$case_id"
  app_prob="0.0"
  phy_prob="0.0"
  case "$DROP_LAYER" in
    app)
      app_prob="$prob"
      ;;
    phy)
      phy_prob="$prob"
      ;;
    both)
      app_prob="$prob"
      phy_prob="$prob"
      ;;
    *)
      echo "Unsupported DROP_LAYER=$DROP_LAYER (expected: app | phy | both)"
      exit 1
      ;;
  esac

  run_args="--sumo-gui=0 --sim-time=$SIM_TIME --met-sup=1 --rx-drop-prob-cam=$app_prob --rx-drop-prob-cpm=0 --rx-drop-prob-phy-cam=$phy_prob --rx-drop-prob-phy-cpm=0 $BASE_RADIO_ARGS"
  if [[ -n "$INCIDENT_ARGS" ]]; then
    run_args+=" $INCIDENT_ARGS"
  fi

  OUT_DIR="$case_dir" \
  NS3_DIR="$NS3_DIR" \
  RUN_ARGS="$run_args" \
  RUN_RETRIES="$RUN_RETRIES" \
  PLOT="$PLOT" \
    "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run.sh"

  echo "$case_id,$DROP_LAYER,$prob,$app_prob,$phy_prob,$case_dir" >> "$CASES_CSV"
done

SUMMARY_CSV="$OUT_BASE/loss_sweep_summary.csv"
SUMMARY_PNG="$OUT_BASE/loss_sweep_summary.png"
export CASES_CSV SUMMARY_CSV SUMMARY_PNG DROP_LAYER
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
drop_layer = os.environ.get("DROP_LAYER", "app").strip().lower()

if drop_layer == "phy":
    x_label = "Injected CAM PHY drop probability [-]"
elif drop_layer == "both":
    x_label = "Injected CAM APP+PHY drop probability [-]"
else:
    x_label = "Injected CAM APP drop probability [-]"

rows = []
with cases_csv.open() as f:
    reader = csv.DictReader(f)
    for case in reader:
        run_dir = Path(case["run_dir"])
        log_path = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
        log_text = log_path.read_text(errors="ignore") if log_path.exists() else ""

        m_prr = re.search(r"Average PRR:\s*([0-9.]+)", log_text)
        m_lat = re.search(r"Average latency \(ms\):\s*([0-9.]+)", log_text)
        m_inc = re.search(r"INCIDENT-APPLIED,id=([^,]+),time_s=([0-9.]+)", log_text)
        avg_prr = float(m_prr.group(1)) if m_prr else np.nan
        avg_latency_ms = float(m_lat.group(1)) if m_lat else np.nan
        incident_vehicle = m_inc.group(1) if m_inc else ""
        incident_time_s = float(m_inc.group(2)) if m_inc else np.nan

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
        ctrl_times = []
        for ctrl_file in sorted((run_dir / "artifacts").glob("*-CTRL.csv")):
            try:
                ctrl_df = pd.read_csv(ctrl_file)
            except Exception:
                pass
                continue
            ctrl_events += len(ctrl_df.index)
            if "time_s" in ctrl_df.columns:
                t = pd.to_numeric(ctrl_df["time_s"], errors="coerce").dropna().to_numpy()
                if t.size:
                    ctrl_times.extend(t.tolist())

        if ctrl_times:
            ctrl_times_np = np.array(ctrl_times, dtype=float)
            first_control_action_s = float(np.min(ctrl_times_np))
            p50_control_action_s = float(np.quantile(ctrl_times_np, 0.5))
            p90_control_action_s = float(np.quantile(ctrl_times_np, 0.9))
            last_control_action_s = float(np.max(ctrl_times_np))
        else:
            first_control_action_s = np.nan
            p50_control_action_s = np.nan
            p90_control_action_s = np.nan
            last_control_action_s = np.nan

        cam_drop_app = 0
        cam_drop_phy = 0
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
            cam_drop_phy += int((msg_type == "CAM_DROP_PHY").sum())
            if "rx_ok" in msg.columns:
                rx_ok = pd.to_numeric(msg["rx_ok"], errors="coerce").fillna(0)
                cam_rx_ok += int(((msg_type == "CAM") & (rx_ok > 0)).sum())

        cam_drop_total = cam_drop_app + cam_drop_phy
        denom = cam_drop_total + cam_rx_ok
        observed_cam_drop_ratio = float(cam_drop_total / denom) if denom > 0 else np.nan

        rows.append(
            {
                "case_id": case["case_id"],
                "drop_layer": case.get("drop_layer", drop_layer),
                "configured_drop_prob": float(case.get("configured_drop_prob", case.get("rx_drop_prob_cam", np.nan))),
                "rx_drop_prob_cam": float(case.get("rx_drop_prob_cam", np.nan)),
                "rx_drop_prob_phy_cam": float(case.get("rx_drop_prob_phy_cam", np.nan)),
                "avg_prr": avg_prr,
                "avg_latency_ms": avg_latency_ms,
                "min_gap_m": min_gap_m,
                "min_ttc_s": min_ttc_s,
                "risky_gap_events": risky_gap_events,
                "risky_ttc_events": risky_ttc_events,
                "control_actions": ctrl_events,
                "first_control_action_s": first_control_action_s,
                "p50_control_action_s": p50_control_action_s,
                "p90_control_action_s": p90_control_action_s,
                "last_control_action_s": last_control_action_s,
                "cam_drop_app_events": cam_drop_app,
                "cam_drop_phy_events": cam_drop_phy,
                "cam_drop_total_events": cam_drop_total,
                "cam_rx_ok_events": cam_rx_ok,
                "observed_cam_drop_ratio": observed_cam_drop_ratio,
                "incident_vehicle": incident_vehicle,
                "incident_time_s": incident_time_s,
                "run_dir": str(run_dir),
            }
        )

summary = pd.DataFrame(rows).sort_values("configured_drop_prob")
summary.to_csv(summary_csv, index=False)

fig, ax = plt.subplots(2, 2, figsize=(10, 7))
x = summary["configured_drop_prob"].to_numpy()

ax[0, 0].plot(x, summary["avg_prr"], marker="o", label="Average PRR")
if "observed_cam_drop_ratio" in summary:
    ax[0, 0].plot(x, summary["observed_cam_drop_ratio"], marker="s", label="Observed CAM drop ratio (APP+PHY)")
ax[0, 0].set_ylabel("Ratio [-]")
ax[0, 0].set_ylim(0, 1.05)
ax[0, 0].grid(alpha=0.3)
ax[0, 0].legend()
ax[0, 0].set_xlabel(x_label)

if "cam_drop_app_events" in summary and float(pd.to_numeric(summary["cam_drop_app_events"], errors="coerce").fillna(0).max()) > 0:
    ax[0, 0].plot(
        x,
        np.divide(
            summary["cam_drop_app_events"],
            (summary["cam_drop_app_events"] + summary["cam_rx_ok_events"]).replace(0, np.nan),
        ),
        marker="^",
        linestyle="--",
        label="Observed CAM APP drop ratio",
    )
if "cam_drop_phy_events" in summary and float(pd.to_numeric(summary["cam_drop_phy_events"], errors="coerce").fillna(0).max()) > 0:
    ax[0, 0].plot(
        x,
        np.divide(
            summary["cam_drop_phy_events"],
            (summary["cam_drop_phy_events"] + summary["cam_rx_ok_events"]).replace(0, np.nan),
        ),
        marker="v",
        linestyle="--",
        label="Observed CAM PHY drop ratio",
    )
ax[0, 0].legend()

ax[0, 1].plot(x, summary["avg_latency_ms"], marker="o", color="#ff7f0e")
ax[0, 1].set_xlabel(x_label)
ax[0, 1].set_ylabel("Average latency [ms]")
ax[0, 1].grid(alpha=0.3)

ax[1, 0].plot(x, summary["risky_ttc_events"], marker="o", label="Risky TTC events")
ax[1, 0].plot(x, summary["risky_gap_events"], marker="s", label="Risky gap events")
ax[1, 0].set_xlabel(x_label)
ax[1, 0].set_ylabel("Events [count]")
ax[1, 0].grid(alpha=0.3)
ax[1, 0].legend()

ax[1, 1].plot(x, summary["control_actions"], marker="o", color="#1f77b4", label="Control actions")
ax[1, 1].set_xlabel(x_label)
ax[1, 1].set_ylabel("Control actions [count]", color="#1f77b4")
ax[1, 1].tick_params(axis="y", labelcolor="#1f77b4")
ax2 = ax[1, 1].twinx()
ax2.plot(x, summary["min_ttc_s"], marker="s", color="#d62728", label="Min TTC")
ax2.set_ylabel("Min TTC [s]", color="#d62728")
ax2.tick_params(axis="y", labelcolor="#d62728")
h1, l1 = ax[1, 1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax[1, 1].legend(h1 + h2, l1 + l2, loc="best")
ax[1, 1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig(summary_png, dpi=150)
plt.close(fig)

timing_png = summary_png.with_name("loss_sweep_behavior_timing.png")
fig, ax = plt.subplots(1, 1, figsize=(7, 4))
ax.plot(x, summary["first_control_action_s"], marker="o", label="First control action")
ax.plot(x, summary["p90_control_action_s"], marker="s", label="P90 control action")
ax.set_xlabel(x_label)
ax.set_ylabel("Control-action time [s]")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(timing_png, dpi=150)
plt.close(fig)

print(summary_csv)
print(summary_png)
print(timing_png)
PY

echo "Sweep done:"
echo "  drop layer: $DROP_LAYER"
echo "  $SUMMARY_CSV"
echo "  $SUMMARY_PNG"

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_BASE" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$PY_BIN" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for loss sweep"
  fi
fi
