#!/usr/bin/env python3
"""Build a compact technology-comparison table for my_scenarios/compare_tech runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


AVG_PRR_RE = re.compile(r"Average PRR:\s*([0-9eE+\-\.]+)")
AVG_LAT_RE = re.compile(r"Average latency \(ms\):\s*([0-9eE+\-\.]+)")
VEH_INFO_RE = re.compile(
    r"INFO-(?P<veh>[^,]+),CAM-SENT:(?P<cam_sent>\d+),CAM-RECEIVED:(?P<cam_rx>\d+),"
    r"CAM-DROPPED-APP:(?P<cam_drop_app>\d+),CAM-DROPPED-PHY:(?P<cam_drop_phy>\d+),"
    r"CPM-SENT:\s*(?P<cpm_sent>\d+),CPM-RECEIVED:\s*(?P<cpm_rx>\d+),"
    r"CPM-DROPPED-APP:(?P<cpm_drop_app>\d+),CPM-DROPPED-PHY:(?P<cpm_drop_phy>\d+),"
    r"CONTROL-ACTIONS:(?P<control_actions>\d+)"
)


def _to_float(v: str | None) -> float:
    try:
        return float(v) if v not in (None, "") else math.nan
    except Exception:
        return math.nan


def _parse_meta(meta_path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not meta_path.exists():
        return meta
    for line in meta_path.read_text().splitlines():
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        meta[k.strip()] = v.strip()
    return meta


def _parse_log_metrics(log_path: Path, focus_vehicle: str) -> tuple[float, float, dict[str, str]]:
    avg_prr = math.nan
    avg_lat = math.nan
    focus_info: dict[str, str] = {}
    if not log_path.exists():
        return avg_prr, avg_lat, focus_info
    for line in log_path.read_text(errors="ignore").splitlines():
        m = AVG_PRR_RE.search(line)
        if m:
            avg_prr = _to_float(m.group(1))
        m = AVG_LAT_RE.search(line)
        if m:
            avg_lat = _to_float(m.group(1))
        m = VEH_INFO_RE.search(line)
        if m and m.group("veh") == focus_vehicle:
            focus_info = m.groupdict()
    return avg_prr, avg_lat, focus_info


def _read_focus_profile(artifacts: Path, focus_vehicle: str) -> tuple[float, float, float]:
    profile_csv = artifacts / f"eva-{focus_vehicle}-PROFILE.csv"
    if not profile_csv.exists():
        return math.nan, math.nan, math.nan
    with profile_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            return (
                _to_float(row.get("target_prr")),
                _to_float(row.get("equiv_tx_power_dbm")),
                _to_float(row.get("rx_drop_prob_phy_cam")),
            )
    return math.nan, math.nan, math.nan


def _read_focus_msg_prr(artifacts: Path, focus_vehicle: str, tx_focus_id: str) -> tuple[int, int, float]:
    msg_csv = artifacts / f"eva-{focus_vehicle}-MSG.csv"
    if not msg_csv.exists():
        return 0, 0, math.nan
    total = 0
    rx_ok = 0
    with msg_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("tx_id") or "").strip() != tx_focus_id:
                continue
            # Receiver-side rows have empty tx_t_s; sender-side rows must be ignored.
            if (row.get("tx_t_s") or "").strip() != "":
                continue
            msg_type = (row.get("msg_type") or "").strip()
            if not msg_type.startswith("CAM"):
                continue
            total += 1
            if msg_type == "CAM" and (row.get("rx_ok") or "").strip() == "1":
                rx_ok += 1
    return total, rx_ok, (rx_ok / total) if total > 0 else math.nan


def _read_focus_ctrl_counts(artifacts: Path, focus_vehicle: str) -> dict[str, int]:
    ctrl_csv = artifacts / f"eva-{focus_vehicle}-CTRL.csv"
    counts = {
        "cam_reaction": 0,
        "drop_decision_no_action": 0,
        "drop_decision_action": 0,
        "crash_mode_forced_speed": 0,
    }
    if not ctrl_csv.exists():
        return counts
    with ctrl_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            et = (row.get("event_type") or "").strip()
            if et in counts:
                counts[et] += 1
    return counts


def _read_risk_summary(artifacts: Path) -> tuple[float, float, int, int]:
    risk_csv = artifacts / "collision_risk" / "collision_risk_summary.csv"
    if not risk_csv.exists():
        return math.nan, math.nan, 0, 0
    with risk_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            min_gap = _to_float(row.get("min_gap_m"))
            min_ttc = _to_float(row.get("min_ttc_s"))
            risky_gap = int(_to_float(row.get("risky_gap_events")) if row.get("risky_gap_events") else 0)
            risky_ttc = int(_to_float(row.get("risky_ttc_events")) if row.get("risky_ttc_events") else 0)
            return min_gap, min_ttc, risky_gap, risky_ttc
    return math.nan, math.nan, 0, 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize my_scenarios/compare_tech matrix runs")
    p.add_argument("--matrix-root", required=True, help="Matrix root directory (scenario/tech layout)")
    p.add_argument("--out-csv", required=True, help="Output CSV path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    matrix_root = Path(args.matrix_root).resolve()
    out_csv = Path(args.out_csv).resolve()
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for scenario_dir in sorted(p for p in matrix_root.iterdir() if p.is_dir()):
        for tech_dir in sorted(p for p in scenario_dir.iterdir() if p.is_dir()):
            artifacts = tech_dir / "artifacts"
            meta = _parse_meta(artifacts / "run_meta.env")
            if not meta:
                continue

            focus_vehicle = meta.get("focus_vehicle", "veh3")
            tx_focus_id = meta.get("tx_focus_id", "2")
            binary = meta.get("binary", "")
            log_path = tech_dir / f"{binary}.log" if binary else tech_dir / "run.log"

            avg_prr, avg_lat_ms, focus_info = _parse_log_metrics(log_path, focus_vehicle)
            target_prr, equiv_dbm, cfg_rx_drop_phy_cam = _read_focus_profile(artifacts, focus_vehicle)
            cam_total, cam_ok, obs_prr = _read_focus_msg_prr(artifacts, focus_vehicle, tx_focus_id)
            ctrl_counts = _read_focus_ctrl_counts(artifacts, focus_vehicle)
            min_gap, min_ttc, risky_gap, risky_ttc = _read_risk_summary(artifacts)

            rows.append(
                {
                    "scenario": scenario_dir.name,
                    "tech": tech_dir.name,
                    "binary": binary,
                    "compare_mode": meta.get("compare_mode", ""),
                    "run_status": meta.get("run_status", ""),
                    "avg_prr_overall": "" if not math.isfinite(avg_prr) else f"{avg_prr:.6f}",
                    "avg_latency_ms_overall": "" if not math.isfinite(avg_lat_ms) else f"{avg_lat_ms:.6f}",
                    "focus_vehicle": focus_vehicle,
                    "focus_target_prr": "" if not math.isfinite(target_prr) else f"{target_prr:.6f}",
                    "focus_equiv_tx_power_dbm": "" if not math.isfinite(equiv_dbm) else f"{equiv_dbm:.6f}",
                    "focus_configured_rx_drop_prob_phy_cam": "" if not math.isfinite(cfg_rx_drop_phy_cam) else f"{cfg_rx_drop_phy_cam:.6f}",
                    "focus_cam_total_from_tx": str(cam_total),
                    "focus_cam_rx_ok_from_tx": str(cam_ok),
                    "focus_observed_prr_from_tx": "" if not math.isfinite(obs_prr) else f"{obs_prr:.6f}",
                    "focus_cam_reaction_count": str(ctrl_counts["cam_reaction"]),
                    "focus_drop_decision_no_action_count": str(ctrl_counts["drop_decision_no_action"]),
                    "focus_drop_decision_action_count": str(ctrl_counts["drop_decision_action"]),
                    "focus_crash_mode_forced_speed_count": str(ctrl_counts["crash_mode_forced_speed"]),
                    "focus_control_actions_log": focus_info.get("control_actions", ""),
                    "focus_cam_sent_log": focus_info.get("cam_sent", ""),
                    "focus_cam_received_log": focus_info.get("cam_rx", ""),
                    "focus_cam_dropped_phy_log": focus_info.get("cam_drop_phy", ""),
                    "min_gap_m": "" if not math.isfinite(min_gap) else f"{min_gap:.6f}",
                    "min_ttc_s": "" if not math.isfinite(min_ttc) else f"{min_ttc:.6f}",
                    "risky_gap_events": str(risky_gap),
                    "risky_ttc_events": str(risky_ttc),
                    "run_dir": str(tech_dir),
                }
            )

    fieldnames = [
        "scenario",
        "tech",
        "binary",
        "compare_mode",
        "run_status",
        "avg_prr_overall",
        "avg_latency_ms_overall",
        "focus_vehicle",
        "focus_target_prr",
        "focus_equiv_tx_power_dbm",
        "focus_configured_rx_drop_prob_phy_cam",
        "focus_cam_total_from_tx",
        "focus_cam_rx_ok_from_tx",
        "focus_observed_prr_from_tx",
        "focus_cam_reaction_count",
        "focus_drop_decision_no_action_count",
        "focus_drop_decision_action_count",
        "focus_crash_mode_forced_speed_count",
        "focus_control_actions_log",
        "focus_cam_sent_log",
        "focus_cam_received_log",
        "focus_cam_dropped_phy_log",
        "min_gap_m",
        "min_ttc_s",
        "risky_gap_events",
        "risky_ttc_events",
        "run_dir",
    ]

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
