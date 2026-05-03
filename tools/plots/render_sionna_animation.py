#!/usr/bin/env python3
"""
Sionna 3D Ray-Tracing Animation Renderer for NEWWAY

Renders per-frame images from a completed scenario run, then stitches
them into a GIF (or MP4). Similar to Chartist/Sionna_SUMO_simu but uses
offline CAM CSV data instead of live SUMO/TraCI.

For each simulation timestep:
  1. Read vehicle positions from CAM CSVs (lat/lon → SUMO-local)
  2. Place low-poly car meshes + TX/RX antennas in Sionna scene
  3. Compute ray-traced paths between all vehicle pairs
  4. Render frame to PNG via Mitsuba (headless, CPU)
  5. Remove vehicles from scene (clean slate for next frame)

Finally, assembles all PNGs into an animated GIF.

Usage:
    SIONNA_MI_VARIANT=llvm_ad_mono_polarized .venv_sionna/bin/python \\
        analysis/render_sionna_animation.py \\
        --run-dir ~/NEWWAY_runs/2026-03-05/crash_sionna_eqm20 \\
        --fps 5

    # Limit frame range:
    ... --t-start 5 --t-end 18

    # Fixed camera:
    ... --camera fixed --cam-pos="-80,-120,80" --cam-look="-60,-60,2"
"""

import argparse
import csv
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

import sionna.rt
from sionna.rt import (
    Camera,
    ITURadioMaterial,
    PathSolver,
    PlanarArray,
    Receiver,
    SceneObject,
    Transmitter,
    load_scene,
)

# ── Constants ────────────────────────────────────────────────────────

NET_OFFSET_X = -394175.96
NET_OFFSET_Y = -4989734.74
ANTENNA_HEIGHT = 1.5
DEFAULT_SCENE = "src/sionna/scenarios/SionnaCircleScenario/scene.xml"


# ── Coordinate conversion ────────────────────────────────────────────

def latlon_to_utm32(lat: float, lon: float):
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    lon0 = 9.0
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
    x = k0 * N * (A + (1 - T + C) * A**3 / 6
                   + (5 - 18 * T + T**2 + 72 * C - 58 * ep2) * A**5 / 120) + 500000
    y = k0 * (M + N * math.tan(lr) * (
        A**2 / 2 + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
        + (61 - 58 * T + T**2 + 600 * C - 330 * ep2) * A**6 / 720))
    return x, y


def latlon_to_sumo(lat, lon):
    ux, uy = latlon_to_utm32(lat, lon)
    return ux + NET_OFFSET_X, uy + NET_OFFSET_Y


def _f(v):
    """Python float list for Mitsuba."""
    return [float(x) for x in v]


# ── Load all CAM data as timeline ────────────────────────────────────

def load_cam_timeline(run_dir: Path):
    """
    Returns dict: veh_id → list of dicts sorted by time,
    each dict has keys: time_s, x, y, heading, speed.

    CAM CSV files are named per *receiver* (e.g. eva-veh2-CAM.csv),
    but each row's `camId` field identifies the *sender* whose position
    is reported.  We key the timeline by sender ("veh{camId}").
    """
    pattern = str(run_dir / "artifacts" / "*-CAM.csv")
    files = sorted(glob.glob(pattern))
    timeline = {}  # veh_id → unsorted list

    for fpath in files:
        with open(fpath) as f:
            for row in csv.DictReader(f):
                cam_id = row.get("camId")
                if cam_id is None:
                    continue
                veh_id = f"veh{cam_id}"

                ts = float(row["timestamp"]) / 1000.0
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                heading = float(row.get("heading", 0))
                speed = float(row.get("speed", 0))
                sx, sy = latlon_to_sumo(lat, lon)

                timeline.setdefault(veh_id, []).append(
                    dict(time_s=ts, x=sx, y=sy, heading=heading, speed=speed)
                )

    # De-duplicate (same camId may appear in multiple receiver files)
    for veh_id in timeline:
        seen = set()
        deduped = []
        for e in timeline[veh_id]:
            key = (round(e["time_s"], 4), round(e["x"], 2), round(e["y"], 2))
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        deduped.sort(key=lambda e: e["time_s"])
        timeline[veh_id] = deduped

    return timeline


