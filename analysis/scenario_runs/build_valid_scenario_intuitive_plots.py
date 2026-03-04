#!/usr/bin/env python3
"""Build intuitive CSV-based plots for the validated EVA scenario."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


VEHICLES = ["veh3", "veh4", "veh5"]
TRUCK_TX_ID = "2"
CAM_OK_TYPES = {"CAM"}
CAM_DROP_TYPES = {"CAM_DROP_PHY", "CAM_DROP_APP"}


@dataclass
class CamEvent:
    time_s: float
    ok: bool


def _to_float(value: str | None) -> float:
    try:
        return float(value)
    except Exception:
        return math.nan


def _to_int(value: str | None, default: int = -1) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build intuitive plots from scenario CSV logs")
    p.add_argument("--run-dir", required=True, help="Run directory with artifacts/")
    p.add_argument("--out-dir", default="", help="Output directory (default: artifacts/valid_scenario_intuitive)")
    return p.parse_args()


def read_cam_events_from_msg(msg_csv: Path, tx_id: str) -> list[CamEvent]:
    events: list[CamEvent] = []
    if not msg_csv.exists():
        return events

    with msg_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("tx_id") or "").strip() != tx_id:
                continue
            msg_type = (row.get("msg_type") or "").strip()
            if msg_type not in CAM_OK_TYPES and msg_type not in CAM_DROP_TYPES:
                continue
            t = _to_float(row.get("rx_t_s"))
            if not math.isfinite(t):
                t = _to_float(row.get("tx_t_s"))
            if not math.isfinite(t):
                continue
            ok = msg_type in CAM_OK_TYPES and (row.get("rx_ok") or "0").strip() == "1"
            events.append(CamEvent(time_s=t, ok=ok))

    events.sort(key=lambda e: e.time_s)
    return events


def read_lane_change_times(ctrl_csv: Path) -> list[float]:
    times: list[float] = []
    if not ctrl_csv.exists():
        return times

    with ctrl_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_type = (row.get("event_type") or "").strip()
            if event_type not in {"cam_reaction", "cpm_reaction"}:
                continue
            lane_before = _to_int(row.get("lane_before"), -1)
            lane_after = _to_int(row.get("lane_after"), -1)
            if lane_before < 0 or lane_after < 0 or lane_before == lane_after:
                continue
            t = _to_float(row.get("time_s"))
            if math.isfinite(t):
                times.append(t)

    times.sort()
    return times


def read_collision_time(causality_csv: Path) -> float:
    if not causality_csv.exists():
        return math.nan
    with causality_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = _to_float(row.get("collision_time_s"))
            if math.isfinite(t):
                return t
    return math.nan


def read_observed_truck_speed(cam_csv: Path) -> tuple[list[float], list[float]]:
    t_out: list[float] = []
    v_out: list[float] = []
    if not cam_csv.exists():
        return t_out, v_out

    with cam_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cam_id = str(_to_int(row.get("camId"), -1))
            if cam_id != TRUCK_TX_ID:
                continue
            t_ms = _to_float(row.get("timestamp"))
            spd = _to_float(row.get("speed"))
            if not math.isfinite(t_ms) or not math.isfinite(spd):
                continue
            t_out.append(t_ms / 1000.0)
            v_out.append(spd)

    order = np.argsort(np.array(t_out, dtype=float)) if t_out else []
    if len(order):
        t_out = [t_out[i] for i in order]
        v_out = [v_out[i] for i in order]
    return t_out, v_out


def build_prr_series(events: list[CamEvent]) -> tuple[list[float], list[float]]:
    x: list[float] = []
    y: list[float] = []
    ok = 0
    total = 0
    for e in events:
        total += 1
        if e.ok:
            ok += 1
        x.append(e.time_s)
        y.append(ok / total)
    return x, y


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    artifacts = run_dir / "artifacts"
    if not artifacts.exists():
        raise FileNotFoundError(f"No artifacts dir: {artifacts}")

    out_dir = Path(args.out_dir).resolve() if args.out_dir else (artifacts / "valid_scenario_intuitive")
    out_dir.mkdir(parents=True, exist_ok=True)

    veh_events: dict[str, list[CamEvent]] = {}
    lane_changes: dict[str, list[float]] = {}
    speed_obs: dict[str, tuple[list[float], list[float]]] = {}

    for veh in VEHICLES:
        veh_events[veh] = read_cam_events_from_msg(artifacts / f"eva-{veh}-MSG.csv", TRUCK_TX_ID)
        lane_changes[veh] = read_lane_change_times(artifacts / f"eva-{veh}-CTRL.csv")
        speed_obs[veh] = read_observed_truck_speed(artifacts / f"eva-{veh}-CAM.csv")

    collision_time = read_collision_time(artifacts / "collision_causality" / "collision_causality.csv")

    summary_csv = out_dir / "intuitive_prr_summary.csv"
    with summary_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "vehicle_id",
                "cam_total_from_truck",
                "cam_received",
                "cam_dropped",
                "final_prr",
                "first_cam_event_s",
                "first_lane_change_s",
            ],
        )
        writer.writeheader()
        for veh in VEHICLES:
            events = veh_events[veh]
            total = len(events)
            received = sum(1 for e in events if e.ok)
            dropped = total - received
            final_prr = (received / total) if total else math.nan
            first_event = events[0].time_s if events else math.nan
            first_lc = lane_changes[veh][0] if lane_changes[veh] else math.nan
            writer.writerow(
                {
                    "vehicle_id": veh,
                    "cam_total_from_truck": total,
                    "cam_received": received,
                    "cam_dropped": dropped,
                    "final_prr": f"{final_prr:.4f}" if math.isfinite(final_prr) else "",
                    "first_cam_event_s": f"{first_event:.5f}" if math.isfinite(first_event) else "",
                    "first_lane_change_s": f"{first_lc:.5f}" if math.isfinite(first_lc) else "",
                }
            )

    key_csv = out_dir / "intuitive_key_events.csv"
    with key_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event", "time_s"])
        writer.writeheader()
        for veh in VEHICLES:
            if lane_changes[veh]:
                writer.writerow({"event": f"{veh}_first_lane_change", "time_s": f"{lane_changes[veh][0]:.5f}"})
        if math.isfinite(collision_time):
            writer.writerow({"event": "collision_time", "time_s": f"{collision_time:.5f}"})

    colors = {"veh3": "#2ca02c", "veh4": "#d62728", "veh5": "#1f77b4"}

    # 1) Cumulative PRR
    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    for veh in VEHICLES:
        x, y = build_prr_series(veh_events[veh])
        if x:
            ax.step(x, y, where="post", label=f"{veh} cumulative PRR", color=colors[veh], linewidth=2)
    if math.isfinite(collision_time):
        ax.axvline(collision_time, linestyle=":", color="black", linewidth=1.5, label="collision")
    ax.set_title("Cumulative CAM PRR from truck (tx_id=2) by receiver")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("PRR [-]")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, ncol=2)
    prr_png = out_dir / "intuitive_prr_cumulative.png"
    fig.tight_layout()
    fig.savefig(prr_png, dpi=170)
    plt.close(fig)

    # 2) Packet raster + lane-change + collision
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    y_map = {"veh3": 3, "veh4": 2, "veh5": 1}
    for veh in VEHICLES:
        y = y_map[veh]
        ok_t = [e.time_s for e in veh_events[veh] if e.ok]
        dr_t = [e.time_s for e in veh_events[veh] if not e.ok]
        if ok_t:
            ax.scatter(ok_t, [y] * len(ok_t), s=18, color="#2ca02c", label=f"{veh} CAM received")
        if dr_t:
            ax.scatter(dr_t, [y] * len(dr_t), s=25, color="#d62728", marker="x", label=f"{veh} CAM dropped")
        for lc in lane_changes[veh]:
            ax.scatter([lc], [y + 0.18], s=55, color="#1f77b4", marker="^", label=f"{veh} lane change")

    if math.isfinite(collision_time):
        ax.axvline(collision_time, linestyle=":", color="black", linewidth=1.8, label="collision")

    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["veh5", "veh4", "veh3"])
    ax.set_xlabel("Time [s]")
    ax.set_title("What happened (CSV only): packets from truck, lane changes, collision")
    ax.grid(alpha=0.3)

    handles, labels = ax.get_legend_handles_labels()
    dedup: dict[str, object] = {}
    for h, l in zip(handles, labels):
        if l not in dedup:
            dedup[l] = h
    ax.legend(dedup.values(), dedup.keys(), fontsize=8, ncol=2, loc="upper right")

    raster_png = out_dir / "intuitive_packet_raster.png"
    fig.tight_layout()
    fig.savefig(raster_png, dpi=170)
    plt.close(fig)

    # 3) Observed truck speed from received CAM
    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    for veh in VEHICLES:
        t_vals, v_vals = speed_obs[veh]
        if t_vals:
            ax.plot(t_vals, v_vals, marker="o", markersize=2.5, linewidth=1.4, label=f"{veh} sees truck speed", color=colors[veh])
    if math.isfinite(collision_time):
        ax.axvline(collision_time, linestyle=":", color="black", linewidth=1.5, label="collision")
    ax.set_title("Truck speed as seen by each receiver (from CAM CSV)")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Observed truck speed [m/s]")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, ncol=2)

    speed_png = out_dir / "intuitive_truck_speed_observed.png"
    fig.tight_layout()
    fig.savefig(speed_png, dpi=170)
    plt.close(fig)

    print(summary_csv)
    print(key_csv)
    print(prr_png)
    print(raster_png)
    print(speed_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
