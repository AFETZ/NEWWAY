#!/usr/bin/env python3
"""Generate all Chapter 3 figures for VKR in unified academic style.

Reads raw CSV/XML data from actual simulation runs and produces
publication-quality figures with Russian labels.

Run directories:
  SAFE_RUN:  ~/NEWWAY_runs/2026-03-04/valid_scenario_veh4_23dbm_sionna_232402
  CRASH_RUN: analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2
  INTERSECTION: ~/NEWWAY_runs/2026-03-05/{live_intersection_crash,live_intersection_safe}

Output: analysis/vkr/figures/figure_3_*.png
"""
from __future__ import annotations

import csv
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "analysis" / "vkr" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

HOME = Path.home()
SAFE_RUN = HOME / "NEWWAY_runs/2026-03-04/valid_scenario_veh4_23dbm_sionna_232402"
CRASH_RUN = ROOT / "analysis/scenario_runs/2026-03-04/valid_scenario_prr_chain_check_v2"

# Intersection runs
INT_CRASH = HOME / "NEWWAY_runs/2026-03-05/live_intersection_crash"
INT_SAFE  = HOME / "NEWWAY_runs/2026-03-05/live_intersection_safe"
INT_FIXED = HOME / "NEWWAY_runs/2026-03-05/intersection_fixed_live"

# Sweep runs
SWEEP_RUNS = {
    -30: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_-30",
    -20: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_-20",
    -10: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_-10",
      0: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_0",
     10: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_10",
     23: HOME / "NEWWAY_runs/2026-03-05/txpower_sweep_23",
}

FOCUS_VEHICLES = ["veh2", "veh3", "veh4", "veh5"]
VEH_COLORS = {
    "veh2": "#c0392b",
    "veh3": "#27ae60",
    "veh4": "#2980b9",
    "veh5": "#8e44ad",
}

# ── Global style ─────────────────────────────────────────────────────
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "lines.linewidth": 2.0,
})


# ═══════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════

def _to_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return math.nan


def _lane_index(lane_id: str) -> int:
    if "_" not in lane_id:
        return -1
    tail = lane_id.rsplit("_", 1)[-1]
    try:
        return int(tail)
    except Exception:
        return -1


def parse_netstate(path: Path, focus: set[str]) -> dict[str, pd.DataFrame]:
    """Parse SUMO netstate XML into per-vehicle DataFrames."""
    records: dict[str, list] = defaultdict(list)
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "timestep":
            continue
        t = _to_float(elem.attrib.get("time"))
        for edge in elem.findall("edge"):
            for lane in edge.findall("lane"):
                lane_id = lane.attrib.get("id", "")
                for veh in lane.findall("vehicle"):
                    vid = veh.attrib.get("id", "")
                    if vid not in focus:
                        continue
                    records[vid].append({
                        "time_s": t,
                        "lane_idx": _lane_index(lane_id),
                        "speed": _to_float(veh.attrib.get("speed")),
                        "pos": _to_float(veh.attrib.get("pos")),
                    })
        elem.clear()
    result = {}
    for vid, rows in records.items():
        df = pd.DataFrame(rows).sort_values("time_s").reset_index(drop=True)
        result[vid] = df
    return result


def parse_collision_xml(path: Path) -> list[dict]:
    """Parse collision XML to get collision events."""
    if not path.exists():
        return []
    root = ET.parse(path).getroot()
    collisions = []
    for c in root.findall("collision"):
        collisions.append({
            "time": _to_float(c.attrib.get("time")),
            "collider": c.attrib.get("collider", ""),
            "victim": c.attrib.get("victim", ""),
        })
    return collisions


def read_msg_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_ctrl_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_profile_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compute_cumulative_prr(msg_df: pd.DataFrame, tx_id: int) -> pd.DataFrame:
    """Compute cumulative PRR for CAM messages from a specific transmitter."""
    if msg_df.empty or "msg_type" not in msg_df.columns:
        return pd.DataFrame(columns=["time_s", "prr"])
    cam = msg_df[msg_df["msg_type"].isin(["CAM", "CAM_DROP_PHY"])].copy()
    cam = cam[pd.to_numeric(cam.get("tx_id"), errors="coerce") == tx_id].copy()
    cam["rx_t_s"] = pd.to_numeric(cam.get("rx_t_s"), errors="coerce")
    cam["tx_t_s"] = pd.to_numeric(cam.get("tx_t_s"), errors="coerce")
    cam["time_s"] = cam["rx_t_s"].fillna(cam["tx_t_s"])
    cam = cam.sort_values("time_s").reset_index(drop=True)
    if cam.empty:
        return pd.DataFrame(columns=["time_s", "prr"])
    cam["rx_ok"] = pd.to_numeric(cam.get("rx_ok"), errors="coerce").fillna(0)
    cam["cum_total"] = range(1, len(cam) + 1)
    cam["cum_ok"] = cam["rx_ok"].cumsum()
    cam["prr"] = cam["cum_ok"] / cam["cum_total"]
    return cam[["time_s", "prr"]].copy()


