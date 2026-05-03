#!/usr/bin/env python3
"""
Sionna 3D Ray-Tracing Visualizer for NEWWAY Scenario Runs

Reads vehicle positions from CAM CSVs (lat/lon → SUMO-local meters),
loads the Sionna scene, places vehicles, computes ray-traced paths,
and renders:
  1. 3D scene with ray paths (perspective view)
  2. Top-down view with ray paths
  3. Coverage / path-gain heatmap (if RadioMap available)

Designed for headless (WSL / no-GPU) usage via Mitsuba llvm backend.

Usage:
    python analysis/visualize_sionna_3d.py \
        --run-dir ~/NEWWAY_runs/2026-03-05/crash_sionna_eqm20 \
        --time-s 25.0

    # Or provide SUMO-local positions directly:
    python analysis/visualize_sionna_3d.py \
        --positions "veh2:-100,5,1.5;veh3:-60,5,1.5"
"""

import argparse
import glob
import math
import os
import sys
from pathlib import Path

# ── Mitsuba variant must be set BEFORE importing sionna ──
os.environ.setdefault("SIONNA_MI_VARIANT", "llvm_ad_mono_polarized")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import mitsuba as mi

mi.set_variant(os.environ["SIONNA_MI_VARIANT"])

import numpy as np
import tensorflow as tf

tf.get_logger().setLevel("ERROR")

from sionna.rt import (
    Camera,
    PathSolver,
    PlanarArray,
    Receiver,
    Transmitter,
    load_scene,
)

# ── SUMO coordinate helpers ──────────────────────────────────────────

# Default net-offset for Circle scenario (UTM zone 32, Turin)
NET_OFFSET_X = -394175.96
NET_OFFSET_Y = -4989734.74


def latlon_to_utm32(lat: float, lon: float):
    """WGS84 lat/lon → UTM zone 32N (x_easting, y_northing)."""
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    lon0 = 9.0  # central meridian zone 32

    lr = math.radians(lat)
    lnr = math.radians(lon)
    l0r = math.radians(lon0)

    N = a / math.sqrt(1 - e2 * math.sin(lr) ** 2)
    T = math.tan(lr) ** 2
    C = ep2 * math.cos(lr) ** 2
    A = (lnr - l0r) * math.cos(lr)

    M = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lr
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lr)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lr)
        - (35 * e2**3 / 3072) * math.sin(6 * lr)
    )

    x = (
        k0
        * N
        * (
            A
            + (1 - T + C) * A**3 / 6
            + (5 - 18 * T + T**2 + 72 * C - 58 * ep2) * A**5 / 120
        )
        + 500000
    )
    y = k0 * (
        M
        + N
        * math.tan(lr)
        * (
            A**2 / 2
            + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
            + (61 - 58 * T + T**2 + 600 * C - 330 * ep2) * A**6 / 720
        )
    )
    return x, y


def latlon_to_sumo(lat: float, lon: float):
    """lat/lon → SUMO-local meters (using net-offset)."""
    ux, uy = latlon_to_utm32(lat, lon)
    return ux + NET_OFFSET_X, uy + NET_OFFSET_Y


# ── Load vehicle positions from CAM CSVs ─────────────────────────────


