import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.simu5g_pipeline import build_simu5g_pipeline


class Simu5GPipelineTest(unittest.TestCase):
    def test_build_simu5g_pipeline(self):
        fixture_path = Path(__file__).resolve().parent / "data" / "simu5g_scavetool_sample.csv"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "simu5g-results"

            build_simu5g_pipeline(
                input_csv=fixture_path,
                output_dir=output_dir,
                scenario="minimal-simu5g",
                run_id="simu5g-pipeline-001",
            )

            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "normalized_metrics.csv").exists())
            self.assertTrue((output_dir / "aggregates_by_metric.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())
            self.assertTrue((output_dir / "run_metadata.yaml").exists())

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                normalized_rows = list(csv.DictReader(f))

            self.assertEqual(len(normalized_rows), 5)

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))

            self.assertEqual(len(metric_rows), 5)
            self.assertEqual(metric_rows[0]["source_stack"], "simu5g")

            with (output_dir / "aggregates_by_metric.csv").open("r", newline="", encoding="utf-8") as f:
                agg_rows = list(csv.DictReader(f))

            self.assertEqual(len(agg_rows), 4)

            sinr_row = next(r for r in agg_rows if r["metric_name"] == "sinr_db")
            self.assertAlmostEqual(float(sinr_row["value_mean"]), 12.75, places=6)
            self.assertEqual(sinr_row["sample_kind"], "vector")

            delay_row = next(r for r in agg_rows if r["metric_name"] == "delay_us")
            self.assertAlmostEqual(float(delay_row["value_mean"]), 15000.0, places=6)

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                overall_row = next(csv.DictReader(f))

            self.assertEqual(overall_row["run_id"], "simu5g-pipeline-001")
            self.assertEqual(overall_row["source_stack"], "simu5g")
            self.assertEqual(overall_row["rows_total"], "5")
            self.assertAlmostEqual(float(overall_row["throughput_mean_bps"]), 1250000.0, places=6)
            self.assertAlmostEqual(float(overall_row["delay_mean_us"]), 15000.0, places=6)
            self.assertAlmostEqual(float(overall_row["sinr_mean_db"]), 12.75, places=6)
            self.assertAlmostEqual(float(overall_row["loss_ratio_mean"]), 0.05, places=6)

            with (output_dir / "diagnostics.csv").open("r", newline="", encoding="utf-8") as f:
                diag_rows = list(csv.DictReader(f))

            self.assertEqual(len(diag_rows), 0)


if __name__ == "__main__":
    unittest.main()
