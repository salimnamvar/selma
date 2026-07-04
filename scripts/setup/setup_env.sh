#!/usr/bin/env bash
# setup_env.sh — A-to-Z project environment provisioning for selma (pure shell).
#
# Reads pyproject.toml automatically.
#
# Usage:
#   bash scripts/setup/setup_env.sh
#   bash scripts/setup/setup_env.sh --dry-run
#   bash scripts/setup/setup_env.sh --steps conda,env,python,vscode,verify,cicd

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SETUP_DIR="${SCRIPT_DIR}"
LIB_DIR="${SETUP_DIR}/lib"

# shellcheck source=lib/common.sh
source "${LIB_DIR}/common.sh"

parse_args "$@"

# shellcheck source=lib/pyproject.sh
source "${LIB_DIR}/pyproject.sh"
# shellcheck source=lib/conda.sh
source "${LIB_DIR}/conda.sh"
# shellcheck source=lib/python.sh
source "${LIB_DIR}/python.sh"
# shellcheck source=lib/vscode.sh
source "${LIB_DIR}/vscode.sh"
# shellcheck source=lib/verify.sh
source "${LIB_DIR}/verify.sh"
# shellcheck source=lib/cicd.sh
source "${LIB_DIR}/cicd.sh"

main() {
  log_step "Environment setup — selma"
  log_info "Project root: ${PROJECT_ROOT}"

  load_local_overrides

  [[ "${SKIP_VSCODE}" == "1" ]] && export SETUP_SKIP_VSCODE=1

  load_pyproject_config

  if step_selected conda; then
    log_step "Conda bootstrap"
    ensure_miniconda
    update_conda
  fi

  if step_selected env; then
    log_step "Conda environment"
    ensure_conda_env
    setup_shell_profile
  fi

  if step_selected python; then
    log_step "Python packages"
    install_project_packages
  fi

  if step_selected vscode; then
    log_step "VS Code / Cursor workspace"
    setup_vscode
  fi

  if step_selected verify; then
    log_step "Verification"
    verify_setup
  fi

  if step_selected cicd; then
    log_step "CI/CD quality gates"
    run_cicd_gates
  fi

  log_step "Setup complete"
  log_ok "Conda env:  ${ENV_NAME} (${ENV_PREFIX})"
  log_ok "Python:     ${PYTHON_BIN}"
  log_info "Reload your editor and open a new terminal to use the ${ENV_NAME} profile."
}

main
