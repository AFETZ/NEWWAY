#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/bootstrap-disposable.sh [options]

Options:
  --destination <dir>        Destination directory (default: /tmp/van3t-bootstrap-<timestamp>)
  --source <dir>             Source repository path (default: repo root)
  --copy-source              Copy current source tree (including uncommitted files, excluding .git) instead of git clone
  --install-dependencies     Pass install-dependencies to sandbox_builder.sh
  --force                    Remove destination if it already exists
  --dry-run                  Print planned commands without executing
  -h, --help                 Show help
EOF
}

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESTINATION=""
INSTALL_DEPS=0
COPY_SOURCE=0
FORCE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --destination)
      DESTINATION="${2:-}"
      shift 2
      ;;
    --source)
      SOURCE_DIR="${2:-}"
      shift 2
      ;;
    --copy-source)
      COPY_SOURCE=1
      shift
      ;;
    --install-dependencies)
      INSTALL_DEPS=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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

if [[ -z "${DESTINATION}" ]]; then
  DESTINATION="/tmp/van3t-bootstrap-$(date +%Y%m%d-%H%M%S)"
fi

REPO_DIR="${DESTINATION}/repo"

run_cmd() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run]'
    for arg in "$@"; do
      printf ' %q' "${arg}"
    done
    printf '\n'
  else
    "$@"
  fi
}

if [[ -e "${DESTINATION}" ]]; then
  if [[ "${FORCE}" -eq 1 ]]; then
    run_cmd rm -rf "${DESTINATION}"
  else
    echo "Destination already exists: ${DESTINATION}" >&2
    echo "Use --force to overwrite." >&2
    exit 1
  fi
fi

run_cmd mkdir -p "${DESTINATION}"
if [[ "${COPY_SOURCE}" -eq 1 ]]; then
  RSYNC_ARGS=(-a --delete --exclude '.git' --exclude '.venv' --exclude '.bootstrap-ns3')
  if [[ "${DESTINATION}" == "${SOURCE_DIR}/"* ]]; then
    REL_DEST="${DESTINATION#${SOURCE_DIR}/}"
    if [[ "${REL_DEST}" != ".bootstrap-ns3" ]]; then
      RSYNC_ARGS+=(--exclude "${REL_DEST}")
    fi
  fi
  run_cmd mkdir -p "${REPO_DIR}"
  if command -v rsync >/dev/null 2>&1; then
    run_cmd rsync "${RSYNC_ARGS[@]}" "${SOURCE_DIR}/" "${REPO_DIR}/"
  else
    echo "rsync is required for --copy-source mode but is not available." >&2
    exit 1
  fi
else
  run_cmd git clone --local "${SOURCE_DIR}" "${REPO_DIR}"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
    if [[ "$EUID" -eq 0 ]]; then
      echo "[dry-run] cd ${REPO_DIR} && ALLOW_ROOT=1 printf '\\n' | ./sandbox_builder.sh install-dependencies"
    else
      echo "[dry-run] cd ${REPO_DIR} && printf '\\n' | ./sandbox_builder.sh install-dependencies"
    fi
  else
    if [[ "$EUID" -eq 0 ]]; then
      echo "[dry-run] cd ${REPO_DIR} && ALLOW_ROOT=1 printf '\\n' | ./sandbox_builder.sh"
    else
      echo "[dry-run] cd ${REPO_DIR} && printf '\\n' | ./sandbox_builder.sh"
    fi
  fi
  echo "[dry-run] expected ns-3 root: ${REPO_DIR}/ns-3-dev"
  exit 0
fi

cd "${REPO_DIR}"
if [[ "$EUID" -eq 0 ]]; then
  export ALLOW_ROOT=1
fi
if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
  printf '\n' | ./sandbox_builder.sh install-dependencies
else
  printf '\n' | ./sandbox_builder.sh
fi

echo "Bootstrap complete."
echo "Working tree: ${REPO_DIR}"
echo "ns-3 root:    ${REPO_DIR}/ns-3-dev"
