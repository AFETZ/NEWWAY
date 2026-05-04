import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline


class Van3TwinCamLogsTest(unittest.TestCase):
    def test_build_pipeline_on_cam_receiver_logs(self):
        fixture_dir = Path(__file__).resolve().parent / "data" / "van3twin_cam_sample"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "van3twin-cam-output"

            result = build_pipeline(
                input_dir=fixture_dir,
                output_dir=output_dir,
                scenario="van3twin-cam-sample",
                run_id="van3twin-cam-test-001",
            )

            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "normalized_metrics.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())
            self.assertIn("normalized_metrics", result)

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                event_rows = list(csv.DictReader(f))

            self.assertEqual(len(event_rows), 5)
            self.assertTrue(all(row["source_kind"] == "cam" for row in event_rows))
            self.assertTrue(all(row["event_type"] == "rx" for row in event_rows))
            self.assertTrue(any(row["src_id"] == "3" and row["dst_id"] == "1" for row in event_rows))
            self.assertTrue(any(row["src_id"] == "1" and row["dst_id"] == "2" for row in event_rows))
            self.assertTrue(any(row["ts_us"] == "3125000" for row in event_rows))

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))

            metric_names = {row["metric_name"] for row in metric_rows}

            self.assertIn("cam_rx_count", metric_names)
            self.assertIn("speed_mps", metric_names)
            self.assertIn("acceleration_mps2", metric_names)
            self.assertTrue(all(row["source_stack"] == "van3twin_ns3" for row in metric_rows))
            self.assertEqual(
                sum(1 for row in metric_rows if row["metric_name"] == "cam_rx_count"),
                5,
            )

            with (output_dir / "diagnostics.csv").open("r", newline="", encoding="utf-8") as f:
                diagnostics = list(csv.DictReader(f))

            issue_types = {row["issue_type"] for row in diagnostics}
            self.assertNotIn("missing_pkt_id", issue_types)
            self.assertNotIn("no_prr_pdr_success_signal", issue_types)


if __name__ == "__main__":
    unittest.main()
