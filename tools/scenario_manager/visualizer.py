"""
Post-run visualization module.

Generates rich, multi-level diagrams covering:
  - Network layer: PRR, latency, SINR, packet drops
  - Transport layer: Speed, lane, gap, TTC time-series
  - Behavioral layer: Control actions, decision timeline
  - Cross-layer: Causal chain from PHY loss -> decision -> collision
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _collect_msg_csvs(artifacts_dir: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(artifacts_dir.glob("*-MSG.csv")):
        df = _safe_read_csv(f)
        if df is not None and not df.empty:
            df["_source_file"] = f.stem
            # Extract vehicle id from filename like "eva-veh3-MSG"
            parts = f.stem.split("-")
            veh_id = parts[1] if len(parts) >= 2 else "unknown"
            df["vehicle_id"] = veh_id
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _collect_ctrl_csvs(artifacts_dir: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(artifacts_dir.glob("*-CTRL.csv")):
        df = _safe_read_csv(f)
        if df is not None and not df.empty:
            parts = f.stem.split("-")
            veh_id = parts[1] if len(parts) >= 2 else "unknown"
            df["vehicle_id"] = veh_id
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _collect_profile_csvs(artifacts_dir: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(artifacts_dir.glob("*-PROFILE.csv")):
        df = _safe_read_csv(f)
        if df is not None and not df.empty:
            parts = f.stem.split("-")
            veh_id = parts[1] if len(parts) >= 2 else "unknown"
            df["vehicle_id"] = veh_id
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── Matplotlib-based plots (static, for PDF / thesis) ───────────────────────

def plot_network_kpi_dashboard(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """Network-layer KPI dashboard: PRR, latency, drops by vehicle."""
    out_dir.mkdir(parents=True, exist_ok=True)
    msg = _collect_msg_csvs(artifacts_dir)
    if msg.empty:
        return []

    paths = []
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Network Layer KPI Dashboard", fontsize=14, fontweight="bold")

    # 1) Message type distribution
    if "msg_type" in msg.columns:
        counts = msg["msg_type"].value_counts()
        colors_map = {
            "CAM": "#2ca02c", "CAM_DROP_APP": "#ff7f0e",
            "CAM_DROP_PHY": "#d62728", "DENM": "#1f77b4",
            "CPM": "#9467bd",
        }
        bar_colors = [colors_map.get(t, "#7f7f7f") for t in counts.index]
        axes[0, 0].barh(counts.index, counts.values, color=bar_colors)
        axes[0, 0].set_xlabel("Count")
        axes[0, 0].set_title("Message Type Distribution")

    # 2) Per-vehicle PRR
    if "msg_type" in msg.columns and "vehicle_id" in msg.columns:
        prr_data = []
        for vid, grp in msg.groupby("vehicle_id"):
            total = len(grp)
            drops = grp["msg_type"].astype(str).str.contains("DROP").sum()
            prr_data.append({"vehicle": vid, "PRR": 1 - drops / total if total > 0 else 0})
        prr_df = pd.DataFrame(prr_data).sort_values("vehicle")
        colors_prr = ["#2ca02c" if p > 0.9 else "#ff7f0e" if p > 0.5 else "#d62728"
                       for p in prr_df["PRR"]]
        axes[0, 1].bar(prr_df["vehicle"], prr_df["PRR"], color=colors_prr)
        axes[0, 1].set_ylabel("PRR [-]")
        axes[0, 1].set_ylim(0, 1.05)
        axes[0, 1].axhline(0.9, color="black", linestyle="--", alpha=0.4, label="0.9 threshold")
        axes[0, 1].legend()
        axes[0, 1].set_title("Per-Vehicle PRR")

    # 3) Latency distribution
    if "latency_ms" in msg.columns:
        lat = pd.to_numeric(msg["latency_ms"], errors="coerce").dropna()
        if not lat.empty:
            axes[1, 0].hist(lat, bins=40, color="#1f77b4", alpha=0.8, edgecolor="white")
            axes[1, 0].axvline(lat.median(), color="#d62728", linestyle="--",
                               label=f"Median: {lat.median():.1f} ms")
            axes[1, 0].set_xlabel("Latency [ms]")
            axes[1, 0].set_ylabel("Count")
            axes[1, 0].set_title("Latency Distribution")
            axes[1, 0].legend()

    # 4) Drops over time
    if "msg_type" in msg.columns and "time_s" in msg.columns:
        drops = msg[msg["msg_type"].astype(str).str.contains("DROP")].copy()
        if not drops.empty:
            drops["time_s"] = pd.to_numeric(drops["time_s"], errors="coerce")
            drops = drops.dropna(subset=["time_s"])
            if not drops.empty:
                axes[1, 1].hist(drops["time_s"], bins=30, color="#d62728", alpha=0.8,
                                edgecolor="white")
                axes[1, 1].set_xlabel("Time [s]")
                axes[1, 1].set_ylabel("Drop count")
                axes[1, 1].set_title("Packet Drops Over Time")

    for ax in axes.flat:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    p = out_dir / "network_kpi_dashboard.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)
    return paths


def plot_transport_safety_dashboard(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """Transport-layer: speed, lane, gap, TTC from collision risk data."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    risk_dir = artifacts_dir / "collision_risk"
    timeseries_csv = risk_dir / "collision_risk_timeseries.csv"
    summary_csv = risk_dir / "collision_risk_summary.csv"

    ts_df = _safe_read_csv(timeseries_csv)
    summary_df = _safe_read_csv(summary_csv)

    if ts_df is not None and not ts_df.empty:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Transport Layer Safety Dashboard", fontsize=14, fontweight="bold")

        # Speed per vehicle over time
        if "time_s" in ts_df.columns and "speed_mps" in ts_df.columns:
            for vid, grp in ts_df.groupby("vehicle_id") if "vehicle_id" in ts_df.columns else []:
                axes[0, 0].plot(grp["time_s"], grp["speed_mps"], label=vid, alpha=0.8)
            axes[0, 0].set_xlabel("Time [s]")
            axes[0, 0].set_ylabel("Speed [m/s]")
            axes[0, 0].set_title("Vehicle Speed Over Time")
            axes[0, 0].legend(fontsize=7)

        # Gap over time
        if "gap_m" in ts_df.columns and "time_s" in ts_df.columns:
            for vid, grp in ts_df.groupby("vehicle_id") if "vehicle_id" in ts_df.columns else []:
                axes[0, 1].plot(grp["time_s"], grp["gap_m"], label=vid, alpha=0.8)
            axes[0, 1].set_xlabel("Time [s]")
            axes[0, 1].set_ylabel("Gap [m]")
            axes[0, 1].set_title("Inter-Vehicle Gap")
            axes[0, 1].legend(fontsize=7)

        # TTC over time
        if "ttc_s" in ts_df.columns and "time_s" in ts_df.columns:
            for vid, grp in ts_df.groupby("vehicle_id") if "vehicle_id" in ts_df.columns else []:
                ttc = pd.to_numeric(grp["ttc_s"], errors="coerce")
                axes[1, 0].plot(grp["time_s"], ttc, label=vid, alpha=0.8)
            axes[1, 0].axhline(3.0, color="red", linestyle="--", alpha=0.6, label="TTC=3s")
            axes[1, 0].set_xlabel("Time [s]")
            axes[1, 0].set_ylabel("TTC [s]")
            axes[1, 0].set_title("Time-to-Collision")
            axes[1, 0].set_ylim(0, 20)
            axes[1, 0].legend(fontsize=7)

        # Summary bar chart
        if summary_df is not None and not summary_df.empty:
            metrics = ["min_gap_m", "min_ttc_s", "risky_gap_events", "risky_ttc_events"]
            available = [m for m in metrics if m in summary_df.columns]
            if available:
                vals = [float(pd.to_numeric(summary_df[m].iloc[0], errors="coerce"))
                        for m in available]
                colors = ["#1f77b4", "#d62728", "#ff7f0e", "#9467bd"][:len(available)]
                axes[1, 1].bar(available, vals, color=colors)
                axes[1, 1].set_title("Safety Summary Metrics")
                for i, v in enumerate(vals):
                    axes[1, 1].text(i, v + 0.05 * max(vals) if max(vals) > 0 else 0.1,
                                     f"{v:.2f}", ha="center", fontsize=9)

        for ax in axes.flat:
            ax.grid(alpha=0.3)
        fig.tight_layout()
        p = out_dir / "transport_safety_dashboard.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        paths.append(p)

    return paths


