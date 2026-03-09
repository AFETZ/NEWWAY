from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class NormalizedEvent:
    run_id: str
    scenario: str
    source_kind: str
    event_type: str
    ts_us: Optional[int] = None
    src_id: Optional[str] = None
    dst_id: Optional[str] = None
    pkt_id: Optional[str] = None
    size_bytes: Optional[int] = None
    latency_us: Optional[float] = None
    rssi_dbm: Optional[float] = None
    sinr_db: Optional[float] = None
    bler: Optional[float] = None
    distance_m: Optional[float] = None
    prr_value: Optional[float] = None
    pdr_value: Optional[float] = None
    success: Optional[bool] = None
    drop_reason: Optional[str] = None
    raw_file: str = ""
    raw_row_num: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


NORMALIZED_EVENT_FIELDS = list(NormalizedEvent.__dataclass_fields__.keys())

AGGREGATE_FIELDS = [
    "run_id",
    "scenario",
    "rows_total",
    "input_files_count",
    "success_count",
    "tx_count",
    "rx_count",
    "prr_mean",
    "pdr_mean",
    "latency_mean_us",
    "latency_p50_us",
    "latency_p95_us",
    "sinr_mean_db",
    "bler_mean",
]

DIAGNOSTIC_FIELDS = ["issue_type", "count", "details", "sample_ref"]
