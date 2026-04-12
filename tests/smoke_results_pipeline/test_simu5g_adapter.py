import unittest
from pathlib import Path

from tools.results_pipeline.readers.simu5g_scavetool_csv import read_simu5g_scavetool_csv


class Simu5GAdapterTest(unittest.TestCase):
    def test_read_simu5g_scavetool_csv(self):
        fixture_path = Path(__file__).resolve().parent / "data" / "simu5g_scavetool_sample.csv"

        rows = read_simu5g_scavetool_csv(
            path=fixture_path,
            scenario="minimal-simu5g",
            run_id="simu5g-smoke-001",
        )

        self.assertEqual(len(rows), 5)

        throughput_row = rows[0]
        self.assertEqual(throughput_row["source_stack"], "simu5g")
        self.assertEqual(throughput_row["metric_name"], "throughput_bps")
        self.assertEqual(throughput_row["sample_kind"], "scalar")
        self.assertEqual(throughput_row["entity_id"], "ue[0]")
        self.assertAlmostEqual(throughput_row["value"], 1250000.0, places=6)
        self.assertEqual(throughput_row["unit"], "bps")

        delay_row = rows[1]
        self.assertEqual(delay_row["metric_name"], "delay_us")
        self.assertAlmostEqual(delay_row["value"], 15000.0, places=6)
        self.assertEqual(delay_row["unit"], "us")

        sinr_row = rows[2]
        self.assertEqual(sinr_row["metric_name"], "sinr_db")
        self.assertEqual(sinr_row["sample_kind"], "vector")
        self.assertEqual(sinr_row["ts_us"], 100000)
        self.assertAlmostEqual(sinr_row["value"], 12.5, places=6)
        self.assertEqual(sinr_row["entity_id"], "ue[0]")

        loss_row = rows[4]
        self.assertEqual(loss_row["metric_name"], "loss_ratio")
        self.assertAlmostEqual(loss_row["value"], 0.05, places=6)


if __name__ == "__main__":
    unittest.main()

