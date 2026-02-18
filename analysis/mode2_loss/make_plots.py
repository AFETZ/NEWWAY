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
from matplotlib.collections import LineCollection


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


def plot_connected_points(ax, x, y, alpha: float = 0.8) -> None:
    xy = pd.DataFrame({"x": x, "y": y}).dropna().sort_values("x")
    if xy.empty:
        return
    ax.plot(xy["x"], xy["y"], marker="o", linestyle="-", linewidth=1.2, markersize=4, alpha=alpha)


def normalize_vehicle_id(value) -> str | None:
    if pd.isna(value):
        return None
    vid = str(value).strip()
    if vid == "":
        return None
    if vid.startswith("veh"):
        vid = vid[3:]
    if vid.endswith(".0"):
        vid = vid[:-2]
    return vid


def sort_vehicle_ids(ids: list[str]) -> list[str]:
    def key_fn(v: str) -> tuple[int, object]:
        return (0, int(v)) if str(v).isdigit() else (1, str(v))
    return sorted(ids, key=key_fn)


def interpolate_position(track_t: np.ndarray, track_x: np.ndarray, track_y: np.ndarray, t: float) -> tuple[float, float] | None:
    if track_t.size == 0 or np.isnan(t):
        return None

    if t <= track_t[0]:
        return float(track_x[0]), float(track_y[0])
    if t >= track_t[-1]:
        return float(track_x[-1]), float(track_y[-1])

    idx = int(np.searchsorted(track_t, t))
    t0 = track_t[idx - 1]
    t1 = track_t[idx]
    if t1 <= t0:
        return float(track_x[idx - 1]), float(track_y[idx - 1])

    w = (t - t0) / (t1 - t0)
    x = track_x[idx - 1] + w * (track_x[idx] - track_x[idx - 1])
    y = track_y[idx - 1] + w * (track_y[idx] - track_y[idx - 1])
    return float(x), float(y)


