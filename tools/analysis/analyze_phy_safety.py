#!/usr/bin/env python3
"""
PHY-Safety Correlation Analyzer for NR-V2X Experiments

Reads per-vehicle PHY CSVs (*-PHY.csv) from EVA scenario runs and produces
analysis showing how PHY-layer metrics (SINR, SNR, RSSI, RSRP) correlate
with safety outcomes (message reception, control actions, collisions).

Plots:
  1. SINR distribution (histogram) per vehicle
  2. SINR vs distance scatter
  3. SINR timeline per vehicle (time-series)
  4. CDF of SINR across all vehicles / per sweep condition
  5. Four-metric overview (SINR, SNR, RSSI, RSRP)
  6. PHY metrics vs reception outcome
  7. Distance-binned reception rate vs mean SINR
"""

import argparse
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_phy_csvs(run_dir: Path) -> pd.DataFrame:
    """Load and concatenate all *-PHY.csv files from a run directory."""
    pattern = str(run_dir / "artifacts" / "*-PHY.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        # Try flat directory
        pattern = str(run_dir / "*-PHY.csv")
        files = sorted(glob.glob(pattern))
    if not files:
        print(f"No PHY CSV files found in {run_dir}", file=sys.stderr)
        return pd.DataFrame()

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"Warning: failed to read {f}: {e}", file=sys.stderr)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(combined)} PHY records from {len(files)} files")
    return combined


def load_ctrl_csvs(run_dir: Path) -> pd.DataFrame:
    """Load CTRL CSVs for correlating PHY with safety events."""
    pattern = str(run_dir / "artifacts" / "*-CTRL.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame()
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if not df.empty:
                frames.append(df)
        except Exception:
            pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def plot_sinr_histogram(phy: pd.DataFrame, out_dir: Path):
    """SINR distribution per vehicle."""
    if "sinr_dB" not in phy.columns:
        return
    sinr = phy["sinr_dB"].dropna()
    sinr = sinr[np.isfinite(sinr)]
    if sinr.empty:
        return

    vehicles = phy["vehicle_id"].unique()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall histogram
    axes[0].hist(sinr, bins=60, edgecolor="black", alpha=0.7, color="#1976D2")
    axes[0].axvline(sinr.median(), color="red", linestyle="--",
                    label=f"median={sinr.median():.1f} dB")
    axes[0].set_xlabel("SINR (dB)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Overall SINR Distribution")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Per-vehicle boxplot
    veh_data = [phy.loc[phy["vehicle_id"] == v, "sinr_dB"].dropna().values
                for v in sorted(vehicles)]
    veh_labels = [str(v) for v in sorted(vehicles)]
    if veh_data and any(len(d) > 0 for d in veh_data):
        axes[1].boxplot(veh_data, labels=veh_labels, vert=True)
        axes[1].set_xlabel("Vehicle")
        axes[1].set_ylabel("SINR (dB)")
        axes[1].set_title("SINR per Vehicle")
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_dir / "phy_sinr_histogram.png", dpi=150)
    plt.close(fig)
    print(f"  phy_sinr_histogram.png")


def plot_sinr_vs_distance(phy: pd.DataFrame, out_dir: Path):
    """SINR vs distance scatter."""
    cols = ["sinr_dB", "distance_m"]
    if not all(c in phy.columns for c in cols):
        return
    df = phy[cols].dropna()
    df = df[(df["distance_m"] > 0) & np.isfinite(df["sinr_dB"])]
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(df["distance_m"], df["sinr_dB"], alpha=0.2, s=8, c="#E65100")
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("SINR (dB)")
    ax.set_title("SINR vs Distance (each dot = 1 received CAM)")
    ax.grid(True, alpha=0.3)

    # Binned mean
    df["dist_bin"] = (df["distance_m"] // 10) * 10
    binned = df.groupby("dist_bin")["sinr_dB"].agg(["mean", "std", "count"])
    binned = binned[binned["count"] >= 5]
    if not binned.empty:
        ax.plot(binned.index + 5, binned["mean"], "r-", linewidth=2, label="10m-bin mean")
        ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / "phy_sinr_vs_distance.png", dpi=150)
    plt.close(fig)
    print("  phy_sinr_vs_distance.png")


