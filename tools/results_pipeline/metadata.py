import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import __version__


REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_value(args):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def build_metadata(run_id, scenario, input_files):
    return {
        "run_id": run_id,
        "scenario": scenario,
        "source": "van3twin_csv",
        "pipeline_version": __version__,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_branch": _git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "git_commit": _git_value(["rev-parse", "HEAD"]),
        "input_files": [str(p) for p in input_files],
    }