def interpolate_position(entries, t):
    """Linear interpolation of vehicle position at time t."""
    if not entries:
        return None
    if t <= entries[0]["time_s"]:
        return entries[0]
    if t >= entries[-1]["time_s"]:
        return entries[-1]
    for i in range(len(entries) - 1):
        t0 = entries[i]["time_s"]
        t1 = entries[i + 1]["time_s"]
        if t0 <= t <= t1:
            alpha = (t - t0) / (t1 - t0) if t1 > t0 else 0
            e0, e1 = entries[i], entries[i + 1]
            return dict(
                time_s=t,
                x=e0["x"] + alpha * (e1["x"] - e0["x"]),
                y=e0["y"] + alpha * (e1["y"] - e0["y"]),
                heading=e0["heading"] + alpha * (e1["heading"] - e0["heading"]),
                speed=e0["speed"] + alpha * (e1["speed"] - e0["speed"]),
            )
    return entries[-1]


# Scene bounding box for SionnaCircleScenario
SCENE_BBOX = {"x_min": -150, "x_max": 200, "y_min": -115, "y_max": 10}


def get_positions_at_time(timeline, t, scene_filter=False):
    """Get all vehicle positions at time t (interpolated).
    If scene_filter=True, only return vehicles within the Sionna scene bounds."""
    positions = {}
    for veh_id, entries in timeline.items():
        # Only include vehicle if it exists at this time
        if entries and entries[0]["time_s"] <= t <= entries[-1]["time_s"]:
            e = interpolate_position(entries, t)
            if e:
                if scene_filter:
                    if not (SCENE_BBOX["x_min"] <= e["x"] <= SCENE_BBOX["x_max"]
                            and SCENE_BBOX["y_min"] <= e["y"] <= SCENE_BBOX["y_max"]):
                        continue
                positions[veh_id] = (e["x"], e["y"], e["heading"], e["speed"])
    return positions


# ── Per-frame scene update (à la Chartist) ───────────────────────────

def _closest_pairs(positions, max_pairs):
    """Return up to max_pairs (tx_veh, rx_veh) sorted by distance."""
    veh_list = sorted(positions.keys())
    pairs = []
    for i in range(len(veh_list)):
        for j in range(i + 1, len(veh_list)):
            vi, vj = veh_list[i], veh_list[j]
            d = math.sqrt((positions[vi][0] - positions[vj][0]) ** 2
                          + (positions[vi][1] - positions[vj][1]) ** 2)
            pairs.append((d, vi, vj))
    pairs.sort()
    result = []
    for d, vi, vj in pairs[:max_pairs]:
        result.append((vi, vj))
        result.append((vj, vi))
    return result


