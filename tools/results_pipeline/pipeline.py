from datetime import datetime, timezone
from pathlib import Path

from .aggregate import build_aggregates
from .diagnostics import build_diagnostics
from .metadata import build_metadata
from .readers.van3twin_csv import read_artifacts
from .schema import AGGREGATE_FIELDS, DIAGNOSTIC_FIELDS, NORMALIZED_EVENT_FIELDS
from .writers import write_csv, write_json, write_yaml


def _default_run_id(scenario):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{scenario}-{stamp}"


def build_pipeline(input_dir, output_dir, scenario, run_id=None):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = run_id or _default_run_id(scenario)

    events, reader_diagnostics, input_files = read_artifacts(
        input_dir=input_dir,
        scenario=scenario,
        run_id=run_id,
    )

    aggregates = build_aggregates(
        events=events,
        run_id=run_id,
        scenario=scenario,
        input_files_count=len(input_files),
    )

    diagnostics = build_diagnostics(events, reader_diagnostics)
    metadata = build_metadata(run_id, scenario, input_files)

    write_csv(
        output_dir / "normalized_events.csv",
        [event.to_dict() for event in events],
        NORMALIZED_EVENT_FIELDS,
    )
    write_csv(
        output_dir / "aggregates_overall.csv",
        [aggregates],
        AGGREGATE_FIELDS,
    )
    write_csv(
        output_dir / "diagnostics.csv",
        diagnostics,
        DIAGNOSTIC_FIELDS,
    )
    write_json(output_dir / "run_metadata.json", metadata)
    write_yaml(output_dir / "run_metadata.yaml", metadata)

    return {
        "normalized_events": str(output_dir / "normalized_events.csv"),
        "aggregates_overall": str(output_dir / "aggregates_overall.csv"),
        "diagnostics": str(output_dir / "diagnostics.csv"),
        "run_metadata_json": str(output_dir / "run_metadata.json"),
        "run_metadata_yaml": str(output_dir / "run_metadata.yaml"),
    }
