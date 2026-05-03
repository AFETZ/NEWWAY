#!/usr/bin/env python3
"""Summarize sensor/CPM comparison runs for cpm_perception."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET


MODES = ("sensor_only", "sensor_good_cpm", "sensor_bad_cpm")


def _to_float(value: str | None) -> float:
    try:
        return float(value)
    except Exception:
        return math.nan


def read_collision_time(collision_xml: Path) -> float:
    if not collision_xml.exists():
        return math.nan
    try:
        root = ET.parse(collision_xml).getroot()
    except Exception:
        return math.nan
    first = math.nan
    for coll in root.findall("collision"):
        t = _to_float(coll.attrib.get("time"))
        if math.isfinite(t) and (not math.isfinite(first) or t < first):
            first = t
    return first


def read_collision_for_vehicle(collision_xml: Path, vehicle_id: str) -> tuple[bool, float]:
    if not collision_xml.exists():
        return False, math.nan
    try:
        root = ET.parse(collision_xml).getroot()
    except Exception:
        return False, math.nan

    in_collision = False
    first = math.nan
    for coll in root.findall("collision"):
        collider = (coll.attrib.get("collider") or "").strip()
        victim = (coll.attrib.get("victim") or "").strip()
        if collider != vehicle_id and victim != vehicle_id:
            continue
        in_collision = True
        t = _to_float(coll.attrib.get("time"))
        if math.isfinite(t) and (not math.isfinite(first) or t < first):
            first = t
    return in_collision, first


def read_first_ctrl_times(ctrl_csv: Path) -> dict[str, float]:
    out = {
        "sensor_reaction": math.nan,
        "cpm_reaction": math.nan,
        "cam_reaction": math.nan,
        "first_lane_change_s": math.nan,
    }
    if not ctrl_csv.exists():
        return out

    with ctrl_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event = (row.get("event_type") or "").strip()
            t = _to_float(row.get("time_s"))
            if not math.isfinite(t):
                continue
            if event in ("sensor_reaction", "cpm_reaction", "cam_reaction"):
                if not math.isfinite(out[event]):
                    out[event] = t
            lane_before = row.get("lane_before")
            lane_after = row.get("lane_after")
            try:
                lb = int(float(lane_before)) if lane_before not in (None, "") else -1
                la = int(float(lane_after)) if lane_after not in (None, "") else -1
            except Exception:
                lb = -1
                la = -1
            if lb >= 0 and la >= 0 and lb != la and not math.isfinite(out["first_lane_change_s"]):
                out["first_lane_change_s"] = t
    return out


def count_veh4_cpm_msg(msg_csv: Path) -> dict[str, int]:
    out = {
        "cpm_rx_total": 0,
        "cpm_rx_from_veh3": 0,
        "cpm_drop_total": 0,
        "cpm_drop_from_veh3": 0,
    }
    if not msg_csv.exists():
        return out

    with msg_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            msg_type = (row.get("msg_type") or "").strip()
            tx_id = (row.get("tx_id") or "").strip()
            if msg_type == "CPM":
                out["cpm_rx_total"] += 1
                if tx_id == "3":
                    out["cpm_rx_from_veh3"] += 1
            elif msg_type in ("CPM_DROP_PHY", "CPM_DROP_APP"):
                out["cpm_drop_total"] += 1
                if tx_id == "3":
                    out["cpm_drop_from_veh3"] += 1
    return out


def read_veh4_info_counters(log_path: Path) -> dict[str, int]:
    out = {"cpm_received": 0, "cpm_dropped_phy": 0, "control_actions": 0}
    if not log_path.exists():
        return out

    pattern = re.compile(
        r"INFO-veh4,.*CPM-RECEIVED:\s*(\d+),CPM-DROPPED-APP:\s*(\d+),CPM-DROPPED-PHY:\s*(\d+),CONTROL-ACTIONS:(\d+)"
    )
    with log_path.open() as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            out["cpm_received"] = int(m.group(1))
            out["cpm_dropped_phy"] = int(m.group(3))
            out["control_actions"] = int(m.group(4))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize valid CPM perception scenario runs")
    p.add_argument("--runs-root", required=True, help="Directory containing per-mode run dirs")
    p.add_argument("--out-dir", required=True, help="Output directory for summary CSV")
    p.add_argument(
        "--modes",
        nargs="+",
        choices=MODES,
        default=list(MODES),
        help="Subset of modes to summarize",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    runs_root = Path(args.runs_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "cpm_perception_mode_summary.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mode",
                "run_dir",
                "collision_happened",
                "collision_time_s",
                "veh4_in_collision",
                "veh4_collision_time_s",
                "veh4_sensor_reaction_s",
                "veh4_cpm_reaction_s",
                "veh4_cam_reaction_s",
                "veh4_first_lane_change_s",
                "veh4_cpm_rx_total",
                "veh4_cpm_rx_from_veh3",
                "veh4_cpm_drop_total",
                "veh4_cpm_drop_from_veh3",
                "veh4_cpm_received_info",
                "veh4_cpm_dropped_phy_info",
                "veh4_control_actions_info",
            ],
        )
        writer.writeheader()

        for mode in args.modes:
            run_dir = runs_root / mode
            artifacts = run_dir / "artifacts"
            collision_t = read_collision_time(artifacts / "eva-collision.xml")
            veh4_in_collision, veh4_collision_t = read_collision_for_vehicle(
                artifacts / "eva-collision.xml", "veh4"
            )
            ctrl_times = read_first_ctrl_times(artifacts / "eva-veh4-CTRL.csv")
            cpm_counts = count_veh4_cpm_msg(artifacts / "eva-veh4-MSG.csv")
            info_counts = read_veh4_info_counters(run_dir / "v2v-emergencyVehicleAlert-nrv2x.log")

            writer.writerow(
                {
                    "mode": mode,
                    "run_dir": str(run_dir),
                    "collision_happened": "1" if math.isfinite(collision_t) else "0",
                    "collision_time_s": f"{collision_t:.5f}" if math.isfinite(collision_t) else "",
                    "veh4_in_collision": "1" if veh4_in_collision else "0",
                    "veh4_collision_time_s": f"{veh4_collision_t:.5f}" if math.isfinite(veh4_collision_t) else "",
                    "veh4_sensor_reaction_s": f"{ctrl_times['sensor_reaction']:.5f}" if math.isfinite(ctrl_times["sensor_reaction"]) else "",
                    "veh4_cpm_reaction_s": f"{ctrl_times['cpm_reaction']:.5f}" if math.isfinite(ctrl_times["cpm_reaction"]) else "",
                    "veh4_cam_reaction_s": f"{ctrl_times['cam_reaction']:.5f}" if math.isfinite(ctrl_times["cam_reaction"]) else "",
                    "veh4_first_lane_change_s": f"{ctrl_times['first_lane_change_s']:.5f}" if math.isfinite(ctrl_times["first_lane_change_s"]) else "",
                    "veh4_cpm_rx_total": cpm_counts["cpm_rx_total"],
                    "veh4_cpm_rx_from_veh3": cpm_counts["cpm_rx_from_veh3"],
                    "veh4_cpm_drop_total": cpm_counts["cpm_drop_total"],
                    "veh4_cpm_drop_from_veh3": cpm_counts["cpm_drop_from_veh3"],
                    "veh4_cpm_received_info": info_counts["cpm_received"],
                    "veh4_cpm_dropped_phy_info": info_counts["cpm_dropped_phy"],
                    "veh4_control_actions_info": info_counts["control_actions"],
                }
            )

    print(out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
