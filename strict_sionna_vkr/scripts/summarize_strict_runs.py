#!/usr/bin/env python3
"""Summaries for strict scenario runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any


def _to_float(value: str | None) -> float:
    try:
        return float(value) if value not in (None, "") else math.nan
    except Exception:
        return math.nan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize strict thesis runs")
    parser.add_argument("--run-dir", help="Single run directory")
    parser.add_argument("--runs-root", help="Root directory containing multiple run dirs")
    return parser.parse_args()


def load_manifest(run_dir: Path) -> dict[str, Any]:
    with (run_dir / "run_manifest.json").open() as handle:
        return json.load(handle)


def read_first_event(ctrl_csv: Path, event_type: str) -> float:
    if not ctrl_csv.exists():
        return math.nan
    best = math.nan
    with ctrl_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("event_type") or "").strip() != event_type:
                continue
            current = _to_float(row.get("time_s"))
            if math.isfinite(current) and (not math.isfinite(best) or current < best):
                best = current
    return best


def read_first_lane_change(ctrl_csv: Path) -> float:
    if not ctrl_csv.exists():
        return math.nan
    with ctrl_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            lane_before = row.get("lane_before")
            lane_after = row.get("lane_after")
            try:
                before = int(float(lane_before)) if lane_before not in (None, "") else -1
                after = int(float(lane_after)) if lane_after not in (None, "") else -1
            except Exception:
                continue
            if before >= 0 and after >= 0 and before != after:
                return _to_float(row.get("time_s"))
    return math.nan


def read_observed_prr(msg_csv: Path, tx_id: str) -> float:
    if not msg_csv.exists():
        return math.nan
    total = 0
    ok = 0
    with msg_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            current_tx = (row.get("tx_id") or "").strip()
            if current_tx != tx_id:
                continue
            msg_type = (row.get("msg_type") or "").strip()
            if not msg_type.startswith("CAM"):
                continue
            total += 1
            if (row.get("rx_ok") or "").strip() == "1" and msg_type == "CAM":
                ok += 1
    return (ok / total) if total else math.nan


def read_collision(collision_xml: Path, pair: list[str] | None) -> tuple[int, float]:
    if not collision_xml.exists():
        return 0, math.nan
    try:
        root = ET.parse(collision_xml).getroot()
    except Exception:
        return 0, math.nan

    found = 0
    first = math.nan
    wanted = set(pair or [])
    for coll in root.findall("collision"):
        collider = (coll.attrib.get("collider") or "").strip()
        victim = (coll.attrib.get("victim") or "").strip()
        if wanted and {collider, victim} != wanted:
            continue
        current = _to_float(coll.attrib.get("time"))
        found = 1
        if math.isfinite(current) and (not math.isfinite(first) or current < first):
            first = current
    return found, first


def read_risk_summary(summary_csv: Path) -> dict[str, float]:
    result = {"min_gap_m": math.nan, "min_ttc_s": math.nan}
    if not summary_csv.exists():
        return result
    with summary_csv.open(newline="") as handle:
        for row in csv.DictReader(handle):
            result["min_gap_m"] = _to_float(row.get("min_gap_m"))
            result["min_ttc_s"] = _to_float(row.get("min_ttc_s"))
            break
    return result


def read_corruption(csv_path: Path, field: str) -> tuple[int, int, float]:
    if not csv_path.exists():
        return 0, 0, math.nan
    total = 0
    corrupt = 0
    with csv_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            if (row.get(field) or "").strip() == "1":
                corrupt += 1
    return total, corrupt, (corrupt / total) if total else math.nan


def intervals_overlap(start_a: int, len_a: int, start_b: int, len_b: int) -> bool:
    end_a = start_a + len_a - 1
    end_b = start_b + len_b - 1
    return start_a <= end_b and start_b <= end_a


def read_pssch_overlap(pssch_tx_csv: Path) -> tuple[int, int]:
    if not pssch_tx_csv.exists():
        return 0, 0
    rows: list[dict[str, str]] = []
    with pssch_tx_csv.open(newline="") as handle:
        rows.extend(csv.DictReader(handle))
    overlaps = 0
    for idx, row_a in enumerate(rows):
        for row_b in rows[idx + 1 :]:
            if row_a.get("frame") != row_b.get("frame"):
                continue
            if row_a.get("subframe") != row_b.get("subframe"):
                continue
            if row_a.get("slot") != row_b.get("slot"):
                continue
            if row_a.get("rnti") == row_b.get("rnti"):
                continue
            if not intervals_overlap(
                int(row_a["rb_start"]),
                int(row_a["rb_len"]),
                int(row_b["rb_start"]),
                int(row_b["rb_len"]),
            ):
                continue
            if not intervals_overlap(
                int(row_a["sym_start"]),
                int(row_a["sym_len"]),
                int(row_b["sym_start"]),
                int(row_b["sym_len"]),
            ):
                continue
            overlaps += 1
    return len(rows), overlaps


def summarize_run(run_dir: Path) -> dict[str, Any]:
    manifest = load_manifest(run_dir)
    analysis = manifest.get("analysis", {})
    behavior_dir = run_dir / "behavior"
    native_dir = run_dir / "native_nr"
    artifacts = behavior_dir / "artifacts"
    focus_vehicle = analysis.get("focus_vehicle", "")
    tx_station_id = str(analysis.get("focus_tx_station_id", ""))
    ctrl_csv = artifacts / f"eva-{focus_vehicle}-CTRL.csv"
    msg_csv = artifacts / f"eva-{focus_vehicle}-MSG.csv"
    pair = analysis.get("collision_pair")

    cam_reaction = read_first_event(ctrl_csv, "cam_reaction")
    cpm_reaction = read_first_event(ctrl_csv, "cpm_reaction")
    sensor_reaction = read_first_event(ctrl_csv, "sensor_reaction")
    first_control = min(
        [value for value in (cam_reaction, cpm_reaction, sensor_reaction) if math.isfinite(value)],
        default=math.nan,
    )
    first_useful_warning = min(
        [value for value in (cam_reaction, cpm_reaction) if math.isfinite(value)],
        default=math.nan,
    )
    collision_flag, collision_time = read_collision(artifacts / "eva-collision.xml", pair)
    risk_summary = read_risk_summary(artifacts / "collision_risk" / "collision_risk_summary.csv")
    pscch_total, pscch_corrupt, pscch_rate = read_corruption(native_dir / "native_nr-pscch.csv", "corrupt")
    pssch_total, pssch_corrupt, pssch_rate = read_corruption(native_dir / "native_nr-pssch.csv", "corrupt")
    _, sci2_corrupt, sci2_rate = read_corruption(native_dir / "native_nr-pssch.csv", "sci2_corrupted")
    pssch_tx_total, overlap_pairs = read_pssch_overlap(native_dir / "native_nr-pssch-tx.csv")

    return {
        "scenario_id": manifest["scenario_id"],
        "mode": manifest["mode"],
        "seed": manifest["run"]["rng_run"],
        "run_dir": str(run_dir),
        "focus_vehicle": focus_vehicle,
        "focus_tx_station_id": tx_station_id,
        "observed_prr_focus_vehicle": read_observed_prr(msg_csv, tx_station_id),
        "first_cam_reaction_s": cam_reaction,
        "first_cpm_reaction_s": cpm_reaction,
        "first_sensor_reaction_s": sensor_reaction,
        "first_control_action_s": first_control,
        "first_useful_warning_s": first_useful_warning,
        "first_lane_change_s": read_first_lane_change(ctrl_csv),
        "collision_flag": collision_flag,
        "collision_time_s": collision_time,
        "min_gap_m": risk_summary["min_gap_m"],
        "min_ttc_s": risk_summary["min_ttc_s"],
        "pscch_rx_total": pscch_total,
        "pscch_corrupt_total": pscch_corrupt,
        "pscch_corrupt_rate": pscch_rate,
        "pssch_rx_total": pssch_total,
        "pssch_corrupt_total": pssch_corrupt,
        "pssch_corrupt_rate": pssch_rate,
        "sci2_corrupt_total": sci2_corrupt,
        "sci2_corrupt_rate": sci2_rate,
        "pssch_tx_total": pssch_tx_total,
        "pssch_overlap_pairs": overlap_pairs,
    }


def write_seed_summary(out_csv: Path, rows: list[dict[str, Any]]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with out_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            normalized = {
                key: ("" if isinstance(value, float) and not math.isfinite(value) else value)
                for key, value in row.items()
            }
            writer.writerow(normalized)


def write_mode_summary(out_csv: Path, rows: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["scenario_id"], row["mode"])].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (scenario_id, mode), items in sorted(groups.items()):
        def mean_of(key: str) -> float:
            values = [float(item[key]) for item in items if math.isfinite(float(item[key]))]
            return statistics.fmean(values) if values else math.nan

        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "mode": mode,
                "num_runs": len(items),
                "collision_rate": statistics.fmean(float(item["collision_flag"]) for item in items),
                "mean_observed_prr_focus_vehicle": mean_of("observed_prr_focus_vehicle"),
                "mean_first_useful_warning_s": mean_of("first_useful_warning_s"),
                "mean_first_control_action_s": mean_of("first_control_action_s"),
                "mean_min_gap_m": mean_of("min_gap_m"),
                "mean_min_ttc_s": mean_of("min_ttc_s"),
                "mean_pscch_corrupt_rate": mean_of("pscch_corrupt_rate"),
                "mean_pssch_corrupt_rate": mean_of("pssch_corrupt_rate"),
                "mean_sci2_corrupt_rate": mean_of("sci2_corrupt_rate"),
                "mean_pssch_overlap_pairs": mean_of("pssch_overlap_pairs"),
            }
        )

    write_seed_summary(out_csv, summary_rows)


def discover_runs(root: Path) -> list[Path]:
    return sorted(path.parent for path in root.rglob("run_manifest.json"))


def main() -> int:
    args = parse_args()
    rows: list[dict[str, Any]]

    if args.run_dir:
        run_dir = Path(args.run_dir).resolve()
        rows = [summarize_run(run_dir)]
        write_seed_summary(run_dir / "seed_summary.csv", rows)
        with (run_dir / "run_summary.json").open("w") as handle:
            json.dump(rows[0], handle, indent=2, sort_keys=True)
        print(run_dir / "seed_summary.csv")
        return 0

    if not args.runs_root:
        raise SystemExit("Either --run-dir or --runs-root is required")

    runs_root = Path(args.runs_root).resolve()
    run_dirs = discover_runs(runs_root)
    rows = [summarize_run(run_dir) for run_dir in run_dirs]
    if not rows:
        raise SystemExit(f"No run_manifest.json found under {runs_root}")
    write_seed_summary(runs_root / "seed_summary.csv", rows)
    write_mode_summary(runs_root / "mode_summary.csv", rows)
    print(runs_root / "seed_summary.csv")
    print(runs_root / "mode_summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