def plot_behavioral_dashboard(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """Behavioral layer: control actions, decision timeline, maneuver types."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    ctrl = _collect_ctrl_csvs(artifacts_dir)
    if ctrl.empty:
        return paths

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Behavioral Layer Dashboard", fontsize=14, fontweight="bold")

    # 1) Control actions per vehicle
    if "vehicle_id" in ctrl.columns:
        counts = ctrl["vehicle_id"].value_counts().sort_index()
        axes[0, 0].bar(counts.index, counts.values, color="#2ca02c")
        axes[0, 0].set_ylabel("Control actions [count]")
        axes[0, 0].set_title("Control Actions per Vehicle")

    # 2) Control action timeline (scatter)
    if "time_s" in ctrl.columns and "vehicle_id" in ctrl.columns:
        for vid, grp in ctrl.groupby("vehicle_id"):
            t = pd.to_numeric(grp["time_s"], errors="coerce").dropna()
            axes[0, 1].scatter(t, [vid] * len(t), alpha=0.6, s=20, label=vid)
        axes[0, 1].set_xlabel("Time [s]")
        axes[0, 1].set_title("Control Action Timeline")
        axes[0, 1].legend(fontsize=7)

    # 3) Action type distribution (if available)
    action_col = None
    for col in ["action", "action_type", "decision", "maneuver"]:
        if col in ctrl.columns:
            action_col = col
            break
    if action_col:
        action_counts = ctrl[action_col].value_counts()
        axes[1, 0].pie(action_counts.values, labels=action_counts.index,
                        autopct="%1.1f%%", startangle=90)
        axes[1, 0].set_title("Action Type Distribution")
    else:
        axes[1, 0].text(0.5, 0.5, "No action type data", ha="center", va="center",
                         transform=axes[1, 0].transAxes, fontsize=12, color="gray")
        axes[1, 0].set_title("Action Type Distribution")

    # 4) Control actions density (events per second)
    if "time_s" in ctrl.columns:
        t = pd.to_numeric(ctrl["time_s"], errors="coerce").dropna()
        if not t.empty:
            bins = np.arange(t.min(), t.max() + 1, 1.0)
            axes[1, 1].hist(t, bins=bins, color="#ff7f0e", alpha=0.8, edgecolor="white")
            axes[1, 1].set_xlabel("Time [s]")
            axes[1, 1].set_ylabel("Events per second")
            axes[1, 1].set_title("Control Action Density")

    for ax in axes.flat:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    p = out_dir / "behavioral_dashboard.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    paths.append(p)
    return paths


def plot_cross_layer_causal_chain(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """
    Cross-layer causal chain diagram:
    PHY drop probability -> Observed drop ratio -> Control actions -> Min TTC -> Collision
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    msg = _collect_msg_csvs(artifacts_dir)
    ctrl = _collect_ctrl_csvs(artifacts_dir)
    profiles = _collect_profile_csvs(artifacts_dir)

    if msg.empty:
        return paths

    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    fig.suptitle("Cross-Layer Causal Chain: PHY → Decision → Safety",
                 fontsize=14, fontweight="bold")

    # Build the chain boxes
    boxes = [
        ("PHY Layer\n(Channel/Radio)", 1, 4.5, "#3498db"),
        ("Network Layer\n(Packet Delivery)", 3.5, 4.5, "#2ecc71"),
        ("Application Layer\n(Decision Logic)", 6, 4.5, "#f39c12"),
        ("Transport Layer\n(Vehicle Safety)", 8.5, 4.5, "#e74c3c"),
    ]

    for label, x, y, color in boxes:
        rect = mpatches.FancyBboxPatch(
            (x - 0.8, y - 0.5), 1.6, 1.0,
            boxstyle="round,pad=0.1", facecolor=color, alpha=0.3,
            edgecolor=color, linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=10, fontweight="bold")

    # Arrows
    for i in range(len(boxes) - 1):
        x1 = boxes[i][1] + 0.8
        x2 = boxes[i + 1][1] - 0.8
        y = boxes[i][2]
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                     arrowprops=dict(arrowstyle="->", lw=2, color="#555"))

    # Add metrics below each box
    # PHY metrics
    if not profiles.empty and "drop_prob" in profiles.columns:
        probs = profiles.groupby("vehicle_id")["drop_prob"].first()
        text = "\n".join(f"{v}: p={p:.2f}" for v, p in probs.items())
        ax.text(1, 3.2, text, ha="center", va="top", fontsize=8,
                fontfamily="monospace", bbox=dict(boxstyle="round", facecolor="#ecf0f1"))

    # Network metrics
    if "msg_type" in msg.columns:
        total = len(msg)
        drops = msg["msg_type"].astype(str).str.contains("DROP").sum()
        ok = total - drops
        ax.text(3.5, 3.2, f"TX: {total}\nRX OK: {ok}\nDropped: {drops}\n"
                f"Drop ratio: {drops/total:.3f}" if total > 0 else "No data",
                ha="center", va="top", fontsize=8, fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="#ecf0f1"))

    # Behavioral metrics
    n_ctrl = len(ctrl) if not ctrl.empty else 0
    first_ctrl = "N/A"
    if not ctrl.empty and "time_s" in ctrl.columns:
        t = pd.to_numeric(ctrl["time_s"], errors="coerce").dropna()
        if not t.empty:
            first_ctrl = f"{t.min():.2f}s"
    ax.text(6, 3.2, f"Control actions: {n_ctrl}\nFirst action: {first_ctrl}",
            ha="center", va="top", fontsize=8, fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="#ecf0f1"))

    # Safety metrics
    risk_csv = artifacts_dir / "collision_risk" / "collision_risk_summary.csv"
    risk_df = _safe_read_csv(risk_csv)
    if risk_df is not None and not risk_df.empty:
        r = risk_df.iloc[0]
        min_ttc = pd.to_numeric(r.get("min_ttc_s"), errors="coerce")
        min_gap = pd.to_numeric(r.get("min_gap_m"), errors="coerce")
        ax.text(8.5, 3.2,
                f"Min TTC: {min_ttc:.2f}s\nMin gap: {min_gap:.2f}m",
                ha="center", va="top", fontsize=8, fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="#ecf0f1"))

    # Legend at bottom
    ax.text(5, 0.5,
            "Causal path: Radio quality degradation → Packet loss → "
            "Fewer/delayed decisions → Reduced safety margins",
            ha="center", va="center", fontsize=10, fontstyle="italic",
            color="#555")

    p = out_dir / "cross_layer_causal_chain.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(p)
    return paths


