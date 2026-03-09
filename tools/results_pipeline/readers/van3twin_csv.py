import csv
from pathlib import Path

from ..schema import NormalizedEvent


ALIASES = {
    "src_id": ["src_id", "src", "source", "tx_id", "sender", "node_id", "senderid", "txnodeid"],
    "dst_id": ["dst_id", "dst", "destination", "rx_id", "receiver", "neighbor_id", "receiverid", "rxnodeid"],
    "pkt_id": ["pkt_uid", "pkt_id", "packet_id", "uid", "msg_id", "message_id", "cam_id", "id"],
    "ts": [
        "ts_us", "time_us", "timestamp_us",
        "ts_ms", "time_ms", "timestamp_ms",
        "ts_s", "time_s", "timestamp_s",
        "timestamp", "time", "simtime", "sim_time"
    ],
    "latency": ["latency_us", "delay_us", "latency_ms", "delay_ms", "latency_s", "delay_s", "latency", "delay"],
    "sinr_db": ["sinr_db", "sinr", "sinrdb", "snr"],
    "rssi_dbm": ["rssi_dbm", "rssi", "rss_dbm", "rx_power_dbm"],
    "bler": ["bler"],
    "prr_value": ["prr", "packet_reception_ratio"],
    "pdr_value": ["pdr", "packet_delivery_ratio"],
    "success": ["success", "received", "rx_ok", "delivered", "is_received", "ok"],
    "drop_reason": ["drop_reason", "reason", "failure_reason", "dropcause"],
    "event_type": ["event_type", "event", "type", "state", "status"],
    "size_bytes": ["size_bytes", "bytes", "pkt_size", "packet_size", "len", "length"],
    "distance_m": ["distance_m", "distance", "range_m"],
}


def _issue(issue_type, count, details="", sample_ref=""):
    return {
        "issue_type": issue_type,
        "count": count,
        "details": details,
        "sample_ref": sample_ref,
    }


def _lower_key_map(row):
    return {str(k).strip().lower(): k for k in row.keys() if k is not None}


def _pick_with_key(row, aliases):
    key_map = _lower_key_map(row)
    for alias in aliases:
        real_key = key_map.get(alias.lower())
        if real_key is None:
            continue
        value = row.get(real_key)
        if value is None:
            continue
        value = str(value).strip()
        if value == "":
            continue
        return real_key, value
    return None, None


def _parse_number(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except Exception:
        return None


def _parse_int(value):
    number = _parse_number(value)
    if number is None:
        return None
    return int(round(number))


def _parse_bool(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "ok"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _to_microseconds(field_name, value):
    number = _parse_number(value)
    if number is None:
        return None

    key = (field_name or "").strip().lower()

    if "us" in key:
        return int(round(number))
    if "ms" in key:
        return int(round(number * 1000))
    if key.endswith("_s") or "timestamp_s" in key or "time_s" in key or "latency_s" in key or "delay_s" in key:
        return int(round(number * 1000000))

    if key in {"timestamp", "time", "simtime", "sim_time"}:
        if number < 1e4:
            return int(round(number * 1000000))
        if number < 1e8:
            return int(round(number * 1000))
        return int(round(number))

    return int(round(number))


def _infer_source_kind(path: Path):
    name = path.name.lower()
    if "phy" in name:
        return "phy"
    if "prr" in name:
        return "prr"
    if "ctrl" in name:
        return "ctrl"
    if "msg" in name:
        return "msg"
    return "csv"


def _infer_event_type(row, success, source_kind):
    _, explicit = _pick_with_key(row, ALIASES["event_type"])
    if explicit:
        return explicit.strip().lower()
    if success is True:
        return "rx"
    if success is False:
        return "drop"
    return source_kind


def _interesting_csvs(input_dir: Path):
    all_csvs = sorted(input_dir.rglob("*.csv"))
    if not all_csvs:
        return []

    phy_files = [p for p in all_csvs if p.name.lower() == "phy_with_sionna_nrv2x.csv"]
    prr_files = [p for p in all_csvs if p.name.lower() == "prr_with_sionna_nrv2x.csv"]

    duplicates = []
    if len(phy_files) > 1:
        duplicates.append("phy_with_sionna_nrv2x.csv")
    if len(prr_files) > 1:
        duplicates.append("prr_with_sionna_nrv2x.csv")

    if duplicates:
        dup = ", ".join(duplicates)
        raise ValueError(
            f"Ambiguous input: multiple matching files found for {dup} under {input_dir}. "
            "Pass exactly one run/artifacts directory."
        )

    selected = []
    if phy_files:
        selected.append(phy_files[0])
    if prr_files:
        selected.append(prr_files[0])

    if selected:
        return selected

    return all_csvs


def read_artifacts(input_dir, scenario, run_id):
    input_dir = Path(input_dir)
    diagnostics = []
    events = []
    input_files = _interesting_csvs(input_dir)

    if not input_files:
        diagnostics.append(_issue("input_files_missing", 1, f"No CSV files found under {input_dir}"))
        return events, diagnostics, input_files

    for path in input_files:
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    diagnostics.append(_issue("empty_csv_file", 1, "CSV has no header", str(path)))
                    continue

                source_kind = _infer_source_kind(path)

                for row_num, row in enumerate(reader, start=2):
                    ts_key, ts_value = _pick_with_key(row, ALIASES["ts"])
                    latency_key, latency_value = _pick_with_key(row, ALIASES["latency"])
                    _, src_value = _pick_with_key(row, ALIASES["src_id"])
                    _, dst_value = _pick_with_key(row, ALIASES["dst_id"])
                    _, pkt_value = _pick_with_key(row, ALIASES["pkt_id"])
                    _, size_value = _pick_with_key(row, ALIASES["size_bytes"])
                    _, distance_value = _pick_with_key(row, ALIASES["distance_m"])
                    _, sinr_value = _pick_with_key(row, ALIASES["sinr_db"])
                    _, rssi_value = _pick_with_key(row, ALIASES["rssi_dbm"])
                    _, bler_value = _pick_with_key(row, ALIASES["bler"])
                    _, prr_value = _pick_with_key(row, ALIASES["prr_value"])
                    _, pdr_value = _pick_with_key(row, ALIASES["pdr_value"])
                    _, success_value = _pick_with_key(row, ALIASES["success"])
                    _, drop_reason_value = _pick_with_key(row, ALIASES["drop_reason"])

                    success = _parse_bool(success_value)
                    event_type = _infer_event_type(row, success, source_kind)

                    event = NormalizedEvent(
                        run_id=run_id,
                        scenario=scenario,
                        source_kind=source_kind,
                        event_type=event_type,
                        ts_us=_to_microseconds(ts_key, ts_value),
                        src_id=src_value,
                        dst_id=dst_value,
                        pkt_id=pkt_value,
                        size_bytes=_parse_int(size_value),
                        latency_us=_to_microseconds(latency_key, latency_value),
                        rssi_dbm=_parse_number(rssi_value),
                        sinr_db=_parse_number(sinr_value),
                        bler=_parse_number(bler_value),
                        distance_m=_parse_number(distance_value),
                        prr_value=_parse_number(prr_value),
                        pdr_value=_parse_number(pdr_value),
                        success=success,
                        drop_reason=drop_reason_value,
                        raw_file=str(path),
                        raw_row_num=row_num,
                    )
                    events.append(event)

        except Exception as exc:
            diagnostics.append(_issue("csv_read_error", 1, repr(exc), str(path)))

    return events, diagnostics, input_files
