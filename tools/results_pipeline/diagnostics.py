def issue(issue_type, count, details="", sample_ref=""):
    return {
        "issue_type": issue_type,
        "count": count,
        "details": details,
        "sample_ref": sample_ref,
    }


def build_diagnostics(events, reader_diagnostics):
    diagnostics = list(reader_diagnostics)

    if not events:
        diagnostics.append(issue("empty_input", 1, "No rows were normalized"))
        return diagnostics

    negative_latency = [e for e in events if e.latency_us is not None and e.latency_us < 0]
    if negative_latency:
        sample = negative_latency[0]
        diagnostics.append(
            issue(
                "negative_latency",
                len(negative_latency),
                "Rows with latency_us < 0",
                f"{sample.raw_file}:{sample.raw_row_num}",
            )
        )

    missing_pkt = [e for e in events if e.source_kind not in {"phy", "prr"} and not e.pkt_id]
    if missing_pkt:
        sample = missing_pkt[0]
        diagnostics.append(
            issue(
                "missing_pkt_id",
                len(missing_pkt),
                "Rows without pkt_id",
                f"{sample.raw_file}:{sample.raw_row_num}",
            )
        )

    missing_ts = [e for e in events if e.source_kind not in {"phy", "prr"} and e.ts_us is None]
    if missing_ts:
        sample = missing_ts[0]
        diagnostics.append(
            issue(
                "missing_ts_us",
                len(missing_ts),
                "Rows without normalized timestamp",
                f"{sample.raw_file}:{sample.raw_row_num}",
            )
        )

    no_metric_or_success = [
        e for e in events
        if e.source_kind not in {"phy", "prr"}
        and e.prr_value is None and e.pdr_value is None and e.success is None
    ]
    if no_metric_or_success:
        sample = no_metric_or_success[0]
        diagnostics.append(
            issue(
                "no_prr_pdr_success_signal",
                len(no_metric_or_success),
                "Rows do not expose prr/pdr/success fields",
                f"{sample.raw_file}:{sample.raw_row_num}",
            )
        )

    return diagnostics
