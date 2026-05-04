import unittest
from pathlib import Path


class ResultsPipelineUserLayerStructureTest(unittest.TestCase):
    def test_user_layer_expected_files_exist(self):
        repo_root = Path(__file__).resolve().parents[2]
        user_layer = repo_root / "scripts" / "results_pipeline"

        expected_paths = [
            user_layer / "README.md",
            user_layer / "run.ps1",
            user_layer / "run_van3twin_cam.ps1",
            user_layer / "run_simu5g.ps1",
            user_layer / "sample_inputs" / "van3twin_cam" / "test_1_p0005-veh1-CAM.csv",
            user_layer / "sample_inputs" / "van3twin_cam" / "test_1_p0005-veh2-CAM.csv",
            user_layer / "sample_inputs" / "simu5g_scavetool" / "output_all_sample.csv",
        ]

        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing user-facing artifact: {path}")

    def test_readme_mentions_new_entrypoint(self):
        repo_root = Path(__file__).resolve().parents[2]
        readme = (repo_root / "scripts" / "results_pipeline" / "README.md").read_text(encoding="utf-8")

        self.assertIn(r".\scripts\results_pipeline\run.ps1", readme)
        self.assertIn("VaN3Twin", readme)
        self.assertIn("Simu5G", readme)
        self.assertIn("normalized_metrics.csv", readme)


if __name__ == "__main__":
    unittest.main()
