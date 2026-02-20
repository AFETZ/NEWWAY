#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.gpu.yml"
SERVICE="van3t-gpu"
USE_SUDO_DOCKER="${USE_SUDO_DOCKER:-0}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

docker_cmd() {
  if [[ "$USE_SUDO_DOCKER" == "1" ]]; then
    sudo docker "$@"
  else
    docker "$@"
  fi
}

if [[ "$USE_SUDO_DOCKER" != "1" ]]; then
  if ! docker info >/dev/null 2>&1; then
    if command -v sudo >/dev/null 2>&1; then
      USE_SUDO_DOCKER=1
    fi
  fi
fi

if ! docker_cmd info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable. Start Docker or use USE_SUDO_DOCKER=1." >&2
  exit 1
fi

export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"

if [[ "${BUILD_IMAGE:-1}" == "1" ]]; then
  docker_cmd compose -f "$COMPOSE_FILE" build "$SERVICE"
fi

if [[ $# -gt 0 ]]; then
  docker_cmd compose -f "$COMPOSE_FILE" run --rm "$SERVICE" "$@"
  exit $?
fi

docker_cmd compose -f "$COMPOSE_FILE" run --rm "$SERVICE" \
  bash -lc "SIONNA_GPU=\${SIONNA_GPU:-1} COMPARE_NON_SIONNA=\${COMPARE_NON_SIONNA:-1} scenarios/v2v-emergencyVehicleAlert-nrv2x/run_sionna_incident_sweep.sh"