def frame_handler(scene, positions, car_material, solver, max_depth,
                  cam, out_path, resolution, max_pairs=10):
    """
    Single-frame render cycle:
    1. Add car meshes + TX/RX
    2. Compute ray-traced paths (up to max_pairs closest links)
    3. Render to file
    4. Remove everything (clean for next frame)
    """
    veh_list = sorted(positions.keys())
    if not veh_list:
        return None

    # Add low-poly car meshes
    cars = []
    for veh in veh_list:
        x, y, heading, speed = positions[veh]
        car = SceneObject(
            fname=sionna.rt.scene.low_poly_car,
            name=f"car_mesh_{veh}",
            radio_material=car_material,
        )
        cars.append(car)

    scene.edit(add=cars)

    # Position cars and add TX/RX antennas
    for i, veh in enumerate(veh_list):
        x, y, heading, speed = positions[veh]
        cars[i].position = mi.Point3f(float(x), float(y), float(1.0))
        angle_rad = float(((360 - heading) % 360 + 90) * np.pi / 180)
        cars[i].orientation = mi.Point3f(angle_rad, 0.0, 0.0)
        cars[i].scaling = mi.Float(2.5)

        scene.add(Transmitter(
            f"tx_{veh}",
            position=_f([x, y, ANTENNA_HEIGHT]),
            display_radius=2.0,
        ))

    for i, veh in enumerate(veh_list):
        x, y, heading, speed = positions[veh]
        scene.add(Receiver(
            f"rx_{veh}",
            position=_f([x, y, ANTENNA_HEIGHT]),
            display_radius=2.0,
        ))

    # Compute paths — limit to closest pairs for performance
    paths = None
    pl_info = {}
    if len(veh_list) > 1:
        pairs_to_compute = _closest_pairs(positions, max_pairs)
        for tx_veh, rx_veh in pairs_to_compute:
            tx_pos = positions[tx_veh]
            rx_pos = positions[rx_veh]
            dist = math.sqrt((tx_pos[0] - rx_pos[0]) ** 2
                             + (tx_pos[1] - rx_pos[1]) ** 2)

            tmp_tx = f"_tmp_tx_{tx_veh}"
            tmp_rx = f"_tmp_rx_{rx_veh}"
            scene.add(Transmitter(tmp_tx, position=_f([tx_pos[0], tx_pos[1], ANTENNA_HEIGHT])))
            scene.add(Receiver(tmp_rx, position=_f([rx_pos[0], rx_pos[1], ANTENNA_HEIGHT])))

            pair_paths = solver(
                scene=scene, max_depth=max_depth,
                los=True, specular_reflection=True,
                diffuse_reflection=True, refraction=False,
                synthetic_array=False, seed=42,
            )
            pair_paths.normalize_delays = False

            try:
                a_r, a_i = pair_paths.a
                a_np = a_r.numpy() + 1j * a_i.numpy()
                powers = np.abs(a_np[0, 0, 0, 0, :]) ** 2
                total = float(np.sum(powers))
                pl = -10 * np.log10(total) if total > 0 else float("inf")
            except Exception:
                pl = float("inf")

            pair = f"{tx_veh}->{rx_veh}"
            pl_info[pair] = (pl, dist)

            if paths is None or int(pair_paths.valid.numpy().sum()) > 0:
                paths = pair_paths

            scene.remove(tmp_tx)
            scene.remove(tmp_rx)

    # Render with rays for the closest pair
    if len(veh_list) >= 2:
        closest = _closest_pairs(positions, 1)
        tx_v, rx_v = closest[0]
        scene.add(Transmitter("_render_tx", position=_f([
            positions[tx_v][0], positions[tx_v][1], ANTENNA_HEIGHT])))
        scene.add(Receiver("_render_rx", position=_f([
            positions[rx_v][0], positions[rx_v][1], ANTENNA_HEIGHT])))
        try:
            render_paths = solver(
                scene=scene, max_depth=max_depth,
                los=True, specular_reflection=True,
                diffuse_reflection=True, refraction=False,
                synthetic_array=False, seed=42,
            )
            render_paths.normalize_delays = False
        except Exception:
            render_paths = None

        try:
            scene.render_to_file(
                camera=cam,
                filename=out_path,
                resolution=resolution,
                paths=render_paths,
                show_devices=True,
            )
        except Exception as e:
            print(f"  Render error: {e}")
            scene.render_to_file(
                camera=cam, filename=out_path,
                resolution=resolution, show_devices=True,
            )
        scene.remove("_render_tx")
        scene.remove("_render_rx")
    else:
        scene.render_to_file(
            camera=cam, filename=out_path,
            resolution=resolution, show_devices=True,
        )

    # Cleanup
    for veh in veh_list:
        scene.remove(f"tx_{veh}")
        scene.remove(f"rx_{veh}")
    scene.edit(remove=cars)

    return pl_info


# ── GIF assembly ─────────────────────────────────────────────────────

