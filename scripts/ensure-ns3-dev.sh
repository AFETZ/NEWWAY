#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/ensure-ns3-dev.sh [options]

Options:
  --root <dir>                    Repository root (default: auto-detect)
  --ns3-dir <dir>                 Preferred ns-3-dev path to validate first
  --bootstrap-destination <dir>   Bootstrap destination (default: <root>/.bootstrap-ns3)
  --no-bootstrap                  Fail if ns-3-dev is missing (do not bootstrap)
  -h, --help                      Show help

Environment:
  AUTO_BOOTSTRAP_NS3=0|1          Enable/disable auto bootstrap (default: 1)
  NS3_BOOTSTRAP_FORCE=0|1         Force recreation of bootstrap destination (default: 0)
  NS3_BOOTSTRAP_COPY_SOURCE=0|1   Copy current working tree into disposable bootstrap repo (default: 1)
USAGE
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT_NS3_DIR=""
BOOTSTRAP_DEST=""
AUTO_BOOTSTRAP="${AUTO_BOOTSTRAP_NS3:-1}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    --ns3-dir)
      INPUT_NS3_DIR="${2:-}"
      shift 2
      ;;
    --bootstrap-destination)
      BOOTSTRAP_DEST="${2:-}"
      shift 2
      ;;
    --no-bootstrap)
      AUTO_BOOTSTRAP=0
      shift
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

if [[ -z "$BOOTSTRAP_DEST" ]]; then
  BOOTSTRAP_DEST="$ROOT/.bootstrap-ns3"
fi

if [[ -n "$INPUT_NS3_DIR" ]]; then
  if [[ -x "$INPUT_NS3_DIR/ns3" ]]; then
    printf '%s\n' "$INPUT_NS3_DIR"
    exit 0
  fi
  if [[ "$AUTO_BOOTSTRAP" != "1" ]]; then
    echo "Missing executable: $INPUT_NS3_DIR/ns3" >&2
    exit 1
  fi
fi

if [[ -x "$ROOT/ns-3-dev/ns3" ]]; then
  printf '%s\n' "$ROOT/ns-3-dev"
  exit 0
fi

BOOTSTRAP_NS3="$BOOTSTRAP_DEST/repo/ns-3-dev"
if [[ -x "$BOOTSTRAP_NS3/ns3" ]]; then
  printf '%s\n' "$BOOTSTRAP_NS3"
  exit 0
fi

if [[ "$AUTO_BOOTSTRAP" != "1" ]]; then
  echo "Missing ns-3 executable. Checked:" >&2
  echo "  $ROOT/ns-3-dev/ns3" >&2
  echo "  $BOOTSTRAP_NS3/ns3" >&2
  echo "Set NS3_DIR or enable auto bootstrap (AUTO_BOOTSTRAP_NS3=1)." >&2
  exit 1
fi

echo "[ensure-ns3-dev] ns-3-dev not found. Bootstrapping disposable local tree..." >&2
echo "[ensure-ns3-dev] destination: $BOOTSTRAP_DEST" >&2

BOOTSTRAP_SCRIPT="$ROOT/scripts/bootstrap-disposable.sh"
if [[ ! -x "$BOOTSTRAP_SCRIPT" ]]; then
  echo "Missing bootstrap script: $BOOTSTRAP_SCRIPT" >&2
  exit 1
fi

args=(--source "$ROOT" --destination "$BOOTSTRAP_DEST")
if [[ "${NS3_BOOTSTRAP_COPY_SOURCE:-1}" == "1" ]]; then
  args+=(--copy-source)
fi
if [[ "${NS3_BOOTSTRAP_FORCE:-0}" == "1" ]]; then
  args+=(--force)
elif [[ -e "$BOOTSTRAP_DEST" ]]; then
  # Destination exists but does not contain a usable ns3 executable.
  args+=(--force)
fi

"$BOOTSTRAP_SCRIPT" "${args[@]}" >&2

if [[ ! -x "$BOOTSTRAP_NS3/ns3" ]]; then
  echo "Bootstrap finished but ns3 is still missing: $BOOTSTRAP_NS3/ns3" >&2
  exit 1
fi

printf '%s\n' "$BOOTSTRAP_NS3"
