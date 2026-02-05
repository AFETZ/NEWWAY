#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

from bootstrap import ensure_deps

ensure_deps()

import pandas as pd
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Input file or directory")
    p.add_argument("--out", required=True, help="Output directory")
    p.add_argument("--emergency-tx-id", type=int, default=2, help="Emergency vehicle stationId (default: 2)")
    return p.parse_args()


def extract_sweep_point_id(path: Path) -> Optional[str]:
    parts = path.parts
    if "sweep" in parts:
        idx = parts.index("sweep")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def parse_run_id(path: Path) -> str:
    point_id = extract_sweep_point_id(path)
    if point_id:
        return point_id
    name = path.stem
    for token in ["-veh", "-server", "-sinr_ni", "-phy_with", "-prr_with", "-MSG", "-CAM"]:
        if token in name:
            return name.split(token)[0]
    return name


def infer_tech(run_id: str) -> str:
    rid = run_id.lower()
    if "80211p" in rid:
        return "80211p"
    if "nrv2x" in rid:
        return "nrv2x"
    if "cv2x" in rid or "ltev2x" in rid:
        return "cv2x"
    if "lte" in rid:
        return "lte"
    return "unknown"


def load_sweep_ids(in_path: Path) -> Optional[Set[str]]:
    if not in_path.is_dir():
        return None
    if "sweep" not in in_path.parts:
        return None
    cfg_path = Path("analysis/mode2_loss/sweep_config.yaml")
    if not cfg_path.exists():
        return None
    try:
        import yaml
        with cfg_path.open() as fp:
            cfg = yaml.safe_load(fp) or {}
        points = cfg.get("sweep_points", [])
        ids = {p.get("id") for p in points if isinstance(p, dict) and p.get("id")}
        return ids or None
    except Exception:
        return None


def col(df: pd.DataFrame, name: str):
    for c in df.columns:
        if c.lower() == name.lower():
            return df[c]
    return None


def detect_type(df: pd.DataFrame, fname: str) -> str:
    cols = {c.lower() for c in df.columns}
    if {"messageid", "camid", "timestamp", "latitude", "longitude", "heading", "speed", "acceleration"}.issubset(cols):
        return "cam_state"
    if {"messageid", "originatingstationid", "sequence", "referencetime", "detectiontime", "stationid"}.issubset(cols):
        return "asa_event"
    if {"vehicle_id", "msg_seq", "tx_t_s", "rx_t_s", "rx_ok", "msg_type"}.issubset(cols):
        return "msg_log"
    if {"tx_id", "rx_id", "distance", "rssi", "snr"}.issubset(cols):
        return "sionna_phy"
    if {"node_id", "prr"}.issubset(cols):
        return "sionna_prr"
    if {"time", "rx", "tx", "rx_lat", "rx_lon", "tx_lat", "tx_lon", "technology", "distance", "los", "sinr"}.issubset(cols):
        return "coexistence_phy"
    return "unknown"


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return r * c


