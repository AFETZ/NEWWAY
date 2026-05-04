import csv
import re
from pathlib import Path

from ..schema import NormalizedEvent


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


def _to_bool(raw):
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _read_header(path: Path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    return {str(name).strip().lower() for name in fieldnames if name is not None}


def _classify_artifact(path: Path):
    if path.suffix.lower() != ".csv":
        return None

    header = _read_header(path)
    if not header:
        return None

    lower_name = path.name.lower()

    # Foreign Simu5G / scavetool-style export must be ignored by van3twin reader.
    if {"run", "module", "name", "type"}.issubset(header):
        return None

    # Real VaN3Twin/ns-3 CAM receiver log:
    # messageId,camId,timestamp,latitude,longitude,heading,speed,acceleration
    if {
        "messageid",
        "camid",
        "timestamp",
        "latitude",
        "longitude",
        "heading",
        "speed",
        "acceleration",
    }.issubset(header):
        return "cam_receiver_log"

    # Mini synthetic fixture format
    if {"timestamp_ms", "src", "dst", "pkt_id"}.issubset(header):
        if "latency_ms" in header or "sinr_db" in header or "rssi_dbm" in header:
            return "mini_phy"
        if "prr" in header or "pdr" in header:
            return "mini_prr"

    # Real-style VaN3Twin/ns-3 PHY export
    if {"tx_id", "rx_id", "distance", "rssi", "snr"}.issubset(header):
        return "real_phy"

    # Real-style VaN3Twin/ns-3 PRR export
    if {"node_id", "prr"}.issubset(header):
        return "real_prr"

    # Filename-level fallback for expected ns-3 artifacts only
    if "phy_with_sionna_nrv2x" in lower_name and {"tx_id", "rx_id"}.issubset(header):
        return "real_phy"
    if "prr_with_sionna_nrv2x" in lower_name and "prr" in header:
        return "real_prr"

    return None


def _read_mini_phy(path: Path, scenario: str, run_id: str):
    events = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            ts_ms = _to_float(row.get("timestamp_ms"))
            latency_ms = _to_float(row.get("latency_ms"))

            events.append(
                NormalizedEvent(
                    run_id=run_id,
                    scenario=scenario,
                    source_kind="phy",
                    event_type="rx",
                    ts_us=int(round(ts_ms * 1000.0)) if ts_ms is not None else None,
                    src_id=(row.get("src") or "").strip() or None,
                    dst_id=(row.get("dst") or "").strip() or None,
                    pkt_id=(row.get("pkt_id") or "").strip() or None,
                    latency_us=(latency_ms * 1000.0) if latency_ms is not None else None,
                    rssi_dbm=_to_float(row.get("rssi_dbm")),
                    sinr_db=_to_float(row.get("sinr_db")),
                    success=_to_bool(row.get("success")),
                    raw_file=str(path),
                    raw_row_num=row_num,
                )
            )
    return events


def _read_mini_prr(path: Path, scenario: str, run_id: str):
    events = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            ts_ms = _to_float(row.get("timestamp_ms"))
            success = _to_bool(row.get("success"))

            if success is True:
                event_type = "rx"
            elif success is False:
                event_type = "drop"
            else:
                event_type = "prr"

            events.append(
                NormalizedEvent(
                    run_id=run_id,
                    scenario=scenario,
                    source_kind="prr",
                    event_type=event_type,
                    ts_us=int(round(ts_ms * 1000.0)) if ts_ms is not None else None,
                    src_id=(row.get("src") or "").strip() or None,
                    dst_id=(row.get("dst") or "").strip() or None,
                    pkt_id=(row.get("pkt_id") or "").strip() or None,
                    prr_value=_to_float(row.get("prr")),
                    pdr_value=_to_float(row.get("pdr")),
                    success=success,
                    raw_file=str(path),
                    raw_row_num=row_num,
                )
            )
    return events


def _read_real_phy(path: Path, scenario: str, run_id: str):
    events = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            events.append(
                NormalizedEvent(
                    run_id=run_id,
                    scenario=scenario,
                    source_kind="phy",
                    event_type="phy",
                    src_id=(row.get("tx_id") or "").strip() or None,
                    dst_id=(row.get("rx_id") or "").strip() or None,
                    distance_m=_to_float(row.get("distance")),
                    rssi_dbm=_to_float(row.get("rssi")),
                    sinr_db=_to_float(row.get("snr")),
                    raw_file=str(path),
                    raw_row_num=row_num,
                )
            )
    return events


def _read_real_prr(path: Path, scenario: str, run_id: str):
    events = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            node_id = (row.get("node_id") or "").strip() or None
            events.append(
                NormalizedEvent(
                    run_id=run_id,
                    scenario=scenario,
                    source_kind="prr",
                    event_type="prr",
                    src_id=node_id,
                    prr_value=_to_float(row.get("prr")),
                    raw_file=str(path),
                    raw_row_num=row_num,
                )
            )
    return events


def _extract_vehicle_id_from_cam_filename(path: Path):
    match = re.search(r"-veh(\d+)-cam\.csv$", path.name, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def _read_cam_receiver_log(path: Path, scenario: str, run_id: str):
    events = []
    vehicle_id = _extract_vehicle_id_from_cam_filename(path)

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            timestamp = _to_float(row.get("timestamp"))
            cam_id = (row.get("camId") or row.get("camid") or "").strip() or None

            events.append(
                NormalizedEvent(
                    run_id=run_id,
                    scenario=scenario,
                    source_kind="cam",
                    event_type="rx",
                    ts_us=int(round(timestamp * 1000.0)) if timestamp is not None else None,
                    src_id=cam_id,
                    dst_id=vehicle_id,
                    pkt_id=None,
                    speed_mps=_to_float(row.get("speed")),
                    acceleration_mps2=_to_float(row.get("acceleration")),
                    raw_file=str(path),
                    raw_row_num=row_num,
                )
            )

    return events


def _iter_candidate_csvs(input_path: Path):
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".csv" else []
    if input_path.is_dir():
        return sorted(input_path.glob("*.csv"))
    return []


def read_artifacts(input_dir, scenario, run_id):
    input_path = Path(input_dir)

    events = []
    input_files = []
    reader_diagnostics = []

    for path in _iter_candidate_csvs(input_path):
        artifact_type = _classify_artifact(path)
        if artifact_type is None:
            continue

        input_files.append(str(path))

        if artifact_type == "mini_phy":
            events.extend(_read_mini_phy(path, scenario, run_id))
        elif artifact_type == "mini_prr":
            events.extend(_read_mini_prr(path, scenario, run_id))
        elif artifact_type == "real_phy":
            events.extend(_read_real_phy(path, scenario, run_id))
        elif artifact_type == "real_prr":
            events.extend(_read_real_prr(path, scenario, run_id))
        elif artifact_type == "cam_receiver_log":
            events.extend(_read_cam_receiver_log(path, scenario, run_id))

    return events, reader_diagnostics, input_files