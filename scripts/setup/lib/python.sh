#!/usr/bin/env bash
# Install the project in editable mode inside the conda env.

if [[ -n "${SETUP_PYTHON_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_PYTHON_SH=1

install_project_packages() {
  [[ -f "${PYPROJECT_PATH}" ]] || die "pyproject.toml not found"
  [[ -x "${PYTHON_BIN}" ]] || die "python not ready"

  conda_runtime_env() {
    # shellcheck disable=SC1090
    source "${ENV_PREFIX}/bin/activate" 2>/dev/null || true
  }

  conda_runtime_env

  run_cmd "${PIP_BIN}" install --upgrade pip setuptools wheel

  if [[ "${PROJECT_HAS_DEV_EXTRAS}" == "1" ]]; then
    run_cmd "${PIP_BIN}" install --upgrade -e "${PIP_INSTALL_TARGET}[dev]"
  else
    run_cmd "${PIP_BIN}" install --upgrade -e "${PIP_INSTALL_TARGET}"
  fi

  log_ok "Installed nasim (editable) into ${ENV_NAME}"
}
