import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline


class RealFormatFixtureTest(unittest.TestCase):
    def test_build_pipeline_on_real_style_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            output_dir = tmp_path / "out"
            input_dir.mkdir(parents=True, exist_ok=True)

            (input_dir / "phy_with_sionna_nrv2x.csv").write_text(
                "tx_id,rx_id,distance,rssi,snr\n8,1,100.0,-90.0,10.0\n8,2,200.0,-80.0,20.0\n",
                encoding="utf-8"
            )
            (input_dir / "prr_with_sionna_nrv2x.csv").write_text(
                "node_id,prr\n1,0.8\n2,0.6\n",
                encoding="utf-8"
            )

            build_pipeline(
                input_dir=input_dir,
                output_dir=output_dir,
                scenario="v2v-cam-exchange-sionna-nrv2x",
                run_id="real-format-001",
            )

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            self.assertEqual(row["rows_total"], "4")
            self.assertAlmostEqual(float(row["prr_mean"]), 0.7, places=6)
            self.assertAlmostEqual(float(row["sinr_mean_db"]), 15.0, places=6)
            self.assertEqual(row["pdr_mean"], "")

            with (output_dir / "diagnostics.csv").open("r", newline="", encoding="utf-8") as f:
                diag_rows = list(csv.DictReader(f))

            self.assertEqual(len(diag_rows), 0)

            with (output_dir / "normalized_events.csv").open("r", newline="", encoding="utf-8") as f:
                norm_rows = list(csv.DictReader(f))

            self.assertEqual(norm_rows[0]["distance_m"], "100.0")
            self.assertEqual(norm_rows[0]["sinr_db"], "10.0")


if __name__ == "__main__":
    unittest.main()
