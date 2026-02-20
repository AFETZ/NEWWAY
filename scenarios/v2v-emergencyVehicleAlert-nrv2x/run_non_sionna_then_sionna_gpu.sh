#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Common run knobs.
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/eva-non-sionna-then-sionna-gpu-$(date +%H%M%S)}"
SIM_TIME="${SIM_TIME:-25}"
TX_POWERS="${TX_POWERS:-23}"
RNG_RUN="${RNG_RUN:-1}"
SUMO_GUI="${SUMO_GUI:-0}"
RUN_RETRIES="${RUN_RETRIES:-1}"
PLOT_CASE="${PLOT_CASE:-1}"

# Force strict GPU path for Sionna (no LLVM CPU fallback).
SIONNA_PY="${SIONNA_PY:-$ROOT/.venv_sionna/bin/python}"
SIONNA_GPU="${SIONNA_GPU:-1}"
SIONNA_ALLOW_LLVM_FALLBACK="${SIONNA_ALLOW_LLVM_FALLBACK:-0}"
SIONNA_SERVER_READY_TIMEOUT="${SIONNA_SERVER_READY_TIMEOUT:-2400}"

# Optional runtime tuning for faster smoke-runs.
INCIDENT_ARGS="${INCIDENT_ARGS:---incident-enable=1 --incident-vehicle-id=veh2 --incident-time-s=12 --incident-stop-duration-s=18}"
RADIO_ARGS="${RADIO_ARGS:---enableSensing=1 --enableChannelRandomness=1 --channelUpdatePeriod=100 --slThresPsschRsrp=-126}"
EXTRA_ARGS="${EXTRA_ARGS:-}"

# GPU monitor.
MONITOR_GPU="${MONITOR_GPU:-1}"
MONITOR_INTERVAL_S="${MONITOR_INTERVAL_S:-1}"
GPU_MONITOR_LOG="${GPU_MONITOR_LOG:-$OUT_BASE/gpu_monitor.csv}"
GPU_MONITOR_PID=""
NVIDIA_SMI_BIN=""
NVIDIA_LINUX_DRIVER_VER="${NVIDIA_LINUX_DRIVER_VER:-590.48.01}"
SIONNA_OPTIX_LIB_DIR="${SIONNA_OPTIX_LIB_DIR:-$ROOT/.optix-wsl/lib}"

mkdir -p "$OUT_BASE"

