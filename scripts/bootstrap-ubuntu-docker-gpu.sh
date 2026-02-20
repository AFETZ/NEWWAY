#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_AFTER_SETUP="${RUN_AFTER_SETUP:-0}"
SKIP_DOCKER_INSTALL="${SKIP_DOCKER_INSTALL:-0}"
SKIP_TOOLKIT_INSTALL="${SKIP_TOOLKIT_INSTALL:-0}"

usage() {
  cat <<'EOF'
Usage:
  scripts/bootstrap-ubuntu-docker-gpu.sh

Environment overrides:
  RUN_AFTER_SETUP=1      Run default EVA+Sionna docker scenario after setup.
  SKIP_DOCKER_INSTALL=1  Skip Docker Engine installation.
  SKIP_TOOLKIT_INSTALL=1 Skip NVIDIA Container Toolkit installation.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -f /etc/os-release ]]; then
  echo "Unsupported system: /etc/os-release not found." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "Warning: script is tuned for Ubuntu. Detected ID=${ID:-unknown}."
fi

if [[ "$SKIP_DOCKER_INSTALL" != "1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "[setup] Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sh
  else
    echo "[setup] Docker already installed."
  fi
else
  echo "[setup] Skipping Docker install."
fi

if command -v docker >/dev/null 2>&1; then
  if ! groups "$USER" | grep -q '\bdocker\b'; then
    echo "[setup] Adding user '$USER' to docker group..."
    sudo usermod -aG docker "$USER"
    echo "[setup] You may need to log out/in for docker group to apply."
  fi
fi

if [[ "$SKIP_TOOLKIT_INSTALL" != "1" ]]; then
  echo "[setup] Installing NVIDIA Container Toolkit..."
  distribution="$(
    . /etc/os-release
    echo "${ID}${VERSION_ID}"
  )"
  keyring="/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg"
  list_file="/etc/apt/sources.list.d/nvidia-container-toolkit.list"

  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o "$keyring"
  curl -s -L "https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list" | \
    sed "s#deb https://#deb [signed-by=${keyring}] https://#g" | \
    sudo tee "$list_file" >/dev/null

  sudo apt update
  sudo apt install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
else
  echo "[setup] Skipping NVIDIA Container Toolkit install."
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[check] Host GPU:"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
else
  echo "[check] WARNING: nvidia-smi not found on host."
fi

echo "[check] Docker GPU test..."
if ! sudo docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi >/dev/null; then
  echo "[check] WARNING: Docker GPU test failed. Check NVIDIA driver/toolkit setup." >&2
else
  echo "[check] Docker GPU test OK."
fi

echo "[build] Building project image..."
LOCAL_UID="$(id -u)" LOCAL_GID="$(id -g)" sudo docker compose -f "$ROOT/docker-compose.gpu.yml" build van3t-gpu

if [[ "$RUN_AFTER_SETUP" == "1" ]]; then
  echo "[run] Starting default EVA+Sionna scenario..."
  USE_SUDO_DOCKER=1 BUILD_IMAGE=0 "$ROOT/scripts/docker-run-eva-sionna.sh"
fi

cat <<EOF

Setup complete.
Next command:
  cd $ROOT
  scripts/docker-run-eva-sionna.sh

If docker permission is denied in current shell:
  USE_SUDO_DOCKER=1 scripts/docker-run-eva-sionna.sh
EOF
