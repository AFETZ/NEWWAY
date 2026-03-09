import math
from statistics import mean


def _avg(values):
    values = [v for v in values if v is not None]
    return mean(values) if values else None


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


def build_aggregates(events, run_id, scenario, input_files_count):
    latencies = [e.latency_us for e in events if e.latency_us is not None]
    sinrs = [e.sinr_db for e in events if e.sinr_db is not None]
    blers = [e.bler for e in events if e.bler is not None]
    prrs = [e.prr_value for e in events if e.prr_value is not None]
    pdrs = [e.pdr_value for e in events if e.pdr_value is not None]

    success_count = sum(1 for e in events if e.success is True)
    tx_count = sum(1 for e in events if str(e.event_type).lower() == "tx")
    rx_count = sum(1 for e in events if str(e.event_type).lower() == "rx")

    ratio_from_counts = None
    if tx_count > 0:
        ratio_from_counts = rx_count / tx_count

    has_success_signal = any(e.success is not None for e in events)
    success_ratio = (success_count / len(events)) if events and has_success_signal else None

    prr_mean = _avg(prrs)
    if prr_mean is None:
        prr_mean = ratio_from_counts if ratio_from_counts is not None else success_ratio

    pdr_mean = _avg(pdrs)
    if pdr_mean is None and ratio_from_counts is not None:
        pdr_mean = ratio_from_counts

    return {
        "run_id": run_id,
        "scenario": scenario,
        "rows_total": len(events),
        "input_files_count": input_files_count,
        "success_count": success_count,
        "tx_count": tx_count,
        "rx_count": rx_count,
        "prr_mean": prr_mean,
        "pdr_mean": pdr_mean,
        "latency_mean_us": _avg(latencies),
        "latency_p50_us": _percentile(latencies, 50),
        "latency_p95_us": _percentile(latencies, 95),
        "sinr_mean_db": _avg(sinrs),
        "bler_mean": _avg(blers),
    }
