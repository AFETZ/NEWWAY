import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline


class SmokePipelineTest(unittest.TestCase):
    def test_build_pipeline_on_small_fixture(self):
        fixture_root = Path(__file__).resolve().parent / "data"

        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "input"
            output_dir = Path(tmp) / "output"
            input_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy2(fixture_root / "mini_phy_with_sionna_nrv2x.csv", input_dir / "mini_phy_with_sionna_nrv2x.csv")
            shutil.copy2(fixture_root / "mini_prr_with_sionna_nrv2x.csv", input_dir / "mini_prr_with_sionna_nrv2x.csv")

            result = build_pipeline(
                input_dir=input_dir,
                output_dir=output_dir,
                scenario="v2v-cam-exchange-sionna-nrv2x",
                run_id="smoke-cli-001",
            )

            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "normalized_metrics.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())
            self.assertIn("normalized_metrics", result)

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                event_rows = list(csv.DictReader(f))

            self.assertEqual(len(event_rows), 4)

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))

            self.assertEqual(len(metric_rows), 10)
            self.assertTrue(any(r["metric_name"] == "latency_us" and r["unit"] == "us" for r in metric_rows))
            self.assertTrue(any(r["metric_name"] == "rssi_dbm" and r["unit"] == "dBm" for r in metric_rows))
            self.assertTrue(any(r["metric_name"] == "sinr_db" and r["unit"] == "dB" for r in metric_rows))
            self.assertTrue(any(r["metric_name"] == "prr_value" and r["unit"] == "ratio" for r in metric_rows))
            self.assertTrue(any(r["metric_name"] == "pdr_value" and r["unit"] == "ratio" for r in metric_rows))
            self.assertTrue(all(r["source_stack"] == "van3twin_ns3" for r in metric_rows))

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            self.assertEqual(row["run_id"], "smoke-cli-001")
            self.assertEqual(row["rows_total"], "4")
            self.assertEqual(row["input_files_count"], "2")
            self.assertAlmostEqual(float(row["prr_mean"]), 0.75, places=6)
            self.assertAlmostEqual(float(row["pdr_mean"]), 0.75, places=6)
            self.assertAlmostEqual(float(row["latency_mean_us"]), 11000.0, places=6)
            self.assertAlmostEqual(float(row["sinr_mean_db"]), 19.0, places=6)

    def test_build_pipeline_on_single_csv_fixture(self):
        fixture_root = Path(__file__).resolve().parent / "data"
        input_file = fixture_root / "mini_phy_with_sionna_nrv2x.csv"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "output"

            result = build_pipeline(
                input_path=input_file,
                output_dir=output_dir,
                scenario="single-file-ns3",
                run_id="smoke-single-file-001",
            )

            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "normalized_metrics.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())
            self.assertIn("normalized_metrics", result)

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                event_rows = list(csv.DictReader(f))
            self.assertEqual(len(event_rows), 2)

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                metric_rows = list(csv.DictReader(f))
            self.assertEqual(len(metric_rows), 6)
            self.assertTrue(all(r["source_stack"] == "van3twin_ns3" for r in metric_rows))

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            self.assertEqual(row["run_id"], "smoke-single-file-001")
            self.assertEqual(row["rows_total"], "2")
            self.assertEqual(row["input_files_count"], "1")
            self.assertAlmostEqual(float(row["latency_mean_us"]), 11000.0, places=6)
            self.assertAlmostEqual(float(row["sinr_mean_db"]), 19.0, places=6)


if __name__ == "__main__":
    unittest.main()