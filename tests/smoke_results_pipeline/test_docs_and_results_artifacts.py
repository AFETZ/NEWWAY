import csv
import unittest
from pathlib import Path


class DocsAndResultsArtifactsTest(unittest.TestCase):
    def test_developer_docs_and_contracts_exist(self):
        repo_root = Path(__file__).resolve().parents[2]

        expected_docs = [
            repo_root / "docs" / "results_pipeline_developer_guide.md",
            repo_root / "docs" / "results_pipeline_delivery_scope.md",
            repo_root / "docs" / "results_pipeline_handoff_checklist.md",
            repo_root / "docs" / "results_pipeline_user_layer_behavior.md",
            repo_root / "docs" / "van3twin_input_contract.md",
            repo_root / "docs" / "simu5g_input_contract.md",
        ]

        for path in expected_docs:
            self.assertTrue(path.exists(), f"Missing developer doc: {path}")

    def test_contracts_mention_supported_sources(self):
        repo_root = Path(__file__).resolve().parents[2]
        van3twin_contract = (repo_root / "docs" / "van3twin_input_contract.md").read_text(encoding="utf-8")
        simu5g_contract = (repo_root / "docs" / "simu5g_input_contract.md").read_text(encoding="utf-8")

        self.assertIn("camId", van3twin_contract)
        self.assertIn("speed_mps", van3twin_contract)
        self.assertIn("acceleration_mps2", van3twin_contract)

        self.assertIn("vectime", simu5g_contract)
        self.assertIn("vecvalue", simu5g_contract)
        self.assertIn("sinr_db", simu5g_contract)

    def test_canonical_sample_outputs_exist_and_are_readable(self):
        repo_root = Path(__file__).resolve().parents[2]
        results_root = repo_root / "experiments" / "results_pipeline" / "results"
        van3twin_metrics = results_root / "van3twin_sample" / "normalized_metrics.csv"
        simu5g_metrics = results_root / "simu5g_sample" / "normalized_metrics.csv"

        self.assertTrue(van3twin_metrics.exists(), f"Missing: {van3twin_metrics}")
        self.assertTrue(simu5g_metrics.exists(), f"Missing: {simu5g_metrics}")

        with van3twin_metrics.open("r", newline="", encoding="utf-8") as f:
            van3twin_rows = list(csv.DictReader(f))

        with simu5g_metrics.open("r", newline="", encoding="utf-8") as f:
            simu5g_rows = list(csv.DictReader(f))

        self.assertTrue(any(row["metric_name"] == "cam_rx_count" for row in van3twin_rows))
        self.assertTrue(any(row["metric_name"] == "speed_mps" for row in van3twin_rows))
        self.assertTrue(any(row["metric_name"] == "sinr_db" for row in simu5g_rows))


if __name__ == "__main__":
    unittest.main()
