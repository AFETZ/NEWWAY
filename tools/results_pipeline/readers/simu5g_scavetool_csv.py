import csv
import math
import re
from pathlib import Path


SERVICE_ROW_TYPES = {"attr", "config", "runattr"}


def _diagnostic(issue_type, count, details="", sample_ref=""):
    return {
        "issue_type": issue_type,
        "count": count,
        "details": details,
        "sample_ref": sample_ref,
    }


def _to_float(raw):
    if raw is None:
        return None
    text = str(raw).strip().replace(",", ".")
    if text == "":
        return None
    try:
        value = float(text)
    except Exception:
        return None
    return value if math.isfinite(value) else None


def _split_vector_text(raw):
    if raw is None:
        return []

    text = str(raw).strip()
    if text == "":
        return []

    text = text.strip().strip('"').strip("'").strip()
    text = text.strip("[]")

    if text == "":
        return []

    return [part for part in re.split(r"\s+", text) if part]


def _parse_vector_numbers(raw, *, input_file, row_num, field_name):
    values = []
    diagnostics = []

    for token in _split_vector_text(raw):
        value = _to_float(token)
        if value is None:
            diagnostics.append(
                _diagnostic(
                    "non_numeric_value",
                    1,
                    f"Non-numeric value in {field_name}: {token}",
                    f"{input_file}:{row_num}",
                )
            )
            continue
        values.append(value)

    return values, diagnostics


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


def _normalize_sample_kind(raw_type):
    key = (raw_type or "").strip().lower()
    if key == "vector":
        return "vector"
    return "scalar"


def _normalize_metric(raw_name):
    raw = (raw_name or "").strip().lower()
    raw = re.sub(r":vector$", "", raw)
    key = re.sub(r"[^a-z0-9]+", "", raw)

    if not key:
        return ("unknown_metric", "global", "")

    if "sinr" in key or key == "snr" or key.endswith("snr"):
        return ("sinr_db", "link", "dB")

    if "throughput" in key or "thruput" in key:
        return ("throughput_bps", "node", "bps")

    if "delay" in key or "latency" in key:
        return ("delay_us", "node", "us")

    if "packetloss" in key or "lossratio" in key or key in {"loss", "packetlost"}:
        return ("loss_ratio", "node", "ratio")

    return ("unknown_metric", "global", "")


def _normalize_value_and_unit(metric_name, value, unit):
    if value is None:
        return None, unit

    unit_key = (unit or "").strip().lower()

    if metric_name == "delay_us":
        if unit_key in {"s", "sec", "second", "seconds", ""}:
            return value * 1_000_000.0, "us"
        if unit_key in {"ms", "millisecond", "milliseconds"}:
            return value * 1_000.0, "us"
        if unit_key in {"us", "microsecond", "microseconds"}:
            return value, "us"
        if unit_key in {"ns", "nanosecond", "nanoseconds"}:
            return value / 1_000.0, "us"
        return value, "us"

    if metric_name == "throughput_bps":
        if unit_key in {"bps", ""}:
            return value, "bps"
        if unit_key in {"kbps", "kbit/s", "kbits"}:
            return value * 1_000.0, "bps"
        if unit_key in {"mbps", "mbit/s", "mbits"}:
            return value * 1_000_000.0, "bps"
        if unit_key in {"gbps", "gbit/s", "gbits"}:
            return value * 1_000_000_000.0, "bps"
        return value, unit

    if metric_name == "loss_ratio":
        if unit_key in {"ratio", ""}:
            return value, "ratio"
        if unit_key in {"%", "percent", "percentage"}:
            return value / 100.0, "ratio"
        return value, unit

    if metric_name == "sinr_db":
        if unit_key in {"", "db"}:
            return value, "dB"
        return value, unit

    return value, unit


def _normalize_ts_us(vectime_value):
    if vectime_value is None:
        return None
    return int(round(vectime_value * 1_000_000.0))


