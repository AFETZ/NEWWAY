#!/usr/bin/env python3
"""Compute collision-risk proxies from SUMO netstate dump."""

from __future__ import annotations

import argparse
import csv
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze SUMO netstate dump for collision-risk proxies.")
    p.add_argument("--netstate", required=True, help="Path to SUMO netstate XML dump")
    p.add_argument("--out-dir", required=True, help="Output directory for csv/png")
    p.add_argument("--gap-threshold-m", type=float, default=2.0, help="Risk event threshold for inter-vehicle gap")
    p.add_argument("--ttc-threshold-s", type=float, default=1.5, help="Risk event threshold for TTC")
    return p.parse_args()


def _lane_sort_key(vehicle: dict) -> float:
    # Prefer lane-relative coordinate from SUMO netstate; it is always aligned with the lane direction.
    return vehicle["lane_pos"]


def analyze(netstate_path: Path, gap_threshold: float, ttc_threshold: float):
    min_gap_global = math.inf
    min_ttc_global = math.inf
    risky_gap_events = 0
    risky_ttc_events = 0
    timesteps = 0
    vehicle_counts = []
    series = []

    for _, elem in ET.iterparse(netstate_path, events=("end",)):
        if elem.tag != "timestep":
            continue

        t_s = float(elem.attrib.get("time", "0"))
        lane_vehicles = defaultdict(list)
        total_vehicles = 0

        for edge in elem.findall("edge"):
            for lane in edge.findall("lane"):
                lane_id = lane.attrib.get("id", "")
                for veh in lane.findall("vehicle"):
                    lane_pos = float(veh.attrib.get("pos", "nan"))
                    x = float(veh.attrib.get("x", "nan"))
                    if math.isnan(x):
                        x = lane_pos
                    v = {
                        "id": veh.attrib.get("id", ""),
                        "x": x,
                        "y": float(veh.attrib.get("y", "nan")),
                        "lane_pos": lane_pos,
                        "speed": float(veh.attrib.get("speed", "0")),
                    }
                    if not math.isnan(v["lane_pos"]):
                        lane_vehicles[lane_id].append(v)
                        total_vehicles += 1

        min_gap_t = math.inf
        min_ttc_t = math.inf

        for lane_id, vehs in lane_vehicles.items():
            if len(vehs) < 2:
                continue
            vehs.sort(key=_lane_sort_key)

            # Adjacent pairs on the same lane are the relevant candidates for rear-end risk.
            for i in range(1, len(vehs)):
                rear = vehs[i - 1]
                front = vehs[i]
                gap = front["lane_pos"] - rear["lane_pos"]
                if gap <= 0:
                    continue
                min_gap_t = min(min_gap_t, gap)
                min_gap_global = min(min_gap_global, gap)
                if gap < gap_threshold:
                    risky_gap_events += 1

                closing_speed = rear["speed"] - front["speed"]
                if closing_speed > 0:
                    ttc = gap / closing_speed
                    min_ttc_t = min(min_ttc_t, ttc)
                    min_ttc_global = min(min_ttc_global, ttc)
                    if ttc < ttc_threshold:
                        risky_ttc_events += 1

        timesteps += 1
        vehicle_counts.append(total_vehicles)
        series.append(
            {
                "time_s": t_s,
                "min_gap_m": None if math.isinf(min_gap_t) else min_gap_t,
                "min_ttc_s": None if math.isinf(min_ttc_t) else min_ttc_t,
                "vehicles": total_vehicles,
            }
        )
        elem.clear()

    if math.isinf(min_gap_global):
        min_gap_global = None
    if math.isinf(min_ttc_global):
        min_ttc_global = None

    return {
        "timesteps": timesteps,
        "mean_vehicles": (sum(vehicle_counts) / len(vehicle_counts)) if vehicle_counts else 0.0,
        "min_gap_m": min_gap_global,
        "min_ttc_s": min_ttc_global,
        "risky_gap_events": risky_gap_events,
        "risky_ttc_events": risky_ttc_events,
        "series": series,
    }


def save_outputs(out_dir: Path, result: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_csv = out_dir / "collision_risk_summary.csv"
    with summary_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timesteps",
                "mean_vehicles",
                "min_gap_m",
                "min_ttc_s",
                "risky_gap_events",
                "risky_ttc_events",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "timesteps": result["timesteps"],
                "mean_vehicles": f"{result['mean_vehicles']:.3f}",
                "min_gap_m": "" if result["min_gap_m"] is None else f"{result['min_gap_m']:.3f}",
                "min_ttc_s": "" if result["min_ttc_s"] is None else f"{result['min_ttc_s']:.3f}",
                "risky_gap_events": result["risky_gap_events"],
                "risky_ttc_events": result["risky_ttc_events"],
            }
        )

    ts_csv = out_dir / "collision_risk_timeseries.csv"
    with ts_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["time_s", "min_gap_m", "min_ttc_s", "vehicles"])
        writer.writeheader()
        for row in result["series"]:
            writer.writerow(row)

    times = [r["time_s"] for r in result["series"] if r["min_gap_m"] is not None]
    gaps = [r["min_gap_m"] for r in result["series"] if r["min_gap_m"] is not None]
    ttc_times = [r["time_s"] for r in result["series"] if r["min_ttc_s"] is not None]
    ttcs = [r["min_ttc_s"] for r in result["series"] if r["min_ttc_s"] is not None]

    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    if times:
        ax[0].plot(times, gaps, label="Min inter-vehicle gap")
        ax[0].legend(loc="best")
    ax[0].set_ylabel("Gap [m]")
    ax[0].grid(alpha=0.3)

    if ttc_times:
        ax[1].plot(ttc_times, ttcs, label="Min TTC", color="#d62728")
        ax[1].legend(loc="best")
    ax[1].set_ylabel("TTC [s]")
    ax[1].set_xlabel("Time [s]")
    ax[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "collision_risk_timeseries.png", dpi=150)
    plt.close(fig)

    print(summary_csv)
    print(ts_csv)
    print(out_dir / "collision_risk_timeseries.png")


def main() -> None:
    args = parse_args()
    netstate = Path(args.netstate).resolve()
    out_dir = Path(args.out_dir).resolve()
    if not netstate.exists():
        raise FileNotFoundError(netstate)

    result = analyze(netstate, args.gap_threshold_m, args.ttc_threshold_s)
    save_outputs(out_dir, result)


if __name__ == "__main__":
    main()
