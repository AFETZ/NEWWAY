import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class Simu5GCliSmokeTest(unittest.TestCase):
    def test_cli_build_for_simu5g_source(self):
        repo_root = Path(__file__).resolve().parents[2]
        fixture_path = Path(__file__).resolve().parent / "data" / "simu5g_scavetool_sample.csv"

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "cli-simu5g-out"

            cmd = [
                sys.executable,
                "-m",
                "tools.results_pipeline.cli",
                "build",
                "--source",
                "simu5g",
                "--input",
                str(fixture_path),
                "--output",
                str(output_dir),
                "--scenario",
                "minimal-simu5g",
                "--run-id",
                "cli-simu5g-test-001",
            ]

            result = subprocess.run(
                cmd,
                check=True,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.assertTrue(result.stdout.strip() != "")
            self.assertTrue((output_dir / "normalized_events.csv").exists())
            self.assertTrue((output_dir / "aggregates_by_metric.csv").exists())
            self.assertTrue((output_dir / "aggregates_overall.csv").exists())
            self.assertTrue((output_dir / "diagnostics.csv").exists())

            with (output_dir / "aggregates_overall.csv").open("r", newline="", encoding="utf-8") as f:
                row = next(csv.DictReader(f))

            self.assertEqual(row["run_id"], "cli-simu5g-test-001")
            self.assertEqual(row["source_stack"], "simu5g")
            self.assertEqual(row["rows_total"], "5")


if __name__ == "__main__":
    unittest.main()
