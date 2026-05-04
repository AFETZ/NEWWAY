from typing import List

from .schema import NORMALIZED_METRIC_FIELDS


def _metric_row(
    *,
    run_id,
    scenario,
    source_stack,
    sample_kind,
    metric_name,
    metric_scope,
    entity_id="",
    src_id="",
    dst_id="",
    ts_us=None,
    value=None,
    unit="",
    module_path="",
    stat_name="",
    input_file="",
    raw_row_num=0,
):
    return {
        "run_id": run_id,
        "scenario": scenario,
        "source_stack": source_stack,
        "sample_kind": sample_kind,
        "metric_name": metric_name,
        "metric_scope": metric_scope,
        "entity_id": entity_id,
        "src_id": src_id,
        "dst_id": dst_id,
        "ts_us": ts_us,
        "value": value,
        "unit": unit,
        "module_path": module_path,
        "stat_name": stat_name,
        "input_file": input_file,
        "raw_row_num": raw_row_num,
    }


def _event_entity_id(event):
    if getattr(event, "dst_id", None):
        return event.dst_id
    if getattr(event, "src_id", None):
        return event.src_id
    return ""


def project_van3twin_events_to_metrics(events) -> List[dict]:
    rows = []

    metric_specs = [
        ("latency_us", "link", "us"),
        ("rssi_dbm", "link", "dBm"),
        ("sinr_db", "link", "dB"),
        ("bler", "link", "ratio"),
        ("distance_m", "link", "m"),
        ("speed_mps", "node", "m/s"),
        ("acceleration_mps2", "node", "m/s^2"),
        ("prr_value", "link", "ratio"),
        ("pdr_value", "link", "ratio"),
    ]

    for event in events:
        entity_id = _event_entity_id(event)

        if getattr(event, "source_kind", None) == "cam" and getattr(event, "event_type", None) == "rx":
            rows.append(
                _metric_row(
                    run_id=event.run_id,
                    scenario=event.scenario,
                    source_stack="van3twin_ns3",
                    sample_kind="event",
                    metric_name="cam_rx_count",
                    metric_scope="link",
                    entity_id=entity_id,
                    src_id=event.src_id or "",
                    dst_id=event.dst_id or "",
                    ts_us=event.ts_us,
                    value=1,
                    unit="count",
                    module_path="",
                    stat_name="cam_rx_count",
                    input_file=event.raw_file,
                    raw_row_num=event.raw_row_num,
                )
            )

        for field_name, metric_scope, unit in metric_specs:
            value = getattr(event, field_name, None)
            if value is None:
                continue

            rows.append(
                _metric_row(
                    run_id=event.run_id,
                    scenario=event.scenario,
                    source_stack="van3twin_ns3",
                    sample_kind="derived",
                    metric_name=field_name,
                    metric_scope=metric_scope,
                    entity_id=entity_id,
                    src_id=event.src_id or "",
                    dst_id=event.dst_id or "",
                    ts_us=event.ts_us,
                    value=value,
                    unit=unit,
                    module_path="",
                    stat_name=field_name,
                    input_file=event.raw_file,
                    raw_row_num=event.raw_row_num,
                )
            )

    return rows


def project_simu5g_rows_to_metrics(rows) -> List[dict]:
    projected = []

    for row in rows:
        projected.append(
            _metric_row(
                run_id=row.get("run_id", ""),
                scenario=row.get("scenario", ""),
                source_stack=row.get("source_stack", "simu5g"),
                sample_kind=row.get("sample_kind", "scalar"),
                metric_name=row.get("metric_name", ""),
                metric_scope=row.get("metric_scope", "global"),
                entity_id=row.get("entity_id", ""),
                src_id=row.get("src_id", ""),
                dst_id=row.get("dst_id", ""),
                ts_us=row.get("ts_us"),
                value=row.get("value"),
                unit=row.get("unit", ""),
                module_path=row.get("module_path", ""),
                stat_name=row.get("stat_name", ""),
                input_file=row.get("input_file", ""),
                raw_row_num=row.get("raw_row_num", 0),
            )
        )

    return projected


def trim_metric_rows(rows):
    trimmed = []
    for row in rows:
        trimmed.append({field: row.get(field) for field in NORMALIZED_METRIC_FIELDS})
    return trimmed
