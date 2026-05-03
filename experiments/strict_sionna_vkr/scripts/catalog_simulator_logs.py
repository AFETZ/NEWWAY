#!/usr/bin/env python3
"""Build a dataset catalog for strict sidelink + Sionna run artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DatasetSpec:
    dataset_name: str
    simulator: str
    layer: str
    file_glob: str
    dataset_type: str
    purpose: str


DATASET_SPECS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        "run_manifest",
        "strict-runner",
        "orchestration",
        "run_manifest.json",
        "json_manifest",
        "Canonical run configuration: scenario id, mode, SUMO config, Sionna scene, analysis focus, and native 5G-LENA radio parameters.",
    ),
    DatasetSpec(
        "run_summary",
        "strict-runner",
        "orchestration",
        "run_summary.json",
        "json_summary",
        "Compact per-seed outcome summary used for quick acceptance checks and thesis tables.",
    ),
    DatasetSpec(
        "seed_summary",
        "strict-runner",
        "analysis",
        "seed_summary.csv",
        "tabular_summary",
        "Single-row thesis-ready per-seed KPI table joining safety and radio outcomes.",
    ),
    DatasetSpec(
        "behavior_text_log",
        "ms-van3t / ns-3 app",
        "application",
        "behavior/v2v-emergencyVehicleAlert-nrv2x.log",
        "text_log",
        "Human-readable execution log with Sionna handshake, per-vehicle totals, average PRR, and latency.",
    ),
    DatasetSpec(
        "sumo_netstate",
        "SUMO",
        "mobility",
        "behavior/artifacts/eva-netstate.xml",
        "xml_timeseries",
        "Ground-truth vehicle trajectories from SUMO at each simulation step.",
    ),
    DatasetSpec(
        "sumo_collision",
        "SUMO",
        "safety",
        "behavior/artifacts/eva-collision.xml",
        "xml_events",
        "Ground-truth collision events produced by SUMO collision checking.",
    ),
    DatasetSpec(
        "vehicle_cam_state",
        "ms-van3t / ns-3 app",
        "application",
        "behavior/artifacts/eva-veh*-CAM.csv",
        "tabular_per_vehicle",
        "Decoded CAM content as seen by the application layer for each vehicle.",
    ),
    DatasetSpec(
        "vehicle_msg_trace",
        "ms-van3t / ns-3 app",
        "application",
        "behavior/artifacts/eva-veh*-MSG.csv",
        "tabular_per_vehicle",
        "Application-level message ledger for transmitted and received CAM/CPM messages.",
    ),
    DatasetSpec(
        "vehicle_control_trace",
        "ms-van3t / ns-3 app",
        "behavior",
        "behavior/artifacts/eva-veh*-CTRL.csv",
        "tabular_per_vehicle",
        "Behavior-controller decisions triggered by warnings or sensors, including slowdowns and lane actions.",
    ),
    DatasetSpec(
        "vehicle_profile_trace",
        "ms-van3t / ns-3 app",
        "configuration",
        "behavior/artifacts/eva-veh*-PROFILE.csv",
        "tabular_per_vehicle",
        "Per-vehicle reception profile snapshot; useful to verify that strict runs are not using legacy shims.",
    ),
    DatasetSpec(
        "vehicle_phy_trace",
        "ms-van3t / ns-3 app",
        "cross_layer",
        "behavior/artifacts/eva-veh*-PHY.csv",
        "tabular_per_vehicle",
        "Per-packet PHY observations exported to the app layer: SINR, RSRP, distance, size, and reception result.",
    ),
    DatasetSpec(
        "collision_risk_timeseries",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/collision_risk/collision_risk_timeseries.csv",
        "tabular_timeseries",
        "Time series of minimum gap and TTC derived from SUMO netstate.",
    ),
    DatasetSpec(
        "collision_risk_summary",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/collision_risk/collision_risk_summary.csv",
        "tabular_summary",
        "Compact safety summary derived from the collision-risk time series.",
    ),
    DatasetSpec(
        "drop_decision_timeline",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/drop_decision_timeline/event_timeline.csv",
        "tabular_events",
        "Causal join between message drops and later control decisions.",
    ),
    DatasetSpec(
        "drop_decision_summary",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/drop_decision_timeline/summary.csv",
        "tabular_summary",
        "Aggregate statistics for drop-to-decision matching quality.",
    ),
    DatasetSpec(
        "collision_causality_csv",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/collision_causality/collision_causality.csv",
        "tabular_events",
        "Structured collision causality rows linking safety outcomes to communication events when collisions exist.",
    ),
    DatasetSpec(
        "collision_causality_report",
        "analysis pipeline",
        "analysis",
        "behavior/artifacts/collision_causality/collision_causality.md",
        "markdown_report",
        "Human-readable causality interpretation for collisions or empty-collision cases.",
    ),
    DatasetSpec(
        "pscch_rx_trace",
        "5G-LENA NR sidelink",
        "radio_control",
        "native_nr/native_nr-pscch.csv",
        "tabular_radio_trace",
        "Received PSCCH control blocks with SCI stage 1 decoding outcome and reservation metadata.",
    ),
    DatasetSpec(
        "pscch_tx_trace",
        "5G-LENA NR sidelink",
        "radio_control",
        "native_nr/native_nr-pscch-tx.csv",
        "tabular_radio_trace",
        "Transmitted PSCCH control grants and reservation structure selected by Mode 2 SPS.",
    ),
    DatasetSpec(
        "pssch_rx_trace",
        "5G-LENA NR sidelink",
        "radio_data",
        "native_nr/native_nr-pssch.csv",
        "tabular_radio_trace",
        "Received PSSCH data blocks with TB corruption, SCI2 corruption, and RB allocation fields.",
    ),
    DatasetSpec(
        "pssch_tx_trace",
        "5G-LENA NR sidelink",
        "radio_data",
        "native_nr/native_nr-pssch-tx.csv",
        "tabular_radio_trace",
        "Transmitted PSSCH blocks with HARQ/NDI, source/destination L2 ids, and reselection counters.",
    ),
    DatasetSpec(
        "cam_rx_radio_trace",
        "5G-LENA NR sidelink",
        "radio_data",
        "native_nr/native_nr-cam.csv",
        "tabular_radio_trace",
        "Per-received CAM radio sample with distance, RSSI, and SNR.",
    ),
    DatasetSpec(
        "prr_summary",
        "5G-LENA NR sidelink",
        "radio_summary",
        "native_nr/native_nr-prr.csv",
        "tabular_summary",
        "Per-node packet reception ratio summary exported by the native PHY experiment.",
    ),
    DatasetSpec(
        "native_nr_text_log",
        "5G-LENA NR sidelink",
        "radio_summary",
        "native_nr/v2v-5g-phy-metrics-experiment.log",
        "text_log",
        "Execution log for the native PHY sidecar, including trace attachment and output paths.",
    ),
    DatasetSpec(
        "native_nr_summary",
        "5G-LENA NR sidelink",
        "radio_summary",
        "native_nr/native_nr-summary.txt",
        "text_summary",
        "Compact experiment summary with MCS, numerology, PRR, latency, and wall-clock time.",
    ),
)


def summarize_csv(path: Path) -> tuple[str, str, int]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return ("csv", "empty_csv", 0)
        row_count = sum(1 for _ in reader)
    return ("csv", ",".join(header), row_count)


def summarize_json(path: Path) -> tuple[str, str, int]:
    with path.open() as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return ("json", "keys=" + ",".join(payload.keys()), len(payload))
    if isinstance(payload, list):
        return ("json", "list_items", len(payload))
    return ("json", type(payload).__name__, 1)


def _count_xml_records(root: ET.Element) -> int:
    if root.tag == "netstate":
        return sum(1 for _ in root.iter("vehicle"))
    if root.tag == "collisions":
        return sum(1 for _ in root.iter("collision"))
    return len(list(root))


def summarize_xml(path: Path) -> tuple[str, str, int]:
    root = ET.parse(path).getroot()
    child_tags = sorted({child.tag for child in root[:5]})
    structure = f"root={root.tag}"
    if child_tags:
        structure += "; children=" + ",".join(child_tags)
    return ("xml", structure, _count_xml_records(root))


def summarize_text(path: Path) -> tuple[str, str, int]:
    with path.open() as handle:
        non_empty = [line.strip() for line in handle if line.strip()]
    preview = " | ".join(non_empty[:3])
    return (path.suffix.lstrip(".") or "text", preview[:240], len(non_empty))


def summarize_file(path: Path) -> tuple[str, str, int]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return summarize_csv(path)
    if suffix == ".json":
        return summarize_json(path)
    if suffix == ".xml":
        return summarize_xml(path)
    return summarize_text(path)


def iter_matches(run_dir: Path, file_glob: str) -> list[Path]:
    return sorted(path for path in run_dir.glob(file_glob) if path.is_file())


def build_rows(run_dir: Path) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for spec in DATASET_SPECS:
        matches = iter_matches(run_dir, spec.file_glob)
        if not matches:
            continue

        sample = matches[0]
        file_format, schema_hint, sample_records = summarize_file(sample)
        total_records = 0
        for path in matches:
            _, _, records = summarize_file(path)
            total_records += records

        rows.append(
            {
                "dataset_name": spec.dataset_name,
                "simulator": spec.simulator,
                "layer": spec.layer,
                "dataset_type": spec.dataset_type,
                "purpose": spec.purpose,
                "file_pattern": spec.file_glob,
                "format": file_format,
                "files_found": len(matches),
                "records_total": total_records,
                "sample_records": sample_records,
                "schema_hint": schema_hint,
                "sample_path": str(sample.resolve()),
                "matched_paths": "; ".join(str(path.resolve()) for path in matches),
            }
        )
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, str | int]]) -> None:
    rows = list(rows)
    fieldnames = [
        "dataset_name",
        "simulator",
        "layer",
        "dataset_type",
        "purpose",
        "file_pattern",
        "format",
        "files_found",
        "records_total",
        "sample_records",
        "schema_hint",
        "sample_path",
        "matched_paths",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: Iterable[dict[str, str | int]], run_dir: Path) -> None:
    rows = list(rows)
    lines = [
        "# Simulator Log Dataset Catalog",
        "",
        f"Run directory: `{run_dir.resolve()}`",
        "",
        "| Dataset | Simulator | Layer | Type | Files | Records | Purpose | Schema hint | Sample path |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["dataset_name"]),
                    str(row["simulator"]),
                    str(row["layer"]),
                    str(row["dataset_type"]),
                    str(row["files_found"]),
                    str(row["records_total"]),
                    str(row["purpose"]).replace("|", "/"),
                    str(row["schema_hint"]).replace("|", "/"),
                    f"`{row['sample_path']}`",
                ]
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Strict run directory to catalog")
    parser.add_argument(
        "--out-csv",
        help="Output CSV path; defaults to <run-dir>/dataset_catalog.csv",
    )
    parser.add_argument(
        "--out-md",
        help="Output Markdown path; defaults to <run-dir>/dataset_catalog.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir).resolve()
    rows = build_rows(run_dir)
    out_csv = Path(args.out_csv).resolve() if args.out_csv else run_dir / "dataset_catalog.csv"
    out_md = Path(args.out_md).resolve() if args.out_md else run_dir / "dataset_catalog.md"
    write_csv(out_csv, rows)
    write_markdown(out_md, rows, run_dir)
    print(f"Wrote {len(rows)} dataset rows to {out_csv}")
    print(f"Wrote markdown catalog to {out_md}")


if __name__ == "__main__":
    main()
