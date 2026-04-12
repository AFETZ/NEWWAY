import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline


class Van3TwinSourceFilterTest(unittest.TestCase):
    def test_build_pipeline_ignores_foreign_simu5g_csv(self):
        fixture_root = Path(__file__).resolve().parent / "data"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "output"

            result = build_pipeline(
                input_dir=fixture_root,
                output_dir=output_dir,
                scenario="v2v-cam-exchange-sionna-nrv2x",
                run_id="mixed-source-001",
            )

            self.assertIn("normalized_metrics", result)

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                event_rows = list(csv.DictReader(f))

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                overall_row = next(csv.DictReader(f))

            with (output_dir / "diagnostics.csv").open("r", newline="", encoding="utf-8") as f:
                diagnostic_rows = list(csv.DictReader(f))

            self.assertEqual(len(event_rows), 8)
            self.assertEqual(len(metric_rows), 18)
            self.assertEqual(overall_row["rows_total"], "8")
            self.assertEqual(overall_row["input_files_count"], "4")

            self.assertTrue(all("simu5g_scavetool_sample.csv" not in r["raw_file"] for r in event_rows))
            self.assertTrue(all("simu5g_scavetool_sample.csv" not in r["input_file"] for r in metric_rows))
            self.assertTrue(all("simu5g_scavetool_sample.csv" not in r["sample_ref"] for r in diagnostic_rows))


if __name__ == "__main__":
    unittest.main()
