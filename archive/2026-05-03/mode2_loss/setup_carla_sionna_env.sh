#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  analysis/mode2_loss/setup_carla_sionna_env.sh [NS3_DIR]

Environment overrides:
  MINIFORGE_DIR=$HOME/miniforge3
  OPENCDA_ENV=msvan3t_carla
  SIONNA_VENV=<NS3_DIR>/.venv_sionna
  SIONNA_BASE_PYTHON=/usr/bin/python3.12
  BUILD_JOBS=2
EOF
  exit 0
fi

NS3_DIR="${1:-$(pwd)}"
MINIFORGE_DIR="${MINIFORGE_DIR:-$HOME/miniforge3}"
OPENCDA_ENV="${OPENCDA_ENV:-msvan3t_carla}"
SIONNA_VENV="${SIONNA_VENV:-$NS3_DIR/.venv_sionna}"
SIONNA_BASE_PYTHON="${SIONNA_BASE_PYTHON:-/usr/bin/python3.12}"
BUILD_JOBS="${BUILD_JOBS:-2}"

CONF_FILE="$NS3_DIR/CARLA-OpenCDA.conf"
CARLA_DIR="$NS3_DIR/CARLA_0.9.12"
OPENCDA_DIR="$NS3_DIR/OpenCDA"
CARLA_WHEEL="$CARLA_DIR/PythonAPI/carla/dist/carla-0.9.12-cp37-cp37m-manylinux_2_27_x86_64.whl"
OPENCDA_PY="$MINIFORGE_DIR/envs/$OPENCDA_ENV/bin/python"
SIONNA_PY="$SIONNA_VENV/bin/python"

if [[ ! -d "$NS3_DIR" ]]; then
  echo "ERROR: NS3_DIR does not exist: $NS3_DIR" >&2
  exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
  echo "ERROR: do not run this script as root; use your normal user to avoid permission issues." >&2
  exit 1
fi

if [[ ! -d "$CARLA_DIR" ]]; then
  echo "ERROR: CARLA directory not found: $CARLA_DIR" >&2
  exit 1
fi

if [[ ! -d "$OPENCDA_DIR" ]]; then
  echo "ERROR: OpenCDA directory not found: $OPENCDA_DIR" >&2
  exit 1
fi

if [[ ! -x "$SIONNA_BASE_PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    SIONNA_BASE_PYTHON="$(command -v python3)"
  else
    echo "ERROR: no usable python3 interpreter for Sionna venv" >&2
    exit 1
  fi
fi

if [[ ! -x "$MINIFORGE_DIR/bin/conda" ]]; then
  echo "[setup] Installing Miniforge in $MINIFORGE_DIR"
  tmp_installer="/tmp/Miniforge3-Linux-x86_64.sh"
  wget -O "$tmp_installer" "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
  bash "$tmp_installer" -b -p "$MINIFORGE_DIR"
fi

eval "$("$MINIFORGE_DIR/bin/conda" shell.bash hook)"
conda config --set auto_activate_base false >/dev/null

if conda env list | awk '{print $1}' | grep -qx "$OPENCDA_ENV"; then
  echo "[setup] Conda env '$OPENCDA_ENV' already exists"
else
  echo "[setup] Creating conda env '$OPENCDA_ENV' from OpenCDA/environment.yml"
  conda env create -n "$OPENCDA_ENV" -f "$OPENCDA_DIR/environment.yml"
fi

echo "[setup] Installing OpenCDA runtime extras"
conda run -n "$OPENCDA_ENV" python -m pip install --upgrade pip
conda run -n "$OPENCDA_ENV" python -m pip install grpcio grpcio-tools pyzmq zmq filterpy conan==1.54.0

if ! conda run -n "$OPENCDA_ENV" python - <<'PY'
import importlib.util
ok = importlib.util.find_spec("carla") is not None
raise SystemExit(0 if ok else 1)
PY
then
  if [[ -f "$CARLA_WHEEL" ]]; then
    echo "[setup] Installing local CARLA wheel: $CARLA_WHEEL"
    conda run -n "$OPENCDA_ENV" python -m pip install "$CARLA_WHEEL"
  else
    echo "ERROR: CARLA module missing and wheel not found: $CARLA_WHEEL" >&2
    exit 1
  fi
fi

echo "[setup] Verifying OpenCDA python modules"
conda run -n "$OPENCDA_ENV" python - <<'PY'
import importlib.util as u, sys
mods = ("carla", "grpc", "zmq")
missing = [m for m in mods if u.find_spec(m) is None]
if missing:
    print("MISSING_OPENCDA_MODULES=" + ",".join(missing))
    sys.exit(2)
print("OpenCDA modules OK")
PY

echo "[setup] Creating/refreshing Sionna venv: $SIONNA_VENV"
"$SIONNA_BASE_PYTHON" -m venv "$SIONNA_VENV"
"$SIONNA_VENV/bin/pip" install --upgrade pip
"$SIONNA_VENV/bin/pip" install "tensorflow[and-cuda]==2.16.1" "sionna==1.0.0" grpcio

echo "[setup] Verifying Sionna python modules"
"$SIONNA_PY" - <<'PY'
import importlib.util as u, sys
mods = ("tensorflow", "sionna", "grpc")
missing = [m for m in mods if u.find_spec(m) is None]
if missing:
    print("MISSING_SIONNA_MODULES=" + ",".join(missing))
    sys.exit(2)
print("Sionna modules OK")
PY

if [[ -f /usr/lib/wsl/lib/libnvoptix.so.1 ]] && nm -D /usr/lib/wsl/lib/libnvoptix.so.1 2>/dev/null | grep -q optixQueryFunctionTable; then
  echo "[setup] OptiX symbol check: OK"
else
  echo "[setup] WARNING: OptiX symbol missing in /usr/lib/wsl/lib/libnvoptix.so.1"
  echo "[setup]          For Sionna RT GPU path tracing on WSL run:"
  echo "[setup]          sudo analysis/mode2_loss/fix_wsl_optix.sh"
fi

cat > "$CONF_FILE" <<EOF
CARLA_HOME=$CARLA_DIR
OpenCDA_HOME=$OPENCDA_DIR
Python_Interpreter=$OPENCDA_PY
EOF
echo "[setup] Wrote $CONF_FILE"

MODE_FILE="$NS3_DIR/src/automotive/aux-files/current-mode.txt"
if [[ -f "$MODE_FILE" ]] && [[ "$(head -n1 "$MODE_FILE")" == "CARLA" ]]; then
  echo "[setup] CARLA mode is already active"
else
  echo "[setup] Switching ns-3 tree to CARLA mode"
  "$OPENCDA_PY" "$NS3_DIR/adapt_files.py" CARLA || true
fi

if [[ -d "$NS3_DIR/cmake-cache" ]]; then
  echo "[setup] Building ns-3 targets"
  (
    cd "$NS3_DIR/cmake-cache"
    cmake --build . -j "$BUILD_JOBS" --target v2v-carla-nrv2x v2v-cam-exchange-sionna-nrv2x
  )
fi

cat <<EOF

Setup finished.
Run command:
  cd $NS3_DIR
  SIONNA_PYTHON=$SIONNA_PY SIONNA_GPU=1 analysis/mode2_loss/run_carla_sionna_nrv2x.sh $NS3_DIR

Optional (separate terminal):
  cd $CARLA_DIR
  ./CarlaUE4.sh
EOF
