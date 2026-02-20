# Docker deployment on Ubuntu (local GPU, no remote Sionna)

This setup is for your case: dual-boot Ubuntu + local GPU runs of `v2v-emergencyVehicleAlert-nrv2x` with Sionna.

## 1) Host prerequisites (Ubuntu)

1. Install NVIDIA driver on host and verify:

```bash
nvidia-smi
```

2. Install Docker Engine:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
```

Log out and log back in (or reboot) after adding your user to the `docker` group.

3. Install NVIDIA Container Toolkit:

```bash
distribution=$(. /etc/os-release;echo ${ID}${VERSION_ID})
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L "https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list" | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

4. Quick GPU check inside Docker:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## 2) Build and run this repository in Docker

From repository root:

```bash
scripts/docker-run-eva-sionna.sh
```

## Fast bootstrap (recommended)

If you want a single setup command on fresh Ubuntu:

```bash
scripts/bootstrap-ubuntu-docker-gpu.sh
```

It installs Docker + NVIDIA Container Toolkit, verifies GPU-in-Docker, and builds the project image.

If you want setup + first scenario run in one command:

```bash
scripts/quickstart-ubuntu-gpu.sh
```

What this does:
- builds image `van3t-gpu:local` (if `BUILD_IMAGE=1`, default);
- starts container with GPU + host network;
- runs `scenarios/v2v-emergencyVehicleAlert-nrv2x/run_sionna_incident_sweep.sh`
  with `SIONNA_GPU=1` and `COMPARE_NON_SIONNA=1` (unless you override them).

## 3) Useful variants

Run a custom command in the same container:

```bash
scripts/docker-run-eva-sionna.sh bash
```

Skip image rebuild:

```bash
BUILD_IMAGE=0 scripts/docker-run-eva-sionna.sh
```

If current shell still has docker permission issues right after install:

```bash
USE_SUDO_DOCKER=1 scripts/docker-run-eva-sionna.sh
```

Run baseline-vs-lossy visual script:

```bash
scripts/docker-run-eva-sionna.sh \
  bash scenarios/v2v-emergencyVehicleAlert-nrv2x/run_baseline_vs_lossy_visual.sh
```

## Notes

- Container definition: `docker-compose.gpu.yml`.
- Image definition: `docker/Dockerfile.gpu`.
- Repo is mounted into `/workspace`, so outputs stay on host.
- This flow is local-only (no remote Sionna server).
