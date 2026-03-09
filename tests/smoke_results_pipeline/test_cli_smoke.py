import csv
import tempfile
import unittest
from pathlib import Path

from tools.results_pipeline.pipeline import build_pipeline


class SmokePipelineTest(unittest.TestCase):
    def test_build_pipeline_on_small_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            output_dir = tmp_path / "out"
            input_dir.mkdir(parents=True, exist_ok=True)

            (input_dir / "mini_phy_with_sionna_nrv2x.csv").write_text(
                "timestamp_ms,src,dst,pkt_id,latency_ms,sinr_db,rssi_dbm,success\n1.0,car1,car2,p1,10,20,-70,1\n2.0,car1,car2,p2,12,18,-72,1\n",
                encoding="utf-8"
            )
            (input_dir / "mini_prr_with_sionna_nrv2x.csv").write_text(
                "timestamp_ms,src,dst,pkt_id,prr,pdr,success\n3.0,car1,car2,p3,0.90,0.90,1\n4.0,car1,car2,p4,0.60,0.60,0\n",
                encoding="utf-8"
            )

            build_pipeline(
                input_dir=input_dir,
                output_dir=output_dir,
                scenario="v2v-cam-exchange-sionna-nrv2x",
                run_id="smoke-001",
            )

            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())
            self.assertTrue((output_dir / "run_metadata.yaml").exists())

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            self.assertEqual(row["rows_total"], "4")
            self.assertEqual(row["success_count"], "3")
            self.assertAlmostEqual(float(row["prr_mean"]), 0.75, places=6)
            self.assertAlmostEqual(float(row["pdr_mean"]), 0.75, places=6)
            self.assertAlmostEqual(float(row["latency_mean_us"]), 11000.0, places=6)


if __name__ == "__main__":
    unittest.main()
