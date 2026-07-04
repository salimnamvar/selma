#!/usr/bin/env bash
# Shared helpers for setup_env modules (nasim).

if [[ -n "${SETUP_COMMON_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_COMMON_SH=1

set -euo pipefail

: "${PROJECT_ROOT:?PROJECT_ROOT must be set}"
: "${SETUP_DIR:?SETUP_DIR must be set}"

DRY_RUN="${DRY_RUN:-0}"
RECREATE_ENV="${RECREATE_ENV:-0}"
SKIP_VERIFY="${SKIP_VERIFY:-0}"
SKIP_VSCODE="${SKIP_VSCODE:-0}"
SKIP_CICD="${SKIP_CICD:-0}"

ALL_STEPS=(conda env python vscode verify cicd)
SELECTED_STEPS=()

log_step() { printf '\n── %s ──\n' "$1" >&2; }
log_info() { local s=""; [[ "${DRY_RUN}" == "1" ]] && s=" [dry-run]"; printf '· %s%s\n' "$1" "$s" >&2; }
log_ok()   { local s=""; [[ "${DRY_RUN}" == "1" ]] && s=" [dry-run]"; printf '✓ %s%s\n' "$1" "$s" >&2; }
log_warn() { printf '! %s\n' "$1" >&2; }
log_error(){ printf '✗ %s\n' "$1" >&2; }

die() { log_error "$1"; exit 1; }

run_cmd() {
  local d; d="$(printf '%q ' "$@")"; d="${d% }"
  log_info "${d}"
  [[ "${DRY_RUN}" == "1" ]] && return 0
  "$@"
}

step_selected() {
  local step="$1"; local s
  for s in "${SELECTED_STEPS[@]}"; do [[ "$s" == "$step" ]] && return 0; done
  return 1
}

parse_args() {
  SELECTED_STEPS=("${ALL_STEPS[@]}")
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run) DRY_RUN=1; shift ;;
      --steps)
        shift
        IFS=',' read -ra SELECTED_STEPS <<< "$1"
        shift
        ;;
      *) shift ;;
    esac
  done
}

load_local_overrides() {
  local f="${SETUP_DIR}/environment.local.sh"
  [[ -f "$f" ]] && source "$f" || true
}

detect_platform() {
  case "$(uname -s)" in
    Linux*) echo linux ;;
    Darwin*) echo darwin ;;
    *) echo linux ;;
  esac
}

# Defaults that pyproject.sh will override
PROJECT_NAME="nasim"
ENV_NAME="nasim"
PYTHON_VERSION="3.11"
CONDA_DIR="${SETUP_CONDA_DIR:-${HOME}/miniconda3}"
CONDA_BIN="${CONDA_DIR}/bin/conda"
PYTHON_BIN=""
PIP_BIN=""
ENV_PREFIX=""
PYTEST_BIN=""
BLACK_LINE_LENGTH="120"
RUFF_LINE_LENGTH="120"
ISORT_PROFILE="google"
ISORT_LINE_LENGTH="120"
PYTEST_TESTPATHS="tests"
PYTHON_ANALYSIS_PATHS="nasim"
TERMINAL_PROFILE_NAME="nasim (conda)"
PACKAGE_INCLUDE_GLOB="nasim*"
PIP_INSTALL_TARGET="."
PROJECT_HAS_DEV_EXTRAS=1
