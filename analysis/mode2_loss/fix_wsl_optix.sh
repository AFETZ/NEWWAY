#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  sudo analysis/mode2_loss/fix_wsl_optix.sh [NVIDIA_LINUX_DRIVER_VERSION]

Default version:
  580.95.05

What it does:
  1) Checks if /usr/lib/wsl/lib/libnvoptix.so.1 exports optixQueryFunctionTable.
  2) Downloads and extracts NVIDIA Linux .run driver.
  3) Backs up current /usr/lib/wsl/lib OptiX-related files.
  4) Installs libnvoptix/libnvidia-rtcore/libnvidia-ptxjitcompiler/libnvidia-gpucomp + nvoptix.bin.
  5) Verifies the OptiX symbol again.
EOF
  exit 0
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: run as root (e.g. sudo ...)." >&2
  exit 1
fi

DRIVER_VER="${1:-${NVIDIA_LINUX_DRIVER_VERSION:-580.95.05}}"
URL="https://us.download.nvidia.com/XFree86/Linux-x86_64/${DRIVER_VER}/NVIDIA-Linux-x86_64-${DRIVER_VER}.run"
DST="/usr/lib/wsl/lib"
WORK="/tmp/wsl-optix-fix-${DRIVER_VER}"
RUN_FILE="${WORK}/NVIDIA-Linux-x86_64-${DRIVER_VER}.run"
EXTRACT_DIR="${WORK}/extracted"

if [[ ! -d "$DST" ]]; then
  echo "ERROR: target directory missing: $DST" >&2
  exit 1
fi

if nm -D "$DST/libnvoptix.so.1" 2>/dev/null | grep -q 'optixQueryFunctionTable'; then
  echo "OptiX symbol already present in $DST/libnvoptix.so.1"
  exit 0
fi

mkdir -p "$WORK"

if [[ ! -f "$RUN_FILE" ]]; then
  echo "[fix] Downloading NVIDIA Linux driver ${DRIVER_VER}"
  wget -O "$RUN_FILE" "$URL"
fi

chmod +x "$RUN_FILE"
rm -rf "$EXTRACT_DIR"
echo "[fix] Extracting driver payload"
"$RUN_FILE" --extract-only --target "$EXTRACT_DIR" >/tmp/fix_wsl_optix_extract.log 2>&1 || {
  tail -n 120 /tmp/fix_wsl_optix_extract.log >&2
  exit 1
}

required_files=(
  "libnvoptix.so.${DRIVER_VER}"
  "libnvidia-rtcore.so.${DRIVER_VER}"
  "libnvidia-ptxjitcompiler.so.${DRIVER_VER}"
  "libnvidia-gpucomp.so.${DRIVER_VER}"
  "nvoptix.bin"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "$EXTRACT_DIR/$f" ]]; then
    echo "ERROR: missing extracted file: $EXTRACT_DIR/$f" >&2
    exit 1
  fi
done

BKP="${DST}/backup-optix-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BKP"
echo "[fix] Backup directory: $BKP"

for f in \
  libnvoptix.so.1 \
  libnvoptix_loader.so.1 \
  libnvidia-gpucomp.so \
  libnvidia-gpucomp.so.590.57 \
  libnvidia-rtcore.so.1 \
  libnvidia-ptxjitcompiler.so.1 \
  nvoptix.bin; do
  if [[ -e "$DST/$f" ]]; then
    cp -a "$DST/$f" "$BKP/"
  fi
done

echo "[fix] Installing new OptiX-related libraries"
cp -f "$EXTRACT_DIR/libnvoptix.so.${DRIVER_VER}" "$DST/"
cp -f "$EXTRACT_DIR/libnvidia-rtcore.so.${DRIVER_VER}" "$DST/"
cp -f "$EXTRACT_DIR/libnvidia-ptxjitcompiler.so.${DRIVER_VER}" "$DST/"
cp -f "$EXTRACT_DIR/libnvidia-gpucomp.so.${DRIVER_VER}" "$DST/"
cp -f "$EXTRACT_DIR/nvoptix.bin" "$DST/"

ln -sfn "libnvoptix.so.${DRIVER_VER}" "$DST/libnvoptix.so.1"
ln -sfn "libnvoptix.so.1" "$DST/libnvoptix_loader.so.1"
ln -sfn "libnvidia-rtcore.so.${DRIVER_VER}" "$DST/libnvidia-rtcore.so.1"
ln -sfn "libnvidia-ptxjitcompiler.so.${DRIVER_VER}" "$DST/libnvidia-ptxjitcompiler.so.1"
ln -sfn "libnvidia-gpucomp.so.${DRIVER_VER}" "$DST/libnvidia-gpucomp.so"
# Keep this alias used in some WSL builds.
ln -sfn "libnvidia-gpucomp.so.${DRIVER_VER}" "$DST/libnvidia-gpucomp.so.590.57"

chmod 755 \
  "$DST/libnvoptix.so.${DRIVER_VER}" \
  "$DST/libnvidia-rtcore.so.${DRIVER_VER}" \
  "$DST/libnvidia-ptxjitcompiler.so.${DRIVER_VER}" \
  "$DST/libnvidia-gpucomp.so.${DRIVER_VER}"
chmod 644 "$DST/nvoptix.bin"

if nm -D "$DST/libnvoptix.so.1" 2>/dev/null | grep -q 'optixQueryFunctionTable'; then
  echo "[fix] SUCCESS: optixQueryFunctionTable is now available."
else
  echo "[fix] ERROR: symbol still missing after installation." >&2
  exit 1
fi

echo "[fix] Done."
