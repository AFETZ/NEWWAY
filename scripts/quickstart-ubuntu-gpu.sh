#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$ROOT/scripts/bootstrap-ubuntu-docker-gpu.sh" ]]; then
  echo "Missing bootstrap script: $ROOT/scripts/bootstrap-ubuntu-docker-gpu.sh" >&2
  exit 1
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  scripts/quickstart-ubuntu-gpu.sh

What it does:
  1) Installs/updates Docker + NVIDIA Container Toolkit on Ubuntu host.
  2) Validates GPU access in Docker.
  3) Builds project Docker image.
  4) Runs default local EVA+Sionna scenario in container.
EOF
  exit 0
fi

RUN_AFTER_SETUP=1 "$ROOT/scripts/bootstrap-ubuntu-docker-gpu.sh"
