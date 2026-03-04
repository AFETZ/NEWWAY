#!/usr/bin/env python3
"""Build intuitive CSV-based plots for the validated EVA scenario."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

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


@dataclass
class ProfileConfig:
    source: str
    rx_drop_prob_phy_cam: float
    equiv_tx_power_dbm: float
    target_prr: float


@dataclass
class DecisionEvent:
    event_type: str
    time_s: float


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


def read_first_decision(ctrl_csv: Path) -> DecisionEvent:
    return read_first_decision_after(ctrl_csv, min_time_s=-1e9)


def read_first_decision_after(ctrl_csv: Path, min_time_s: float) -> DecisionEvent:
    first_type = ""
    first_time = math.nan
    if not ctrl_csv.exists():
        return DecisionEvent(event_type=first_type, time_s=first_time)

    with ctrl_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_type = (row.get("event_type") or "").strip()
            t = _to_float(row.get("time_s"))
            if not event_type or not math.isfinite(t):
                continue
            if t < min_time_s:
                continue
            if not math.isfinite(first_time) or t < first_time:
                first_type = event_type
                first_time = t
    return DecisionEvent(event_type=first_type, time_s=first_time)


def read_profile_config(profile_csv: Path) -> ProfileConfig:
    cfg = ProfileConfig(
        source="",
        rx_drop_prob_phy_cam=math.nan,
        equiv_tx_power_dbm=math.nan,
        target_prr=math.nan,
    )
    if not profile_csv.exists():
        return cfg

    with profile_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cfg.source = (row.get("profile_source") or "").strip()
            cfg.rx_drop_prob_phy_cam = _to_float(row.get("rx_drop_prob_phy_cam"))
            cfg.equiv_tx_power_dbm = _to_float(row.get("equiv_tx_power_dbm"))
            cfg.target_prr = _to_float(row.get("target_prr"))
            break
    return cfg


def read_collision_vehicles(collision_xml: Path) -> set[str]:
    vehicles: set[str] = set()
    if not collision_xml.exists():
        return vehicles

    try:
        root = ET.parse(collision_xml).getroot()
    except Exception:
        return vehicles

    for coll in root.findall("collision"):
        collider = (coll.attrib.get("collider") or "").strip()
        victim = (coll.attrib.get("victim") or "").strip()
        if collider:
            vehicles.add(collider)
        if victim:
            vehicles.add(victim)
    return vehicles


def read_incident_time(log_path: Path, incident_vehicle: str = "veh2") -> float:
    if not log_path.exists():
        return math.nan
    marker = f"INCIDENT-APPLIED,id={incident_vehicle},time_s="
    with log_path.open() as f:
        for line in f:
            pos = line.find(marker)
            if pos < 0:
                continue
            value = line[pos + len(marker) :].strip()
            if "," in value:
                value = value.split(",", 1)[0].strip()
            return _to_float(value)
    return math.nan


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
    decisions: dict[str, DecisionEvent] = {}
    profile_cfg: dict[str, ProfileConfig] = {}
    incident_time = read_incident_time(run_dir / "v2v-emergencyVehicleAlert-nrv2x.log", incident_vehicle="veh2")

    for veh in VEHICLES:
        veh_events[veh] = read_cam_events_from_msg(artifacts / f"eva-{veh}-MSG.csv", TRUCK_TX_ID)
        lane_changes[veh] = read_lane_change_times(artifacts / f"eva-{veh}-CTRL.csv")
        speed_obs[veh] = read_observed_truck_speed(artifacts / f"eva-{veh}-CAM.csv")
        if math.isfinite(incident_time):
            decisions[veh] = read_first_decision_after(
                artifacts / f"eva-{veh}-CTRL.csv", min_time_s=incident_time
            )
        else:
            decisions[veh] = read_first_decision(artifacts / f"eva-{veh}-CTRL.csv")
        profile_cfg[veh] = read_profile_config(artifacts / f"eva-{veh}-PROFILE.csv")

    collision_time = read_collision_time(artifacts / "collision_causality" / "collision_causality.csv")
    collision_vehicles = read_collision_vehicles(artifacts / "eva-collision.xml")

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
                "profile_source",
                "equiv_tx_power_dbm",
                "target_prr",
                "configured_rx_drop_prob_phy_cam",
                "first_cam_event_s",
                "first_decision_event",
                "first_decision_time_s",
                "first_lane_change_s",
                "decision_outcome",
                "in_collision_xml",
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
            cfg = profile_cfg[veh]
            first_decision = decisions[veh]
            outcome = "no_maneuver"
            if lane_changes[veh]:
                if math.isfinite(collision_time) and lane_changes[veh][0] >= collision_time:
                    outcome = "late_maneuver_after_collision"
                else:
                    outcome = "maneuver_before_collision"
            if veh in collision_vehicles and (
                not lane_changes[veh] or (math.isfinite(collision_time) and lane_changes[veh][0] >= collision_time)
            ):
                outcome = "no_maneuver_before_collision"
            writer.writerow(
                {
                    "vehicle_id": veh,
                    "cam_total_from_truck": total,
                    "cam_received": received,
                    "cam_dropped": dropped,
                    "final_prr": f"{final_prr:.4f}" if math.isfinite(final_prr) else "",
                    "profile_source": cfg.source,
                    "equiv_tx_power_dbm": f"{cfg.equiv_tx_power_dbm:.4f}" if math.isfinite(cfg.equiv_tx_power_dbm) else "",
                    "target_prr": f"{cfg.target_prr:.4f}" if math.isfinite(cfg.target_prr) else "",
                    "configured_rx_drop_prob_phy_cam": f"{cfg.rx_drop_prob_phy_cam:.6f}" if math.isfinite(cfg.rx_drop_prob_phy_cam) else "",
                    "first_cam_event_s": f"{first_event:.5f}" if math.isfinite(first_event) else "",
                    "first_decision_event": first_decision.event_type,
                    "first_decision_time_s": f"{first_decision.time_s:.5f}" if math.isfinite(first_decision.time_s) else "",
                    "first_lane_change_s": f"{first_lc:.5f}" if math.isfinite(first_lc) else "",
                    "decision_outcome": outcome,
                    "in_collision_xml": "1" if veh in collision_vehicles else "0",
                }
            )

    key_csv = out_dir / "intuitive_key_events.csv"
    with key_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event", "time_s"])
        writer.writeheader()
        if math.isfinite(incident_time):
            writer.writerow({"event": "incident_time", "time_s": f"{incident_time:.5f}"})
        for veh in VEHICLES:
            if lane_changes[veh]:
                writer.writerow({"event": f"{veh}_first_lane_change", "time_s": f"{lane_changes[veh][0]:.5f}"})
        if math.isfinite(collision_time):
            writer.writerow({"event": "collision_time", "time_s": f"{collision_time:.5f}"})

    chain_csv = out_dir / "intuitive_dbm_prr_maneuver_chain.csv"
    with chain_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "vehicle_id",
                "equiv_tx_power_dbm",
                "target_prr",
                "observed_prr",
                "prr_error_observed_minus_target",
                "configured_rx_drop_prob_phy_cam",
                "first_decision_event",
                "first_decision_time_s",
                "first_lane_change_s",
                "decision_outcome",
                "in_collision_xml",
            ],
        )
        writer.writeheader()
        for veh in VEHICLES:
            events = veh_events[veh]
            total = len(events)
            observed_prr = (sum(1 for e in events if e.ok) / total) if total else math.nan
            cfg = profile_cfg[veh]
            prr_error = (
                observed_prr - cfg.target_prr
                if math.isfinite(observed_prr) and math.isfinite(cfg.target_prr)
                else math.nan
            )
            first_lc = lane_changes[veh][0] if lane_changes[veh] else math.nan
            first_decision = decisions[veh]
            outcome = "no_maneuver"
            if lane_changes[veh]:
                if math.isfinite(collision_time) and lane_changes[veh][0] >= collision_time:
                    outcome = "late_maneuver_after_collision"
                else:
                    outcome = "maneuver_before_collision"
            if veh in collision_vehicles and (
                not lane_changes[veh] or (math.isfinite(collision_time) and lane_changes[veh][0] >= collision_time)
            ):
                outcome = "no_maneuver_before_collision"
            writer.writerow(
                {
                    "vehicle_id": veh,
                    "equiv_tx_power_dbm": f"{cfg.equiv_tx_power_dbm:.4f}" if math.isfinite(cfg.equiv_tx_power_dbm) else "",
                    "target_prr": f"{cfg.target_prr:.4f}" if math.isfinite(cfg.target_prr) else "",
                    "observed_prr": f"{observed_prr:.4f}" if math.isfinite(observed_prr) else "",
                    "prr_error_observed_minus_target": f"{prr_error:.4f}" if math.isfinite(prr_error) else "",
                    "configured_rx_drop_prob_phy_cam": f"{cfg.rx_drop_prob_phy_cam:.6f}" if math.isfinite(cfg.rx_drop_prob_phy_cam) else "",
                    "first_decision_event": first_decision.event_type,
                    "first_decision_time_s": f"{first_decision.time_s:.5f}" if math.isfinite(first_decision.time_s) else "",
                    "first_lane_change_s": f"{first_lc:.5f}" if math.isfinite(first_lc) else "",
                    "decision_outcome": outcome,
                    "in_collision_xml": "1" if veh in collision_vehicles else "0",
                }
            )

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

    # 4) dBm -> PRR -> decision chain (target vs observed)
    fig, ax = plt.subplots(1, 3, figsize=(13.2, 4.2))
    x_idx = np.arange(len(VEHICLES))
    target_prr = []
    observed_prr = []
    for veh in VEHICLES:
        cfg = profile_cfg[veh]
        target_prr.append(cfg.target_prr if math.isfinite(cfg.target_prr) else math.nan)
        events = veh_events[veh]
        total = len(events)
        observed_prr.append((sum(1 for e in events if e.ok) / total) if total else math.nan)

    width = 0.34
    ax[0].bar(x_idx - width / 2.0, target_prr, width=width, label="target PRR", color="#999999")
    ax[0].bar(x_idx + width / 2.0, observed_prr, width=width, label="observed PRR", color="#1f77b4")
    ax[0].set_xticks(x_idx)
    ax[0].set_xticklabels(VEHICLES)
    ax[0].set_ylim(0.0, 1.05)
    ax[0].set_ylabel("PRR [-]")
    ax[0].set_title("Target vs observed PRR")
    ax[0].grid(alpha=0.3, axis="y")
    ax[0].legend(fontsize=8)

    for veh in VEHICLES:
        cfg = profile_cfg[veh]
        x = cfg.equiv_tx_power_dbm
        events = veh_events[veh]
        total = len(events)
        y = (sum(1 for e in events if e.ok) / total) if total else math.nan
        if math.isfinite(x) and math.isfinite(y):
            ax[1].scatter([x], [y], s=70, color=colors[veh], label=veh)
            ax[1].annotate(veh, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=9)
    ax[1].set_xlabel("Equivalent TX power [dBm]")
    ax[1].set_ylabel("Observed PRR [-]")
    ax[1].set_ylim(0.0, 1.05)
    ax[1].set_title("Configured dBm vs observed PRR")
    ax[1].grid(alpha=0.3)

    y_map_chain = {"veh3": 3, "veh4": 2, "veh5": 1}
    for veh in VEHICLES:
        y = y_map_chain[veh]
        first_decision = decisions[veh]
        if math.isfinite(first_decision.time_s):
            marker = "^" if "reaction" in first_decision.event_type else "x"
            ax[2].scatter([first_decision.time_s], [y], s=70, marker=marker, color=colors[veh])
            ax[2].text(first_decision.time_s + 0.2, y + 0.05, first_decision.event_type, fontsize=8)
        if lane_changes[veh]:
            ax[2].scatter([lane_changes[veh][0]], [y + 0.18], s=65, marker="o", color="#1f77b4")
        if veh in collision_vehicles:
            x_c = collision_time if math.isfinite(collision_time) else (first_decision.time_s if math.isfinite(first_decision.time_s) else math.nan)
            if math.isfinite(x_c):
                ax[2].scatter([x_c], [y - 0.18], s=75, marker="s", color="#d62728")
    if math.isfinite(collision_time):
        ax[2].axvline(collision_time, linestyle=":", color="black", linewidth=1.4)
    ax[2].set_yticks([1, 2, 3])
    ax[2].set_yticklabels(["veh5", "veh4", "veh3"])
    ax[2].set_xlabel("Time [s]")
    ax[2].set_title("Decision/maneuver/collision timeline")
    ax[2].grid(alpha=0.3)

    chain_png = out_dir / "intuitive_dbm_prr_maneuver_chain.png"
    fig.tight_layout()
    fig.savefig(chain_png, dpi=170)
    plt.close(fig)

    print(summary_csv)
    print(key_csv)
    print(chain_csv)
    print(prr_png)
    print(raster_png)
    print(speed_png)
    print(chain_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
