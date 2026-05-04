import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline
from tools.results_pipeline.simu5g_pipeline import build_simu5g_pipeline


class ResultsPipelineUserLayerSamplesTest(unittest.TestCase):
    def test_van3twin_user_sample_input_is_processable(self):
        repo_root = Path(__file__).resolve().parents[2]
        input_dir = repo_root / "scripts" / "results_pipeline" / "sample_inputs" / "van3twin_cam"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "van3twin-user-layer-output"

            build_pipeline(
                input_dir=input_dir,
                output_dir=output_dir,
                scenario="user-layer-van3twin-test",
                run_id="user-layer-van3twin-001",
            )

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            metric_names = {row["metric_name"] for row in rows}
            self.assertIn("cam_rx_count", metric_names)
            self.assertIn("speed_mps", metric_names)
            self.assertIn("acceleration_mps2", metric_names)

    def test_simu5g_user_sample_input_is_processable(self):
        repo_root = Path(__file__).resolve().parents[2]
        input_csv = repo_root / "scripts" / "results_pipeline" / "sample_inputs" / "simu5g_scavetool" / "output_all_sample.csv"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "simu5g-user-layer-output"

            build_simu5g_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                scenario="user-layer-simu5g-test",
                run_id="user-layer-simu5g-001",
            )

            with (output_dir / "normalized_metrics.csv").open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 5)
            self.assertTrue(all(row["metric_name"] == "sinr_db" for row in rows))
            self.assertTrue(all(row["sample_kind"] == "vector" for row in rows))


if __name__ == "__main__":
    unittest.main()
