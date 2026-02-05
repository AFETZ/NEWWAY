#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--point-id", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--scenario", default="v2v-emergencyVehicleAlert-nrv2x")
    p.add_argument("--sim-time", type=float, default=30.0)
    p.add_argument("--rng-run", type=int, default=1)
    p.add_argument("--sumo-gui", type=str, default="0")
    p.add_argument("--sumo-updates", type=str, default="0.01")
    p.add_argument("--penetrationRate", type=str, default="0.7")
    p.add_argument("--txPower", type=str, default=None)
    p.add_argument("--mcs", type=str, default=None)
    p.add_argument("--enableSensing", type=str, default=None)
    p.add_argument("--slThresPsschRsrp", type=str, default=None)
    p.add_argument("--enableChannelRandomness", type=str, default=None)
    p.add_argument("--channelUpdatePeriod", type=str, default=None)
    p.add_argument("--sumo-folder", type=str, default="src/automotive/examples/sumo_files_v2v_map/")
    p.add_argument("--mob-trace", type=str, default="cars.rou.xml")
    p.add_argument("--sumo-config", type=str, default="src/automotive/examples/sumo_files_v2v_map/map.sumo.cfg")
    p.add_argument("--extra-arg", action="append", default=[])
    return p.parse_args()


def git_hash() -> str:
    try:
        repo_root = Path(__file__).resolve().parents[2]
        out = subprocess.check_output([
            "git",
            "-c",
            f"safe.directory={repo_root}",
            "-C",
            str(repo_root),
            "rev-parse",
            "HEAD",
        ])
        return out.decode().strip()
    except Exception:
        return "unknown"


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    run_prefix = out_dir / "eva_nrv2x"
    log_path = out_dir / "run.log"

    binary = Path("build/src/automotive/examples/ns3-dev-v2v-emergencyVehicleAlert-nrv2x-optimized")
    if not binary.exists():
        raise SystemExit(f"Missing binary: {binary}")

    cmd = [
        str(binary),
        f"--sumo-gui={args.sumo_gui}",
        f"--sim-time={args.sim_time}",
        f"--csv-log={run_prefix}",
        f"--RngRun={args.rng_run}",
        f"--sumo-updates={args.sumo_updates}",
        f"--penetrationRate={args.penetrationRate}",
        f"--sumo-folder={args.sumo_folder}",
        f"--mob-trace={args.mob_trace}",
        f"--sumo-config={args.sumo_config}",
    ]

    for name in ["txPower", "mcs", "enableSensing", "slThresPsschRsrp", "enableChannelRandomness", "channelUpdatePeriod"]:
        val = getattr(args, name)
        if val is not None:
            cmd.append(f"--{name}={val}")

    for extra in args.extra_arg:
        cmd.append(extra)

    start_time = time.time()
    with log_path.open("w") as log:
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    end_time = time.time()

    meta = {
        "run_id": args.point_id,
        "scenario": args.scenario,
        "out_dir": str(out_dir),
        "command": cmd,
        "git_hash": git_hash(),
        "start_time_epoch": start_time,
        "end_time_epoch": end_time,
        "exit_code": proc.returncode,
        "sim_time": args.sim_time,
        "rng_run": args.rng_run,
        "sumo_gui": args.sumo_gui,
        "sumo_updates": args.sumo_updates,
        "penetrationRate": args.penetrationRate,
        "txPower": args.txPower,
        "mcs": args.mcs,
        "enableSensing": args.enableSensing,
        "slThresPsschRsrp": args.slThresPsschRsrp,
        "enableChannelRandomness": args.enableChannelRandomness,
        "channelUpdatePeriod": args.channelUpdatePeriod,
    }

    with (out_dir / "metadata.json").open("w") as fp:
        json.dump(meta, fp, indent=2)

    if proc.returncode != 0:
        raise SystemExit(f"Run failed with exit code {proc.returncode}. See {log_path}")


if __name__ == "__main__":
    main()
