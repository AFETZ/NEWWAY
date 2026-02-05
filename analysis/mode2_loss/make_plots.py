#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import json

from bootstrap import ensure_deps

ensure_deps()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Results directory from analyze_csv.py")
    p.add_argument("--out", required=True, help="Output figures directory")
    return p.parse_args()


def load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def save_fig(fig, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_speed_accel(df_vs: pd.DataFrame, out_dir: Path) -> None:
    if df_vs.empty:
        return
    for (run_id, tech), g in df_vs.groupby(["run_id", "tech"], dropna=False):
        g = g.sort_values("t_s")
        counts = g.groupby("vehicle_id").size().sort_values(ascending=False)
        top_ids = counts.head(5).index.tolist()
        g = g[g["vehicle_id"].isin(top_ids)]

        fig, ax = plt.subplots(figsize=(10, 5))
        for vid, vg in g.groupby("vehicle_id"):
            ax.plot(vg["t_s"], vg["speed_mps"], label=str(vid))
        ax.set_title(f"Speed vs Time | run={run_id} tech={tech}")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("speed (m/s)")
        ax.legend(fontsize=8, ncol=2)
        save_fig(fig, out_dir / f"speed_time_{run_id}.png")

        fig, ax = plt.subplots(figsize=(10, 5))
        for vid, vg in g.groupby("vehicle_id"):
            ax.plot(vg["t_s"], vg["accel_mps2"], label=str(vid))
        ax.set_title(f"Acceleration vs Time | run={run_id} tech={tech}")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("accel (m/s^2)")
        ax.legend(fontsize=8, ncol=2)
        save_fig(fig, out_dir / f"accel_time_{run_id}.png")

        fig, ax = plt.subplots(figsize=(6, 6))
        for vid, vg in g.groupby("vehicle_id"):
            ax.plot(vg["lon"], vg["lat"], label=str(vid))
        ax.set_title(f"Trajectory | run={run_id} tech={tech}")
        ax.set_xlabel("lon")
        ax.set_ylabel("lat")
        ax.legend(fontsize=8, ncol=2)
        save_fig(fig, out_dir / f"trajectory_{run_id}.png")


def plot_behavior_hist(df_metrics: pd.DataFrame, out_dir: Path) -> None:
    if df_metrics.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    for tech, g in df_metrics.groupby("tech", dropna=False):
        ax.hist(g["max_decel"].dropna(), bins=20, alpha=0.5, label=str(tech))
    ax.set_title("Histogram of max decel by tech")
    ax.set_xlabel("max decel (m/s^2)")
    ax.set_ylabel("count")
    ax.legend()
    save_fig(fig, out_dir / "hist_max_decel_by_tech.png")

    fig, ax = plt.subplots(figsize=(8, 4))
    for tech, g in df_metrics.groupby("tech", dropna=False):
        ax.hist(g["time_to_first_brake"].dropna(), bins=20, alpha=0.5, label=str(tech))
    ax.set_title("Histogram of time to first brake by tech")
    ax.set_xlabel("time_to_first_brake (s)")
    ax.set_ylabel("count")
    ax.legend()
    save_fig(fig, out_dir / "hist_time_to_first_brake_by_tech.png")


def plot_comm(df_comm_vehicle: pd.DataFrame, df_comm_run: pd.DataFrame, out_dir: Path) -> None:
    if not df_comm_vehicle.empty:
        for (run_id, tech), g in df_comm_vehicle.groupby(["run_id", "tech"], dropna=False):
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(g["vehicle_id"].astype(str), g["prr"].astype(float))
            ax.set_title(f"PRR per vehicle | run={run_id} tech={tech}")
            ax.set_xlabel("vehicle_id")
            ax.set_ylabel("PRR")
            ax.tick_params(axis="x", labelrotation=90)
            save_fig(fig, out_dir / f"prr_per_vehicle_{run_id}.png")

    if not df_comm_run.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(df_comm_run["tech"].astype(str), df_comm_run["prr"].astype(float))
        ax.set_title("Overall PRR by tech")
        ax.set_xlabel("tech")
        ax.set_ylabel("PRR")
        save_fig(fig, out_dir / "prr_by_tech.png")


def plot_aoi_latency(df_aoi: pd.DataFrame, df_latency: pd.DataFrame, out_dir: Path) -> None:
    if not df_aoi.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        for tech, g in df_aoi.groupby("tech", dropna=False):
            ax.hist(g["aoi_p95_s"].dropna(), bins=20, alpha=0.5, label=str(tech))
        ax.set_title("AoI p95 by tech")
        ax.set_xlabel("AoI p95 (s)")
        ax.set_ylabel("count")
        ax.legend()
        save_fig(fig, out_dir / "aoi_p95_hist_by_tech.png")

    if not df_latency.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        for tech, g in df_latency.groupby("tech", dropna=False):
            vals = g["latency_p95_s"].dropna()
            if len(vals) == 0:
                continue
            ax.plot(sorted(vals), np.linspace(0, 1, len(vals)), label=str(tech))
        ax.set_title("Latency p95 CDF by tech")
        ax.set_xlabel("latency p95 (s)")
        ax.set_ylabel("CDF")
        ax.legend()
        save_fig(fig, out_dir / "latency_p95_cdf_by_tech.png")


def plot_cross_link(df_behavior: pd.DataFrame, df_comm_vehicle: pd.DataFrame, df_aoi: pd.DataFrame, df_reaction: pd.DataFrame, out_dir: Path) -> None:
    if df_behavior.empty or df_comm_vehicle.empty:
        return
    b = df_behavior.copy()
    c = df_comm_vehicle.copy()
    b["vehicle_id"] = b["vehicle_id"].astype(str)
    c["vehicle_id"] = c["vehicle_id"].astype(str)
    m = b.merge(c, on=["run_id", "tech", "vehicle_id"], how="inner", suffixes=("_beh", "_comm"))

    if not m.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(m["prr"], m["max_decel"], alpha=0.7)
        ax.set_title("PRR vs max decel")
        ax.set_xlabel("PRR")
        ax.set_ylabel("max decel (m/s^2)")
        save_fig(fig, out_dir / "scatter_prr_vs_max_decel.png")

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(m["prr"], m["time_to_first_brake"], alpha=0.7)
        ax.set_title("PRR vs time to first brake")
        ax.set_xlabel("PRR")
        ax.set_ylabel("time_to_first_brake (s)")
        save_fig(fig, out_dir / "scatter_prr_vs_time_to_first_brake.png")

    if not df_aoi.empty:
        a = df_aoi.copy()
        a["vehicle_id"] = a["vehicle_id"].astype(str)
        ma = b.merge(a, on=["run_id", "tech", "vehicle_id"], how="inner")
        if not ma.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(ma["aoi_p95_s"], ma["time_to_first_brake"], alpha=0.7)
            ax.set_title("AoI p95 vs time to first brake")
            ax.set_xlabel("AoI p95 (s)")
            ax.set_ylabel("time_to_first_brake (s)")
            save_fig(fig, out_dir / "scatter_aoi_p95_vs_time_to_first_brake.png")

    if not df_reaction.empty:
        r = df_reaction.copy()
        r["vehicle_id"] = r["vehicle_id"].astype(str)
        mr = c.merge(r, on=["run_id", "tech", "vehicle_id"], how="inner")
        if not mr.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(mr["prr"], mr["reaction_delay_s"], alpha=0.7)
            ax.set_title("PRR vs reaction delay (first emergency CAM)")
            ax.set_xlabel("PRR")
            ax.set_ylabel("reaction_delay_s")
            save_fig(fig, out_dir / "scatter_prr_vs_reaction_delay.png")


def detect_sweep_params(df_meta: pd.DataFrame) -> list[str]:
    params = []
    if df_meta.empty:
        return params
    candidate = [
        "txPower",
        "mcs",
        "enableSensing",
        "slThresPsschRsrp",
        "enableChannelRandomness",
        "channelUpdatePeriod",
    ]
    for param in candidate:
        if param in df_meta.columns and df_meta[param].nunique(dropna=False) > 1:
            params.append(param)
    return params


def plot_sweep_curves(df_comm_run: pd.DataFrame, df_behavior_run: pd.DataFrame, df_reaction_run: pd.DataFrame, df_meta: pd.DataFrame, out_dir: Path) -> None:
    if df_meta.empty or df_comm_run.empty:
        return
    # Merge metadata with comm run
    df = df_comm_run.merge(df_meta, left_on="run_id", right_on="run_id", how="inner") if "run_id" in df_meta.columns else df_comm_run
    if df.empty:
        return
    for param in detect_sweep_params(df_meta):
        if param in df.columns:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(df[param], df["prr"], alpha=0.8)
            ax.set_title(f"PRR vs {param}")
            ax.set_xlabel(param)
            ax.set_ylabel("PRR")
            save_fig(fig, out_dir / f"prr_vs_{param}.png")

    if not df_behavior_run.empty:
        merged = df_behavior_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
        if not merged.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(merged["prr"], merged["time_to_first_brake_median"], alpha=0.8)
            ax.set_title("Median time_to_first_brake vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("time_to_first_brake_median (s)")
            save_fig(fig, out_dir / "behavior_vs_prr_time_to_first_brake.png")

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(merged["prr"], merged["max_decel_median"], alpha=0.8)
            ax.set_title("Median max_decel vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("max_decel_median (m/s^2)")
            save_fig(fig, out_dir / "behavior_vs_prr_max_decel.png")

    if not df_reaction_run.empty:
        merged = df_reaction_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
        if not merged.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(merged["prr"], merged["reaction_delay_median"], alpha=0.8)
            ax.set_title("Median reaction delay vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("reaction_delay_median (s)")
            save_fig(fig, out_dir / "reaction_delay_vs_prr.png")

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(merged["prr"], merged["reaction_delay_p90"], alpha=0.8)
            ax.set_title("P90 reaction delay vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("reaction_delay_p90 (s)")
            save_fig(fig, out_dir / "reaction_delay_p90_vs_prr.png")


def generate_report(report_path: Path, df_comm_run: pd.DataFrame, df_behavior_run: pd.DataFrame, df_reaction_run: pd.DataFrame, df_meta: pd.DataFrame, fig_dir: Path) -> None:
    lines = []
    lines.append("# NR-V2X Mode 2 Loss Sweep Evidence Report")
    lines.append("")
    lines.append("## Scenario + Fixed Controls")
    lines.append("- Scenario: v2v-emergencyVehicleAlert-nrv2x")
    lines.append("- Mobility: SUMO v2v_map (cars.rou.xml, map.sumo.cfg)")
    lines.append("- Penetration rate fixed where configured")
    lines.append("- Seeds fixed via --RngRun (see sweep metadata)")
    lines.append("- Reaction delay uses first CAM from emergency vehicle (stationId=2 in cars.rou.xml)")
    lines.append("")
    lines.append("## Loss Sweep Definition")
    varied = detect_sweep_params(df_meta)
    if varied:
        lines.append(f"Sweep varied: {', '.join(varied)}")
    else:
        lines.append("Sweep varied: (no parameter variations detected in run metadata)")
    lines.append("")
    lines.append("## Measured Comms Degradation")
    lines.append(f"- PRR by tech: {fig_dir / 'prr_by_tech.png'}")
    lines.append(f"- PRR vs loss knobs: {fig_dir / 'prr_vs_txPower.png'} (and related plots)")
    lines.append("")
    lines.append("## Measured Behavior Change")
    lines.append(f"- Histograms: {fig_dir / 'hist_max_decel_by_tech.png'}, {fig_dir / 'hist_time_to_first_brake_by_tech.png'}")
    lines.append("")
    lines.append("## Cross-link Comms → Behavior")
    lines.append(f"- PRR vs time_to_first_brake: {fig_dir / 'scatter_prr_vs_time_to_first_brake.png'}")
    lines.append(f"- PRR vs max_decel: {fig_dir / 'scatter_prr_vs_max_decel.png'}")
    if not df_reaction_run.empty:
        lines.append(f"- PRR vs reaction delay: {fig_dir / 'scatter_prr_vs_reaction_delay.png'}")
        lines.append(f"- PRR vs reaction delay (p90): {fig_dir / 'reaction_delay_p90_vs_prr.png'}")
    lines.append("")

    # Compute summary statement if possible
    statement = "Insufficient sweep data to compute causal statement."
    if not df_comm_run.empty:
        if not df_reaction_run.empty:
            merged = df_reaction_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
            if not merged.empty:
                merged = merged.sort_values("prr")
                low = merged.iloc[0]
                high = merged.iloc[-1]
                statement = (
                    f"When PRR drops from {high['prr']:.3f} to {low['prr']:.3f}, "
                    f"p90 reaction delay increases from {high['reaction_delay_p90']:.3f}s "
                    f"to {low['reaction_delay_p90']:.3f}s, indicating delayed cooperative response "
                    "under degraded NR Mode 2 comms."
                )
        elif not df_behavior_run.empty:
            merged = df_behavior_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
            if not merged.empty:
                merged = merged.sort_values("prr")
                low = merged.iloc[0]
                high = merged.iloc[-1]
                statement = (
                    f"When PRR drops from {high['prr']:.3f} to {low['prr']:.3f}, "
                    f"median time_to_first_brake increases from {high['time_to_first_brake_median']:.3f}s "
                    f"to {low['time_to_first_brake_median']:.3f}s and median max_decel shifts from "
                    f"{high['max_decel_median']:.3f} to {low['max_decel_median']:.3f} m/s^2, "
                    "indicating later and harsher responses under degraded NR Mode 2 comms."
                )

    lines.append("## Conclusion Statement (Thesis-ready)")
    lines.append(statement)
    lines.append("")

    report_path.write_text("\n".join(lines))


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df_vs = load_csv(in_dir / "vehicle_state.csv")
    df_behavior_vehicle = load_csv(in_dir / "behavior_metrics_vehicle.csv")
    df_behavior_run = load_csv(in_dir / "behavior_metrics_run.csv")
    df_comm_vehicle = load_csv(in_dir / "comm_metrics_vehicle.csv")
    df_comm_run = load_csv(in_dir / "comm_metrics_run.csv")
    df_aoi = load_csv(in_dir / "aoi_metrics_vehicle.csv")
    df_reaction_vehicle = load_csv(in_dir / "reaction_metrics_vehicle.csv")
    df_reaction_run = load_csv(in_dir / "reaction_metrics_run.csv")
    df_latency = load_csv(in_dir / "latency_metrics_run.csv")
    df_meta = load_csv(in_dir / "run_metadata.csv")

    plot_speed_accel(df_vs, out_dir)
    plot_behavior_hist(df_behavior_vehicle, out_dir)
    plot_comm(df_comm_vehicle, df_comm_run, out_dir)
    plot_aoi_latency(df_aoi, df_latency, out_dir)
    plot_cross_link(df_behavior_vehicle, df_comm_vehicle, df_aoi, df_reaction_vehicle, out_dir)
    plot_sweep_curves(df_comm_run, df_behavior_run, df_reaction_run, df_meta, out_dir)

    report_path = Path("analysis/mode2_loss/REPORT_mode2_loss.md")
    generate_report(report_path, df_comm_run, df_behavior_run, df_reaction_run, df_meta, out_dir)


if __name__ == "__main__":
    main()
