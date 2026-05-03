import io
import threading
import unittest
from pathlib import Path
from unittest import mock

from tools.scenario_manager import runner
from tools.scenario_manager.scenarios import ROOT, get_scenario, list_scenarios


class _FakePopen:
    last_env = None
    last_cmd = None
    last_cwd = None

    def __init__(self, cmd, stdout, stderr, env, cwd, text, bufsize):
        type(self).last_cmd = cmd
        type(self).last_env = env
        type(self).last_cwd = cwd
        self.stdout = io.StringIO("starting\nDone: ok\n")
        self.returncode = 0

    def wait(self):
        return self.returncode


class ScenarioRegistryTest(unittest.TestCase):
    def test_registry_contains_expected_five_scenarios(self):
        scenario_ids = [scenario.id for scenario in list_scenarios()]
        self.assertEqual(
            scenario_ids,
            [
                "burst_vs_random_loss",
                "density_scaling",
                "latency_vs_loss_tradeoff",
                "truck_lane_change",
                "intersection_crash",
            ],
        )

    def test_all_registered_run_scripts_exist(self):
        for scenario in list_scenarios():
            script_path = ROOT / scenario.run_script
            self.assertTrue(
                script_path.exists(),
                f"Missing run script for {scenario.id}: {script_path}",
            )


class RunnerContractTest(unittest.TestCase):
    @mock.patch("tools.scenario_manager.runner.subprocess.Popen", new=_FakePopen)
    def test_runner_uses_out_base_for_sweep_scenarios(self):
        scenario = get_scenario("burst_vs_random_loss")
        lines = []

        result = runner.run_scenario(scenario, {"SUMO_GUI": "0"}, on_line=lines.append)

        self.assertEqual(_FakePopen.last_cmd[0], "bash")
        self.assertIn("OUT_BASE", _FakePopen.last_env)
        self.assertEqual(_FakePopen.last_env["OUT_BASE"], result.out_dir)
        self.assertTrue(Path(result.out_dir).name.startswith("burst_vs_random_loss-"))
        self.assertEqual(lines[-1], "Done: ok")

    @mock.patch("tools.scenario_manager.runner.subprocess.Popen", new=_FakePopen)
    def test_runner_uses_out_dir_for_fixed_scenarios(self):
        scenario = get_scenario("truck_lane_change")

        result = runner.run_scenario(
            scenario,
            {"SUMO_GUI": "0", "OUT_DIR": "/tmp/newway-truck-lane-change"},
        )

        self.assertEqual(_FakePopen.last_env["OUT_DIR"], "/tmp/newway-truck-lane-change")
        self.assertEqual(result.out_dir, "/tmp/newway-truck-lane-change")

    @mock.patch("tools.scenario_manager.runner.subprocess.Popen", new=_FakePopen)
    def test_runner_invokes_callback_on_caller_thread(self):
        scenario = get_scenario("burst_vs_random_loss")
        caller_thread_id = threading.get_ident()
        callback_thread_ids: list[int] = []

        runner.run_scenario(
            scenario,
            {"SUMO_GUI": "0"},
            on_line=lambda _line: callback_thread_ids.append(threading.get_ident()),
        )

        self.assertTrue(callback_thread_ids)
        self.assertTrue(all(tid == caller_thread_id for tid in callback_thread_ids))


if __name__ == "__main__":
    unittest.main()