def plot_packet_raster(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """Packet raster: every CAM event as a dot — green=received, red=dropped."""
    out_dir.mkdir(parents=True, exist_ok=True)
    msg = _collect_msg_csvs(artifacts_dir)
    if msg.empty or "msg_type" not in msg.columns or "time_s" not in msg.columns:
        return []

    msg["time_s"] = pd.to_numeric(msg["time_s"], errors="coerce")
    msg = msg.dropna(subset=["time_s"])

    vehicles = sorted(msg["vehicle_id"].unique())
    fig, ax = plt.subplots(figsize=(16, max(3, len(vehicles) * 0.8)))
    fig.suptitle("Packet Raster Diagram", fontsize=14, fontweight="bold")

    for i, vid in enumerate(vehicles):
        veh_msg = msg[msg["vehicle_id"] == vid]
        ok = veh_msg[~veh_msg["msg_type"].astype(str).str.contains("DROP")]
        drop = veh_msg[veh_msg["msg_type"].astype(str).str.contains("DROP")]

        ax.scatter(ok["time_s"], [i] * len(ok), c="#2ca02c", s=4, alpha=0.6, marker="|")
        ax.scatter(drop["time_s"], [i] * len(drop), c="#d62728", s=8, alpha=0.8, marker="x")

    ax.set_yticks(range(len(vehicles)))
    ax.set_yticklabels(vehicles)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Vehicle")
    ax.grid(alpha=0.2)

    # Legend
    ok_patch = mpatches.Patch(color="#2ca02c", label="Received")
    drop_patch = mpatches.Patch(color="#d62728", label="Dropped")
    ax.legend(handles=[ok_patch, drop_patch], loc="upper right")

    fig.tight_layout()
    p = out_dir / "packet_raster.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return [p]


def plot_vehicle_profiles(artifacts_dir: Path, out_dir: Path) -> list[Path]:
    """Per-vehicle PHY profile: TX power, target PRR, drop probability."""
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles = _collect_profile_csvs(artifacts_dir)
    if profiles.empty:
        return []

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("Vehicle PHY Profiles", fontsize=14, fontweight="bold")

    vids = sorted(profiles["vehicle_id"].unique())

    for col, ax, ylabel, color in [
        ("tx_power_dbm", axes[0], "TX Power [dBm]", "#1f77b4"),
        ("target_prr", axes[1], "Target PRR [-]", "#2ca02c"),
        ("drop_prob", axes[2], "Drop Probability [-]", "#d62728"),
    ]:
        if col in profiles.columns:
            vals = [pd.to_numeric(
                profiles[profiles["vehicle_id"] == v][col], errors="coerce"
            ).iloc[0] if len(profiles[profiles["vehicle_id"] == v]) > 0 else 0
                    for v in vids]
            ax.bar(vids, vals, color=color, alpha=0.8)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Vehicle")
        ax.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    p = out_dir / "vehicle_profiles.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return [p]


# ── Plotly-based interactive plots (for Streamlit) ──────────────────────────

def plotly_sweep_summary(summary_csv: Path) -> go.Figure | None:
    """Interactive sweep summary chart from any *_summary.csv."""
    if not HAS_PLOTLY:
        return None
    df = _safe_read_csv(summary_csv)
    if df is None or df.empty:
        return None

    # Detect which kind of sweep this is
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return None

    # Auto-detect x-axis candidate
    x_candidates = ["target_drop_prob", "num_vehicles", "loss_prob",
                     "extra_delay_ms", "configured_drop_prob", "tx_power_dbm"]
    x_col = None
    for c in x_candidates:
        if c in df.columns:
            x_col = c
            break
    if x_col is None:
        x_col = numeric_cols[0]

    y_metrics = [c for c in numeric_cols if c != x_col and
                 c not in ("run_dir", "burst_length")]

    # Use group column if available
    group_col = None
    for c in ["loss_pattern", "impairment", "backend"]:
        if c in df.columns:
            group_col = c
            break

    n_metrics = min(len(y_metrics), 6)
    rows = (n_metrics + 1) // 2
    cols = 2

    fig = make_subplots(rows=rows, cols=cols,
                        subplot_titles=y_metrics[:n_metrics])

    for idx, metric in enumerate(y_metrics[:n_metrics]):
        r = idx // 2 + 1
        c = idx % 2 + 1
        if group_col:
            for gname, grp in df.groupby(group_col):
                grp_sorted = grp.sort_values(x_col)
                fig.add_trace(
                    go.Scatter(x=grp_sorted[x_col], y=grp_sorted[metric],
                               mode="lines+markers", name=f"{gname}",
                               legendgroup=str(gname),
                               showlegend=(idx == 0)),
                    row=r, col=c,
                )
        else:
            df_sorted = df.sort_values(x_col)
            fig.add_trace(
                go.Scatter(x=df_sorted[x_col], y=df_sorted[metric],
                           mode="lines+markers", name=metric,
                           showlegend=False),
                row=r, col=c,
            )
        fig.update_xaxes(title_text=x_col, row=r, col=c)
        fig.update_yaxes(title_text=metric, row=r, col=c)

    fig.update_layout(height=350 * rows, title_text="Experiment Results (Interactive)")
    return fig


def plotly_network_sunburst(artifacts_dir: Path) -> go.Figure | None:
    """Sunburst: Vehicle -> Message Type -> Count."""
    if not HAS_PLOTLY:
        return None
    msg = _collect_msg_csvs(artifacts_dir)
    if msg.empty or "msg_type" not in msg.columns:
        return None

    agg = msg.groupby(["vehicle_id", "msg_type"]).size().reset_index(name="count")
    fig = px.sunburst(agg, path=["vehicle_id", "msg_type"], values="count",
                      title="Message Distribution by Vehicle & Type",
                      color="msg_type",
                      color_discrete_map={
                          "CAM": "#2ca02c", "CAM_DROP_APP": "#ff7f0e",
                          "CAM_DROP_PHY": "#d62728", "DENM": "#1f77b4",
                      })
    return fig


def plotly_timeline(artifacts_dir: Path) -> go.Figure | None:
    """Interactive combined timeline: messages + control actions."""
    if not HAS_PLOTLY:
        return None

    msg = _collect_msg_csvs(artifacts_dir)
    ctrl = _collect_ctrl_csvs(artifacts_dir)

    if msg.empty and ctrl.empty:
        return None

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Messages", "Control Actions"],
                        vertical_spacing=0.08)

    if not msg.empty and "time_s" in msg.columns and "msg_type" in msg.columns:
        msg["time_s"] = pd.to_numeric(msg["time_s"], errors="coerce")
        for mt, grp in msg.groupby("msg_type"):
            color = "#2ca02c" if mt == "CAM" else "#d62728" if "DROP" in str(mt) else "#1f77b4"
            fig.add_trace(
                go.Scatter(x=grp["time_s"], y=grp["vehicle_id"],
                           mode="markers", marker=dict(size=3, color=color),
                           name=str(mt)),
                row=1, col=1,
            )

    if not ctrl.empty and "time_s" in ctrl.columns:
        ctrl["time_s"] = pd.to_numeric(ctrl["time_s"], errors="coerce")
        fig.add_trace(
            go.Scatter(x=ctrl["time_s"], y=ctrl["vehicle_id"],
                       mode="markers", marker=dict(size=6, color="#f39c12", symbol="diamond"),
                       name="Control action"),
            row=2, col=1,
        )

    fig.update_xaxes(title_text="Time [s]", row=2, col=1)
    fig.update_layout(height=600, title_text="Event Timeline (Interactive)")
    return fig


