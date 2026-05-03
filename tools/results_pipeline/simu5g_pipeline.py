import argparse
import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from tools.results_pipeline.metrics_projection import project_simu5g_rows_to_metrics, trim_metric_rows
from tools.results_pipeline.readers.simu5g_scavetool_csv import read_simu5g_scavetool_csv
from tools.results_pipeline.schema import NORMALIZED_METRIC_FIELDS
from tools.results_pipeline.writers import write_csv, write_json, write_yaml


SIMU5G_NORMALIZED_FIELDS = [
    "run_id",
    "scenario",
    "source_stack",
    "sample_kind",
    "metric_name",
    "metric_scope",
    "entity_id",
    "src_id",
    "dst_id",
    "ts_us",
    "value",
    "unit",
    "module_path",
    "stat_name",
    "input_file",
    "raw_row_num",
]

SIMU5G_AGGREGATE_BY_METRIC_FIELDS = [
    "run_id",
    "scenario",
    "source_stack",
    "metric_name",
    "sample_kind",
    "rows_count",
    "entity_count",
    "value_mean",
    "value_min",
    "value_max",
    "ts_min_us",
    "ts_max_us",
]

SIMU5G_AGGREGATE_OVERALL_FIELDS = [
    "run_id",
    "scenario",
    "source_stack",
    "rows_total",
    "input_files_count",
    "distinct_metric_count",
    "entity_count",
    "throughput_mean_bps",
    "delay_mean_us",
    "delay_p50_us",
    "delay_p95_us",
    "sinr_mean_db",
    "sinr_p50_db",
    "sinr_p95_db",
    "loss_ratio_mean",
]

SIMU5G_DIAGNOSTIC_FIELDS = [
    "issue_type",
    "count",
    "details",
    "sample_ref",
]