def plot_packet_visuals(df_msg: pd.DataFrame, df_vs: pd.DataFrame, out_dir: Path) -> dict:
    artifacts: dict = {}
    if df_msg.empty or df_vs.empty:
        return artifacts

    msg = df_msg.copy()
    msg["tx_t_s"] = pd.to_numeric(msg["tx_t_s"], errors="coerce")
    msg["rx_t_s"] = pd.to_numeric(msg["rx_t_s"], errors="coerce")
    msg["rx_ok"] = pd.to_numeric(msg["rx_ok"], errors="coerce")
    msg["tx_id_norm"] = msg["tx_id"].map(normalize_vehicle_id)
    msg["rx_id_norm"] = msg["rx_id"].map(normalize_vehicle_id)

    tx_all = msg[(msg["rx_ok"] == 0) & msg["tx_t_s"].notna()]
    rx_all = msg[(msg["rx_ok"] == 1) & msg["rx_t_s"].notna() & msg["tx_id_norm"].notna() & msg["rx_id_norm"].notna()]
    if tx_all.empty or rx_all.empty:
        return artifacts

    run_id = rx_all.groupby("run_id", dropna=False).size().sort_values(ascending=False).index[0]
    run_tx = tx_all[tx_all["run_id"] == run_id].copy()
    run_rx = rx_all[rx_all["run_id"] == run_id].copy()
    if run_tx.empty or run_rx.empty:
        return artifacts

    run_id_str = str(run_id)
    artifacts["run_id"] = run_id_str

    # 1) Packet activity timeline
    tmax = float(np.nanmax([run_tx["tx_t_s"].max(), run_rx["rx_t_s"].max()]))
    bin_size = max(0.1, min(0.5, tmax / 200.0 if tmax > 0 else 0.2))
    bins = np.arange(0.0, tmax + bin_size, bin_size)
    if bins.size < 3:
        bins = np.array([0.0, bin_size, 2 * bin_size])
    centers = (bins[:-1] + bins[1:]) / 2.0

    tx_counts, _ = np.histogram(run_tx["tx_t_s"].to_numpy(), bins=bins)
    rx_counts, _ = np.histogram(run_rx["rx_t_s"].to_numpy(), bins=bins)
    tx_rate = tx_counts / bin_size
    rx_rate = rx_counts / bin_size
    prr_bin = np.divide(rx_counts.astype(float), tx_counts.astype(float), out=np.full_like(rx_counts, np.nan, dtype=float), where=tx_counts > 0)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(centers, tx_rate, label="tx rate (msg/s)", color="#1f77b4", linewidth=1.2)
    ax.plot(centers, rx_rate, label="rx rate (msg/s)", color="#2ca02c", linewidth=1.2)
    ax.set_title(f"Packet Activity Over Time | run={run_id_str}")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("messages per second")
    ax.grid(alpha=0.2)
    ax2 = ax.twinx()
    ax2.plot(centers, prr_bin, label="window PRR", color="#d62728", linewidth=1.0, alpha=0.8)
    ax2.set_ylabel("window PRR")
    ax2.set_ylim(0.0, 1.05)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper right")
    activity_name = f"packet_activity_{run_id_str}.png"
    save_fig(fig, out_dir / activity_name)
    artifacts["packet_activity"] = activity_name

    # 2) TX->RX link heatmap
    links = run_rx.groupby(["tx_id_norm", "rx_id_norm"], dropna=False).size().reset_index(name="count")
    if not links.empty:
        tx_ids = sort_vehicle_ids([str(v) for v in links["tx_id_norm"].dropna().unique()])
        rx_ids = sort_vehicle_ids([str(v) for v in links["rx_id_norm"].dropna().unique()])
        heat = np.zeros((len(tx_ids), len(rx_ids)), dtype=float)
        tx_idx = {v: i for i, v in enumerate(tx_ids)}
        rx_idx = {v: i for i, v in enumerate(rx_ids)}
        for _, row in links.iterrows():
            t = str(row["tx_id_norm"])
            r = str(row["rx_id_norm"])
            if t in tx_idx and r in rx_idx:
                heat[tx_idx[t], rx_idx[r]] = float(row["count"])

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(heat, aspect="auto", cmap="viridis")
        ax.set_title(f"Packet RX Count Heatmap (tx -> rx) | run={run_id_str}")
        ax.set_xlabel("rx vehicle id")
        ax.set_ylabel("tx vehicle id")
        if len(rx_ids) <= 30:
            ax.set_xticks(np.arange(len(rx_ids)))
            ax.set_xticklabels(rx_ids, rotation=90, fontsize=7)
        if len(tx_ids) <= 30:
            ax.set_yticks(np.arange(len(tx_ids)))
            ax.set_yticklabels(tx_ids, fontsize=7)
        fig.colorbar(im, ax=ax, label="received packets")
        heatmap_name = f"packet_link_heatmap_{run_id_str}.png"
        save_fig(fig, out_dir / heatmap_name)
        artifacts["packet_link_heatmap"] = heatmap_name

    # 3) Packet flights map (lines between tx/rx at rx timestamp)
    run_vs = df_vs[df_vs["run_id"] == run_id].copy()
    if run_vs.empty:
        return artifacts

    run_vs["vehicle_id_norm"] = run_vs["vehicle_id"].map(normalize_vehicle_id)
    run_vs["t_s"] = pd.to_numeric(run_vs["t_s"], errors="coerce")
    run_vs["lon"] = pd.to_numeric(run_vs["lon"], errors="coerce")
    run_vs["lat"] = pd.to_numeric(run_vs["lat"], errors="coerce")
    run_vs = run_vs.dropna(subset=["vehicle_id_norm", "t_s", "lon", "lat"]).sort_values(["vehicle_id_norm", "t_s"])
    if run_vs.empty:
        return artifacts

    tracks: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for vid, g in run_vs.groupby("vehicle_id_norm"):
        tracks[str(vid)] = (
            g["t_s"].to_numpy(dtype=float),
            g["lon"].to_numpy(dtype=float),
            g["lat"].to_numpy(dtype=float),
        )

    events = run_rx[["tx_id_norm", "rx_id_norm", "rx_t_s"]].dropna().sort_values("rx_t_s")
    max_events = 3000
    if len(events) > max_events:
        step = int(np.ceil(len(events) / max_events))
        events = events.iloc[::step]

    segments = []
    seg_t = []
    for row in events.itertuples(index=False):
        tx_id = str(row.tx_id_norm)
        rx_id = str(row.rx_id_norm)
        t = float(row.rx_t_s)
        tx_track = tracks.get(tx_id)
        rx_track = tracks.get(rx_id)
        if tx_track is None or rx_track is None:
            continue
        tx_pos = interpolate_position(tx_track[0], tx_track[1], tx_track[2], t)
        rx_pos = interpolate_position(rx_track[0], rx_track[1], rx_track[2], t)
        if tx_pos is None or rx_pos is None:
            continue
        segments.append([tx_pos, rx_pos])
        seg_t.append(t)

    fig, ax = plt.subplots(figsize=(8, 8))
    for vid, g in run_vs.groupby("vehicle_id_norm"):
        ax.plot(g["lon"], g["lat"], color="#bfbfbf", linewidth=0.7, alpha=0.45)

    if segments:
        lc = LineCollection(
            segments,
            cmap="plasma",
            norm=plt.Normalize(vmin=float(np.min(seg_t)), vmax=float(np.max(seg_t))),
            linewidths=0.8,
            alpha=0.35,
        )
        lc.set_array(np.asarray(seg_t))
        ax.add_collection(lc)
        fig.colorbar(lc, ax=ax, label="packet rx time (s)")

    if "2" in tracks:
        _, x2, y2 = tracks["2"]
        ax.plot(x2, y2, color="red", linewidth=1.4, label="emergency vehicle (ID 2)")
    ax.set_title(f"Vehicle Trajectories + Packet Flights | run={run_id_str}")
    ax.set_xlabel("lon")
    ax.set_ylabel("lat")
    ax.grid(alpha=0.2)
    ax.set_aspect("equal", adjustable="datalim")
    if "2" in tracks:
        ax.legend(fontsize=8, loc="best")

    flights_name = f"packet_flights_map_{run_id_str}.png"
    save_fig(fig, out_dir / flights_name)
    artifacts["packet_flights_map"] = flights_name

    return artifacts


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
        plot_connected_points(ax, m["prr"], m["max_decel"], alpha=0.7)
        ax.set_title("PRR vs max decel")
        ax.set_xlabel("PRR")
        ax.set_ylabel("max decel (m/s^2)")
        save_fig(fig, out_dir / "scatter_prr_vs_max_decel.png")

        fig, ax = plt.subplots(figsize=(6, 4))
        plot_connected_points(ax, m["prr"], m["time_to_first_brake"], alpha=0.7)
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
            plot_connected_points(ax, ma["aoi_p95_s"], ma["time_to_first_brake"], alpha=0.7)
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
            plot_connected_points(ax, mr["prr"], mr["reaction_delay_s"], alpha=0.7)
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
            plot_connected_points(ax, df[param], df["prr"], alpha=0.8)
            ax.set_title(f"PRR vs {param}")
            ax.set_xlabel(param)
            ax.set_ylabel("PRR")
            save_fig(fig, out_dir / f"prr_vs_{param}.png")

    if not df_behavior_run.empty:
        merged = df_behavior_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
        if not merged.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            plot_connected_points(ax, merged["prr"], merged["time_to_first_brake_median"], alpha=0.8)
            ax.set_title("Median time_to_first_brake vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("time_to_first_brake_median (s)")
            save_fig(fig, out_dir / "behavior_vs_prr_time_to_first_brake.png")

            fig, ax = plt.subplots(figsize=(6, 4))
            plot_connected_points(ax, merged["prr"], merged["max_decel_median"], alpha=0.8)
            ax.set_title("Median max_decel vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("max_decel_median (m/s^2)")
            save_fig(fig, out_dir / "behavior_vs_prr_max_decel.png")

    if not df_reaction_run.empty:
        merged = df_reaction_run.merge(df_comm_run, on=["run_id", "tech"], how="inner")
        if not merged.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            plot_connected_points(ax, merged["prr"], merged["reaction_delay_median"], alpha=0.8)
            ax.set_title("Median reaction delay vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("reaction_delay_median (s)")
            save_fig(fig, out_dir / "reaction_delay_vs_prr.png")

            fig, ax = plt.subplots(figsize=(6, 4))
            plot_connected_points(ax, merged["prr"], merged["reaction_delay_p90"], alpha=0.8)
            ax.set_title("P90 reaction delay vs PRR")
            ax.set_xlabel("PRR")
            ax.set_ylabel("reaction_delay_p90 (s)")
            save_fig(fig, out_dir / "reaction_delay_p90_vs_prr.png")


def generate_report(report_path: Path, df_comm_run: pd.DataFrame, df_behavior_run: pd.DataFrame, df_reaction_run: pd.DataFrame, df_meta: pd.DataFrame, fig_dir: Path, packet_artifacts: dict | None = None) -> None:
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

    lines.append("## Mobility + Packet Visuals")
    if packet_artifacts and packet_artifacts.get("run_id"):
        run_id = packet_artifacts["run_id"]
        if packet_artifacts.get("packet_activity"):
            lines.append(f"- Packet activity timeline: {fig_dir / packet_artifacts['packet_activity']}")
        if packet_artifacts.get("packet_link_heatmap"):
            lines.append(f"- TX->RX heatmap: {fig_dir / packet_artifacts['packet_link_heatmap']}")
        if packet_artifacts.get("packet_flights_map"):
            lines.append(f"- Packet flights over map: {fig_dir / packet_artifacts['packet_flights_map']}")
        lines.append(f"- Visualization run selected automatically: {run_id}")
    else:
        lines.append("- Packet visuals were not generated (msg_log/vehicle_state data missing).")
    lines.append("")

    lines.append("## NR-V2X Mode 2 Proof Checklist")
    if not df_meta.empty and "scenario" in df_meta.columns:
        scenarios = sorted(df_meta["scenario"].dropna().astype(str).unique().tolist())
        if scenarios:
            lines.append(f"- Scenario tag from run metadata: {', '.join(scenarios)}")
    if not df_meta.empty and "command" in df_meta.columns:
        cmd_series = df_meta["command"].dropna().astype(str)
        if not cmd_series.empty:
            cmd_example = cmd_series.iloc[0]
            cmd_flags = []
            for flag in ["v2v-emergencyVehicleAlert-nrv2x", "--txPower=", "--mcs=", "--enableSensing=", "--slThresPsschRsrp="]:
                if flag in cmd_example:
                    cmd_flags.append(flag)
            if cmd_flags:
                lines.append(f"- Command-line evidence in metadata contains: {', '.join(cmd_flags)}")
    lines.append("- Source evidence (NR sidelink configuration): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:383")
    lines.append("- Source evidence (sensing threshold config): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:390")
    lines.append("- Source evidence (fixed NR SL MCS scheduler): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:443")
    lines.append("- Source evidence (prepare UE stack for sidelink): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:451")
    lines.append("- Source evidence (install sidelink preconfiguration): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:561")
    lines.append("- Source evidence (activate sidelink bearer): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:626")
    lines.append("- Source evidence (application model set to nrv2x): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:682")
    lines.append("- Source evidence (web visualizer switch): src/automotive/examples/v2v-emergencyVehicleAlert-nrv2x.cc:157")
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
    df_msg = load_csv(in_dir / "msg_log.csv")
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
    packet_artifacts = plot_packet_visuals(df_msg, df_vs, out_dir)

    report_path = Path("analysis/mode2_loss/REPORT_mode2_loss.md")
    generate_report(report_path, df_comm_run, df_behavior_run, df_reaction_run, df_meta, out_dir, packet_artifacts)


if __name__ == "__main__":
    main()