# ── Master generate function ────────────────────────────────────────────────

def generate_all_plots(run_dir: Path) -> dict[str, list[Path]]:
    """
    Generate all available visualizations for a completed run.
    Returns dict of category -> list of generated PNG paths.
    """
    results: dict[str, list[Path]] = {}
    viz_dir = run_dir / "visualizations"

    # Find artifacts directories (could be nested in sub-runs for sweeps)
    artifact_dirs = sorted(run_dir.rglob("artifacts"))
    if not artifact_dirs:
        return results

    # Generate per-case plots for each artifacts directory
    for art_dir in artifact_dirs:
        case_name = art_dir.parent.name
        case_viz = viz_dir / case_name

        plots = plot_network_kpi_dashboard(art_dir, case_viz)
        if plots:
            results.setdefault("Network KPI", []).extend(plots)

        plots = plot_transport_safety_dashboard(art_dir, case_viz)
        if plots:
            results.setdefault("Transport Safety", []).extend(plots)

        plots = plot_behavioral_dashboard(art_dir, case_viz)
        if plots:
            results.setdefault("Behavioral Analysis", []).extend(plots)

        plots = plot_cross_layer_causal_chain(art_dir, case_viz)
        if plots:
            results.setdefault("Cross-Layer Causal Chain", []).extend(plots)

        plots = plot_packet_raster(art_dir, case_viz)
        if plots:
            results.setdefault("Packet Raster", []).extend(plots)

        plots = plot_vehicle_profiles(art_dir, case_viz)
        if plots:
            results.setdefault("Vehicle Profiles", []).extend(plots)

    return results