def _build_metric_row(
    *,
    run_id,
    scenario,
    sample_kind,
    metric_name,
    metric_scope,
    entity_id,
    ts_us,
    value,
    unit,
    module_path,
    stat_name,
    input_file,
    raw_row_num,
):
    return {
        "run_id": run_id,
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
        "stat_name": stat_name,
        "input_file": input_file,
        "raw_row_num": raw_row_num,
    }


def read_simu5g_scavetool_csv(path, scenario, run_id=None, *, return_diagnostics=False):
    path = Path(path)
    rows_out = []
    diagnostics = []

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            raw_type = (row.get("type") or "").strip().lower()

            if raw_type in SERVICE_ROW_TYPES:
                continue

            raw_run_id = run_id or (row.get("run_id") or row.get("run") or path.stem)
            module_path = (row.get("module") or "").strip()
            raw_name = (row.get("name") or "").strip()
            sample_kind = _normalize_sample_kind(raw_type)
            raw_unit = (row.get("unit") or "").strip()
            fallback_entity_id = (row.get("entity_id") or "").strip()

            if raw_name == "":
                continue

            metric_name, metric_scope, default_unit = _normalize_metric(raw_name)
            unit = raw_unit if raw_unit else default_unit
            entity_id = _infer_entity_id(module_path, fallback_entity_id)

            if sample_kind == "vector":
                time_values, time_diagnostics = _parse_vector_numbers(
                    row.get("vectime"),
                    input_file=path,
                    row_num=row_num,
                    field_name="vectime",
                )
                value_values, value_diagnostics = _parse_vector_numbers(
                    row.get("vecvalue"),
                    input_file=path,
                    row_num=row_num,
                    field_name="vecvalue",
                )

                diagnostics.extend(time_diagnostics)
                diagnostics.extend(value_diagnostics)

                if not time_values and not value_values:
                    diagnostics.append(
                        _diagnostic(
                            "empty_vector",
                            1,
                            "Vector row has empty vectime and vecvalue",
                            f"{path}:{row_num}",
                        )
                    )
                    continue

                if value_values and not time_values:
                    diagnostics.append(
                        _diagnostic(
                            "vector_missing_timestamp",
                            1,
                            "Vector row has vecvalue but empty vectime",
                            f"{path}:{row_num}",
                        )
                    )
                    continue

                if len(time_values) != len(value_values):
                    diagnostics.append(
                        _diagnostic(
                            "vector_length_mismatch",
                            1,
                            f"vectime has {len(time_values)} samples, vecvalue has {len(value_values)} samples",
                            f"{path}:{row_num}",
                        )
                    )
                    continue

                for ts_value, raw_value in zip(time_values, value_values):
                    value, normalized_unit = _normalize_value_and_unit(metric_name, raw_value, unit)

                    rows_out.append(
                        _build_metric_row(
                            run_id=raw_run_id,
                            scenario=scenario,
                            sample_kind="vector",
                            metric_name=metric_name,
                            metric_scope=metric_scope,
                            entity_id=entity_id,
                            ts_us=_normalize_ts_us(ts_value),
                            value=value,
                            unit=normalized_unit,
                            module_path=module_path,
                            stat_name=raw_name,
                            input_file=str(path),
                            raw_row_num=row_num,
                        )
                    )

                continue

            value_raw = row.get("value")
            if value_raw is None or str(value_raw).strip() == "":
                value_raw = row.get("vecvalue")

            value = _to_float(value_raw)
            if value is None:
                diagnostics.append(
                    _diagnostic(
                        "non_numeric_value",
                        1,
                        "Scalar row has empty or non-numeric value",
                        f"{path}:{row_num}",
                    )
                )
                continue

            value, unit = _normalize_value_and_unit(metric_name, value, unit)

            rows_out.append(
                _build_metric_row(
                    run_id=raw_run_id,
                    scenario=scenario,
                    sample_kind="scalar",
                    metric_name=metric_name,
                    metric_scope=metric_scope,
                    entity_id=entity_id,
                    ts_us=None,
                    value=value,
                    unit=unit,
                    module_path=module_path,
                    stat_name=raw_name,
                    input_file=str(path),
                    raw_row_num=row_num,
                )
            )

    if return_diagnostics:
        return rows_out, diagnostics

    return rows_out
