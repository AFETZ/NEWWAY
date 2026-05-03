#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Compare old (crash-mode) vs new (unaware-mode) intersection scenarios
# ─────────────────────────────────────────────────────────────────────────────
# Usage:
#   ./hardwork/compare_old_vs_new.sh
#
# Runs both scenarios back-to-back (reusing the same Sionna server) and
# prints a side-by-side summary of the key differences.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE_TAG="$(date +%F)"
BASE_DIR="${BASE_DIR:-$HOME/NEWWAY_runs/$DATE_TAG}"

echo "════════════════════════════════════════════════════════════"
echo "  OLD SCENARIO (crash-mode force-speed)"
echo "════════════════════════════════════════════════════════════"
OLD_OUT="${BASE_DIR}/compare_old"
OUT_DIR="$OLD_OUT" \
SUMO_GUI="${SUMO_GUI:-0}" \
USE_SIONNA="${USE_SIONNA:-1}" \
PHY_ONLY=1 \
ALLOW_MANUAL_RX_DROP=0 \
VEH3_EQ_DBM=-30 \
VEH3_TARGET_PRR=0.02 \
"$ROOT/valid_intersection_scenario/run.sh" || true

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  NEW SCENARIO (unaware-mode, natural collision)"
echo "════════════════════════════════════════════════════════════"
NEW_OUT="${BASE_DIR}/compare_new"
OUT_DIR="$NEW_OUT" \
SUMO_GUI="${SUMO_GUI:-0}" \
USE_SIONNA="${USE_SIONNA:-1}" \
"$ROOT/hardwork/run_intersection_natural.sh" || true

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  COMPARISON"
echo "════════════════════════════════════════════════════════════"

compare_file() {
  local label="$1"
  local old_file="$2"
  local new_file="$3"
  echo "── $label ──"
  if [[ -f "$old_file" ]] && [[ -f "$new_file" ]]; then
    diff --side-by-side --width=120 "$old_file" "$new_file" || true
  else
    [[ ! -f "$old_file" ]] && echo "  OLD: not found ($old_file)"
    [[ ! -f "$new_file" ]] && echo "  NEW: not found ($new_file)"
  fi
  echo ""
}

# Compare control event logs
for veh in veh2 veh3 veh4; do
  old_ctrl=$(find "$OLD_OUT" -name "*${veh}-CTRL.csv" 2>/dev/null | head -1)
  new_ctrl=$(find "$NEW_OUT" -name "*${veh}-CTRL.csv" 2>/dev/null | head -1)
  if [[ -n "$old_ctrl" ]] || [[ -n "$new_ctrl" ]]; then
    echo "── Control events: $veh ──"
    echo "OLD:"
    [[ -n "$old_ctrl" ]] && grep -c "crash_mode\|unaware_mode\|cam_reaction\|no_action" "$old_ctrl" 2>/dev/null && head -5 "$old_ctrl" || echo "  (none)"
    echo "NEW:"
    [[ -n "$new_ctrl" ]] && grep -c "crash_mode\|unaware_mode\|cam_reaction\|no_action" "$new_ctrl" 2>/dev/null && head -5 "$new_ctrl" || echo "  (none)"
    echo ""
  fi
done

# Compare summaries
compare_file "Intersection Summary" \
  "$OLD_OUT/artifacts/intersection_summary.csv" \
  "$NEW_OUT/artifacts/intersection_summary.csv"

echo "OLD results: $OLD_OUT"
echo "NEW results: $NEW_OUT"
echo "Done."
