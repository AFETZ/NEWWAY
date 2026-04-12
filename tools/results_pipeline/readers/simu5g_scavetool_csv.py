import csv
import re
from pathlib import Path


def _to_float(raw):
    if raw is None:
        return None
    text = str(raw).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except Exception:
        return None


def _infer_entity_id(module_path, fallback_entity_id):
    if fallback_entity_id:
        return fallback_entity_id

    if not module_path:
        return ""

    match = re.search(r"(ue\[\d+\])", module_path, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"(gnb\[\d+\])", module_path, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    return ""


def _normalize_metric(raw_name):
    key = (raw_name or "").strip().lower()

    mapping = {
        "throughput": ("throughput_bps", "node", "bps"),
        "delay": ("delay_us", "node", "us"),
        "packetloss": ("loss_ratio", "node", "ratio"),
        "lossratio": ("loss_ratio", "node", "ratio"),
        "sinr": ("sinr_db", "link", "dB"),
        "snr": ("sinr_db", "link", "dB"),
    }

    if key in mapping:
        return mapping[key]

    return (key if key else "unknown_metric", "global", "")


def _normalize_value_and_unit(metric_name, value, unit):
    if value is None:
        return None, unit

    unit_key = (unit or "").strip().lower()

    if metric_name == "delay_us":
        if unit_key in {"s", "sec", "second", "seconds"}:
            return value * 1000000.0, "us"
        if unit_key in {"ms", "millisecond", "milliseconds"}:
            return value * 1000.0, "us"
        if unit_key in {"us", "microsecond", "microseconds"}:
            return value, "us"
        return value, "us"

    return value, unit


def _normalize_ts_us(vectime_raw):
    value = _to_float(vectime_raw)
    if value is None:
        return None
    return int(round(value * 1000000.0))


def read_simu5g_scavetool_csv(path, scenario, run_id=None):
    path = Path(path)
    rows_out = []

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            raw_run_id = run_id or (row.get("run_id") or row.get("run") or path.stem)
            module_path = (row.get("module") or "").strip()
            raw_name = (row.get("name") or "").strip()
            sample_kind = ((row.get("type") or "scalar").strip().lower())
            raw_unit = (row.get("unit") or "").strip()
            fallback_entity_id = (row.get("entity_id") or "").strip()

            if raw_name == "":
                continue

            value_raw = row.get("value")
            if sample_kind == "vector" and (value_raw is None or str(value_raw).strip() == ""):
                value_raw = row.get("vecvalue")

            value = _to_float(value_raw)
            if value is None:
                continue

            metric_name, metric_scope, default_unit = _normalize_metric(raw_name)
            unit = raw_unit if raw_unit else default_unit
            value, unit = _normalize_value_and_unit(metric_name, value, unit)
            entity_id = _infer_entity_id(module_path, fallback_entity_id)
            ts_us = _normalize_ts_us(row.get("vectime")) if sample_kind == "vector" else None

            rows_out.append({
                "run_id": raw_run_id,
                "scenario": scenario,
                "source_stack": "simu5g",
                "sample_kind": sample_kind,
                "metric_name": metric_name,
                "metric_scope": metric_scope,
                "entity_id": entity_id,
                "src_id": "",
                "dst_id": "",
                "ts_us": ts_us,
                "value": value,
                "unit": unit,
                "module_path": module_path,
                "stat_name": raw_name,
                "input_file": str(path),
                "raw_row_num": row_num,
            })

    return rows_out
