#!/usr/bin/env python3
"""Build practical plots for scenario run artifacts."""

from __future__ import annotations

import argparse
import csv
import math
import sqlite3
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _latest_file(run_dir: Path, pattern: str) -> Path | None:
    files = sorted((run_dir / "artifacts").glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_cttc(run_dir: Path) -> list[Path]:
    created: list[Path] = []
    out = run_dir / "figures" / "cttc-nr-v2x-demo-simple"
    _ensure_dir(out)
    db = _latest_file(run_dir, "*-nr-v2x-simple-demo.db")
    if not db:
        return created

    with sqlite3.connect(db) as con:
        pkt = pd.read_sql_query("SELECT timeSec, txRx FROM pktTxRx ORDER BY timeSec", con)
        sinr = pd.read_sql_query("SELECT avrgSinr, psschCorrupt FROM psschRxUePhy", con)

    if not pkt.empty:
        tx = pkt[pkt["txRx"] == "tx"]["timeSec"].to_numpy()
        rx = pkt[pkt["txRx"] == "rx"]["timeSec"].to_numpy()
        t_start = math.floor(float(pkt["timeSec"].min()))
        t_end = math.ceil(float(pkt["timeSec"].max())) + 1
        bins = np.arange(t_start, t_end + 0.5, 0.5)
        tx_bin, _ = np.histogram(tx, bins=bins)
        rx_bin, _ = np.histogram(rx, bins=bins)
        t = bins[:-1]

        cum_tx = np.cumsum(tx_bin)
        cum_rx = np.cumsum(rx_bin)
        prr = np.divide(cum_rx, cum_tx, out=np.zeros_like(cum_rx, dtype=float), where=cum_tx > 0)

        fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax[0].step(t, tx_bin, where="post", label="TX packets / 0.5s")
        ax[0].step(t, rx_bin, where="post", label="RX packets / 0.5s")
        ax[0].set_ylabel("Packets")
        ax[0].legend()
        ax[0].grid(alpha=0.3)

        ax[1].plot(t, prr, label="Cumulative PRR")
        ax[1].set_xlabel("Time [s]")
        ax[1].set_ylabel("PRR [-]")
        ax[1].set_ylim(0, 1.05)
        ax[1].grid(alpha=0.3)
        ax[1].legend()

        p = out / "cttc_prr_over_time.png"
        _save(fig, p)
        created.append(p)

    if not sinr.empty:
        sinr_vals = sinr["avrgSinr"].astype(float).to_numpy()
        corr_rate = float((sinr["psschCorrupt"].astype(int) > 0).mean())

        fig, ax = plt.subplots(1, 1, figsize=(9, 4))
        ax.hist(sinr_vals, bins=40, alpha=0.8)
        ax.set_xlabel("Average SINR [dB]")
        ax.set_ylabel("Count")
        ax.set_title(f"PSSCH SINR distribution (corruption rate={corr_rate:.3f})")
        ax.grid(alpha=0.3)
        p = out / "cttc_pssch_sinr_distribution.png"
        _save(fig, p)
        created.append(p)

    return created


def plot_highway(run_dir: Path) -> list[Path]:
    created: list[Path] = []
    out = run_dir / "figures" / "nr-v2x-west-to-east-highway"
    _ensure_dir(out)
    db = _latest_file(run_dir, "*-nr-v2x-west-to-east-highway.db")
    if not db:
        return created

    with sqlite3.connect(db) as con:
        prr = pd.read_sql_query("SELECT Ip, avrgPrr FROM avrgPrr", con)
        pir = pd.read_sql_query("SELECT TxRxDistance, avrgPirSec FROM avrgPir", con)
        th = pd.read_sql_query("SELECT srcIp, dstIp, thputKbps FROM thput", con)
        ov = pd.read_sql_query("SELECT totalTx, numOverlapping FROM simulPsschTx", con)
        tb = pd.read_sql_query("SELECT totalRx, psschFailCount FROM PsschTbRx", con)

    if not prr.empty:
        prr = prr.sort_values("Ip")
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        ax.bar(prr["Ip"], prr["avrgPrr"], color="#1f77b4")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Average PRR [-]")
        ax.set_xlabel("Transmitter IP")
        ax.grid(axis="y", alpha=0.3)
        p = out / "highway_prr_per_tx.png"
        _save(fig, p)
        created.append(p)

    if not pir.empty:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        ax.scatter(pir["TxRxDistance"], pir["avrgPirSec"], alpha=0.75, s=18)
        ax.set_xlabel("TX-RX distance [m]")
        ax.set_ylabel("Average PIR [s]")
        ax.grid(alpha=0.3)
        p = out / "highway_pir_vs_distance.png"
        _save(fig, p)
        created.append(p)

    if not th.empty:
        th["link"] = th["srcIp"] + "->" + th["dstIp"]
        th = th.sort_values("thputKbps", ascending=False).head(12)
        fig, ax = plt.subplots(1, 1, figsize=(10, 4))
        ax.bar(th["link"], th["thputKbps"], color="#2ca02c")
        ax.set_ylabel("Throughput [kbps]")
        for lbl in ax.get_xticklabels():
            lbl.set_rotation(35)
            lbl.set_ha("right")
        ax.grid(axis="y", alpha=0.3)
        p = out / "highway_top_links_throughput.png"
        _save(fig, p)
        created.append(p)

    if not ov.empty and not tb.empty:
        overlap_ratio = float(ov["numOverlapping"].iloc[0]) / float(ov["totalTx"].iloc[0])
        tb_fail_ratio = float(tb["psschFailCount"].iloc[0]) / float(tb["totalRx"].iloc[0])
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        ax.bar(["PSSCH overlap", "PSSCH TB fail"], [overlap_ratio, tb_fail_ratio], color=["#ff7f0e", "#d62728"])
        ax.set_ylim(0, max(0.1, overlap_ratio, tb_fail_ratio) * 1.4)
        ax.set_ylabel("Ratio [-]")
        ax.grid(axis="y", alpha=0.3)
        p = out / "highway_overlap_and_tb_fail_ratio.png"
        _save(fig, p)
        created.append(p)

    return created


def _rolling_median_line(x: np.ndarray, y: np.ndarray, bins: int = 20) -> tuple[np.ndarray, np.ndarray]:
    if len(x) == 0:
        return np.array([]), np.array([])
    order = np.argsort(x)
    xs = x[order]
    ys = y[order]
    edges = np.linspace(xs.min(), xs.max(), bins + 1)
    xm = []
    ym = []
    for i in range(bins):
        mask = (xs >= edges[i]) & (xs < edges[i + 1] if i < bins - 1 else xs <= edges[i + 1])
        if mask.any():
            xm.append(float(np.median(xs[mask])))
            ym.append(float(np.median(ys[mask])))
    return np.array(xm), np.array(ym)


def plot_cam_sionna(run_dir: Path) -> list[Path]:
    created: list[Path] = []
    out = run_dir / "figures" / "v2v-cam-exchange-sionna-nrv2x"
    _ensure_dir(out)
    prr_csv = run_dir / "artifacts" / "prr_with_sionna_nrv2x.csv"
    phy_csv = run_dir / "artifacts" / "phy_with_sionna_nrv2x.csv"

    if prr_csv.exists():
        prr = pd.read_csv(prr_csv).dropna()
        if not prr.empty:
            prr["node_id"] = pd.to_numeric(prr["node_id"], errors="coerce")
            prr["prr"] = pd.to_numeric(prr["prr"], errors="coerce")
            prr = prr.dropna(subset=["node_id", "prr"])
            prr = prr.sort_values("prr")
            fig, ax = plt.subplots(1, 1, figsize=(8, 4))
            ax.bar(prr["node_id"].astype(str), prr["prr"].astype(float), color="#1f77b4")
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("PRR [-]")
            ax.set_xlabel("Node ID")
            ax.grid(axis="y", alpha=0.3)
            p = out / "cam_sionna_prr_per_node.png"
            _save(fig, p)
            created.append(p)

    if phy_csv.exists():
        phy = pd.read_csv(phy_csv).dropna()
        for col in ("distance", "rssi", "snr"):
            phy[col] = pd.to_numeric(phy[col], errors="coerce")
        phy = phy.dropna(subset=["distance", "rssi", "snr"])
        if not phy.empty:
            dist = phy["distance"].to_numpy()
            snr = phy["snr"].to_numpy()
            rssi = phy["rssi"].to_numpy()

            fig, ax = plt.subplots(1, 2, figsize=(12, 4))
            ax[0].scatter(dist, snr, s=8, alpha=0.25)
            x_med, y_med = _rolling_median_line(dist, snr)
            if len(x_med):
                ax[0].plot(x_med, y_med, color="red", linewidth=2, label="Median trend")
                ax[0].legend()
            ax[0].set_xlabel("Distance [m]")
            ax[0].set_ylabel("SNR [dB]")
            ax[0].grid(alpha=0.3)

            ax[1].scatter(dist, rssi, s=8, alpha=0.25)
            x_med, y_med = _rolling_median_line(dist, rssi)
            if len(x_med):
                ax[1].plot(x_med, y_med, color="red", linewidth=2, label="Median trend")
                ax[1].legend()
            ax[1].set_xlabel("Distance [m]")
            ax[1].set_ylabel("RSSI [dBm]")
            ax[1].grid(alpha=0.3)

            p = out / "cam_sionna_phy_vs_distance.png"
            _save(fig, p)
            created.append(p)

    return created


def _cdf(data: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    arr = np.array([v for v in data if v is not None and not math.isnan(v)], dtype=float)
    if arr.size == 0:
        return np.array([]), np.array([])
    arr = np.sort(arr)
    y = np.arange(1, arr.size + 1) / arr.size
    return arr, y


def plot_coexistence(run_dir: Path) -> list[Path]:
    created: list[Path] = []
    out = run_dir / "figures" / "v2v-coexistence-80211p-nrv2x"
    _ensure_dir(out)
    csv_11p = run_dir / "artifacts" / "prr_latency_ns3_coexistence_11p.csv"
    csv_nr = run_dir / "artifacts" / "prr_latency_ns3_coexistence_nrv2x.csv"
    sinr_csv = run_dir / "artifacts" / "sinr_ni.csv"

    if csv_11p.exists() and csv_nr.exists():
        p11 = pd.read_csv(csv_11p).dropna()
        pnr = pd.read_csv(csv_nr).dropna()
        for df in (p11, pnr):
            df["prr"] = pd.to_numeric(df["prr"], errors="coerce")
            df["latency(ms)"] = pd.to_numeric(df["latency(ms)"], errors="coerce")
            df["node_id"] = pd.to_numeric(df["node_id"], errors="coerce")
        p11 = p11.dropna()
        pnr = pnr.dropna()

        if not p11.empty and not pnr.empty:
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            ax[0].bar(["802.11p", "NR-V2X"], [p11["prr"].mean(), pnr["prr"].mean()], color=["#1f77b4", "#ff7f0e"])
            ax[0].set_ylim(0, 1.05)
            ax[0].set_ylabel("Average PRR [-]")
            ax[0].grid(axis="y", alpha=0.3)

            ax[1].bar(
                ["802.11p", "NR-V2X"],
                [p11["latency(ms)"].mean(), pnr["latency(ms)"].mean()],
                color=["#1f77b4", "#ff7f0e"],
            )
            ax[1].set_ylabel("Average latency [ms]")
            ax[1].grid(axis="y", alpha=0.3)

            p = out / "coexistence_prr_latency_by_tech.png"
            _save(fig, p)
            created.append(p)

            merged = pd.merge(
                p11[["node_id", "prr"]].rename(columns={"prr": "prr_11p"}),
                pnr[["node_id", "prr"]].rename(columns={"prr": "prr_nr"}),
                on="node_id",
                how="outer",
            ).sort_values("node_id")
            x = np.arange(len(merged))
            w = 0.4
            fig, ax = plt.subplots(1, 1, figsize=(10, 4))
            ax.bar(x - w / 2, merged["prr_11p"], width=w, label="802.11p")
            ax.bar(x + w / 2, merged["prr_nr"], width=w, label="NR-V2X")
            ax.set_xticks(x)
            ax.set_xticklabels(merged["node_id"].astype(int).astype(str))
            ax.set_ylim(0, 1.05)
            ax.set_xlabel("Node ID")
            ax.set_ylabel("PRR [-]")
            ax.grid(axis="y", alpha=0.3)
            ax.legend()
            p = out / "coexistence_prr_per_node.png"
            _save(fig, p)
            created.append(p)

    if sinr_csv.exists():
        sinr = pd.read_csv(sinr_csv)
        if "technology" in sinr.columns and "sinr" in sinr.columns:
            sinr["sinr"] = pd.to_numeric(sinr["sinr"], errors="coerce")
            sinr = sinr.dropna(subset=["sinr"])
            tech_values = sorted(sinr["technology"].dropna().unique())
            if tech_values:
                fig, ax = plt.subplots(1, 1, figsize=(8, 4))
                for tech in tech_values:
                    x, y = _cdf(sinr.loc[sinr["technology"] == tech, "sinr"].to_list())
                    if len(x):
                        ax.plot(x, y, label=tech)
                ax.set_xlabel("SINR [dB]")
                ax.set_ylabel("CDF [-]")
                ax.grid(alpha=0.3)
                ax.legend()
                p = out / "coexistence_sinr_cdf_by_tech.png"
                _save(fig, p)
                created.append(p)

    return created


def _parse_emergency_info_line(line: str) -> dict[str, float | str] | None:
    if not line.startswith("INFO-"):
        return None
    parts = line.strip().split(",")
    if not parts:
        return None
    row: dict[str, float | str] = {"vehicle_id": parts[0].replace("INFO-", "", 1)}
    for part in parts[1:]:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip().lower().replace("-", "_").replace(" ", "_")
        try:
            row[key] = float(value.strip())
        except ValueError:
            continue
    return row


def plot_emergency(run_dir: Path) -> list[Path]:
    created: list[Path] = []
    out = run_dir / "figures" / "v2v-emergencyVehicleAlert-nrv2x"
    _ensure_dir(out)

    ctrl_files = sorted((run_dir / "artifacts").glob("*-CTRL.csv"))
    if ctrl_files:
        ctrl = pd.concat((pd.read_csv(f) for f in ctrl_files), ignore_index=True)
        if "time_s" in ctrl.columns and "event_type" in ctrl.columns:
            ctrl["time_s"] = pd.to_numeric(ctrl["time_s"], errors="coerce")
            ctrl = ctrl.dropna(subset=["time_s", "event_type"])
            if not ctrl.empty:
                t_start = int(math.floor(float(ctrl["time_s"].min())))
                t_end = int(math.ceil(float(ctrl["time_s"].max()))) + 1
                bins = np.arange(t_start, max(t_start + 1, t_end) + 1, 1.0)
                if bins.size < 2:
                    bins = np.array([t_start, t_start + 1], dtype=float)

                event_types = sorted(ctrl["event_type"].astype(str).unique())
                fig, ax = plt.subplots(1, 2, figsize=(12, 4))
                for ev in event_types:
                    vals = ctrl.loc[ctrl["event_type"] == ev, "time_s"].to_numpy()
                    hist, _ = np.histogram(vals, bins=bins)
                    ax[0].step(bins[:-1], hist, where="post", label=ev)
                ax[0].set_xlabel("Time [s]")
                ax[0].set_ylabel("Control actions / 1s")
                ax[0].grid(alpha=0.3)
                ax[0].legend()

                totals = ctrl.groupby("event_type").size().sort_values(ascending=False)
                ax[1].bar(totals.index.astype(str), totals.values, color="#1f77b4")
                ax[1].set_ylabel("Total control actions [count]")
                ax[1].grid(axis="y", alpha=0.3)
                for lbl in ax[1].get_xticklabels():
                    lbl.set_rotation(25)
                    lbl.set_ha("right")
                p = out / "emergency_control_actions.png"
                _save(fig, p)
                created.append(p)

    risk_csv = run_dir / "artifacts" / "collision_risk" / "collision_risk_timeseries.csv"
    if risk_csv.exists():
        risk = pd.read_csv(risk_csv)
        if "time_s" in risk.columns:
            risk["time_s"] = pd.to_numeric(risk["time_s"], errors="coerce")
            if "min_gap_m" in risk.columns:
                risk["min_gap_m"] = pd.to_numeric(risk["min_gap_m"], errors="coerce")
            else:
                risk["min_gap_m"] = np.nan
            if "min_ttc_s" in risk.columns:
                risk["min_ttc_s"] = pd.to_numeric(risk["min_ttc_s"], errors="coerce")
            else:
                risk["min_ttc_s"] = np.nan
            risk = risk.dropna(subset=["time_s"])
            if not risk.empty:
                fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
                if risk["min_gap_m"].notna().any():
                    ax[0].plot(risk["time_s"], risk["min_gap_m"], label="Min gap", color="#1f77b4")
                    ax[0].axhline(2.0, color="#d62728", linestyle="--", linewidth=1, label="Risk threshold 2m")
                    ax[0].legend()
                ax[0].set_ylabel("Gap [m]")
                ax[0].grid(alpha=0.3)

                if risk["min_ttc_s"].notna().any():
                    ax[1].plot(risk["time_s"], risk["min_ttc_s"], label="Min TTC", color="#ff7f0e")
                    ax[1].axhline(1.5, color="#d62728", linestyle="--", linewidth=1, label="Risk threshold 1.5s")
                    ax[1].legend()
                ax[1].set_xlabel("Time [s]")
                ax[1].set_ylabel("TTC [s]")
                ax[1].grid(alpha=0.3)
                p = out / "emergency_risk_timeseries.png"
                _save(fig, p)
                created.append(p)

    log_file = run_dir / "v2v-emergencyVehicleAlert-nrv2x.log"
    if log_file.exists():
        rows: list[dict[str, float | str]] = []
        for line in log_file.read_text(errors="ignore").splitlines():
            row = _parse_emergency_info_line(line)
            if row:
                rows.append(row)
        if rows:
            info = pd.DataFrame(rows)
            for col in ("cam_received", "cam_dropped_app", "control_actions"):
                if col in info.columns:
                    info[col] = pd.to_numeric(info[col], errors="coerce")
                else:
                    info[col] = 0.0
            denom = info["cam_received"] + info["cam_dropped_app"]
            info["cam_drop_ratio"] = np.divide(
                info["cam_dropped_app"],
                denom,
                out=np.zeros_like(denom, dtype=float),
                where=denom > 0,
            )

            fig, ax = plt.subplots(1, 1, figsize=(7, 4))
            ax.scatter(info["cam_drop_ratio"], info["control_actions"], alpha=0.75, s=28)
            ax.set_xlabel("CAM drop ratio per vehicle [-]")
            ax.set_ylabel("Control actions per vehicle [count]")
            ax.grid(alpha=0.3)
            p = out / "emergency_drop_vs_control_actions.png"
            _save(fig, p)
            created.append(p)

    return created


SCENARIO_FUNCS = {
    "cttc-nr-v2x-demo-simple": plot_cttc,
    "nr-v2x-west-to-east-highway": plot_highway,
    "v2v-cam-exchange-sionna-nrv2x": plot_cam_sionna,
    "v2v-coexistence-80211p-nrv2x": plot_coexistence,
    "v2v-emergencyVehicleAlert-nrv2x": plot_emergency,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate scenario plots from run artifacts.")
    parser.add_argument("--run-dir", required=True, help="Path like analysis/scenario_runs/YYYY-MM-DD")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=sorted(list(SCENARIO_FUNCS.keys()) + ["all"]),
        help="Scenario to plot or 'all'",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory does not exist: {run_dir}")

    scenarios = list(SCENARIO_FUNCS.keys()) if args.scenario == "all" else [args.scenario]
    created: list[Path] = []
    for sc in scenarios:
        created.extend(SCENARIO_FUNCS[sc](run_dir))

    if created:
        manifest = run_dir / "figures" / "manifest.csv"
        _ensure_dir(manifest.parent)
        with manifest.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["scenario", "path"])
            for p in created:
                scenario = p.parent.name
                writer.writerow([scenario, str(p.relative_to(run_dir))])
        print(f"Generated {len(created)} plot(s). Manifest: {manifest}")
    else:
        print("No plots generated (missing artifacts or empty datasets).")


if __name__ == "__main__":
    main()
