#!/usr/bin/env python3
"""Build a compact CSV summary for valid_intersection_scenario runs."""

from __future__ import annotations

import argparse
import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def _to_float(v: str | None) -> float:
    try:
        return float(v) if v is not None and v != "" else math.nan
    except Exception:
        return math.nan


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize intersection scenario artifacts")
    p.add_argument("--run-dir", required=True, help="Run directory that contains artifacts/")
    p.add_argument("--out-csv", default="", help="Output CSV path (default: artifacts/intersection_summary.csv)")
    p.add_argument("--focus-vehicle", default="veh3", help="Vehicle under test (default: veh3)")
    p.add_argument("--tx-id", default="2", help="Transmitter station id to measure PRR against (default: 2)")
    return p.parse_args()


def read_profile(profile_csv: Path) -> tuple[float, float]:
    if not profile_csv.exists():
        return math.nan, math.nan
    with profile_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            return _to_float(row.get("target_prr")), _to_float(row.get("rx_drop_prob_phy_cam"))
    return math.nan, math.nan


def read_tx_cam_total(artifacts: Path, tx_id: str) -> int:
    tx_msg_csv = artifacts / f"eva-veh{tx_id}-MSG.csv"
    if not tx_msg_csv.exists():
        return 0
    total = 0
    with tx_msg_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("msg_type") or "").strip() != "CAM":
                continue
            # TX rows have tx_t_s populated; RX rows have it empty.
            if (row.get("tx_t_s") or "").strip() == "":
                continue
            total += 1
    return total


def read_rx_cam_ok(msg_csv: Path, tx_id: str) -> int:
    if not msg_csv.exists():
        return 0
    rx_ok = 0
    with msg_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("tx_id") or "").strip() != tx_id:
                continue
            if (row.get("msg_type") or "").strip() != "CAM":
                continue
            if (row.get("rx_ok") or "").strip() == "1":
                rx_ok += 1
    return rx_ok


def read_first_event(ctrl_csv: Path, event_type: str) -> float:
    if not ctrl_csv.exists():
        return math.nan
    best = math.nan
    with ctrl_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("event_type") or "").strip() != event_type:
                continue
            t = _to_float(row.get("time_s"))
            if not math.isfinite(t):
                continue
            if not math.isfinite(best) or t < best:
                best = t
    return best


def read_collision(collision_xml: Path, veh_a: str, veh_b: str) -> tuple[int, float]:
    if not collision_xml.exists():
        return 0, math.nan
    try:
        root = ET.parse(collision_xml).getroot()
    except Exception:
        return 0, math.nan
    found = 0
    first_t = math.nan
    for coll in root.findall("collision"):
        c = (coll.attrib.get("collider") or "").strip()
        v = (coll.attrib.get("victim") or "").strip()
        if {c, v} != {veh_a, veh_b}:
            continue
        t = _to_float(coll.attrib.get("time"))
        found = 1
        if math.isfinite(t) and (not math.isfinite(first_t) or t < first_t):
            first_t = t
    return found, first_t


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    artifacts = run_dir / "artifacts"
    if not artifacts.exists():
        raise FileNotFoundError(f"No artifacts directory: {artifacts}")

    focus = args.focus_vehicle
    out_csv = Path(args.out_csv).resolve() if args.out_csv else (artifacts / "intersection_summary.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    target_prr, cfg_drop = read_profile(artifacts / f"eva-{focus}-PROFILE.csv")
    total = read_tx_cam_total(artifacts, args.tx_id)
    ok = read_rx_cam_ok(artifacts / f"eva-{focus}-MSG.csv", args.tx_id)
    observed = (ok / total) if total > 0 else math.nan

    first_cam_reaction = read_first_event(artifacts / f"eva-{focus}-CTRL.csv", "cam_reaction")
    first_drop_no_action = read_first_event(artifacts / f"eva-{focus}-CTRL.csv", "drop_decision_no_action")
    first_crash_mode = read_first_event(artifacts / f"eva-{focus}-CTRL.csv", "crash_mode_forced_speed")

    coll_pair, coll_t = read_collision(artifacts / "eva-collision.xml", focus, "veh2")

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "run_dir",
                "focus_vehicle",
                "tx_id",
                "target_prr",
                "configured_rx_drop_prob_phy_cam",
                "cam_total_from_tx",
                "cam_received_from_tx",
                "observed_prr_from_tx",
                "first_cam_reaction_s",
                "first_drop_decision_no_action_s",
                "first_crash_mode_forced_speed_s",
                "collision_focus_with_veh2",
                "first_collision_time_s",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "run_dir": str(run_dir),
                "focus_vehicle": focus,
                "tx_id": args.tx_id,
                "target_prr": "" if not math.isfinite(target_prr) else f"{target_prr:.6f}",
                "configured_rx_drop_prob_phy_cam": "" if not math.isfinite(cfg_drop) else f"{cfg_drop:.6f}",
                "cam_total_from_tx": total,
                "cam_received_from_tx": ok,
                "observed_prr_from_tx": "" if not math.isfinite(observed) else f"{observed:.6f}",
                "first_cam_reaction_s": "" if not math.isfinite(first_cam_reaction) else f"{first_cam_reaction:.6f}",
                "first_drop_decision_no_action_s": "" if not math.isfinite(first_drop_no_action) else f"{first_drop_no_action:.6f}",
                "first_crash_mode_forced_speed_s": "" if not math.isfinite(first_crash_mode) else f"{first_crash_mode:.6f}",
                "collision_focus_with_veh2": coll_pair,
                "first_collision_time_s": "" if not math.isfinite(coll_t) else f"{coll_t:.6f}",
            }
        )

    print(out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
