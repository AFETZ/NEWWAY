#!/usr/bin/env python3
"""
5G NR-V2X PHY Metrics Plotter

Reads CSV outputs from v2v-5g-phy-metrics-experiment and generates
publication-ready plots:
  1. SINR distribution (histogram + CDF)
  2. TBLER vs SINR scatter
  3. MCS usage bar chart
  4. TB size distribution
  5. PRR per node
  6. Corruption rate over time
  7. PSCCH priority & subchannel usage
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_csv(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        print(f"Warning: {name} file not found: {path}", file=sys.stderr)
        return pd.DataFrame()
    df = pd.read_csv(path)
    print(f"Loaded {name}: {len(df)} rows from {path}")
    return df


def plot_sinr_distribution(pssch: pd.DataFrame, out_dir: Path):
    """SINR histogram + CDF."""
    if pssch.empty or "sinr_db" not in pssch.columns:
        return
    sinr = pssch["sinr_db"].dropna()
    sinr = sinr[np.isfinite(sinr)]
    if sinr.empty:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.hist(sinr, bins=60, edgecolor="black", alpha=0.7, color="#2196F3")
    ax1.set_xlabel("SINR (dB)")
    ax1.set_ylabel("Count")
    ax1.set_title("PSSCH SINR Distribution")
    ax1.grid(True, alpha=0.3)

    sorted_sinr = np.sort(sinr)
    cdf = np.arange(1, len(sorted_sinr) + 1) / len(sorted_sinr)
    ax2.plot(sorted_sinr, cdf, linewidth=2, color="#F44336")
    ax2.set_xlabel("SINR (dB)")
    ax2.set_ylabel("CDF")
    ax2.set_title("PSSCH SINR CDF")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "sinr_distribution.png", dpi=150)
    plt.close(fig)
    print(f"  sinr_distribution.png  (median={sinr.median():.1f} dB)")


def plot_tbler_vs_sinr(pssch: pd.DataFrame, out_dir: Path):
    """TBLER vs SINR scatter plot."""
    if pssch.empty or "sinr_db" not in pssch.columns or "tbler" not in pssch.columns:
        return
    df = pssch[["sinr_db", "tbler"]].dropna()
    df = df[np.isfinite(df["sinr_db"])]
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["sinr_db"], df["tbler"], alpha=0.15, s=8, color="#4CAF50")
    ax.set_xlabel("SINR (dB)")
    ax.set_ylabel("TBLER")
    ax.set_title("TBLER vs SINR (PSSCH)")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "tbler_vs_sinr.png", dpi=150)
    plt.close(fig)
    print("  tbler_vs_sinr.png")


def plot_mcs_usage(pssch: pd.DataFrame, out_dir: Path):
    """MCS usage bar chart."""
    if pssch.empty or "mcs" not in pssch.columns:
        return
    mcs_counts = pssch["mcs"].value_counts().sort_index()
    if mcs_counts.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(mcs_counts.index, mcs_counts.values, color="#FF9800", edgecolor="black")
    ax.set_xlabel("MCS Index")
    ax.set_ylabel("Count")
    ax.set_title("MCS Usage Distribution (PSSCH)")
    ax.set_xticks(range(int(mcs_counts.index.min()), int(mcs_counts.index.max()) + 1))
    ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_dir / "mcs_usage.png", dpi=150)
    plt.close(fig)
    print("  mcs_usage.png")


def plot_tb_size(pssch: pd.DataFrame, out_dir: Path):
    """Transport block size distribution."""
    if pssch.empty or "tb_size_bytes" not in pssch.columns:
        return
    tb = pssch["tb_size_bytes"].dropna()
    if tb.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(tb, bins=50, edgecolor="black", alpha=0.7, color="#9C27B0")
    ax.set_xlabel("TB Size (bytes)")
    ax.set_ylabel("Count")
    ax.set_title("Transport Block Size Distribution (PSSCH)")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "tb_size_distribution.png", dpi=150)
    plt.close(fig)
    print(f"  tb_size_distribution.png  (median={tb.median():.0f} B)")


def plot_prr_per_node(prr: pd.DataFrame, out_dir: Path):
    """PRR per node bar chart."""
    if prr.empty or "prr" not in prr.columns:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(prr["node_id"], prr["prr"], color="#00BCD4", edgecolor="black")
    ax.set_xlabel("Node ID")
    ax.set_ylabel("PRR")
    ax.set_title("Packet Reception Ratio per Node")
    ax.set_ylim(0, 1.05)
    ax.axhline(y=prr["prr"].mean(), color="red", linestyle="--",
               label=f"Mean PRR = {prr['prr'].mean():.3f}")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_dir / "prr_per_node.png", dpi=150)
    plt.close(fig)
    print(f"  prr_per_node.png  (mean={prr['prr'].mean():.3f})")


def plot_corruption_over_time(pssch: pd.DataFrame, out_dir: Path):
    """Corruption rate over time (sliding window)."""
    if pssch.empty or "time_ms" not in pssch.columns or "corrupt" not in pssch.columns:
        return
    df = pssch[["time_ms", "corrupt"]].dropna().copy()
    if df.empty:
        return

    df["time_s"] = df["time_ms"] / 1000.0
    # 1-second bins
    df["time_bin"] = (df["time_s"] // 1.0) * 1.0
    grouped = df.groupby("time_bin").agg(
        total=("corrupt", "count"),
        corrupted=("corrupt", "sum"),
    )
    grouped["corruption_rate"] = grouped["corrupted"] / grouped["total"]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(grouped.index, grouped["corruption_rate"], linewidth=1.5, color="#E91E63")
    ax.fill_between(grouped.index, grouped["corruption_rate"], alpha=0.2, color="#E91E63")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Corruption Rate")
    ax.set_title("TB Corruption Rate Over Time (1s bins)")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "corruption_over_time.png", dpi=150)
    plt.close(fig)
    print(f"  corruption_over_time.png  (avg={grouped['corruption_rate'].mean():.3f})")


def plot_pscch_stats(pscch: pd.DataFrame, out_dir: Path):
    """PSCCH priority and subchannel usage."""
    if pscch.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    if "priority" in pscch.columns:
        prio_counts = pscch["priority"].value_counts().sort_index()
        axes[0].bar(prio_counts.index, prio_counts.values, color="#795548", edgecolor="black")
        axes[0].set_xlabel("Priority")
        axes[0].set_ylabel("Count")
        axes[0].set_title("PSCCH Priority Distribution")
        axes[0].grid(True, alpha=0.3, axis="y")

    if "start_subchannel" in pscch.columns and "length_subchannel" in pscch.columns:
        axes[1].scatter(pscch["start_subchannel"], pscch["length_subchannel"],
                        alpha=0.3, s=10, color="#607D8B")
        axes[1].set_xlabel("Start Subchannel Index")
        axes[1].set_ylabel("Subchannel Length")
        axes[1].set_title("Subchannel Allocation (PSCCH)")
        axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "pscch_stats.png", dpi=150)
    plt.close(fig)
    print("  pscch_stats.png")


def main():
    parser = argparse.ArgumentParser(description="Plot 5G NR-V2X PHY metrics")
    parser.add_argument("--prefix", required=True,
                        help="CSV file prefix (same as --out-prefix in ns-3)")
    parser.add_argument("--out-dir", default=None,
                        help="Output directory for plots (default: same as prefix dir)")
    args = parser.parse_args()

    prefix = Path(args.prefix)
    out_dir = Path(args.out_dir) if args.out_dir else prefix.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== 5G NR-V2X PHY Metrics Plotter ===")
    print(f"Prefix: {prefix}")
    print(f"Output: {out_dir}")
    print()

    pssch = load_csv(Path(f"{prefix}-pssch.csv"), "PSSCH")
    pscch = load_csv(Path(f"{prefix}-pscch.csv"), "PSCCH")
    cam = load_csv(Path(f"{prefix}-cam.csv"), "CAM")
    prr = load_csv(Path(f"{prefix}-prr.csv"), "PRR")

    print()
    print("Generating plots...")

    plot_sinr_distribution(pssch, out_dir)
    plot_tbler_vs_sinr(pssch, out_dir)
    plot_mcs_usage(pssch, out_dir)
    plot_tb_size(pssch, out_dir)
    plot_prr_per_node(prr, out_dir)
    plot_corruption_over_time(pssch, out_dir)
    plot_pscch_stats(pscch, out_dir)

    print()
    print(f"All plots saved to: {out_dir}")


if __name__ == "__main__":
    main()
