#!/usr/bin/env python3
"""Export a compact bundle of run results for external review (e.g., ChatGPT upload)."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Copy practical run outputs into a single export folder.")
    p.add_argument("--run-dir", required=True, help="Run directory to export")
    p.add_argument(
        "--export-root",
        default="analysis/scenario_runs/chatgpt_exports",
        help="Root output directory for exported bundles",
    )
    p.add_argument(
        "--run-label",
        default="",
        help="Optional destination label. Default: run-dir relative to analysis/scenario_runs",
    )
    p.add_argument(
        "--include-raw-csv",
        action="store_true",
        help="Also copy all CSV files (may be large).",
    )
    return p.parse_args()


def _safe_run_label(run_dir: Path, explicit_label: str) -> Path:
    if explicit_label:
        return Path(explicit_label)
    marker = Path("analysis/scenario_runs")
    parts = run_dir.parts
    for i in range(len(parts)):
        if parts[i : i + len(marker.parts)] == marker.parts:
            rel = Path(*parts[i + len(marker.parts) :])
            return rel if str(rel) else Path(run_dir.name)
    return Path(run_dir.name)


def _collect_paths(run_dir: Path, include_raw_csv: bool) -> list[Path]:
    selected: set[Path] = set()

    for p in run_dir.rglob("*.png"):
        selected.add(p)
    for p in run_dir.rglob("*.log"):
        selected.add(p)
    for p in run_dir.rglob("*.md"):
        if p.name.upper() == "REPORT.MD" or p.name.upper() == "README.MD":
            selected.add(p)

    compact_csv_patterns = [
        "**/*summary*.csv",
        "**/cases.csv",
        "**/run_summary.csv",
        "**/manifest.csv",
        "**/collision_risk/*.csv",
    ]
    for pattern in compact_csv_patterns:
        for p in run_dir.glob(pattern):
            if p.is_file():
                selected.add(p)

    if include_raw_csv:
        for p in run_dir.rglob("*.csv"):
            selected.add(p)

    return sorted(selected)


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        raise FileNotFoundError(run_dir)

    export_root = Path(args.export_root).resolve()
    run_label = _safe_run_label(run_dir, args.run_label)
    dst_dir = export_root / run_label
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    files = _collect_paths(run_dir, args.include_raw_csv)
    manifest_rows = []
    for src in files:
        rel = src.relative_to(run_dir)
        dst = dst_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest_rows.append((str(rel), src.stat().st_size))

    manifest = dst_dir / "EXPORT_MANIFEST.csv"
    with manifest.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["relative_path", "size_bytes"])
        writer.writerows(manifest_rows)

    print(dst_dir)
    print(manifest)
    print(f"exported_files={len(manifest_rows)}")


if __name__ == "__main__":
    main()
