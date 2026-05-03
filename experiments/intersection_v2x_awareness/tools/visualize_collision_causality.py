#!/usr/bin/env python3
"""
Visualize the causal chain: PHY drops → unaware mode → collision.

Produces a timeline figure suitable for thesis defense presentation showing
how degraded V2X channel conditions lead to a natural collision.

Usage:
    python3 experiments/intersection_v2x_awareness/tools/visualize_collision_causality.py --run-dir ~/NEWWAY_runs/2026-04-15/intersection_natural
    python3 experiments/intersection_v2x_awareness/tools/visualize_collision_causality.py --run-dir ~/NEWWAY_runs/2026-04-15/intersection_natural --lang ru
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ── Labels ──────────────────────────────────────────────────────────────────

LABELS_EN = {
    "title": "Collision Causality: PHY Channel Degradation → Unaware Mode → Collision",
    "xlabel": "Simulation time (s)",
    "cam_rx": "CAM received",
    "cam_drop_phy": "CAM dropped (PHY)",
    "cam_drop_inferred": "CAM dropped (inferred)",
    "unaware_on": "Unaware mode ON",
    "unaware_off": "Unaware mode OFF",
    "cam_suppressed": "CAM reaction suppressed",
    "collision": "Collision",
    "crash_forced": "Crash-mode forced speed",
    "legend_good": "CAM received (good channel)",
    "legend_drop": "CAM lost (degraded channel)",
    "legend_unaware": "Unaware mode active",
    "legend_collision": "Collision event",
    "subtitle_natural": "Natural collision — no force-speed hack",
    "subtitle_old": "Old scenario — crash-mode force-speed",
    "no_collision": "No collision detected",
}

LABELS_RU = {
    "title": "Причинно-следственная цепочка: деградация канала → режим неосведомленности → столкновение",
    "xlabel": "Время моделирования (с)",
    "cam_rx": "CAM принят",
    "cam_drop_phy": "CAM потерян (PHY)",
    "cam_drop_inferred": "CAM потерян (вывод)",
    "unaware_on": "Режим неосвед. ВКЛ",
    "unaware_off": "Режим неосвед. ВЫКЛ",
    "cam_suppressed": "Реакция на CAM подавлена",
    "collision": "Столкновение",
    "crash_forced": "Принудит. скорость",
    "legend_good": "CAM принят (хороший канал)",
    "legend_drop": "CAM потерян (деградация канала)",
    "legend_unaware": "Режим неосведомленности",
    "legend_collision": "Столкновение",
    "subtitle_natural": "Естественное столкновение — без принудительного управления скоростью",
    "subtitle_old": "Старый сценарий — принудительное управление скоростью",
    "no_collision": "Столкновение не обнаружено",
}


def parse_args():
    p = argparse.ArgumentParser(description="Visualize collision causality timeline")
    p.add_argument("--run-dir", required=True, help="Run output directory")
    p.add_argument("--focus-vehicle", default="veh3", help="Vehicle under analysis")
    p.add_argument("--tx-id", default="2", help="Emergency vehicle station ID")
    p.add_argument("--out", default="", help="Output image path (default: <run-dir>/artifacts/collision_causality_timeline.png)")
    p.add_argument("--lang", default="en", choices=["en", "ru"], help="Label language")
    p.add_argument("--dpi", type=int, default=150)
    return p.parse_args()


def load_msg_events(artifacts: Path, focus_vehicle: str, tx_id: str):
    """Load CAM RX and DROP events for focus_vehicle from tx_id."""
    cam_rx_times = []
    cam_drop_phy_times = []
    cam_drop_inferred_times = []

    for csv_path in sorted(artifacts.glob(f"*{focus_vehicle}-MSG.csv")):
        with csv_path.open(newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 7:
                    continue
                try:
                    rx_time = float(row[3]) if row[3] else None
                except (ValueError, IndexError):
                    continue
                if rx_time is None:
                    continue
                event_type = row[5] if len(row) > 5 else ""
                sender_id = row[6] if len(row) > 6 else ""
                if sender_id != tx_id:
                    continue
                if event_type == "CAM" and row[4] == "1":
                    cam_rx_times.append(rx_time)
                elif event_type == "CAM_DROP_PHY":
                    cam_drop_phy_times.append(rx_time)
                elif event_type == "CAM_DROP_PHY_INFERRED":
                    cam_drop_inferred_times.append(rx_time)

    return cam_rx_times, cam_drop_phy_times, cam_drop_inferred_times


def load_ctrl_events(artifacts: Path, focus_vehicle: str):
    """Load control events for focus_vehicle."""
    events = []
    for csv_path in sorted(artifacts.glob(f"*{focus_vehicle}-CTRL.csv")):
        with csv_path.open(newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3:
                    continue
                try:
                    t = float(row[0])
                except ValueError:
                    continue
                veh_id = row[1]
                event_type = row[2]
                if veh_id == focus_vehicle:
                    events.append((t, event_type))
    return events


def load_collision_time(artifacts: Path, focus_vehicle: str) -> Optional[float]:
    """Find earliest collision time involving focus_vehicle."""
    collision_xml = None
    for candidate in [
        artifacts / "eva-collision.xml",
        artifacts.parent / "collision.xml",
    ]:
        if candidate.exists():
            collision_xml = candidate
            break

    if collision_xml is None:
        # Try collision_causality CSV
        causality_dir = artifacts / "collision_causality"
        for csv_path in sorted(causality_dir.glob("collision_causality*.csv")):
            with csv_path.open(newline="") as f:
                for row_dict in csv.DictReader(f):
                    t = row_dict.get("collision_time_s", "")
                    if t:
                        try:
                            return float(t)
                        except ValueError:
                            pass
        return None

    try:
        tree = ET.parse(collision_xml)
        earliest = None
        for collision in tree.iter("collision"):
            t_str = collision.get("time", "")
            collider = collision.get("collider", "")
            victim = collision.get("victim", "")
            if focus_vehicle in (collider, victim):
                try:
                    t = float(t_str)
                    if earliest is None or t < earliest:
                        earliest = t
                except ValueError:
                    pass
        return earliest
    except Exception:
        return None


def build_timeline_figure(
    cam_rx_times,
    cam_drop_phy_times,
    cam_drop_inferred_times,
    ctrl_events,
    collision_time,
    labels,
    focus_vehicle,
    out_path,
    dpi,
):
    if not HAS_MPL:
        print("matplotlib not available, skipping figure generation", file=sys.stderr)
        return

    fig, ax = plt.subplots(figsize=(14, 5))

    # Plot CAM events on y=1 (received) and y=0 (dropped)
    if cam_rx_times:
        ax.scatter(cam_rx_times, [1.0] * len(cam_rx_times),
                   marker="|", s=100, c="#2ecc71", linewidths=1.5, zorder=3,
                   label=labels["legend_good"])

    all_drops = [(t, "#e74c3c") for t in cam_drop_phy_times] + \
                [(t, "#e67e22") for t in cam_drop_inferred_times]
    if all_drops:
        drop_times = [d[0] for d in all_drops]
        drop_colors = [d[1] for d in all_drops]
        ax.scatter(drop_times, [0.0] * len(drop_times),
                   marker="x", s=80, c=drop_colors, linewidths=1.5, zorder=3,
                   label=labels["legend_drop"])

    # Unaware mode spans
    unaware_starts = [t for t, e in ctrl_events if "unaware_mode_activated" in e]
    unaware_ends = [t for t, e in ctrl_events if "unaware_mode_restore" in e]
    crash_starts = [t for t, e in ctrl_events if "crash_mode_forced_speed" in e]

    for i, start in enumerate(unaware_starts):
        end = unaware_ends[i] if i < len(unaware_ends) else start + 5.0
        ax.axvspan(start, end, alpha=0.15, color="#9b59b6", zorder=1,
                   label=labels["legend_unaware"] if i == 0 else "")

    # Crash mode markers (for old scenario comparison)
    for t in crash_starts:
        ax.axvline(t, color="#c0392b", linestyle="--", alpha=0.7, linewidth=1.5)
        ax.annotate(labels["crash_forced"], (t, 1.3),
                    fontsize=7, color="#c0392b", ha="center")

    # Collision marker
    if collision_time is not None:
        ax.axvline(collision_time, color="#e74c3c", linewidth=3, zorder=5,
                   label=labels["legend_collision"])
        ax.annotate(f"  {labels['collision']} t={collision_time:.1f}s",
                    (collision_time, 1.4), fontsize=9, fontweight="bold",
                    color="#e74c3c")

    # Suppress markers
    suppressed = [t for t, e in ctrl_events if "suppressed_unaware" in e]
    if suppressed:
        ax.scatter(suppressed, [0.5] * len(suppressed),
                   marker="s", s=40, c="#8e44ad", alpha=0.6, zorder=4)

    ax.set_xlabel(labels["xlabel"], fontsize=11)
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.set_yticklabels([labels["cam_drop_phy"], labels["cam_suppressed"], labels["cam_rx"]],
                       fontsize=9)
    ax.set_ylim(-0.3, 1.7)

    is_natural = len(unaware_starts) > 0 and len(crash_starts) == 0
    subtitle = labels["subtitle_natural"] if is_natural else labels["subtitle_old"] if crash_starts else ""
    title = f"{labels['title']}\n({focus_vehicle})"
    if subtitle:
        title += f"\n{subtitle}"
    if collision_time is None:
        title += f"\n[{labels['no_collision']}]"
    ax.set_title(title, fontsize=11, fontweight="bold")

    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main():
    args = parse_args()
    run_dir = Path(args.run_dir)
    artifacts = run_dir / "artifacts"
    labels = LABELS_RU if args.lang == "ru" else LABELS_EN

    if not artifacts.exists():
        print(f"Artifacts directory not found: {artifacts}", file=sys.stderr)
        sys.exit(1)

    cam_rx, cam_drop_phy, cam_drop_inferred = load_msg_events(
        artifacts, args.focus_vehicle, args.tx_id)
    ctrl_events = load_ctrl_events(artifacts, args.focus_vehicle)
    collision_time = load_collision_time(artifacts, args.focus_vehicle)

    out_path = Path(args.out) if args.out else artifacts / "collision_causality_timeline.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Focus vehicle: {args.focus_vehicle}")
    print(f"CAM received: {len(cam_rx)}")
    print(f"CAM dropped (PHY): {len(cam_drop_phy)}")
    print(f"CAM dropped (inferred): {len(cam_drop_inferred)}")
    print(f"Control events: {len(ctrl_events)}")
    print(f"Collision time: {collision_time}")

    # Text summary
    summary_path = out_path.with_suffix(".txt")
    with summary_path.open("w") as f:
        f.write(f"Focus vehicle: {args.focus_vehicle}\n")
        f.write(f"CAM received from tx={args.tx_id}: {len(cam_rx)}\n")
        f.write(f"CAM dropped PHY: {len(cam_drop_phy)}\n")
        f.write(f"CAM dropped inferred: {len(cam_drop_inferred)}\n")
        total_cam = len(cam_rx) + len(cam_drop_phy) + len(cam_drop_inferred)
        prr = len(cam_rx) / total_cam if total_cam > 0 else 0
        f.write(f"Observed PRR: {prr:.3f} ({len(cam_rx)}/{total_cam})\n")
        f.write(f"Collision time: {collision_time}\n\n")

        for t, e in ctrl_events:
            f.write(f"  {t:.3f}s  {e}\n")
    print(f"Saved: {summary_path}")

    build_timeline_figure(
        cam_rx, cam_drop_phy, cam_drop_inferred,
        ctrl_events, collision_time,
        labels, args.focus_vehicle,
        out_path, args.dpi,
    )


if __name__ == "__main__":
    main()
