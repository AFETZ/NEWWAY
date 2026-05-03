"""
Scenario runner — executes experiment scripts and streams output.
"""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .scenarios import ROOT, Scenario


@dataclass
class RunResult:
    scenario_id: str
    out_dir: str
    return_code: int
    duration_s: float
    log_lines: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.return_code == 0


def _default_output_dir(scenario: Scenario) -> str:
    date_tag = time.strftime("%Y-%m-%d")
    time_tag = time.strftime("%H%M%S")
    return str(
        ROOT / "analysis" / "scenario_runs" / date_tag / f"{scenario.id}-{time_tag}"
    )


def run_scenario(
    scenario: Scenario,
    params: dict[str, str],
    on_line: Callable[[str], None] | None = None,
) -> RunResult:
    """
    Execute the scenario's run script with the given parameters as env vars.
    Streams stdout/stderr line-by-line through *on_line* callback.

    The callback is invoked on the caller thread so UI frameworks such as
    Streamlit can safely update widgets while the subprocess is running.
    """
    script = ROOT / scenario.run_script
    if not script.exists():
        raise FileNotFoundError(f"Run script not found: {script}")

    env = os.environ.copy()
    # Propagate all params as env vars (scenario scripts read them)
    for k, v in params.items():
        env[k] = str(v)

    # Ensure the scenario-specific output directory variable is set.
    out_env_var = scenario.output_env_var
    out_dir = params.get(out_env_var, "")
    if not out_dir:
        out_dir = _default_output_dir(scenario)
        env[out_env_var] = out_dir

    log_lines: list[str] = []
    t0 = time.monotonic()

    proc = subprocess.Popen(
        ["bash", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(ROOT),
        text=True,
        bufsize=1,
    )

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n")
        log_lines.append(line)
        if on_line:
            on_line(line)
    proc.wait()

    duration = time.monotonic() - t0
    return RunResult(
        scenario_id=scenario.id,
        out_dir=out_dir,
        return_code=proc.returncode,
        duration_s=duration,
        log_lines=log_lines,
    )


def find_latest_run(scenario_id: str) -> Path | None:
    """Find the most recent run directory for a given scenario."""
    runs_root = ROOT / "analysis" / "scenario_runs"
    if not runs_root.exists():
        return None

    candidates: list[Path] = []
    for date_dir in sorted(runs_root.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for run_dir in sorted(date_dir.iterdir(), reverse=True):
            if run_dir.is_dir() and scenario_id in run_dir.name:
                candidates.append(run_dir)
    return candidates[0] if candidates else None