cleanup() {
  if [[ -n "$GPU_MONITOR_PID" ]] && kill -0 "$GPU_MONITOR_PID" >/dev/null 2>&1; then
    kill "$GPU_MONITOR_PID" >/dev/null 2>&1 || true
    wait "$GPU_MONITOR_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

have_optix_symbol() {
  local lib="$1"
  [[ -f "$lib" ]] || return 1
  # Avoid grep -q with pipefail: it can trigger SIGPIPE in nm and yield false negatives.
  nm -D "$lib" 2>/dev/null | grep -E '[[:space:]]optixQueryFunctionTable$' >/dev/null
}

ensure_user_optix_runtime() {
  local dst="$SIONNA_OPTIX_LIB_DIR"
  local cache_dir="$ROOT/.optix-wsl/cache"
  local run_file="$cache_dir/NVIDIA-Linux-x86_64-${NVIDIA_LINUX_DRIVER_VER}.run"
  local url="https://download.nvidia.com/XFree86/Linux-x86_64/${NVIDIA_LINUX_DRIVER_VER}/NVIDIA-Linux-x86_64-${NVIDIA_LINUX_DRIVER_VER}.run"
  local tmp

  if have_optix_symbol "/usr/lib/wsl/lib/libnvoptix.so.1"; then
    return 0
  fi
  if have_optix_symbol "$dst/libnvoptix.so.1"; then
    return 0
  fi

  echo "System WSL OptiX runtime is incomplete. Preparing local runtime in: $dst"
  mkdir -p "$cache_dir" "$dst"

  if [[ ! -s "$run_file" ]]; then
    echo "Downloading NVIDIA Linux driver $NVIDIA_LINUX_DRIVER_VER ..."
    curl -L --fail --retry 3 --retry-delay 2 -o "$run_file" "$url"
  fi

  tmp="$(mktemp -d)"
  chmod +x "$run_file"
  "$run_file" --extract-only --target "$tmp/extracted" >/dev/null 2>&1

  cp -f "$tmp/extracted/libnvoptix.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/"
  ln -sfn "libnvoptix.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/libnvoptix.so.1"
  ln -sfn "libnvoptix.so.1" "$dst/libnvoptix_loader.so.1"

  cp -f "$tmp/extracted/libnvidia-ptxjitcompiler.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/"
  ln -sfn "libnvidia-ptxjitcompiler.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/libnvidia-ptxjitcompiler.so.1"

  cp -f "$tmp/extracted/libnvidia-rtcore.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/"
  ln -sfn "libnvidia-rtcore.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/libnvidia-rtcore.so.1"

  cp -f "$tmp/extracted/libnvidia-gpucomp.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/"
  ln -sfn "libnvidia-gpucomp.so.${NVIDIA_LINUX_DRIVER_VER}" "$dst/libnvidia-gpucomp.so"

  cp -f "$tmp/extracted/nvoptix.bin" "$dst/"
  chmod 755 "$dst"/libnvoptix.so.* "$dst"/libnvidia-ptxjitcompiler.so.* "$dst"/libnvidia-rtcore.so.* "$dst"/libnvidia-gpucomp.so.*
  chmod 644 "$dst/nvoptix.bin"
  rm -rf "$tmp"

  if ! have_optix_symbol "$dst/libnvoptix.so.1"; then
    echo "Failed to prepare local OptiX runtime (missing optixQueryFunctionTable)."
    exit 1
  fi
}

ensure_user_optix_runtime
if have_optix_symbol "/usr/lib/wsl/lib/libnvoptix.so.1"; then
  echo "OptiX runtime source: system (/usr/lib/wsl/lib)"
else
  echo "OptiX runtime source: local ($SIONNA_OPTIX_LIB_DIR)"
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  NVIDIA_SMI_BIN="$(command -v nvidia-smi)"
elif [[ -x /usr/lib/wsl/lib/nvidia-smi ]]; then
  NVIDIA_SMI_BIN="/usr/lib/wsl/lib/nvidia-smi"
elif [[ -x /mnt/c/Windows/System32/nvidia-smi.exe ]]; then
  NVIDIA_SMI_BIN="/mnt/c/Windows/System32/nvidia-smi.exe"
else
  NVIDIA_SMI_BIN=""
fi

if [[ "$MONITOR_GPU" == "1" ]] && [[ -n "$NVIDIA_SMI_BIN" ]]; then
  {
    echo "timestamp,index,name,utilization_gpu_pct,utilization_mem_pct,memory_used_mib,power_w,temp_c"
    "$NVIDIA_SMI_BIN" \
      --query-gpu=timestamp,index,name,utilization.gpu,utilization.memory,memory.used,power.draw,temperature.gpu \
      --format=csv,noheader,nounits \
      -l "$MONITOR_INTERVAL_S"
  } > "$GPU_MONITOR_LOG" &
  GPU_MONITOR_PID=$!
  echo "GPU monitor started: $GPU_MONITOR_LOG (pid=$GPU_MONITOR_PID, bin=$NVIDIA_SMI_BIN)"
elif [[ "$MONITOR_GPU" == "1" ]]; then
  echo "Warning: nvidia-smi not found. GPU monitor disabled."
fi

echo "Run order: non_sionna -> sionna(gpu)"
echo "Output dir: $OUT_BASE"

OUT_BASE="$OUT_BASE" \
TX_POWERS="$TX_POWERS" \
SIM_TIME="$SIM_TIME" \
RNG_RUN="$RNG_RUN" \
SUMO_GUI="$SUMO_GUI" \
COMPARE_NON_SIONNA=1 \
RUN_RETRIES="$RUN_RETRIES" \
PLOT_CASE="$PLOT_CASE" \
INCIDENT_ARGS="$INCIDENT_ARGS" \
RADIO_ARGS="$RADIO_ARGS" \
EXTRA_ARGS="$EXTRA_ARGS" \
SIONNA_PY="$SIONNA_PY" \
SIONNA_GPU="$SIONNA_GPU" \
SIONNA_ALLOW_LLVM_FALLBACK="$SIONNA_ALLOW_LLVM_FALLBACK" \
SIONNA_SERVER_READY_TIMEOUT="$SIONNA_SERVER_READY_TIMEOUT" \
SIONNA_OPTIX_LIB_DIR="$SIONNA_OPTIX_LIB_DIR" \
bash "$ROOT/scenarios/v2v-emergencyVehicleAlert-nrv2x/run_sionna_incident_sweep.sh"

if [[ "$MONITOR_GPU" == "1" ]] && [[ -f "$GPU_MONITOR_LOG" ]]; then
  awk -F',' '
    NR == 1 { next }
    {
      gsub(/^[ \t]+|[ \t]+$/, "", $4)
      gsub(/^[ \t]+|[ \t]+$/, "", $7)
      if ($4 + 0 > max_util) max_util = $4 + 0
      if ($7 + 0 > max_power) max_power = $7 + 0
    }
    END {
      printf("GPU peak utilization: %.1f%%\n", max_util)
      printf("GPU peak power draw: %.1f W\n", max_power)
    }
  ' "$GPU_MONITOR_LOG"
fi

echo "Done: $OUT_BASE"