def assemble_gif(frames_dir: Path, output_path: str, fps: int = 5,
                 add_labels: bool = True, label_data: dict = None):
    """Assemble PNG frames into an animated GIF using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    frame_files = sorted(frames_dir.glob("frame_*.png"))
    if not frame_files:
        print("No frames found!")
        return

    images = []
    for fpath in frame_files:
        img = Image.open(fpath).convert("RGB")

        if add_labels and label_data:
            frame_key = fpath.stem  # e.g., frame_0042
            info = label_data.get(frame_key, {})
            if info:
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
                except Exception:
                    font = ImageFont.load_default()

                lines = [f"t = {info.get('time_s', 0):.1f}s"]
                for pair, (pl, dist) in info.get("pl", {}).items():
                    pl_str = f"{pl:.0f}" if pl < 300 else "inf"
                    lines.append(f"{pair}: PL={pl_str}dB  d={dist:.0f}m")

                y_off = 10
                for line in lines:
                    draw.text((10, y_off), line, fill=(255, 255, 0), font=font)
                    y_off += 20

        images.append(img)

    duration_ms = int(1000 / fps)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    print(f"GIF saved: {output_path} ({len(images)} frames, {fps} fps)")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sionna 3D Ray-Tracing Animation for NEWWAY scenarios"
    )
    parser.add_argument("--run-dir", required=True,
                        help="Scenario run directory with artifacts/*-CAM.csv")
    parser.add_argument("--scene", default=None,
                        help="Sionna scene.xml path (auto-detected)")
    parser.add_argument("--out-dir", default=None,
                        help="Output dir (default: <run-dir>/visualizations/sionna_3d)")
    parser.add_argument("--t-start", type=float, default=None,
                        help="Start time in seconds (default: first CAM entry)")
    parser.add_argument("--t-end", type=float, default=None,
                        help="End time in seconds (default: last CAM entry)")
    parser.add_argument("--dt", type=float, default=0.5,
                        help="Time step between frames in seconds (default: 0.5)")
    parser.add_argument("--fps", type=int, default=5,
                        help="GIF frame rate (default: 5)")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Ray-tracing max reflections (default: 3, faster)")
    parser.add_argument("--resolution", default="800,600",
                        help="Frame resolution WxH (default: 800,600)")
    parser.add_argument("--num-samples", type=int, default=64,
                        help="Mitsuba samples per pixel (default: 64)")
    parser.add_argument("--frequency", type=float, default=5.89e9,
                        help="Carrier frequency Hz (default: 5.89 GHz)")
    parser.add_argument("--camera", default="follow",
                        choices=["follow", "fixed"],
                        help="Camera mode: follow vehicles or fixed position")
    parser.add_argument("--cam-pos", default=None,
                        help='Fixed camera position "x,y,z" (with --camera=fixed)')
    parser.add_argument("--cam-look", default=None,
                        help='Fixed camera look-at "x,y,z" (with --camera=fixed)')
    parser.add_argument("--no-labels", action="store_true",
                        help="Skip text overlay on frames")
    parser.add_argument("--skip-gif", action="store_true",
                        help="Only render frames, do not assemble GIF")
    parser.add_argument("--scene-filter", action="store_true",
                        help="Only render vehicles within Sionna scene bounds")
    parser.add_argument("--max-pairs", type=int, default=5,
                        help="Max vehicle pairs to compute paths for (default: 5)")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent

    # Scene path
    scene_path = args.scene or str(root / DEFAULT_SCENE)
    if not os.path.isfile(scene_path):
        print(f"ERROR: Scene not found: {scene_path}", file=sys.stderr)
        sys.exit(1)

    # Output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = run_dir / "visualizations" / "sionna_3d"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Resolution
    res = tuple(int(x) for x in args.resolution.split(","))

    # ── Load timeline ──
    print("Loading CAM timeline...")
    timeline = load_cam_timeline(run_dir)
    if not timeline:
        print("ERROR: No CAM CSVs found", file=sys.stderr)
        sys.exit(1)

    all_times = []
    for entries in timeline.values():
        all_times.extend(e["time_s"] for e in entries)
    t_min, t_max = min(all_times), max(all_times)

    t_start = args.t_start if args.t_start is not None else t_min
    t_end = args.t_end if args.t_end is not None else t_max
    dt = args.dt

    n_frames = int((t_end - t_start) / dt) + 1
    print(f"Vehicles: {sorted(timeline.keys())}")
    print(f"Time range: {t_min:.1f}s - {t_max:.1f}s")
    print(f"Rendering: {t_start:.1f}s - {t_end:.1f}s, dt={dt}s -> {n_frames} frames")
    print(f"Resolution: {res[0]}x{res[1]}, samples: {args.num_samples}")
    print()

    # ── Load scene ──
    print(f"Loading Sionna scene: {scene_path}")
    scene = load_scene(scene_path, merge_shapes_exclude_regex="car")
    scene.frequency = args.frequency
    scene.bandwidth = 10e6

    scene.tx_array = PlanarArray(
        num_rows=1, num_cols=1,
        vertical_spacing=0.5, horizontal_spacing=0.5,
        pattern="iso", polarization="V",
    )
    scene.rx_array = PlanarArray(
        num_rows=1, num_cols=1,
        vertical_spacing=0.5, horizontal_spacing=0.5,
        pattern="iso", polarization="V",
    )

    car_material = ITURadioMaterial(
        "car-material", "metal",
        thickness=0.01, color=(0.8, 0.1, 0.1),
    )
    solver = PathSolver()

    print(f"Scene loaded: {len(scene.objects)} objects\n")

    # ── Parse fixed camera if needed ──
    fixed_cam_pos = None
    fixed_cam_look = None
    if args.camera == "fixed":
        if args.cam_pos:
            fixed_cam_pos = _f([float(x) for x in args.cam_pos.split(",")])
        if args.cam_look:
            fixed_cam_look = _f([float(x) for x in args.cam_look.split(",")])

    # ── Render frames ──
    label_data = {}

    for i, t in enumerate(np.arange(t_start, t_end + dt / 2, dt)):
        t = float(t)
        positions = get_positions_at_time(timeline, t, scene_filter=args.scene_filter)
        if not positions:
            print(f"  Frame {i:04d} t={t:.1f}s — no vehicles, skipping")
            continue

        # Camera
        if args.camera == "follow":
            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            cx, cy = float(np.mean(xs)), float(np.mean(ys))
            cam = Camera(
                position=_f([cx - 30, cy - 40, 35]),
                look_at=_f([cx, cy, 1.5]),
            )
        else:
            cp = fixed_cam_pos or _f([-50, -100, 80])
            cl = fixed_cam_look or _f([-50, -50, 2])
            cam = Camera(position=cp, look_at=cl)

        frame_path = str(frames_dir / f"frame_{i:04d}.png")
        print(f"  Frame {i:04d} t={t:.1f}s  vehicles={sorted(positions.keys())}", end="")

        pl_info = frame_handler(
            scene, positions, car_material, solver,
            args.max_depth, cam, frame_path, res,
            max_pairs=args.max_pairs,
        )

        if pl_info:
            for pair, (pl, dist) in pl_info.items():
                pl_str = f"{pl:.0f}" if pl < 300 else "inf"
                print(f"  {pair}:PL={pl_str}dB", end="")

        label_data[f"frame_{i:04d}"] = {
            "time_s": t,
            "pl": pl_info or {},
        }
        print()

    # ── Assemble GIF ──
    if not args.skip_gif:
        gif_path = str(out_dir / "animation.gif")
        print(f"\nAssembling GIF ({args.fps} fps)...")
        assemble_gif(
            frames_dir, gif_path, fps=args.fps,
            add_labels=not args.no_labels,
            label_data=label_data,
        )

    print(f"\nDone. Output: {out_dir}")


if __name__ == "__main__":
    main()
