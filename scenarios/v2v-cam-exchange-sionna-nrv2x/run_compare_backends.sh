#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NS3_DIR="${NS3_DIR:-}"
SIM_TIME="${SIM_TIME:-20}"
OUT_BASE="${OUT_BASE:-$ROOT/analysis/scenario_runs/$(date +%F)/cam-sionna-backend-compare-$(date +%H%M%S)}"
SIONNA_PY="${SIONNA_PY:-$ROOT/.venv/bin/python}"
SIONNA_GPU="${SIONNA_GPU:-0}"
EXPORT_RESULTS="${EXPORT_RESULTS:-1}"
EXPORT_ROOT="${EXPORT_ROOT:-$ROOT/analysis/scenario_runs/chatgpt_exports}"
EXPORT_INCLUDE_RAW_CSV="${EXPORT_INCLUDE_RAW_CSV:-0}"

NS3_DIR="$("$ROOT/scripts/ensure-ns3-dev.sh" --root "$ROOT" --ns3-dir "$NS3_DIR")"
SCENE_XML="${SCENE_XML:-$NS3_DIR/src/sionna/scenarios/SionnaCircleScenario/scene.xml}"

if [[ ! -f "$NS3_DIR/src/sionna/sionna_v1_server_script.py" ]]; then
  echo "Missing Sionna server script in $NS3_DIR/src/sionna/"
  exit 1
fi
if [[ ! -x "$SIONNA_PY" ]]; then
  SIONNA_PY="python3"
fi

mkdir -p "$OUT_BASE"

echo "[1/3] Running non-Sionna baseline..."
OUT_NO="$OUT_BASE/non_sionna"
OUT_DIR="$OUT_NO" NS3_DIR="$NS3_DIR" RUN_ARGS="--sumo-gui=0 --sim-time=$SIM_TIME --sionna=0" \
  "$ROOT/scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh"

echo "[2/3] Checking Sionna runtime dependencies..."
if ! "$SIONNA_PY" - <<'PY'
import importlib.util
mods = ("tensorflow", "sionna", "mitsuba")
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print("MISSING:", ",".join(missing))
    raise SystemExit(1)
print("OK")
PY
then
  echo "Sionna stack is missing (tensorflow/sionna/mitsuba)."
  echo "Non-Sionna baseline is done in: $OUT_NO"
  echo "To run the terrain-aware backend comparison, install dependencies then rerun."
  exit 0
fi

echo "[3/3] Running Sionna-enabled scenario..."
OUT_SI="$OUT_BASE/sionna"
mkdir -p "$OUT_SI"
"$SIONNA_PY" "$NS3_DIR/src/sionna/sionna_v1_server_script.py" \
  --path-to-xml-scenario "$SCENE_XML" \
  --local-machine \
  --gpu "$SIONNA_GPU" \
  > "$OUT_BASE/sionna_server.log" 2>&1 &
SIONNA_PID=$!
cleanup() {
  if kill -0 "$SIONNA_PID" >/dev/null 2>&1; then
    kill "$SIONNA_PID" >/dev/null 2>&1 || true
    wait "$SIONNA_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
sleep 5

OUT_DIR="$OUT_SI" NS3_DIR="$NS3_DIR" RUN_ARGS="--sumo-gui=0 --sim-time=$SIM_TIME --sionna=1 --sionna-local-machine=1 --sionna-server-ip=127.0.0.1" \
  "$ROOT/scenarios/v2v-cam-exchange-sionna-nrv2x/run.sh"

cleanup
trap - EXIT

COMPARE_CSV="$OUT_BASE/backend_compare_summary.csv"
COMPARE_PNG="$OUT_BASE/backend_compare_summary.png"
export COMPARE_CSV COMPARE_PNG OUT_NO OUT_SI SIONNA_PY
"$SIONNA_PY" - <<'PY'
import csv
import os
import re
from pathlib import Path

import matplotlib.pyplot as plt

def parse_metrics(path: Path):
    txt = path.read_text()
    def grab(name):
        m = re.search(rf"{name}:\s*([0-9.]+)", txt)
        return float(m.group(1)) if m else None
    return {
        "prr": grab("Average PRR"),
        "latency_ms": grab("Average latency \\(ms\\)"),
    }

out_no = Path(os.environ["OUT_NO"]) / "artifacts" / "v2v-cam-exchange-sionna-nrv2x_output.txt"
out_si = Path(os.environ["OUT_SI"]) / "artifacts" / "v2v-cam-exchange-sionna-nrv2x_output.txt"
csv_path = Path(os.environ["COMPARE_CSV"])
png_path = Path(os.environ["COMPARE_PNG"])

rows = [
    {"backend": "non_sionna", **parse_metrics(out_no)},
    {"backend": "sionna", **parse_metrics(out_si)},
]

with csv_path.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["backend", "prr", "latency_ms"])
    w.writeheader()
    w.writerows(rows)

labels = [r["backend"] for r in rows]
prr = [r["prr"] if r["prr"] is not None else 0.0 for r in rows]
lat = [r["latency_ms"] if r["latency_ms"] is not None else 0.0 for r in rows]

fig, ax = plt.subplots(1, 2, figsize=(8, 4))
ax[0].bar(labels, prr, color=["#1f77b4", "#ff7f0e"])
ax[0].set_ylim(0, 1.05)
ax[0].set_ylabel("Average PRR [-]")
ax[0].grid(axis="y", alpha=0.3)

ax[1].bar(labels, lat, color=["#1f77b4", "#ff7f0e"])
ax[1].set_ylabel("Average latency [ms]")
ax[1].grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig(png_path, dpi=150)
plt.close(fig)
print(csv_path)
print(png_path)
PY

echo "Comparison done:"
echo "  $COMPARE_CSV"
echo "  $COMPARE_PNG"

if [[ "$EXPORT_RESULTS" == "1" ]]; then
  export_args=(--run-dir "$OUT_BASE" --export-root "$EXPORT_ROOT")
  if [[ "$EXPORT_INCLUDE_RAW_CSV" == "1" ]]; then
    export_args+=(--include-raw-csv)
  fi
  if ! "$SIONNA_PY" "$ROOT/analysis/scenario_runs/export_results_bundle.py" "${export_args[@]}"; then
    echo "Warning: export bundle generation failed for backend compare"
  fi
fi
