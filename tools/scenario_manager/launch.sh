#!/usr/bin/env bash
# Launch the NEWWAY Scenario Manager UI
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY_BIN="$ROOT/.venv/bin/python"

if [[ ! -x "$PY_BIN" ]]; then
  echo "Error: Python venv not found at $PY_BIN"
  echo "Create it: python3 -m venv .venv && .venv/bin/pip install streamlit plotly matplotlib pandas numpy"
  exit 1
fi

# Check dependencies without importing the full stack, which can make startup
# look like a hang before Streamlit even begins listening on the port.
"$ROOT/.venv/bin/pip" show streamlit plotly matplotlib pandas numpy >/dev/null 2>&1 || {
  echo "Installing missing dependencies..."
  "$ROOT/.venv/bin/pip" install streamlit plotly matplotlib pandas numpy
}

PORT="${PORT:-8501}"

echo ""
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║                                                          ║"
echo "  ║    🚗  NEWWAY Scenario Manager                           ║"
echo "  ║    V2X Experiment Platform                               ║"
echo "  ║                                                          ║"
echo "  ║    URL: http://localhost:$PORT                           ║"
echo "  ║                                                          ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo ""

cd "$ROOT"
exec "$ROOT/.venv/bin/streamlit" run tools/scenario_manager/app.py \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false