def count_ctrl_events(ctrl_df: pd.DataFrame) -> pd.DataFrame:
    """Count CTRL events per second for event flow plot."""
    if ctrl_df.empty or "time_s" not in ctrl_df.columns:
        return pd.DataFrame(columns=["time_bin", "count", "event_type"])
    ctrl_df = ctrl_df.copy()
    ctrl_df["time_s"] = pd.to_numeric(ctrl_df["time_s"], errors="coerce")
    ctrl_df["time_bin"] = ctrl_df["time_s"].apply(lambda x: int(x))
    grouped = ctrl_df.groupby(["time_bin", "event_type"]).size().reset_index(name="count")
    return grouped


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.1 — Safe mode: speed + lane timeseries
# ═══════════════════════════════════════════════════════════════════════

def figure_3_1(run_dir: Path):
    print("  Figure 3.1: speed/lane safe mode ...")
    art = run_dir / "artifacts"
    ns = parse_netstate(art / "eva-netstate.xml", set(FOCUS_VEHICLES))

    fig, (ax_speed, ax_lane) = plt.subplots(2, 1, figsize=(12, 7),
                                             sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    for vid in FOCUS_VEHICLES:
        if vid not in ns:
            continue
        df = ns[vid]
        ax_speed.plot(df["time_s"], df["speed"], color=VEH_COLORS[vid], label=vid)
        ax_lane.plot(df["time_s"], df["lane_idx"], color=VEH_COLORS[vid], label=vid)

    # Incident marker
    ax_speed.axvline(6.0, color="gray", linestyle="--", alpha=0.7, label="инцидент (t=6 c)")

    ax_speed.set_ylabel("Скорость [м/с]")
    ax_speed.set_title("Безопасный режим: скорости транспортных средств")
    ax_speed.legend(loc="upper right", ncol=3, framealpha=0.9)

    ax_lane.set_ylabel("Индекс полосы")
    ax_lane.set_xlabel("Время [с]")
    ax_lane.set_title("Безопасный режим: полосы движения")
    ax_lane.legend(loc="upper right", ncol=3, framealpha=0.9)
    ax_lane.set_ylim(-0.1, 1.5)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_1_speed_lane_safe.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.2 — Safe mode: cumulative PRR
# ═══════════════════════════════════════════════════════════════════════

def figure_3_2(run_dir: Path):
    print("  Figure 3.2: cumulative PRR safe mode ...")
    art = run_dir / "artifacts"

    fig, ax = plt.subplots(figsize=(12, 5))

    for vid in ["veh3", "veh4", "veh5"]:
        msg_df = read_msg_csv(art / f"eva-{vid}-MSG.csv")
        prr_df = compute_cumulative_prr(msg_df, tx_id=2)
        if not prr_df.empty:
            ax.plot(prr_df["time_s"], prr_df["prr"],
                    color=VEH_COLORS[vid], label=f"{vid}")

    ax.axvline(6.0, color="gray", linestyle="--", alpha=0.6, label="инцидент")
    ax.set_xlabel("Время [с]")
    ax.set_ylabel("Накопительный PRR")
    ax.set_ylim(-0.02, 1.05)
    ax.set_title("Накопительный PRR предупредительных CAM от veh2 (безопасный режим)")
    ax.legend(loc="lower right", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_2_prr_cumulative_safe.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.3 — Safe mode: dBm → PRR → maneuver chain
# ═══════════════════════════════════════════════════════════════════════

def figure_3_3(run_dir: Path):
    print("  Figure 3.3: dBm-PRR-maneuver chain safe mode ...")
    art = run_dir / "artifacts"
    chain_path = art / "valid_scenario_intuitive" / "intuitive_dbm_prr_maneuver_chain.csv"
    if not chain_path.exists():
        print("    WARNING: intuitive_dbm_prr_maneuver_chain.csv not found, skipping")
        return

    df = pd.read_csv(chain_path)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    vehicles = df["vehicle_id"].tolist()
    x = np.arange(len(vehicles))
    width = 0.6
    colors = [VEH_COLORS.get(v, "#333") for v in vehicles]

    # Panel 1: equiv_tx_power_dbm
    ax = axes[0]
    ax.bar(x, df["equiv_tx_power_dbm"], width, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_ylabel("Эквив. мощность [дБм]")
    ax.set_title("Мощность передатчика")
    ax.axhline(0, color="gray", linewidth=0.5)

    # Panel 2: observed PRR
    ax = axes[1]
    ax.bar(x, df["observed_prr"], width, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_ylabel("Наблюдаемый PRR")
    ax.set_ylim(0, 1.1)
    ax.set_title("Наблюдаемый PRR")

    # Panel 3: outcome
    outcome_col = "decision_outcome" if "decision_outcome" in df.columns else "first_decision_event"
    outcome_labels = {
        "maneuver_before_collision": "маневр\nдо столкновения",
        "no_maneuver_before_collision": "нет маневра\nдо столкновения",
        "late_maneuver_after_collision": "поздний\nманевр",
        "no_collision_safe": "безопасный\nисход",
    }
    ax = axes[2]
    outcome_colors = []
    outcome_texts = []
    for _, row in df.iterrows():
        oc = row.get("decision_outcome", row.get("first_decision_event", ""))
        if oc in ("maneuver_before_collision", "no_collision_safe"):
            outcome_colors.append("#27ae60")
        elif oc == "no_maneuver_before_collision":
            outcome_colors.append("#c0392b")
        else:
            outcome_colors.append("#f39c12")
        outcome_texts.append(outcome_labels.get(oc, oc))

    ax.bar(x, [1]*len(vehicles), width, color=outcome_colors, alpha=0.85)
    for i, txt in enumerate(outcome_texts):
        ax.text(i, 0.5, txt, ha="center", va="center", fontsize=8, fontweight="bold", color="white")
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_title("Исход")
    ax.set_yticks([])

    fig.suptitle("Цепочка «мощность - PRR - маневр» (безопасный режим)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "figure_3_3_dbm_prr_chain_safe.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.4 — Crash mode: speed + lane timeseries
# ═══════════════════════════════════════════════════════════════════════

def figure_3_4(run_dir: Path):
    print("  Figure 3.4: speed/lane crash mode ...")
    art = run_dir / "artifacts"
    ns = parse_netstate(art / "eva-netstate.xml", set(FOCUS_VEHICLES))

    # Find collision time
    collisions = parse_collision_xml(art / "eva-collision.xml")
    coll_time = None
    for c in collisions:
        if c["collider"] == "veh4" and c["victim"] == "veh2":
            coll_time = c["time"]
            break

    fig, (ax_speed, ax_lane) = plt.subplots(2, 1, figsize=(12, 7),
                                             sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    for vid in FOCUS_VEHICLES:
        if vid not in ns:
            continue
        df = ns[vid]
        ax_speed.plot(df["time_s"], df["speed"], color=VEH_COLORS[vid], label=vid)
        ax_lane.plot(df["time_s"], df["lane_idx"], color=VEH_COLORS[vid], label=vid)

    ax_speed.axvline(6.0, color="gray", linestyle="--", alpha=0.7, label="инцидент (t=6 c)")
    if coll_time:
        ax_speed.axvline(coll_time, color="red", linestyle="-.", alpha=0.8,
                         label=f"столкновение (t={coll_time:.1f} c)")
    ax_speed.set_ylabel("Скорость [м/с]")
    ax_speed.set_title("Аварийный режим: скорости транспортных средств")
    ax_speed.legend(loc="upper right", ncol=3, framealpha=0.9)

    ax_lane.set_ylabel("Индекс полосы")
    ax_lane.set_xlabel("Время [с]")
    ax_lane.set_title("Аварийный режим: полосы движения")
    ax_lane.legend(loc="upper right", ncol=3, framealpha=0.9)
    ax_lane.set_ylim(-0.1, 1.5)
    if coll_time:
        ax_lane.axvline(coll_time, color="red", linestyle="-.", alpha=0.5)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_4_speed_lane_crash.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.5 — Crash mode: event flow
# ═══════════════════════════════════════════════════════════════════════

def figure_3_5(run_dir: Path):
    print("  Figure 3.5: event flow crash mode ...")
    art = run_dir / "artifacts"

    # Gather all CTRL events from all focus vehicles
    all_ctrl = []
    for vid in FOCUS_VEHICLES:
        ctrl_df = read_ctrl_csv(art / f"eva-{vid}-CTRL.csv")
        if not ctrl_df.empty:
            ctrl_df["vehicle_id"] = vid
            all_ctrl.append(ctrl_df)

    if not all_ctrl:
        print("    WARNING: No CTRL data found, skipping")
        return

    combined = pd.concat(all_ctrl, ignore_index=True)
    combined["time_s"] = pd.to_numeric(combined["time_s"], errors="coerce")
    combined["time_bin"] = combined["time_s"].apply(lambda x: int(x) if math.isfinite(x) else -1)
    combined = combined[combined["time_bin"] >= 0]

    event_types = ["cam_reaction", "drop_decision_no_action", "crash_mode_forced_speed"]
    event_labels = {
        "cam_reaction": "CAM-реакция",
        "drop_decision_no_action": "потеря без действия",
        "crash_mode_forced_speed": "форсированная скорость",
    }
    event_colors = {
        "cam_reaction": "#27ae60",
        "drop_decision_no_action": "#e74c3c",
        "crash_mode_forced_speed": "#f39c12",
    }

    fig, ax = plt.subplots(figsize=(12, 5))

    time_bins = sorted(combined["time_bin"].unique())
    bottom = np.zeros(len(time_bins))

    for etype in event_types:
        counts = []
        for tb in time_bins:
            mask = (combined["time_bin"] == tb) & (combined["event_type"] == etype)
            counts.append(mask.sum())
        counts = np.array(counts)
        if counts.sum() > 0:
            ax.bar(time_bins, counts, bottom=bottom, width=0.8,
                   color=event_colors.get(etype, "#999"),
                   label=event_labels.get(etype, etype), alpha=0.85)
            bottom += counts

    # Also count "other" events
    other_mask = ~combined["event_type"].isin(event_types)
    if other_mask.any():
        other_counts = []
        for tb in time_bins:
            mask = (combined["time_bin"] == tb) & other_mask
            other_counts.append(mask.sum())
        other_counts = np.array(other_counts)
        if other_counts.sum() > 0:
            ax.bar(time_bins, other_counts, bottom=bottom, width=0.8,
                   color="#bdc3c7", label="прочие", alpha=0.7)

    ax.axvline(6.0, color="gray", linestyle="--", alpha=0.7, label="инцидент")

    collisions = parse_collision_xml(art / "eva-collision.xml")
    for c in collisions:
        if c["collider"] == "veh4" and c["victim"] == "veh2":
            ax.axvline(c["time"], color="red", linestyle="-.", alpha=0.8,
                       label=f"столкновение ({c['time']:.1f} c)")

    ax.set_xlabel("Время [с]")
    ax.set_ylabel("Число событий в секунду")
    ax.set_title("Поток сетевых событий и решений (аварийный режим)")
    ax.legend(loc="upper right", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_5_events_crash.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.6 — Crash mode: event chain timeline
# ═══════════════════════════════════════════════════════════════════════

def figure_3_6(run_dir: Path):
    print("  Figure 3.6: event chain timeline crash mode ...")
    art = run_dir / "artifacts"
    chain_path = art / "valid_scenario_story" / "event_chain.csv"

    if not chain_path.exists():
        print("    WARNING: event_chain.csv not found, skipping")
        return

    df = pd.read_csv(chain_path)

    fig, ax = plt.subplots(figsize=(13, 4))

    event_labels_ru = {
        "incident_applied_veh2": "Инцидент veh2",
        "veh3_first_lane_change": "Перестроение veh3",
        "collision_veh4_into_veh2": "Столкновение\nveh4 → veh2",
        "veh4_first_lane_change": "Перестроение veh4",
        "veh5_first_lane_change": "Перестроение veh5",
    }
    event_colors_map = {
        "incident_applied_veh2": "#7f8c8d",
        "veh3_first_lane_change": VEH_COLORS["veh3"],
        "collision_veh4_into_veh2": "#c0392b",
        "veh4_first_lane_change": VEH_COLORS["veh4"],
        "veh5_first_lane_change": VEH_COLORS["veh5"],
    }
    event_markers = {
        "incident_applied_veh2": "D",
        "veh3_first_lane_change": "o",
        "collision_veh4_into_veh2": "X",
        "veh4_first_lane_change": "o",
        "veh5_first_lane_change": "o",
    }

    for i, row in df.iterrows():
        name = row["event_name"]
        t = row["time_s"]
        label = event_labels_ru.get(name, name)
        color = event_colors_map.get(name, "#333")
        marker = event_markers.get(name, "o")

        ax.scatter(t, 0, s=120, marker=marker, color=color, zorder=5, edgecolors="white", linewidth=0.8)
        ax.annotate(label, (t, 0), xytext=(0, 15 if i % 2 == 0 else -25),
                    textcoords="offset points", ha="center", va="bottom" if i % 2 == 0 else "top",
                    fontsize=9, fontweight="bold", color=color,
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.8))
        ax.annotate(f"t = {t:.2f} c", (t, 0), xytext=(0, 28 if i % 2 == 0 else -38),
                    textcoords="offset points", ha="center",
                    va="bottom" if i % 2 == 0 else "top",
                    fontsize=8, color="#666")

    ax.axhline(0, color="#ddd", linewidth=2, zorder=1)
    ax.set_xlim(5, max(df["time_s"]) + 1.5)
    ax.set_ylim(-0.6, 0.6)
    ax.set_xlabel("Время [с]")
    ax.set_title("Причинная шкала событий (аварийный режим)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_6_event_chain_crash.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.7 — Crash mode: dBm → PRR → decision → outcome chain
# ═══════════════════════════════════════════════════════════════════════

def figure_3_7(run_dir: Path):
    print("  Figure 3.7: dBm-PRR-decision-outcome chain crash mode ...")
    art = run_dir / "artifacts"
    chain_path = art / "valid_scenario_intuitive" / "intuitive_dbm_prr_maneuver_chain.csv"
    if not chain_path.exists():
        print("    WARNING: intuitive_dbm_prr_maneuver_chain.csv not found, skipping")
        return

    df = pd.read_csv(chain_path)

    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    vehicles = df["vehicle_id"].tolist()
    x = np.arange(len(vehicles))
    width = 0.6
    colors = [VEH_COLORS.get(v, "#333") for v in vehicles]

    # Panel 1: equiv_tx_power_dbm
    ax = axes[0]
    ax.bar(x, df["equiv_tx_power_dbm"], width, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_ylabel("дБм")
    ax.set_title("Эквив. мощность")
    ax.axhline(0, color="gray", linewidth=0.5)

    # Panel 2: observed PRR
    ax = axes[1]
    ax.bar(x, df["observed_prr"], width, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_ylabel("PRR")
    ax.set_ylim(0, 1.1)
    ax.set_title("Наблюдаемый PRR")

    # Panel 3: first lane change time
    ax = axes[2]
    lane_times = pd.to_numeric(df.get("first_lane_change_s", pd.Series(dtype=float)), errors="coerce")
    ax.bar(x, lane_times, width, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_ylabel("Время [с]")
    ax.set_title("Первое перестроение")
    # collision line
    ax.axhline(7.94, color="red", linestyle="--", alpha=0.6, label="столкновение")
    ax.legend(fontsize=8)

    # Panel 4: outcome
    outcome_col = "decision_outcome" if "decision_outcome" in df.columns else "first_decision_event"
    outcome_labels = {
        "maneuver_before_collision": "маневр\nдо столкн.",
        "no_maneuver_before_collision": "нет маневра\nдо столкн.",
        "late_maneuver_after_collision": "поздний\nманевр",
    }
    ax = axes[3]
    outcome_colors_list = []
    outcome_texts = []
    for _, row in df.iterrows():
        oc = row.get(outcome_col, "")
        if oc == "maneuver_before_collision":
            outcome_colors_list.append("#27ae60")
        elif oc == "no_maneuver_before_collision":
            outcome_colors_list.append("#c0392b")
        else:
            outcome_colors_list.append("#f39c12")
        outcome_texts.append(outcome_labels.get(oc, str(oc)[:15]))

    ax.bar(x, [1]*len(vehicles), width, color=outcome_colors_list, alpha=0.85)
    for i, txt in enumerate(outcome_texts):
        ax.text(i, 0.5, txt, ha="center", va="center", fontsize=8, fontweight="bold", color="white")
    ax.set_xticks(x)
    ax.set_xticklabels(vehicles)
    ax.set_title("Исход")
    ax.set_yticks([])

    fig.suptitle("Цепочка «качество канала - PRR - решение - исход» (аварийный режим)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "figure_3_7_dbm_prr_chain_crash.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# INTERSECTION SCENARIO HELPERS
# ═══════════════════════════════════════════════════════════════════════

def parse_intersection_netstate(path: Path) -> pd.DataFrame:
    """Parse intersection netstate into a flat DataFrame with x,y via pos on lane."""
    rows = []
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "timestep":
            continue
        t = _to_float(elem.attrib.get("time"))
        for edge in elem.findall("edge"):
            edge_id = edge.attrib.get("id", "")
            for lane in edge.findall("lane"):
                lane_id = lane.attrib.get("id", "")
                for veh in lane.findall("vehicle"):
                    rows.append({
                        "time_s": t,
                        "vehicle_id": veh.attrib.get("id", ""),
                        "edge_id": edge_id,
                        "lane_id": lane_id,
                        "pos_m": _to_float(veh.attrib.get("pos")),
                        "speed_mps": _to_float(veh.attrib.get("speed")),
                    })
        elem.clear()
    return pd.DataFrame(rows).sort_values(["vehicle_id", "time_s"]).reset_index(drop=True)


def load_intersection_mode(run_dir: Path) -> dict:
    """Load intersection mode artifacts."""
    art = run_dir / "artifacts"
    ctrl_veh3 = read_ctrl_csv(art / "eva-veh3-CTRL.csv")
    msg_veh2 = read_msg_csv(art / "eva-veh2-MSG.csv")
    msg_veh3 = read_msg_csv(art / "eva-veh3-MSG.csv")
    collision_time = math.nan
    collisions = parse_collision_xml(art / "eva-collision.xml")
    for c in collisions:
        if {"veh2", "veh3"} == {c["collider"], c["victim"]}:
            collision_time = c["time"]
            break

    first_cam = math.nan
    first_sensor = math.nan
    if not ctrl_veh3.empty and "event_type" in ctrl_veh3.columns:
        ctrl_veh3["time_s"] = pd.to_numeric(ctrl_veh3["time_s"], errors="coerce")
        cam_mask = ctrl_veh3["event_type"] == "cam_reaction"
        if cam_mask.any():
            first_cam = ctrl_veh3.loc[cam_mask, "time_s"].min()
        sensor_mask = ctrl_veh3["event_type"] == "sensor_reaction"
        if sensor_mask.any():
            first_sensor = ctrl_veh3.loc[sensor_mask, "time_s"].min()

    summary_path = art / "intersection_summary.csv"
    summary = {}
    if summary_path.exists():
        sdf = pd.read_csv(summary_path)
        if not sdf.empty:
            summary = sdf.iloc[0].to_dict()

    return {
        "run_dir": run_dir,
        "netstate_df": parse_intersection_netstate(art / "eva-netstate.xml"),
        "ctrl_df": ctrl_veh3,
        "tx_df": msg_veh2,
        "rx_df": msg_veh3,
        "collision_time": collision_time,
        "first_cam": first_cam,
        "first_sensor": first_sensor,
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.8 — XY trajectories on intersection
# ═══════════════════════════════════════════════════════════════════════

def figure_3_8():
    print("  Figure 3.8: XY trajectories intersection ...")
    modes = {
        "radar_bad_link": load_intersection_mode(INT_CRASH),
        "radar_only": None,
        "radar_good_link": load_intersection_mode(INT_SAFE),
    }

    mode_labels = {
        "radar_bad_link": "Radar + деградированная связь",
        "radar_only": "Только радар",
        "radar_good_link": "Radar + качественная связь",
    }
    mode_colors_border = {
        "radar_bad_link": "#c0392b",
        "radar_only": "#d68910",
        "radar_good_link": "#1e8449",
    }
    int_veh_colors = {"veh2": "#c0392b", "veh3": "#1f618d"}

    available_modes = [m for m in modes if modes[m] is not None]
    n = len(available_modes)

    fig, axes_list = plt.subplots(1, n, figsize=(7 * n, 5.5), constrained_layout=True)
    if n == 1:
        axes_list = [axes_list]

    for ax, mode in zip(axes_list, available_modes):
        art = modes[mode]
        ndf = art["netstate_df"]

        for vid in ["veh2", "veh3"]:
            vdf = ndf[ndf["vehicle_id"] == vid]
            # Use pos_m on lane as proxy for progress
            ax.plot(vdf["time_s"], vdf["pos_m"], color=int_veh_colors[vid],
                    linewidth=2, label=vid)

        if math.isfinite(art["collision_time"]):
            ax.axvline(art["collision_time"], color="black", linestyle="-.", alpha=0.6,
                       label=f"столкновение ({art['collision_time']:.1f} c)")
        if math.isfinite(art["first_cam"]):
            ax.axvline(art["first_cam"], color="#1e8449", linestyle="--", alpha=0.6,
                       label=f"CAM-реакция ({art['first_cam']:.2f} c)")
        if math.isfinite(art["first_sensor"]):
            ax.axvline(art["first_sensor"], color="#d68910", linestyle=":", alpha=0.6,
                       label=f"сенсор ({art['first_sensor']:.2f} c)")

        ax.set_title(mode_labels[mode], color=mode_colors_border[mode], fontweight="bold")
        ax.set_xlabel("Время [с]")
        ax.set_ylabel("Позиция на маршруте [м]")
        ax.legend(fontsize=8, loc="best")

    fig.suptitle("Траектории транспортных средств на перекрестке", fontsize=13, fontweight="bold")
    fig.savefig(OUT / "figure_3_8_xy_trajectories.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.9 — veh3 speed profile on intersection
# ═══════════════════════════════════════════════════════════════════════

def figure_3_9():
    print("  Figure 3.9: veh3 speed profile intersection ...")
    modes_data = {
        "radar_bad_link": load_intersection_mode(INT_CRASH),
        "radar_good_link": load_intersection_mode(INT_SAFE),
    }
    mode_labels = {
        "radar_bad_link": "Radar + деград. связь",
        "radar_good_link": "Radar + качеств. связь",
    }
    mode_colors = {
        "radar_bad_link": "#c0392b",
        "radar_good_link": "#1e8449",
    }

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for mode, art in modes_data.items():
        vdf = art["netstate_df"]
        vdf = vdf[vdf["vehicle_id"] == "veh3"]
        ax.plot(vdf["time_s"], vdf["speed_mps"], color=mode_colors[mode],
                linewidth=2, label=mode_labels[mode])
        if math.isfinite(art["first_cam"]):
            ax.axvline(art["first_cam"], color=mode_colors[mode], linestyle="--", alpha=0.65)
            ax.text(art["first_cam"] + 0.05, ax.get_ylim()[1] * 0.9,
                    f"CAM: {art['first_cam']:.2f} c", fontsize=8, color=mode_colors[mode])
        if math.isfinite(art["first_sensor"]):
            ax.axvline(art["first_sensor"], color=mode_colors[mode], linestyle=":", alpha=0.65)
        if math.isfinite(art["collision_time"]):
            ax.axvline(art["collision_time"], color=mode_colors[mode], linestyle="-.", alpha=0.55)

    ax.set_xlabel("Время [с]")
    ax.set_ylabel("Скорость veh3 [м/с]")
    ax.set_title("Скоростной профиль veh3 и моменты реакции (сценарий перекрестка)")
    ax.legend(loc="upper right", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_9_veh3_speed.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.10 — CAM delivery + cumulative PRR on intersection
# ═══════════════════════════════════════════════════════════════════════

def figure_3_10():
    print("  Figure 3.10: CAM delivery + PRR intersection ...")
    modes_data = {
        "radar_bad_link": load_intersection_mode(INT_CRASH),
        "radar_good_link": load_intersection_mode(INT_SAFE),
    }
    mode_labels = {
        "radar_bad_link": "Radar + деград. связь",
        "radar_good_link": "Radar + качеств. связь",
    }
    mode_colors = {
        "radar_bad_link": "#c0392b",
        "radar_good_link": "#1e8449",
    }

    fig, (ax_count, ax_prr) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for mode, art in modes_data.items():
        tx_df = art["tx_df"]
        rx_df = art["rx_df"]

        # TX count (from veh2)
        if not tx_df.empty and "msg_type" in tx_df.columns:
            tx_cam = tx_df[(tx_df["msg_type"] == "CAM")]
            tx_times = pd.to_numeric(tx_cam.get("tx_t_s"), errors="coerce").dropna().sort_values()
            tx_cum = np.arange(1, len(tx_times) + 1)
            ax_count.step(tx_times, tx_cum, where="post",
                         color=mode_colors[mode], linestyle="--", linewidth=1.5,
                         label=f"{mode_labels[mode]} TX", alpha=0.7)

        # RX ok count (at veh3 from veh2)
        if not rx_df.empty and "msg_type" in rx_df.columns:
            rx_cam = rx_df[
                (rx_df["msg_type"] == "CAM") &
                (pd.to_numeric(rx_df.get("tx_id"), errors="coerce") == 2) &
                (pd.to_numeric(rx_df.get("rx_ok"), errors="coerce") == 1)
            ]
            rx_times = pd.to_numeric(rx_cam.get("rx_t_s"), errors="coerce").dropna().sort_values()
            rx_cum = np.arange(1, len(rx_times) + 1)
            ax_count.step(rx_times, rx_cum, where="post",
                         color=mode_colors[mode], linewidth=2,
                         label=f"{mode_labels[mode]} RX ok")

        # Cumulative PRR
        prr_df = compute_cumulative_prr(rx_df, tx_id=2)
        if not prr_df.empty:
            ax_prr.step(prr_df["time_s"], prr_df["prr"], where="post",
                       color=mode_colors[mode], linewidth=2, label=mode_labels[mode])

    ax_count.set_ylabel("Число сообщений")
    ax_count.set_title("Доставка CAM от veh2 к veh3 (live Sionna)")
    ax_count.legend(ncol=2, fontsize=9)

    ax_prr.set_xlabel("Время [с]")
    ax_prr.set_ylabel("Накопительный PRR")
    ax_prr.set_ylim(-0.02, 1.05)
    ax_prr.set_title("Накопительный PRR")
    ax_prr.legend()

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_10_comm_delivery.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.11 — Pre-event speed spread
# ═══════════════════════════════════════════════════════════════════════

def figure_3_11():
    print("  Figure 3.11: pre-event speed spread intersection ...")
    modes_data = {
        "radar_bad_link": load_intersection_mode(INT_CRASH),
        "radar_good_link": load_intersection_mode(INT_SAFE),
    }

    # Find first control event across modes
    event_times = []
    for art in modes_data.values():
        if math.isfinite(art["first_cam"]):
            event_times.append(art["first_cam"])
        if math.isfinite(art["first_sensor"]):
            event_times.append(art["first_sensor"])
    first_control = min(event_times) if event_times else 5.0

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    for ax, vid in zip(axes, ["veh2", "veh3"]):
        # Get speed timeseries for each mode
        speed_series = {}
        for mode, art in modes_data.items():
            vdf = art["netstate_df"]
            vdf = vdf[vdf["vehicle_id"] == vid][["time_s", "speed_mps"]].copy()
            vdf = vdf.sort_values("time_s")
            speed_series[mode] = vdf.set_index("time_s")["speed_mps"]

        # Compute spread at each common time
        if speed_series:
            all_times = sorted(set().union(*(set(s.index) for s in speed_series.values())))
            spreads = []
            for t in all_times:
                vals = [s.loc[t] if t in s.index else math.nan for s in speed_series.values()]
                vals = [v for v in vals if math.isfinite(v)]
                spreads.append(max(vals) - min(vals) if len(vals) > 1 else 0.0)

            ax.plot(all_times, spreads, color="#34495e", linewidth=2)

        ax.axvline(first_control, color="#7f8c8d", linestyle="--",
                   label=f"первое управляющее событие ({first_control:.2f} c)")
        ax.set_ylabel(f"{vid}: разброс скоростей [м/с]")
        ax.legend(fontsize=9)

    axes[0].set_title("Разброс скоростей между режимами = 0 до первого управляющего воздействия")
    axes[1].set_xlabel("Время [с]")

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_11_pre_event_spread.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 3.12 — dBm sweep on intersection
# ═══════════════════════════════════════════════════════════════════════

def figure_3_12():
    print("  Figure 3.12: dBm sweep intersection ...")

    # Build sweep dataset from all available intersection runs.
    # The txpower_sweep runs cover -30..-10, 0, 10, 23 dBm.
    # The crash mode (live_intersection_crash at -25 dBm) and the
    # intersection_fixed_live (-30 dBm with collision) provide collision points.
    rows = []
    for dbm, run_dir in sorted(SWEEP_RUNS.items()):
        summary_path = run_dir / "artifacts" / "intersection_summary.csv"
        if not summary_path.exists():
            continue
        sdf = pd.read_csv(summary_path)
        if sdf.empty:
            continue
        row = sdf.iloc[0].to_dict()
        collisions = parse_collision_xml(run_dir / "artifacts" / "eva-collision.xml")
        has_collision = 0
        for c in collisions:
            if {"veh2", "veh3"} == {c["collider"], c["victim"]}:
                has_collision = 1
                break
        rows.append({
            "dbm": dbm,
            "prr": _to_float(row.get("observed_prr_from_tx", row.get("observed_prr_veh3_from_veh2", 0))),
            "first_cam": _to_float(row.get("first_cam_reaction_s")),
            "first_sensor": _to_float(row.get("first_sensor_reaction_s", math.nan)),
            "collision": has_collision,
        })

    # Add crash mode data (-25 dBm, collision=1) if not already present
    for dbm_val, run_dir in [(-25, INT_CRASH), (-30, INT_FIXED)]:
        summary_path = run_dir / "artifacts" / "intersection_summary.csv"
        if not summary_path.exists():
            continue
        sdf = pd.read_csv(summary_path)
        if sdf.empty:
            continue
        row = sdf.iloc[0].to_dict()
        collisions = parse_collision_xml(run_dir / "artifacts" / "eva-collision.xml")
        has_collision = 0
        for c in collisions:
            if {"veh2", "veh3"} == {c["collider"], c["victim"]}:
                has_collision = 1
                break
        # For -30, replace the non-collision sweep point with the collision one
        existing = [r for r in rows if r["dbm"] == dbm_val]
        if existing and has_collision:
            for r in rows:
                if r["dbm"] == dbm_val:
                    r["prr"] = _to_float(row.get("observed_prr_from_tx",
                                                  row.get("observed_prr_veh3_from_veh2", 0)))
                    r["first_cam"] = _to_float(row.get("first_cam_reaction_s"))
                    r["collision"] = has_collision
        elif not existing:
            rows.append({
                "dbm": dbm_val,
                "prr": _to_float(row.get("observed_prr_from_tx",
                                          row.get("observed_prr_veh3_from_veh2", 0))),
                "first_cam": _to_float(row.get("first_cam_reaction_s")),
                "first_sensor": _to_float(row.get("first_sensor_reaction_s", math.nan)),
                "collision": has_collision,
            })

    if not rows:
        print("    WARNING: No sweep data found, skipping")
        return

    sweep_df = pd.DataFrame(rows).sort_values("dbm").reset_index(drop=True)

    fig, (ax_prr, ax_reaction) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    colors = sweep_df["collision"].map({1: "#c0392b", 0: "#1e8449"})

    # PRR panel
    ax_prr.plot(sweep_df["dbm"], sweep_df["prr"], color="#2e86c1", linewidth=1.6)
    ax_prr.scatter(sweep_df["dbm"], sweep_df["prr"], c=colors, s=80, zorder=3, edgecolors="white", linewidth=0.8)
    ax_prr.set_ylabel("Наблюдаемый PRR")
    ax_prr.set_title("Sweep по эквивалентной мощности: PRR и исход на перекрестке")

    # Legend for collision markers
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#1e8449', markersize=10, label='безопасный исход'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#c0392b', markersize=10, label='столкновение'),
    ]
    ax_prr.legend(handles=legend_elements, loc="lower right")

    # Reaction time panel
    earliest = np.where(
        np.isfinite(sweep_df["first_cam"].values),
        sweep_df["first_cam"].values,
        sweep_df["first_sensor"].values,
    )
    ax_reaction.plot(sweep_df["dbm"], earliest, color="#7d3c98", linewidth=1.6)
    ax_reaction.scatter(sweep_df["dbm"], earliest, c=colors, s=80, zorder=3,
                        edgecolors="white", linewidth=0.8)
    ax_reaction.set_xlabel("Эквивалентная мощность veh3 [дБм]")
    ax_reaction.set_ylabel("Время первого действия [с]")
    ax_reaction.set_title("Момент первого управляющего воздействия определяет исход")

    fig.tight_layout()
    fig.savefig(OUT / "figure_3_12_dbm_sweep.png", facecolor="white")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Generating VKR Chapter 3 figures ...")
    print(f"Output directory: {OUT}")
    print()

    # ── Scenario 1: Valid scenario (obstacle avoidance) ──────────────
    print("=== Scenario 1: Obstacle avoidance ===")

    # Figures 3.1-3.3: Safe mode
    if SAFE_RUN.exists():
        figure_3_1(SAFE_RUN)
        figure_3_2(SAFE_RUN)
        figure_3_3(SAFE_RUN)
    else:
        print(f"  WARNING: Safe run not found: {SAFE_RUN}")

    # Figures 3.4-3.7: Crash mode
    if CRASH_RUN.exists():
        figure_3_4(CRASH_RUN)
        figure_3_5(CRASH_RUN)
        figure_3_6(CRASH_RUN)
        figure_3_7(CRASH_RUN)
    else:
        print(f"  WARNING: Crash run not found: {CRASH_RUN}")

    print()
    print("=== Scenario 2: Intersection ===")

    # Figures 3.8-3.12: Intersection
    if INT_CRASH.exists() and INT_SAFE.exists():
        figure_3_8()
        figure_3_9()
        figure_3_10()
        figure_3_11()
        figure_3_12()
    else:
        print(f"  WARNING: Intersection runs not found")

    print()
    print("Done! All figures saved to:", OUT)


if __name__ == "__main__":
    main()
