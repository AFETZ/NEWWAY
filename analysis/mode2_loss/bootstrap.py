#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path


def ensure_deps(required_modules: list[str] | None = None) -> None:
    """Ensure required python deps are available via a local venv and re-exec if needed."""
    if required_modules is None:
        required_modules = ["pandas", "matplotlib", "yaml"]

    try:
        for mod in required_modules:
            __import__(mod)
        return
    except Exception:
        if os.environ.get("MODE2_VENV_ACTIVE") == "1":
            raise

    script_dir = Path(__file__).resolve().parent
    venv_dir = script_dir / ".venv"
    venv_python = venv_dir / "bin" / "python"
    requirements = script_dir / "requirements.txt"

    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    # Upgrade pip and install requirements
    subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
    if requirements.exists():
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", str(requirements)])
    else:
        # Fallback if requirements.txt is missing
        subprocess.check_call([str(venv_python), "-m", "pip", "install"] + required_modules)

    env = os.environ.copy()
    env["MODE2_VENV_ACTIVE"] = "1"
    os.execvpe(str(venv_python), [str(venv_python)] + sys.argv, env)


if __name__ == "__main__":
    ensure_deps()
