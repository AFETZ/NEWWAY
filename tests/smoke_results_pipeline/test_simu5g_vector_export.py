import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.simu5g_pipeline import build_simu5g_pipeline


class Simu5GVectorExportTest(unittest.TestCase):
    def test_scavetool_vector_rows_are_expanded(self):
        fixture_path = (
            Path(__file__).resolve().parent
            / "data"
            / "simu5g_scavetool_vector_sinr_sample.csv"
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "simu5g-vector-output"

            build_simu5g_pipeline(
                input_csv=fixture_path,
                output_dir=output_dir,
                scenario="simu5g-vector-sample",
                run_id="simu5g-vector-test-001",
            )

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))

            self.assertEqual(len(metric_rows), 5)
            self.assertTrue(all(row["source_stack"] == "simu5g" for row in metric_rows))
            self.assertTrue(all(row["sample_kind"] == "vector" for row in metric_rows))
            self.assertTrue(all(row["metric_name"] == "sinr_db" for row in metric_rows))
            self.assertTrue(all(row["unit"] == "dB" for row in metric_rows))

            self.assertTrue(any(row["entity_id"] == "ue[0]" for row in metric_rows))
            self.assertTrue(any(row["entity_id"] == "ue[1]" for row in metric_rows))
            self.assertTrue(any(row["ts_us"] == "100000" and row["value"] == "37.1" for row in metric_rows))
            self.assertTrue(any(row["ts_us"] == "500000" and row["value"] == "21.0" for row in metric_rows))

            with (output_dir / "aggregates_by_metric.csv").open("r", newline="", encoding="utf-8") as f:
                aggregate_rows = list(csv.DictReader(f))

            sinr_row = next(row for row in aggregate_rows if row["metric_name"] == "sinr_db")
            self.assertEqual(sinr_row["rows_count"], "5")
            self.assertEqual(sinr_row["sample_kind"], "vector")
            self.assertEqual(sinr_row["entity_count"], "2")

            with (output_dir / "diagnostics.csv").open("r", newline="", encoding="utf-8") as f:
                diagnostics = list(csv.DictReader(f))

            issue_types = {row["issue_type"] for row in diagnostics}
            self.assertNotIn("empty_input", issue_types)
            self.assertNotIn("vector_length_mismatch", issue_types)


if __name__ == "__main__":
    unittest.main()
