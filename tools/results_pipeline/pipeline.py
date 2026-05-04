from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .aggregate import build_aggregates
from .diagnostics import build_diagnostics
from .metadata import build_metadata
from .metrics_projection import project_van3twin_events_to_metrics, trim_metric_rows
from .readers.van3twin_csv import read_artifacts
from .schema import (
    AGGREGATE_FIELDS,
    DIAGNOSTIC_FIELDS,
    NORMALIZED_EVENT_FIELDS,
    NORMALIZED_METRIC_FIELDS,
)
from .writers import write_csv, write_json, write_yaml


def _default_run_id(scenario: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{scenario}-{stamp}"


def build_pipeline(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    scenario: str | None = None,
    run_id: str | None = None,
    *,
    input_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build normalized ns-3 / VaN3Twin results artifacts from a directory or a single CSV file."""

    effective_input = input_path if input_path is not None else input_dir
    if effective_input is None:
        raise ValueError("build_pipeline requires input_dir or input_path")
    if output_dir is None:
        raise ValueError("build_pipeline requires output_dir")
    if scenario is None:
        raise ValueError("build_pipeline requires scenario")

    input_path_obj = Path(effective_input)
    output_path_obj = Path(output_dir)
    output_path_obj.mkdir(parents=True, exist_ok=True)

    run_id = run_id or _default_run_id(scenario)

    events, reader_diagnostics, input_files = read_artifacts(
        input_dir=input_path_obj,
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
    metric_rows = trim_metric_rows(project_van3twin_events_to_metrics(events))

    normalized_events_path = output_path_obj / "normalized_events.csv"
    normalized_metrics_path = output_path_obj / "normalized_metrics.csv"
    aggregates_path = output_path_obj / "aggregates_overall.csv"
    diagnostics_path = output_path_obj / "diagnostics.csv"
    metadata_json_path = output_path_obj / "run_metadata.json"
    metadata_yaml_path = output_path_obj / "run_metadata.yaml"

    write_csv(
        normalized_events_path,
        [event.to_dict() for event in events],
        NORMALIZED_EVENT_FIELDS,
    )
    write_csv(
        normalized_metrics_path,
        metric_rows,
        NORMALIZED_METRIC_FIELDS,
    )
    write_csv(
        aggregates_path,
        [aggregates],
        AGGREGATE_FIELDS,
    )
    write_csv(
        diagnostics_path,
        diagnostics,
        DIAGNOSTIC_FIELDS,
    )
    write_json(metadata_json_path, metadata)
    write_yaml(metadata_yaml_path, metadata)

    return {
        "normalized_events": str(normalized_events_path),
        "normalized_metrics": str(normalized_metrics_path),
        "aggregates_overall": str(aggregates_path),
        "diagnostics": str(diagnostics_path),
        "run_metadata_json": str(metadata_json_path),
        "run_metadata_yaml": str(metadata_yaml_path),
    }