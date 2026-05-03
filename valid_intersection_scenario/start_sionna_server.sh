#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENE_FILE="${SCENE_FILE:-src/sionna/scenarios/SionnaCircleScenario/scene.xml}"
SIONNA_VERBOSE="${SIONNA_VERBOSE:-1}"
SIONNA_GPUS="${SIONNA_GPUS:-1}"
SIONNA_MI_VARIANT="${SIONNA_MI_VARIANT:-llvm_ad_mono_polarized}"
WSL_OPTIX_LIB="/usr/lib/wsl/lib/libnvoptix.so.1"

PY_BIN="$ROOT/.venv_sionna/bin/python"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

VERBOSE_ARG=()
if [[ "$SIONNA_VERBOSE" == "1" ]]; then
  VERBOSE_ARG+=(--verbose)
fi

cd "$ROOT"
export SIONNA_MI_VARIANT
if [[ -z "${DRJIT_LIBOPTIX_PATH:-}" ]] && [[ "$SIONNA_MI_VARIANT" == cuda_* ]] && [[ -f "$WSL_OPTIX_LIB" ]]; then
  export DRJIT_LIBOPTIX_PATH="$WSL_OPTIX_LIB"
fi
if [[ "$SIONNA_MI_VARIANT" == cuda_* ]] && [[ -d /usr/lib/wsl/lib ]]; then
  export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
exec "$PY_BIN" src/sionna/sionna_v1_server_script.py \
  --path-to-xml-scenario "$SCENE_FILE" \
  --local-machine \
  --gpu "$SIONNA_GPUS" \
  "${VERBOSE_ARG[@]}"
