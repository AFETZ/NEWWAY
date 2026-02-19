#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/sync-overlay-into-bootstrap-ns3.sh [options]

Options:
  --root <dir>      Repository root (default: auto-detect)
  --ns3-dir <dir>   ns-3-dev directory to sync into (required)
  -h, --help        Show help

Environment:
  NS3_SYNC_OVERLAY=0|1  Enable/disable sync (default: 1)
USAGE
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NS3_DIR=""
DO_SYNC="${NS3_SYNC_OVERLAY:-1}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    --ns3-dir)
      NS3_DIR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$DO_SYNC" != "1" ]]; then
  exit 0
fi

if [[ -z "$NS3_DIR" ]]; then
  echo "--ns3-dir is required" >&2
  exit 1
fi

BOOTSTRAP_NS3="$ROOT/.bootstrap-ns3/repo/ns-3-dev"
if [[ "$NS3_DIR" != "$BOOTSTRAP_NS3" ]]; then
  # Sync is only needed for disposable bootstrap trees that are detached copies.
  exit 0
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "Warning: rsync not available, skipping overlay sync into bootstrap ns-3 tree." >&2
  exit 0
fi

if [[ ! -d "$ROOT/src" ]] || [[ ! -d "$NS3_DIR/src" ]]; then
  echo "Warning: missing src directory, skipping overlay sync." >&2
  exit 0
fi

echo "[sync-overlay] syncing overlay sources into bootstrap ns-3 tree (non-destructive)..." >&2
rsync -a "$ROOT/src/" "$NS3_DIR/src/"

for top_file in switch_ms-van3t-interference.sh switch_ms-van3t-CARLA.sh enable_v2x_emulator.sh; do
  if [[ -f "$ROOT/$top_file" ]]; then
    cp -f "$ROOT/$top_file" "$NS3_DIR/$top_file"
  fi
done

echo "[sync-overlay] done" >&2
