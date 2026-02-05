#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import os
import re
import subprocess
from pathlib import Path

from bootstrap import ensure_deps

ensure_deps(["yaml"])

import yaml


def slugify(s: str) -> str:
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-]+", "", s)
    return s


def load_config(path: Path) -> dict:
    with path.open() as fp:
        return yaml.safe_load(fp)


def build_points(cfg: dict) -> list[dict]:
    if "sweep_points" in cfg:
        return cfg["sweep_points"]
    if "sweep" not in cfg:
        return []
    sweep = cfg["sweep"]
    keys = list(sweep.keys())
    values = [sweep[k] for k in keys]
    points = []
    for combo in itertools.product(*values):
        point = {k: v for k, v in zip(keys, combo)}
        points.append(point)
    return points


def main() -> None:
    cfg_path = Path("analysis/mode2_loss/sweep_config.yaml")
    cfg = load_config(cfg_path)

    base_args = cfg.get("base_args", [])
    sim_time = cfg.get("sim_time_s", 30)
    rng_run = cfg.get("rng_run", 1)
    sumo_gui = cfg.get("sumo_gui", 0)
    sumo_updates = cfg.get("sumo_updates", 0.01)
    penetrationRate = cfg.get("penetrationRate", 0.7)
    scenario = cfg.get("scenario", "v2v-emergencyVehicleAlert-nrv2x")

    points = build_points(cfg)
    if not points:
        raise SystemExit("No sweep points defined in sweep_config.yaml")

    out_root = Path("analysis/mode2_loss/data/sweep")
    out_root.mkdir(parents=True, exist_ok=True)

    for idx, point in enumerate(points):
        point_id = point.get("id")
        if not point_id:
            parts = [f"{k}-{point[k]}" for k in sorted(point.keys())]
            point_id = slugify("_".join(parts))
        point_dir = out_root / point_id
        point_dir.mkdir(parents=True, exist_ok=True)
        meta_path = point_dir / "metadata.json"

        cmd = [
            "python3",
            "analysis/mode2_loss/run_one.py",
            "--point-id",
            point_id,
            "--out-dir",
            str(point_dir),
            "--scenario",
            scenario,
            "--sim-time",
            str(sim_time),
            "--rng-run",
            str(rng_run),
            "--sumo-gui",
            str(sumo_gui),
            "--sumo-updates",
            str(sumo_updates),
            "--penetrationRate",
            str(penetrationRate),
        ]

        for k in ["txPower", "mcs", "enableSensing", "slThresPsschRsrp", "enableChannelRandomness", "channelUpdatePeriod"]:
            if k in point:
                cmd.extend([f"--{k}", str(point[k])])

        for extra in base_args:
            cmd.extend(["--extra-arg", extra])

        def norm(val):
            if isinstance(val, bool):
                return "true" if val else "false"
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                low = val.lower()
                if low in ("true", "false"):
                    return low
                try:
                    return float(val)
                except Exception:
                    return val
            return str(val)

        if meta_path.exists():
            try:
                with meta_path.open() as fp:
                    meta = json.load(fp)
                if meta.get("exit_code") == 0:
                    matches = True
                    for k in ["txPower", "mcs", "enableSensing", "slThresPsschRsrp", "enableChannelRandomness", "channelUpdatePeriod"]:
                        if norm(meta.get(k)) != norm(point.get(k)):
                            matches = False
                            break
                    if norm(meta.get("sim_time")) != norm(sim_time):
                        matches = False
                    if norm(meta.get("rng_run")) != norm(rng_run):
                        matches = False
                    if norm(meta.get("sumo_gui")) != norm(sumo_gui):
                        matches = False
                    if norm(meta.get("sumo_updates")) != norm(sumo_updates):
                        matches = False
                    if norm(meta.get("penetrationRate")) != norm(penetrationRate):
                        matches = False
                    if matches:
                        print(f"[SKIP] {idx+1}/{len(points)} -> {point_id} (metadata up-to-date)")
                        continue
            except Exception:
                pass

        print(f"[SWEEP] {idx+1}/{len(points)} -> {point_id}")
        subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