def _git_value(args):
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _percentile(values, p):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return values[0]

    k = (len(values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return values[int(k)]

    return values[f] * (c - k) + values[c] * (k - f)


def _build_metadata(run_id, scenario, input_csv):
    return {
        "run_id": run_id,
        "scenario": scenario,
        "source_stack": "simu5g",
        "input_format": "scavetool_csv",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": _git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_commit": _git_value(["rev-parse", "HEAD"]),
        "input_files": [str(input_csv)],
    }


def _sample_ref(sample):
    return str(sample.get("input_file", "")) + ":" + str(sample.get("raw_row_num", ""))


def _build_diagnostics(rows, input_csv):
    diagnostics = []

    if not rows:
        diagnostics.append({
            "issue_type": "empty_input",
            "count": 1,
            "details": "No rows were produced by Simu5G adapter",
            "sample_ref": str(input_csv),
        })
        return diagnostics

    unknown_metric_rows = [r for r in rows if r.get("metric_name") == "unknown_metric"]
    if unknown_metric_rows:
        sample = unknown_metric_rows[0]
        diagnostics.append({
            "issue_type": "unknown_metric",
            "count": len(unknown_metric_rows),
            "details": "Rows with metric name that could not be normalized",
            "sample_ref": _sample_ref(sample),
        })

    vector_without_ts = [r for r in rows if r.get("sample_kind") == "vector" and r.get("ts_us") is None]
    if vector_without_ts:
        sample = vector_without_ts[0]
        diagnostics.append({
            "issue_type": "vector_missing_timestamp",
            "count": len(vector_without_ts),
            "details": "Vector rows without timestamp",
            "sample_ref": _sample_ref(sample),
        })

    return diagnostics


def _build_aggregates_by_metric(rows, run_id, scenario):
    grouped = defaultdict(list)
    for row in rows:
        key = (row.get("metric_name"), row.get("sample_kind"))
        grouped[key].append(row)

    aggregates = []
    for (metric_name, sample_kind), items in grouped.items():
        values = [item["value"] for item in items if item.get("value") is not None]
        entities = {item.get("entity_id") for item in items if item.get("entity_id")}
        timestamps = [item["ts_us"] for item in items if item.get("ts_us") is not None]

        aggregates.append({
            "run_id": run_id,
            "scenario": scenario,
            "source_stack": "simu5g",
            "metric_name": metric_name,
            "sample_kind": sample_kind,
            "rows_count": len(items),
            "entity_count": len(entities),
            "value_mean": mean(values) if values else None,
            "value_min": min(values) if values else None,
            "value_max": max(values) if values else None,
            "ts_min_us": min(timestamps) if timestamps else None,
            "ts_max_us": max(timestamps) if timestamps else None,
        })

    return aggregates


def _metric_values(rows, metric_name):
    return [r["value"] for r in rows if r.get("metric_name") == metric_name and r.get("value") is not None]


def _build_aggregates_overall(rows, run_id, scenario):
    throughput_values = _metric_values(rows, "throughput_bps")
    delay_values = _metric_values(rows, "delay_us")
    sinr_values = _metric_values(rows, "sinr_db")
    loss_values = _metric_values(rows, "loss_ratio")

    entities = {r.get("entity_id") for r in rows if r.get("entity_id")}
    metrics = {r.get("metric_name") for r in rows if r.get("metric_name")}

    return [{
        "run_id": run_id,
        "scenario": scenario,
        "source_stack": "simu5g",
        "rows_total": len(rows),
        "input_files_count": 1,
        "distinct_metric_count": len(metrics),
        "entity_count": len(entities),
        "throughput_mean_bps": mean(throughput_values) if throughput_values else None,
        "delay_mean_us": mean(delay_values) if delay_values else None,
        "delay_p50_us": _percentile(delay_values, 50),
        "delay_p95_us": _percentile(delay_values, 95),
        "sinr_mean_db": mean(sinr_values) if sinr_values else None,
        "sinr_p50_db": _percentile(sinr_values, 50),
        "sinr_p95_db": _percentile(sinr_values, 95),
        "loss_ratio_mean": mean(loss_values) if loss_values else None,
    }]


def build_simu5g_pipeline(input_csv, output_dir, scenario, run_id=None):
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = run_id or input_csv.stem

    rows = read_simu5g_scavetool_csv(
        path=input_csv,
        scenario=scenario,
        run_id=run_id,
    )

    diagnostics = _build_diagnostics(rows, input_csv)
    aggregates_by_metric = _build_aggregates_by_metric(rows, run_id, scenario)
    aggregates_overall = _build_aggregates_overall(rows, run_id, scenario)
    metadata = _build_metadata(run_id, scenario, input_csv)
    metric_rows = trim_metric_rows(project_simu5g_rows_to_metrics(rows))

    write_csv(output_dir / "normalized_events.csv", rows, SIMU5G_NORMALIZED_FIELDS)
    write_csv(output_dir / "normalized_metrics.csv", metric_rows, NORMALIZED_METRIC_FIELDS)
    write_csv(output_dir / "aggregates_by_metric.csv", aggregates_by_metric, SIMU5G_AGGREGATE_BY_METRIC_FIELDS)
    write_csv(output_dir / "aggregates_overall.csv", aggregates_overall, SIMU5G_AGGREGATE_OVERALL_FIELDS)
    write_csv(output_dir / "diagnostics.csv", diagnostics, SIMU5G_DIAGNOSTIC_FIELDS)
    write_json(output_dir / "run_metadata.json", metadata)
    write_yaml(output_dir / "run_metadata.yaml", metadata)

    return {
        "normalized_events": str(output_dir / "normalized_events.csv"),
        "normalized_metrics": str(output_dir / "normalized_metrics.csv"),
        "aggregates_by_metric": str(output_dir / "aggregates_by_metric.csv"),
        "aggregates_overall": str(output_dir / "aggregates_overall.csv"),
        "diagnostics": str(output_dir / "diagnostics.csv"),
        "run_metadata_json": str(output_dir / "run_metadata.json"),
        "run_metadata_yaml": str(output_dir / "run_metadata.yaml"),
    }


def main():
    parser = argparse.ArgumentParser(description="Simu5G CSV export pipeline")
    parser.add_argument("--input", required=True, help="Path to exported Simu5G CSV")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--scenario", required=True, help="Scenario name")
    parser.add_argument("--run-id", default=None, help="Optional explicit run id")
    args = parser.parse_args()

    result = build_simu5g_pipeline(
        input_csv=args.input,
        output_dir=args.output,
        scenario=args.scenario,
        run_id=args.run_id,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