def compute_behavior_metrics(df_vs: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    metrics = []
    for (run_id, tech, vehicle_id), g in df_vs.groupby(["run_id", "tech", "vehicle_id"], dropna=False):
        g = g.sort_values("t_s")
        t = g["t_s"].to_numpy()
        speed = g["speed_mps"].to_numpy()
        accel = g["accel_mps2"].to_numpy()
        lat = g["lat"].to_numpy()
        lon = g["lon"].to_numpy()

        min_speed = np.nanmin(speed) if len(speed) else np.nan
        max_decel = np.nanmin(accel) if len(accel) else np.nan

        # jerk
        jerk = np.array([])
        if len(t) > 1:
            dt = np.diff(t)
            da = np.diff(accel)
            with np.errstate(divide="ignore", invalid="ignore"):
                jerk = np.where(dt > 0, da / dt, np.nan)
        max_abs_jerk = np.nanmax(np.abs(jerk)) if jerk.size else np.nan
        mean_abs_jerk = np.nanmean(np.abs(jerk)) if jerk.size else np.nan

        # braking event by accel
        brake_t_accel = np.nan
        if len(t) > 1:
            mask = accel <= -2.0
            start = None
            for i in range(len(t)):
                if mask[i] and start is None:
                    start = t[i]
                if (not mask[i] or i == len(t) - 1) and start is not None:
                    end = t[i] if not mask[i] else t[i]
                    if end - start >= 0.2:
                        brake_t_accel = start
                        break
                    start = None

        # braking event by speed drop >= 2 m/s within 1s
        brake_t_speed = np.nan
        if len(t) > 1:
            j = 0
            for i in range(len(t)):
                while j < len(t) and t[j] - t[i] <= 1.0:
                    j += 1
                window = speed[i:j]
                if window.size and (speed[i] - np.nanmin(window)) >= 2.0:
                    brake_t_speed = t[i]
                    break

        brake_times = [x for x in [brake_t_accel, brake_t_speed] if not np.isnan(x)]
        time_to_first_brake = min(brake_times) if brake_times else np.nan

        # path length
        path_len = np.nan
        if len(lat) > 1:
            path_len = np.nansum(haversine_m(lat[:-1], lon[:-1], lat[1:], lon[1:]))

        # stop count (speed < 0.5 m/s for >= 1 s)
        stop_count = 0
        if len(t) > 1:
            mask = speed < 0.5
            start = None
            for i in range(len(t)):
                if mask[i] and start is None:
                    start = t[i]
                if (not mask[i] or i == len(t) - 1) and start is not None:
                    end = t[i] if not mask[i] else t[i]
                    if end - start >= 1.0:
                        stop_count += 1
                    start = None

        metrics.append({
            "run_id": run_id,
            "tech": tech,
            "vehicle_id": vehicle_id,
            "min_speed": min_speed,
            "max_decel": max_decel,
            "time_to_first_brake": time_to_first_brake,
            "max_abs_jerk": max_abs_jerk,
            "mean_abs_jerk": mean_abs_jerk,
            "path_length_m": path_len,
            "stop_count": stop_count,
        })

    metrics_df = pd.DataFrame(metrics)

    # Run-level aggregates
    agg = []
    if not metrics_df.empty:
        for (run_id, tech), g in metrics_df.groupby(["run_id", "tech"], dropna=False):
            def q(x, p):
                return np.nanpercentile(x, p) if np.isfinite(x).any() else np.nan
            agg.append({
                "run_id": run_id,
                "tech": tech,
                "vehicles": len(g),
                "min_speed_median": np.nanmedian(g["min_speed"]),
                "min_speed_p10": q(g["min_speed"].to_numpy(), 10),
                "min_speed_p90": q(g["min_speed"].to_numpy(), 90),
                "max_decel_median": np.nanmedian(g["max_decel"]),
                "max_decel_p10": q(g["max_decel"].to_numpy(), 10),
                "max_decel_p90": q(g["max_decel"].to_numpy(), 90),
                "time_to_first_brake_median": np.nanmedian(g["time_to_first_brake"]),
                "time_to_first_brake_p10": q(g["time_to_first_brake"].to_numpy(), 10),
                "time_to_first_brake_p90": q(g["time_to_first_brake"].to_numpy(), 90),
                "stop_count_mean": np.nanmean(g["stop_count"]),
            })
    agg_df = pd.DataFrame(agg)
    return metrics_df, agg_df


def compute_comm_metrics(df_msg: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df_msg.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df = df_msg.copy()
    df["rx_ok"] = pd.to_numeric(df["rx_ok"], errors="coerce").fillna(0).astype(int)
    df["tx_t_s"] = pd.to_numeric(df["tx_t_s"], errors="coerce")
    df["rx_t_s"] = pd.to_numeric(df["rx_t_s"], errors="coerce")

    tx = df[df["rx_ok"] == 0].copy()
    rx = df[df["rx_ok"] == 1].copy()

    # PRR per receiver: received / expected (all tx excluding self)
    tx_total = tx.groupby(["run_id", "tech"], dropna=False).size().rename("sent_total")
    tx_by_sender = tx.groupby(["run_id", "tech", "tx_id"], dropna=False).size().rename("sent_by_sender")
    rx_by_receiver = rx.groupby(["run_id", "tech", "rx_id"], dropna=False).size().rename("received")

    prr_rows = []
    idx_vehicle = set(tx_by_sender.index) | set(rx_by_receiver.index)
    for run_id, tech, veh_id in idx_vehicle:
        sent_total = tx_total.get((run_id, tech), 0)
        sent_self = tx_by_sender.get((run_id, tech, veh_id), 0)
        expected = sent_total - sent_self
        received = rx_by_receiver.get((run_id, tech, veh_id), 0)
        prr_rows.append({
            "run_id": run_id,
            "tech": tech,
            "vehicle_id": veh_id,
            "sent": expected,
            "received": received,
            "prr": (received / expected) if expected > 0 else np.nan,
            "msg_type": "CAM",
        })
    prr = pd.DataFrame(prr_rows)

    # Run-level PRR
    run_prr = prr.groupby(["run_id", "tech"], dropna=False).agg({"sent": "sum", "received": "sum"}).reset_index()
    run_prr["prr"] = run_prr.apply(lambda r: r["received"] / r["sent"] if r["sent"] > 0 else np.nan, axis=1)

    # AoI per receiver
    aoi_rows = []
    for (run_id, tech, rx_id), g in rx.groupby(["run_id", "tech", "rx_id"], dropna=False):
        g = g.sort_values("rx_t_s")
        t = g["rx_t_s"].dropna().to_numpy()
        if t.size < 2:
            continue
        aoi = np.diff(t)
        aoi_rows.append({
            "run_id": run_id,
            "tech": tech,
            "vehicle_id": rx_id,
            "aoi_mean_s": float(np.nanmean(aoi)),
            "aoi_p95_s": float(np.nanpercentile(aoi, 95)),
            "aoi_max_s": float(np.nanmax(aoi)),
        })
    aoi_df = pd.DataFrame(aoi_rows)

    # Latency (best-effort match by tx_id+msg_seq)
    lat_rows = []
    if not tx.empty and not rx.empty and "msg_seq" in df.columns:
        key_cols = ["run_id", "tech", "tx_id", "msg_seq"]
        tx_key = tx[key_cols + ["tx_t_s"]].dropna(subset=["tx_t_s"]).copy()
        rx_key = rx[key_cols + ["rx_t_s"]].dropna(subset=["rx_t_s"]).copy()
        merged = rx_key.merge(tx_key, on=key_cols, how="left")
        merged["latency_s"] = merged["rx_t_s"] - merged["tx_t_s"]
        merged = merged[(merged["latency_s"] >= 0) & (merged["latency_s"] < 10)]
        for (run_id, tech), g in merged.groupby(["run_id", "tech"], dropna=False):
            lat_rows.append({
                "run_id": run_id,
                "tech": tech,
                "latency_mean_s": float(np.nanmean(g["latency_s"])),
                "latency_p95_s": float(np.nanpercentile(g["latency_s"], 95)),
                "latency_max_s": float(np.nanmax(g["latency_s"])),
                "latency_samples": int(len(g)),
            })
    latency_df = pd.DataFrame(lat_rows)

    return prr, run_prr, aoi_df, latency_df


def compute_reaction_metrics(df_msg: pd.DataFrame, emergency_tx_id: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if df_msg.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df_msg.copy()
    df["rx_ok"] = pd.to_numeric(df["rx_ok"], errors="coerce").fillna(0).astype(int)
    df["tx_id"] = pd.to_numeric(df["tx_id"], errors="coerce")
    df["rx_id"] = pd.to_numeric(df["rx_id"], errors="coerce")
    df["rx_t_s"] = pd.to_numeric(df["rx_t_s"], errors="coerce")

    rx = df[(df["rx_ok"] == 1) & (df["tx_id"] == emergency_tx_id)].copy()
    if rx.empty:
        return pd.DataFrame(), pd.DataFrame()

    first_rx = rx.groupby(["run_id", "tech", "rx_id"], dropna=False)["rx_t_s"].min().reset_index()
    first_rx = first_rx.rename(columns={"rx_id": "vehicle_id", "rx_t_s": "reaction_delay_s"})

    # Build full vehicle list per run/tech (exclude the emergency vehicle itself)
    rows = []
    for (run_id, tech), g in df.groupby(["run_id", "tech"], dropna=False):
        ids = pd.unique(pd.concat([g["tx_id"], g["rx_id"]], ignore_index=True).dropna())
        for vid in ids:
            if int(vid) == int(emergency_tx_id):
                continue
            delay = first_rx.loc[(first_rx["run_id"] == run_id) & (first_rx["tech"] == tech) & (first_rx["vehicle_id"] == vid), "reaction_delay_s"]
            rows.append({
                "run_id": run_id,
                "tech": tech,
                "vehicle_id": vid,
                "reaction_delay_s": float(delay.iloc[0]) if len(delay) else np.nan,
            })

    reaction_vehicle_df = pd.DataFrame(rows)

    agg = []
    if not reaction_vehicle_df.empty:
        for (run_id, tech), g in reaction_vehicle_df.groupby(["run_id", "tech"], dropna=False):
            vals = g["reaction_delay_s"].dropna().to_numpy()
            received_frac = float(np.mean(np.isfinite(g["reaction_delay_s"]))) if len(g) else np.nan
            if vals.size:
                agg.append({
                    "run_id": run_id,
                    "tech": tech,
                    "reaction_delay_median": float(np.nanmedian(vals)),
                    "reaction_delay_p10": float(np.nanpercentile(vals, 10)),
                    "reaction_delay_p90": float(np.nanpercentile(vals, 90)),
                    "reaction_received_frac": received_frac,
                })
    reaction_run_df = pd.DataFrame(agg)
    return reaction_vehicle_df, reaction_run_df


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = []
    if in_path.is_file():
        files = [in_path]
    else:
        files = sorted([p for p in in_path.rglob("*.csv")])
    sweep_ids = load_sweep_ids(in_path)

    vehicle_state_rows: List[Dict] = []
    comm_stats_rows: List[Dict] = []
    sionna_phy_rows: List[Dict] = []
    coexistence_phy_rows: List[Dict] = []
    msg_log_rows: List[Dict] = []

    # Metadata JSON in sweep runs
    metadata_rows: List[Dict] = []
    for meta in in_path.rglob("metadata.json"):
        try:
            with meta.open() as fp:
                data = json.load(fp)
            data["metadata_path"] = str(meta)
            metadata_rows.append(data)
        except Exception:
            continue
    run_id_to_tech: Dict[str, str] = {}
    for data in metadata_rows:
        run_id = data.get("run_id")
        scenario = str(data.get("scenario", ""))
        tech = infer_tech(scenario)
        if run_id and tech != "unknown":
            run_id_to_tech[run_id] = tech

    for f in files:
        point_id = extract_sweep_point_id(f)
        if sweep_ids is not None and point_id and point_id not in sweep_ids:
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        run_id = parse_run_id(f)
        tech = infer_tech(run_id)
        if run_id in run_id_to_tech:
            tech = run_id_to_tech[run_id]
        ftype = detect_type(df, f.name)

        if ftype == "cam_state":
            msg_id = col(df, "messageId")
            cam_id = col(df, "camId")
            ts = col(df, "timestamp")
            lat = col(df, "latitude")
            lon = col(df, "longitude")
            heading = col(df, "heading")
            speed = col(df, "speed")
            accel = col(df, "acceleration")
            vehicle_id = None
            if cam_id is not None:
                vehicle_id = cam_id
            for i in range(len(df)):
                vehicle_state_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "vehicle_id": str(vehicle_id.iloc[i]) if vehicle_id is not None else None,
                    "timestamp_ms": float(ts.iloc[i]) if ts is not None else np.nan,
                    "lat": float(lat.iloc[i]) if lat is not None else np.nan,
                    "lon": float(lon.iloc[i]) if lon is not None else np.nan,
                    "heading_deg": float(heading.iloc[i]) if heading is not None else np.nan,
                    "speed_mps": float(speed.iloc[i]) if speed is not None else np.nan,
                    "accel_mps2": float(accel.iloc[i]) if accel is not None else np.nan,
                    "source_camId": str(cam_id.iloc[i]) if cam_id is not None else None,
                    "message_id": str(msg_id.iloc[i]) if msg_id is not None else None,
                })

        elif ftype == "asa_event":
            # Treat as comm events (no position info)
            st_id = col(df, "stationID")
            det_t = col(df, "detectionTime")
            ref_t = col(df, "referenceTime")
            for i in range(len(df)):
                t_raw = det_t.iloc[i] if det_t is not None else (ref_t.iloc[i] if ref_t is not None else np.nan)
                comm_stats_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "vehicle_id": str(st_id.iloc[i]) if st_id is not None else None,
                    "t_s": float(t_raw) / 1000.0 if pd.notna(t_raw) else np.nan,
                    "msg_type": "ASA",
                    "sent": 0,
                    "received": 1,
                    "prr": np.nan,
                })

        elif ftype == "msg_log":
            for _, row in df.iterrows():
                msg_log_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "vehicle_id": row.get("vehicle_id"),
                    "msg_seq": row.get("msg_seq"),
                    "tx_t_s": row.get("tx_t_s"),
                    "rx_t_s": row.get("rx_t_s"),
                    "rx_ok": row.get("rx_ok"),
                    "msg_type": row.get("msg_type"),
                    "tx_id": row.get("tx_id"),
                    "rx_id": row.get("rx_id"),
                    "cam_gdt_ms": row.get("cam_gdt_ms"),
                })

        elif ftype == "sionna_phy":
            for _, row in df.iterrows():
                sionna_phy_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "tx_id": row.get("tx_id"),
                    "rx_id": row.get("rx_id"),
                    "distance": row.get("distance"),
                    "rssi": row.get("rssi"),
                    "snr": row.get("snr"),
                })

        elif ftype == "sionna_prr":
            for _, row in df.iterrows():
                comm_stats_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "vehicle_id": row.get("node_id"),
                    "t_s": np.nan,
                    "msg_type": "sionna_prr",
                    "sent": np.nan,
                    "received": np.nan,
                    "prr": row.get("prr"),
                })

        elif ftype == "coexistence_phy":
            t_raw = df["time"].astype(float)
            # heuristic: if time is large, assume microseconds
            t_s = np.where(t_raw > 1e5, t_raw / 1e6, t_raw / 1000.0)
            for i, row in df.iterrows():
                coexistence_phy_rows.append({
                    "run_id": run_id,
                    "tech": tech,
                    "t_s": float(t_s[i]),
                    "rx": row.get("rx"),
                    "tx": row.get("tx"),
                    "rx_lat": row.get("rx_lat"),
                    "rx_lon": row.get("rx_lon"),
                    "tx_lat": row.get("tx_lat"),
                    "tx_lon": row.get("tx_lon"),
                    "technology": row.get("technology"),
                    "distance": row.get("distance"),
                    "los": row.get("los"),
                    "sinr": row.get("sinr"),
                })

    df_vs = pd.DataFrame(vehicle_state_rows)
    if not df_vs.empty:
        df_vs["timestamp_ms"] = pd.to_numeric(df_vs["timestamp_ms"], errors="coerce")
        df_vs["t_s"] = df_vs.groupby(["run_id", "vehicle_id"], dropna=False)["timestamp_ms"].transform(
            lambda s: (s - s.min()) / 1000.0
        )

    df_msg = pd.DataFrame(msg_log_rows)

    behavior_vehicle_df, behavior_run_df = compute_behavior_metrics(df_vs) if not df_vs.empty else (pd.DataFrame(), pd.DataFrame())

    comm_vehicle_df, comm_run_df, aoi_vehicle_df, latency_run_df = compute_comm_metrics(df_msg) if not df_msg.empty else (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    reaction_vehicle_df, reaction_run_df = compute_reaction_metrics(df_msg, args.emergency_tx_id) if not df_msg.empty else (pd.DataFrame(), pd.DataFrame())

    df_comm_stats = pd.DataFrame(comm_stats_rows)
    df_sionna_phy = pd.DataFrame(sionna_phy_rows)
    df_coexistence_phy = pd.DataFrame(coexistence_phy_rows)
    df_meta = pd.DataFrame(metadata_rows)

    # Write outputs
    if not df_vs.empty:
        df_vs.to_csv(out_dir / "vehicle_state.csv", index=False)
    if not df_comm_stats.empty:
        df_comm_stats.to_csv(out_dir / "comm_stats.csv", index=False)
    if not df_sionna_phy.empty:
        df_sionna_phy.to_csv(out_dir / "sionna_phy.csv", index=False)
    if not df_coexistence_phy.empty:
        df_coexistence_phy.to_csv(out_dir / "coexistence_phy.csv", index=False)
    if not df_msg.empty:
        df_msg.to_csv(out_dir / "msg_log.csv", index=False)
    if not behavior_vehicle_df.empty:
        behavior_vehicle_df.to_csv(out_dir / "behavior_metrics_vehicle.csv", index=False)
    if not behavior_run_df.empty:
        behavior_run_df.to_csv(out_dir / "behavior_metrics_run.csv", index=False)
    if not comm_vehicle_df.empty:
        comm_vehicle_df.to_csv(out_dir / "comm_metrics_vehicle.csv", index=False)
    if not comm_run_df.empty:
        comm_run_df.to_csv(out_dir / "comm_metrics_run.csv", index=False)
    if not aoi_vehicle_df.empty:
        aoi_vehicle_df.to_csv(out_dir / "aoi_metrics_vehicle.csv", index=False)
    if not latency_run_df.empty:
        latency_run_df.to_csv(out_dir / "latency_metrics_run.csv", index=False)
    if not reaction_vehicle_df.empty:
        reaction_vehicle_df.to_csv(out_dir / "reaction_metrics_vehicle.csv", index=False)
    if not reaction_run_df.empty:
        reaction_run_df.to_csv(out_dir / "reaction_metrics_run.csv", index=False)
    if not df_meta.empty:
        df_meta.to_csv(out_dir / "run_metadata.csv", index=False)


if __name__ == "__main__":
    main()