def load_positions_from_cam_csvs(run_dir: Path, time_s: float):
    """
    Read CAM CSVs, find rows closest to `time_s`, return dict of
    vehicle_id → (x_sumo, y_sumo, heading_deg, speed_mps).
    """
    import csv

    pattern = str(run_dir / "artifacts" / "*-CAM.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}

    positions = {}
    for fpath in files:
        with open(fpath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            continue

        # Extract vehicle id from filename (e.g., eva-veh2-CAM.csv → veh2)
        fname = Path(fpath).stem  # e.g., eva-veh2-CAM
        parts = fname.split("-")
        veh_id = None
        for p in parts:
            if p.startswith("veh"):
                veh_id = p
                break
        if not veh_id:
            continue

        # Find the row closest to time_s (CAM timestamp is in ms)
        target_ms = time_s * 1000
        best_row = None
        best_diff = float("inf")
        for row in rows:
            ts = float(row.get("timestamp", 0))
            diff = abs(ts - target_ms)
            if diff < best_diff:
                best_diff = diff
                best_row = row

        if best_row is None:
            continue

        lat = float(best_row["latitude"])
        lon = float(best_row["longitude"])
        heading = float(best_row.get("heading", 0))
        speed = float(best_row.get("speed", 0))

        sx, sy = latlon_to_sumo(lat, lon)
        positions[veh_id] = (sx, sy, heading, speed)

    return positions


def parse_manual_positions(pos_str: str):
    """Parse 'veh2:-100,5,1.5;veh3:-60,5,1.5' → dict."""
    positions = {}
    for item in pos_str.split(";"):
        item = item.strip()
        if not item:
            continue
        name, coords = item.split(":")
        parts = [float(x) for x in coords.split(",")]
        x, y = parts[0], parts[1]
        positions[name.strip()] = (x, y, 0.0, 0.0)
    return positions


# ── Sionna scene setup ───────────────────────────────────────────────

DEFAULT_SCENE = "src/sionna/scenarios/SionnaCircleScenario/scene.xml"
ANTENNA_HEIGHT = 1.5


def setup_scene(scene_path: str, positions: dict, frequency: float = 5.89e9):
    """Load scene, place vehicles at given positions, return scene."""
    scene = load_scene(scene_path, merge_shapes_exclude_regex="car")
    scene.frequency = frequency
    scene.bandwidth = 10e6

    scene.tx_array = PlanarArray(
        num_rows=1,
        num_cols=1,
        vertical_spacing=0.5,
        horizontal_spacing=0.5,
        pattern="iso",
        polarization="V",
    )
    scene.rx_array = PlanarArray(
        num_rows=1,
        num_cols=1,
        vertical_spacing=0.5,
        horizontal_spacing=0.5,
        pattern="iso",
        polarization="V",
    )

    veh_names = sorted(positions.keys())

    for veh in veh_names:
        x, y, heading, speed = positions[veh]
        veh_num = veh.replace("veh", "")

        # Move the car mesh if it exists in the scene
        car_obj_name = f"car_{veh_num}"
        car_obj = scene.get(car_obj_name)
        if car_obj is not None:
            car_obj.position = [x, y, 0.0]
            orientation_rad = ((360 - heading) % 360 + 90) * np.pi / 180
            car_obj.orientation = [orientation_rad, 0, 0]

        # Add TX and RX antennas
        tx_name = f"tx_{veh}"
        rx_name = f"rx_{veh}"
        pos3d = [x, y, ANTENNA_HEIGHT]

        scene.add(Transmitter(tx_name, position=pos3d))
        scene.add(Receiver(rx_name, position=pos3d))

    return scene, veh_names


# ── Ray tracing & rendering ──────────────────────────────────────────


def compute_paths(scene, max_depth: int = 5):
    """Compute ray-traced paths between all TX/RX pairs."""
    solver = PathSolver()
    paths = solver(
        scene=scene,
        max_depth=max_depth,
        los=True,
        specular_reflection=True,
        diffuse_reflection=True,
        refraction=False,
        synthetic_array=True,
        seed=42,
    )
    paths.normalize_delays = False
    n_valid = int(paths.valid.numpy().sum())
    print(f"  Ray tracing complete: {n_valid} valid paths found")
    return paths


def _f(v):
    """Convert to list of Python floats (Mitsuba needs float32-compatible)."""
    return [float(x) for x in v]


def render_perspective(scene, paths, out_path: str, positions: dict):
    """Render a perspective view of the scene with ray paths."""
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    cx, cy = float(np.mean(xs)), float(np.mean(ys))

    # Camera above and behind, looking at the center of vehicles
    cam = Camera(
        position=_f([cx - 60, cy - 80, 60]),
        look_at=_f([cx, cy, 2]),
    )

    scene.render_to_file(
        camera=cam,
        paths=paths,
        filename=out_path,
        resolution=(1280, 960),
        num_samples=128,
        show_devices=True,
        show_orientations=True,
    )
    print(f"  Perspective render: {out_path}")


def render_topdown(scene, paths, out_path: str, positions: dict):
    """Render a top-down (bird's eye) view."""
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    cx, cy = float(np.mean(xs)), float(np.mean(ys))

    # Spread — how much area to show
    spread = max(
        max(xs) - min(xs), max(ys) - min(ys), 80
    )
    height = spread * 1.2

    cam = Camera(
        position=_f([cx, cy, height]),
        look_at=_f([cx, cy, 0]),
    )

    scene.render_to_file(
        camera=cam,
        paths=paths,
        filename=out_path,
        resolution=(1280, 1280),
        num_samples=128,
        show_devices=True,
    )
    print(f"  Top-down render: {out_path}")


def render_closeup_per_pair(scene, paths, out_dir: str, positions: dict):
    """Render a close-up for each TX→RX pair."""
    veh_list = sorted(positions.keys())
    if len(veh_list) < 2:
        return

    for i, tx_veh in enumerate(veh_list):
        for j, rx_veh in enumerate(veh_list):
            if i >= j:
                continue
            tx_pos = positions[tx_veh]
            rx_pos = positions[rx_veh]
            mx = (tx_pos[0] + rx_pos[0]) / 2
            my = (tx_pos[1] + rx_pos[1]) / 2
            dist = math.sqrt((tx_pos[0] - rx_pos[0]) ** 2 + (tx_pos[1] - rx_pos[1]) ** 2)

            cam = Camera(
                position=_f([mx - 30, my - 40, max(30, dist * 0.6)]),
                look_at=_f([mx, my, 1.5]),
            )

            fname = os.path.join(out_dir, f"closeup_{tx_veh}_{rx_veh}.png")
            scene.render_to_file(
                camera=cam,
                paths=paths,
                filename=fname,
                resolution=(1280, 960),
                num_samples=128,
                show_devices=True,
            )
            print(f"  Close-up {tx_veh}↔{rx_veh}: {fname}")


def compute_path_gains(paths, positions: dict):
    """Compute and print path gain for each TX→RX pair."""
    a_real, a_imag = paths.a
    coeffs = a_real.numpy() + 1j * a_imag.numpy()
    veh_list = sorted(positions.keys())

    print("\n  Path gains (ray-traced):")
    n_tx = len(veh_list)
    for tx_idx in range(n_tx):
        for rx_idx in range(n_tx):
            if tx_idx == rx_idx:
                continue
            try:
                c = coeffs[rx_idx, 0, tx_idx, 0, :]
                power = float(np.abs(np.sum(c)) ** 2)
                if power > 0:
                    pl_db = -10 * np.log10(power)
                else:
                    pl_db = float("inf")
                dist = math.sqrt(
                    (positions[veh_list[tx_idx]][0] - positions[veh_list[rx_idx]][0]) ** 2
                    + (positions[veh_list[tx_idx]][1] - positions[veh_list[rx_idx]][1]) ** 2
                )
                print(
                    f"    {veh_list[tx_idx]} → {veh_list[rx_idx]}: "
                    f"PL={pl_db:.1f} dB, dist={dist:.1f} m"
                )
            except (IndexError, ValueError):
                pass


# ── Main ─────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Sionna 3D Ray-Tracing Visualizer for NEWWAY"
    )
    parser.add_argument(
        "--run-dir",
        type=str,
        default=None,
        help="Scenario run directory with artifacts/*-CAM.csv",
    )
    parser.add_argument(
        "--time-s",
        type=float,
        default=25.0,
        help="Simulation time (s) to snapshot vehicle positions (default: 25)",
    )
    parser.add_argument(
        "--positions",
        type=str,
        default=None,
        help='Manual SUMO-local positions: "veh2:-100,5;veh3:-60,5"',
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="Path to Sionna scene.xml (auto-detected from repo root)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory for rendered images",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Max ray-tracing depth (reflections). Default: 5",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=5.89e9,
        help="Carrier frequency in Hz (default: 5.89 GHz)",
    )
    parser.add_argument(
        "--skip-closeups",
        action="store_true",
        help="Skip per-pair close-up renders (faster)",
    )
    args = parser.parse_args()

    # ── Resolve paths ──
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent  # NEWWAY repo root

    scene_path = args.scene
    if scene_path is None:
        scene_path = str(root / DEFAULT_SCENE)
    if not os.path.isfile(scene_path):
        print(f"ERROR: Scene file not found: {scene_path}", file=sys.stderr)
        sys.exit(1)

    # ── Get vehicle positions ──
    if args.positions:
        positions = parse_manual_positions(args.positions)
        print(f"Using manual positions for {len(positions)} vehicles")
    elif args.run_dir:
        run_dir = Path(args.run_dir)
        positions = load_positions_from_cam_csvs(run_dir, args.time_s)
        if not positions:
            print(
                f"ERROR: No vehicle positions found in {run_dir} at t={args.time_s}s",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Loaded {len(positions)} vehicle positions at t={args.time_s}s")
    else:
        print("ERROR: Provide --run-dir or --positions", file=sys.stderr)
        sys.exit(1)

    for veh, (x, y, h, s) in sorted(positions.items()):
        print(f"  {veh}: x={x:.1f}, y={y:.1f}, heading={h:.0f}°, speed={s:.1f} m/s")

    # ── Output directory ──
    if args.out_dir:
        out_dir = Path(args.out_dir)
    elif args.run_dir:
        out_dir = Path(args.run_dir) / "visualizations" / "sionna_3d"
    else:
        out_dir = Path("sionna_3d_output")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load scene & compute rays ──
    print(f"\nLoading Sionna scene: {scene_path}")
    scene, veh_names = setup_scene(scene_path, positions, args.frequency)
    print(f"Scene loaded: {len(scene.objects)} objects")

    print("\nComputing ray-traced paths (max_depth={})...".format(args.max_depth))
    paths = compute_paths(scene, max_depth=args.max_depth)
    compute_path_gains(paths, positions)

    # ── Render images ──
    print("\nRendering 3D views...")
    render_perspective(
        scene, paths, str(out_dir / "perspective.png"), positions
    )
    render_topdown(
        scene, paths, str(out_dir / "topdown.png"), positions
    )

    if not args.skip_closeups and len(positions) >= 2:
        render_closeup_per_pair(scene, paths, str(out_dir), positions)

    # ── Summary ──
    print(f"\nAll renders saved to: {out_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