def plot_sinr_timeline(phy: pd.DataFrame, out_dir: Path):
    """SINR time-series per vehicle."""
    if "sinr_dB" not in phy.columns or "time_s" not in phy.columns:
        return
    vehicles = sorted(phy["vehicle_id"].unique())
    n = min(len(vehicles), 6)  # max 6 subplots
    if n == 0:
        return

    fig, axes = plt.subplots(n, 1, figsize=(14, 3 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for i, veh in enumerate(vehicles[:n]):
        vdf = phy[phy["vehicle_id"] == veh].sort_values("time_s")
        sinr = vdf["sinr_dB"].values
        time = vdf["time_s"].values
        valid = np.isfinite(sinr)
        axes[i].plot(time[valid], sinr[valid], linewidth=0.8, alpha=0.7)
        axes[i].set_ylabel("SINR (dB)")
        axes[i].set_title(f"{veh}", fontsize=10)
        axes[i].grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (s)")
    fig.suptitle("SINR Timeline per Vehicle", fontsize=13)
    fig.tight_layout()
    fig.savefig(out_dir / "phy_sinr_timeline.png", dpi=150)
    plt.close(fig)
    print("  phy_sinr_timeline.png")


def plot_sinr_cdf(phy: pd.DataFrame, out_dir: Path):
    """CDF of SINR — overall and per vehicle."""
    if "sinr_dB" not in phy.columns:
        return
    fig, ax = plt.subplots(figsize=(10, 6))

    # Overall
    sinr_all = phy["sinr_dB"].dropna()
    sinr_all = sinr_all[np.isfinite(sinr_all)]
    if sinr_all.empty:
        return
    sorted_vals = np.sort(sinr_all)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    ax.plot(sorted_vals, cdf, linewidth=2, color="black", label="All vehicles")

    # Per vehicle (lighter)
    vehicles = sorted(phy["vehicle_id"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, min(len(vehicles), 10)))
    for i, veh in enumerate(vehicles[:10]):
        vsinr = phy.loc[phy["vehicle_id"] == veh, "sinr_dB"].dropna()
        vsinr = vsinr[np.isfinite(vsinr)]
        if len(vsinr) < 5:
            continue
        vs = np.sort(vsinr)
        vc = np.arange(1, len(vs) + 1) / len(vs)
        ax.plot(vs, vc, linewidth=1, alpha=0.6, color=colors[i % 10], label=str(veh))

    ax.set_xlabel("SINR (dB)")
    ax.set_ylabel("CDF")
    ax.set_title("SINR CDF — Overall and Per Vehicle")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "phy_sinr_cdf.png", dpi=150)
    plt.close(fig)
    print("  phy_sinr_cdf.png")


def plot_four_metrics(phy: pd.DataFrame, out_dir: Path):
    """Overview of all 4 PHY metrics: SINR, SNR, RSSI, RSRP."""
    metrics = [
        ("sinr_dB", "SINR (dB)", "#1976D2"),
        ("snr_dB", "SNR (dB)", "#388E3C"),
        ("rssi_dBm", "RSSI (dBm)", "#F57C00"),
        ("rsrp_dBm", "RSRP (dBm)", "#7B1FA2"),
    ]
    available = [(col, label, c) for col, label, c in metrics if col in phy.columns]
    if not available:
        return

    n = len(available)
    fig, axes = plt.subplots(2, n, figsize=(5 * n, 8))
    if n == 1:
        axes = axes.reshape(-1, 1)

    for i, (col, label, color) in enumerate(available):
        vals = phy[col].dropna()
        vals = vals[np.isfinite(vals)]
        if vals.empty:
            continue

        # Histogram
        axes[0, i].hist(vals, bins=50, edgecolor="black", alpha=0.7, color=color)
        axes[0, i].set_xlabel(label)
        axes[0, i].set_ylabel("Count")
        axes[0, i].set_title(f"{label} Distribution")
        axes[0, i].axvline(vals.median(), color="red", linestyle="--", linewidth=1)
        axes[0, i].grid(True, alpha=0.3)

        # vs distance
        if "distance_m" in phy.columns:
            mask = phy[col].notna() & (phy["distance_m"] > 0) & np.isfinite(phy[col])
            if mask.sum() > 10:
                axes[1, i].scatter(phy.loc[mask, "distance_m"], phy.loc[mask, col],
                                   alpha=0.15, s=6, color=color)
                axes[1, i].set_xlabel("Distance (m)")
                axes[1, i].set_ylabel(label)
                axes[1, i].set_title(f"{label} vs Distance")
                axes[1, i].grid(True, alpha=0.3)

    fig.suptitle("PHY Metrics Overview", fontsize=14, y=1.01)
    fig.tight_layout()
    fig.savefig(out_dir / "phy_four_metrics.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  phy_four_metrics.png")


def plot_distance_binned_reception(phy: pd.DataFrame, out_dir: Path):
    """Distance-binned reception rate vs mean SINR — key safety insight."""
    if "sinr_dB" not in phy.columns or "distance_m" not in phy.columns:
        return
    df = phy[["distance_m", "sinr_dB", "rx_ok"]].dropna()
    df = df[(df["distance_m"] > 0) & np.isfinite(df["sinr_dB"])]
    if df.empty:
        return

    df["dist_bin"] = (df["distance_m"] // 20) * 20
    binned = df.groupby("dist_bin").agg(
        mean_sinr=("sinr_dB", "mean"),
        rx_rate=("rx_ok", "mean"),
        count=("rx_ok", "count"),
    )
    binned = binned[binned["count"] >= 3]
    if binned.empty:
        return

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.bar(binned.index + 10, binned["mean_sinr"], width=15, alpha=0.6,
            color="#1976D2", label="Mean SINR")
    ax2.plot(binned.index + 10, binned["rx_rate"], "r-o", linewidth=2,
             markersize=6, label="Reception Rate")

    ax1.set_xlabel("Distance bin (m)")
    ax1.set_ylabel("Mean SINR (dB)", color="#1976D2")
    ax2.set_ylabel("Reception Rate", color="red")
    ax2.set_ylim(0, 1.05)
    ax1.set_title("PHY-Safety Link: SINR and Reception vs Distance")
    ax1.grid(True, alpha=0.3)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="lower left")

    fig.tight_layout()
    fig.savefig(out_dir / "phy_distance_reception.png", dpi=150)
    plt.close(fig)
    print("  phy_distance_reception.png")


def print_summary(phy: pd.DataFrame):
    """Print key statistics."""
    print("\n=== PHY Metrics Summary ===")
    for col, label in [("sinr_dB", "SINR"), ("snr_dB", "SNR"),
                        ("rssi_dBm", "RSSI"), ("rsrp_dBm", "RSRP")]:
        if col not in phy.columns:
            continue
        vals = phy[col].dropna()
        vals = vals[np.isfinite(vals)]
        if vals.empty:
            continue
        print(f"  {label:6s}: median={vals.median():7.1f}  mean={vals.mean():7.1f}  "
              f"std={vals.std():5.1f}  min={vals.min():7.1f}  max={vals.max():7.1f}  N={len(vals)}")

    if "distance_m" in phy.columns:
        dist = phy["distance_m"].dropna()
        dist = dist[dist > 0]
        if not dist.empty:
            print(f"  Distance: median={dist.median():.0f}m  max={dist.max():.0f}m")

    if "rx_ok" in phy.columns:
        print(f"  Overall rx_ok rate: {phy['rx_ok'].mean():.3f}")

    print(f"  Total records: {len(phy)}")
    print(f"  Vehicles: {phy['vehicle_id'].nunique()}")


def main():
    parser = argparse.ArgumentParser(description="PHY-Safety Correlation Analyzer")
    parser.add_argument("--run-dir", required=True,
                        help="Scenario run directory containing artifacts/")
    parser.add_argument("--out-dir", default=None,
                        help="Output directory for plots (default: run-dir/phy_analysis/)")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    out_dir = Path(args.out_dir) if args.out_dir else run_dir / "phy_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== PHY-Safety Correlation Analyzer ===")
    print(f"Run dir: {run_dir}")
    print(f"Output:  {out_dir}")
    print()

    phy = load_phy_csvs(run_dir)
    if phy.empty:
        print("ERROR: No PHY data found. Ensure EVA was run with PHY logging enabled.")
        sys.exit(1)

    print_summary(phy)
    print("\nGenerating plots...")

    plot_sinr_histogram(phy, out_dir)
    plot_sinr_vs_distance(phy, out_dir)
    plot_sinr_timeline(phy, out_dir)
    plot_sinr_cdf(phy, out_dir)
    plot_four_metrics(phy, out_dir)
    plot_distance_binned_reception(phy, out_dir)

    print(f"\nAll plots saved to: {out_dir}")


if __name__ == "__main__":
    main()
