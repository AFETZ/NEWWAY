#!/usr/bin/env python3
"""Compare baseline vs lossy emergency-incident runs on a common timeline."""

from __future__ import annotations

import argparse
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _floor_seconds(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    return np.floor(vals).astype("Int64")


def _load_msg_timeline(run_dir: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    msg_files = sorted((run_dir / "artifacts").glob("*-MSG.csv"))
    if not msg_files:
        empty = pd.DataFrame(
            columns=["time_s", "cam_drop_events", "cam_rx_ok_events", "cam_drop_ratio"]
        )
        return empty, {
            "total_cam_drop_events": 0.0,
            "total_cam_rx_ok_events": 0.0,
            "overall_cam_drop_ratio": math.nan,
        }

    rows = []
    for f in msg_files:
        try:
            df = pd.read_csv(f, usecols=["rx_t_s", "rx_ok", "msg_type"])
        except Exception:
            continue
        if df.empty:
            continue
        df["rx_t_s"] = pd.to_numeric(df["rx_t_s"], errors="coerce")
        df["rx_ok"] = pd.to_numeric(df["rx_ok"], errors="coerce")
        df["msg_type"] = df["msg_type"].astype(str)
        df = df.dropna(subset=["rx_t_s"])
        if df.empty:
            continue
        rows.append(df)

    if not rows:
        empty = pd.DataFrame(
            columns=["time_s", "cam_drop_events", "cam_rx_ok_events", "cam_drop_ratio"]
        )
        return empty, {
            "total_cam_drop_events": 0.0,
            "total_cam_rx_ok_events": 0.0,
            "overall_cam_drop_ratio": math.nan,
        }

    msg = pd.concat(rows, ignore_index=True)
    msg["time_s"] = _floor_seconds(msg["rx_t_s"])
    msg = msg.dropna(subset=["time_s"])
    msg["time_s"] = msg["time_s"].astype(int)

    msg["is_cam_drop"] = msg["msg_type"].isin(["CAM_DROP_APP", "CAM_DROP_PHY"]).astype(int)
    msg["is_cam_ok"] = ((msg["msg_type"] == "CAM") & (msg["rx_ok"] > 0)).astype(int)

    grouped = (
        msg.groupby("time_s", as_index=False)[["is_cam_drop", "is_cam_ok"]]
        .sum()
        .rename(columns={"is_cam_drop": "cam_drop_events", "is_cam_ok": "cam_rx_ok_events"})
    )
    denom = grouped["cam_drop_events"] + grouped["cam_rx_ok_events"]
    grouped["cam_drop_ratio"] = np.divide(
        grouped["cam_drop_events"],
        denom,
        out=np.full(len(grouped), np.nan, dtype=float),
        where=denom > 0,
    )

    total_drop = float(grouped["cam_drop_events"].sum())
    total_ok = float(grouped["cam_rx_ok_events"].sum())
    overall_ratio = float(total_drop / (total_drop + total_ok)) if (total_drop + total_ok) > 0 else math.nan
    summary = {
        "total_cam_drop_events": total_drop,
        "total_cam_rx_ok_events": total_ok,
        "overall_cam_drop_ratio": overall_ratio,
    }
    return grouped, summary


def _load_ctrl_timeline(run_dir: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    ctrl_files = sorted((run_dir / "artifacts").glob("*-CTRL.csv"))
    if not ctrl_files:
        return pd.DataFrame(columns=["time_s", "control_actions_per_s"]), {
            "total_control_actions": 0.0,
            "first_control_action_s": math.nan,
            "p90_control_action_s": math.nan,
        }

    times = []
    for f in ctrl_files:
        try:
            df = pd.read_csv(f, usecols=["time_s"])
        except Exception:
            continue
        if df.empty:
            continue
        ts = pd.to_numeric(df["time_s"], errors="coerce").dropna()
        if not ts.empty:
            times.extend(ts.to_list())

    if not times:
        return pd.DataFrame(columns=["time_s", "control_actions_per_s"]), {
            "total_control_actions": 0.0,
            "first_control_action_s": math.nan,
            "p90_control_action_s": math.nan,
        }

    t = pd.Series(times, dtype=float)
    sec = np.floor(t).astype(int)
    grouped = sec.value_counts().sort_index().rename_axis("time_s").reset_index(name="control_actions_per_s")
    summary = {
        "total_control_actions": float(len(t)),
        "first_control_action_s": float(np.min(t)),
        "p90_control_action_s": float(np.quantile(t, 0.9)),
    }
    return grouped, summary


def _load_risk_timeline(run_dir: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    risk_ts = run_dir / "artifacts" / "collision_risk" / "collision_risk_timeseries.csv"
    risk_summary = run_dir / "artifacts" / "collision_risk" / "collision_risk_summary.csv"
    out_summary = {
        "min_gap_m": math.nan,
        "min_ttc_s": math.nan,
        "risky_gap_events": math.nan,
        "risky_ttc_events": math.nan,
    }

    if risk_summary.exists():
        try:
            s = pd.read_csv(risk_summary)
            if not s.empty:
                row = s.iloc[0]
                out_summary["min_gap_m"] = float(pd.to_numeric(row.get("min_gap_m"), errors="coerce"))
                out_summary["min_ttc_s"] = float(pd.to_numeric(row.get("min_ttc_s"), errors="coerce"))
                out_summary["risky_gap_events"] = float(
                    pd.to_numeric(row.get("risky_gap_events"), errors="coerce")
                )
                out_summary["risky_ttc_events"] = float(
                    pd.to_numeric(row.get("risky_ttc_events"), errors="coerce")
                )
        except Exception:
            pass

    if not risk_ts.exists():
        return pd.DataFrame(columns=["time_s", "min_gap_m", "min_ttc_s"]), out_summary

    try:
        risk = pd.read_csv(risk_ts, usecols=["time_s", "min_gap_m", "min_ttc_s"])
    except Exception:
        return pd.DataFrame(columns=["time_s", "min_gap_m", "min_ttc_s"]), out_summary

    if risk.empty:
        return pd.DataFrame(columns=["time_s", "min_gap_m", "min_ttc_s"]), out_summary

    risk["time_s"] = _floor_seconds(risk["time_s"])
    risk["min_gap_m"] = pd.to_numeric(risk["min_gap_m"], errors="coerce")
    risk["min_ttc_s"] = pd.to_numeric(risk["min_ttc_s"], errors="coerce")
    risk = risk.dropna(subset=["time_s"])
    risk["time_s"] = risk["time_s"].astype(int)
    grouped = risk.groupby("time_s", as_index=False)[["min_gap_m", "min_ttc_s"]].min()
    return grouped, out_summary


def _load_collision_timeline(run_dir: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    candidates = [
        run_dir / "artifacts" / "eva-collision.xml",
        run_dir / "artifacts" / "collision-output.xml",
    ]
    collision_file = None
    for c in candidates:
        if c.exists():
            collision_file = c
            break
    if collision_file is None:
        extra = sorted((run_dir / "artifacts").glob("*collision*.xml"))
        if extra:
            collision_file = extra[0]

    if collision_file is None:
        return pd.DataFrame(columns=["time_s", "collisions_per_s"]), {"collisions_count": 0.0}

    times = []
    try:
        for _, elem in ET.iterparse(collision_file, events=("end",)):
            tag = elem.tag if isinstance(elem.tag, str) else ""
            if not tag.endswith("collision"):
                elem.clear()
                continue
            t = elem.attrib.get("time")
            if t is not None:
                try:
                    times.append(float(t))
                except ValueError:
                    pass
            elem.clear()
    except Exception:
        return pd.DataFrame(columns=["time_s", "collisions_per_s"]), {"collisions_count": 0.0}

    if not times:
        return pd.DataFrame(columns=["time_s", "collisions_per_s"]), {"collisions_count": 0.0}

    sec = np.floor(np.array(times, dtype=float)).astype(int)
    grouped = (
        pd.Series(sec)
        .value_counts()
        .sort_index()
        .rename_axis("time_s")
        .reset_index(name="collisions_per_s")
    )
    return grouped, {"collisions_count": float(len(times))}


def _parse_log_summary(run_dir: Path) -> dict[str, float]:
    log = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
    out = {
        "avg_prr": math.nan,
        "avg_latency_ms": math.nan,
        "incident_time_s": math.nan,
        "incident_duration_s": math.nan,
    }
    if not log.exists():
        return out
    txt = log.read_text(errors="ignore")
    m_prr = re.search(r"Average PRR:\s*([0-9.]+)", txt)
    m_lat = re.search(r"Average latency \(ms\):\s*([0-9.]+)", txt)
    m_inc = re.search(r"INCIDENT-APPLIED,.*time_s=([0-9.]+).*duration_s=([0-9.]+)", txt)
    if m_prr:
        out["avg_prr"] = float(m_prr.group(1))
    if m_lat:
        out["avg_latency_ms"] = float(m_lat.group(1))
    if m_inc:
        out["incident_time_s"] = float(m_inc.group(1))
        out["incident_duration_s"] = float(m_inc.group(2))
    return out


def _build_case(run_dir: Path, label: str) -> tuple[pd.DataFrame, dict[str, float]]:
    msg_t, msg_s = _load_msg_timeline(run_dir)
    ctrl_t, ctrl_s = _load_ctrl_timeline(run_dir)
    risk_t, risk_s = _load_risk_timeline(run_dir)
    coll_t, coll_s = _load_collision_timeline(run_dir)
    log_s = _parse_log_summary(run_dir)

    max_time = 0
    for df in (msg_t, ctrl_t, risk_t, coll_t):
        if not df.empty:
            max_time = max(max_time, int(df["time_s"].max()))
    timeline = pd.DataFrame({"time_s": np.arange(0, max_time + 1, dtype=int)})
    for df in (msg_t, ctrl_t, risk_t, coll_t):
        if not df.empty:
            timeline = timeline.merge(df, on="time_s", how="left")

    for c in ("cam_drop_events", "cam_rx_ok_events", "control_actions_per_s", "collisions_per_s"):
        if c not in timeline:
            timeline[c] = 0.0
        timeline[c] = timeline[c].fillna(0.0)
    if "cam_drop_ratio" in timeline:
        timeline["cam_drop_ratio"] = timeline["cam_drop_ratio"].astype(float)
    else:
        timeline["cam_drop_ratio"] = np.nan
    if "min_gap_m" not in timeline:
        timeline["min_gap_m"] = np.nan
    if "min_ttc_s" not in timeline:
        timeline["min_ttc_s"] = np.nan
    if "collisions_per_s" not in timeline:
        timeline["collisions_per_s"] = 0.0

    timeline["collisions_cum"] = timeline["collisions_per_s"].cumsum()
    timeline["case"] = label

    summary = {"case": label, "run_dir": str(run_dir)}
    summary.update(msg_s)
    summary.update(ctrl_s)
    summary.update(risk_s)
    summary.update(coll_s)
    summary.update(log_s)
    return timeline, summary


def _plot(
    baseline_t: pd.DataFrame,
    lossy_t: pd.DataFrame,
    baseline_s: dict[str, float],
    lossy_s: dict[str, float],
    out_png: Path,
    gap_threshold: float,
    ttc_threshold: float,
) -> None:
    fig, ax = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

    ax[0].plot(baseline_t["time_s"], baseline_t["cam_drop_ratio"], label=f"{baseline_s['case']} drop ratio")
    ax[0].plot(lossy_t["time_s"], lossy_t["cam_drop_ratio"], label=f"{lossy_s['case']} drop ratio")
    ax[0].set_ylabel("CAM drop ratio [-]")
    ax[0].set_ylim(0, 1.05)
    ax[0].grid(alpha=0.3)
    ax[0].legend()

    ax[1].step(
        baseline_t["time_s"], baseline_t["control_actions_per_s"], where="post", label=f"{baseline_s['case']} control/s"
    )
    ax[1].step(lossy_t["time_s"], lossy_t["control_actions_per_s"], where="post", label=f"{lossy_s['case']} control/s")
    ax[1].set_ylabel("Control actions / 1s")
    ax[1].grid(alpha=0.3)
    ax[1].legend()

    ax[2].plot(baseline_t["time_s"], baseline_t["min_gap_m"], label=f"{baseline_s['case']} min gap")
    ax[2].plot(lossy_t["time_s"], lossy_t["min_gap_m"], label=f"{lossy_s['case']} min gap")
    ax[2].axhline(gap_threshold, linestyle="--", color="tab:red", linewidth=1, label=f"Gap threshold {gap_threshold} m")
    ax[2].set_ylabel("Min gap [m]")
    ax[2].grid(alpha=0.3)
    ax[2].legend()

    ax[3].plot(baseline_t["time_s"], baseline_t["min_ttc_s"], label=f"{baseline_s['case']} min TTC")
    ax[3].plot(lossy_t["time_s"], lossy_t["min_ttc_s"], label=f"{lossy_s['case']} min TTC")
    ax[3].axhline(ttc_threshold, linestyle="--", color="tab:red", linewidth=1, label=f"TTC threshold {ttc_threshold} s")
    ax[3].set_ylabel("Min TTC [s]")
    ax[3].set_xlabel("Time [s]")
    ax[3].grid(alpha=0.3)
    ax[3].legend()

    for stats, style in ((baseline_s, ":"), (lossy_s, "-.")):
        inc_t = stats.get("incident_time_s", math.nan)
        dur = stats.get("incident_duration_s", math.nan)
        if pd.notna(inc_t):
            for a in ax:
                a.axvline(float(inc_t), color="gray", linestyle=style, linewidth=1, alpha=0.7)
        if pd.notna(inc_t) and pd.notna(dur):
            for a in ax:
                a.axvline(float(inc_t + dur), color="gray", linestyle=style, linewidth=1, alpha=0.7)

    # Mark collision times (if present) on the gap plot.
    for tdf, color in ((baseline_t, "tab:blue"), (lossy_t, "tab:orange")):
        coll = tdf.loc[tdf["collisions_per_s"] > 0, "time_s"]
        if not coll.empty:
            y = np.full(len(coll), gap_threshold)
            ax[2].scatter(coll, y, marker="x", color=color, zorder=5)

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Compare baseline vs lossy emergency-incident runs.")
    p.add_argument("--baseline-dir", required=True, help="Path to baseline run directory")
    p.add_argument("--lossy-dir", required=True, help="Path to lossy run directory")
    p.add_argument("--out-dir", required=True, help="Output directory for comparison artifacts")
    p.add_argument("--baseline-label", default="baseline", help="Label for baseline case")
    p.add_argument("--lossy-label", default="lossy", help="Label for lossy case")
    p.add_argument("--gap-threshold-m", type=float, default=2.0, help="Gap threshold shown on plots")
    p.add_argument("--ttc-threshold-s", type=float, default=1.5, help="TTC threshold shown on plots")
    args = p.parse_args()

    baseline_dir = Path(args.baseline_dir).resolve()
    lossy_dir = Path(args.lossy_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_t, baseline_s = _build_case(baseline_dir, args.baseline_label)
    lossy_t, lossy_s = _build_case(lossy_dir, args.lossy_label)

    timeline_long = pd.concat([baseline_t, lossy_t], ignore_index=True)
    timeline_csv = out_dir / "comparison_timeline.csv"
    summary_csv = out_dir / "comparison_summary.csv"
    plot_png = out_dir / "comparison_timeline.png"
    timeline_long.to_csv(timeline_csv, index=False)
    pd.DataFrame([baseline_s, lossy_s]).to_csv(summary_csv, index=False)

    _plot(
        baseline_t,
        lossy_t,
        baseline_s,
        lossy_s,
        plot_png,
        gap_threshold=args.gap_threshold_m,
        ttc_threshold=args.ttc_threshold_s,
    )

    print(summary_csv)
    print(timeline_csv)
    print(plot_png)


if __name__ == "__main__":
    main()
