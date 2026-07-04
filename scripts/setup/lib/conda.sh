#!/usr/bin/env bash
# Conda bootstrap and environment for nasim.

if [[ -n "${SETUP_CONDA_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_CONDA_SH=1

_miniconda_installer_url() {
  local platform arch
  platform="$(detect_platform)"
  arch="$(uname -m)"
  case "${platform}" in
    linux) printf 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-%s.sh' "${arch}" ;;
    darwin) printf 'https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-%s.sh' "${arch}" ;;
  esac
}

ensure_miniconda() {
  if [[ "${SETUP_SKIP_CONDA_INSTALL:-0}" == "1" ]]; then
    log_info "Skipping Miniconda install"
    return 0
  fi
  if [[ -x "${CONDA_BIN}" ]]; then
    log_ok "Miniconda found: ${CONDA_DIR}"
    return 0
  fi
  log_info "Installing Miniconda to ${CONDA_DIR}"
  if [[ "${DRY_RUN}" == "1" ]]; then return 0; fi

  local url path
  url="$(_miniconda_installer_url)"
  path="$(mktemp /tmp/miniconda.XXXXXX.sh)"
  trap 'rm -f "${path}"' RETURN
  mkdir -p "$(dirname "${CONDA_DIR}")"
  if command -v curl >/dev/null; then curl -fsSL "$url" -o "$path"
  elif command -v wget >/dev/null; then wget -q "$url" -O "$path"
  else die "curl or wget required"; fi

  run_cmd bash "$path" -b -p "${CONDA_DIR}"
  run_cmd "${CONDA_BIN}" config --set auto_activate_base false || true
}

update_conda() {
  [[ -x "${CONDA_BIN}" ]] || return 0
  run_cmd "${CONDA_BIN}" update -y -n base conda || true
}

ensure_conda_env() {
  [[ -x "${CONDA_BIN}" ]] || die "conda not found"
  local env_exists=0
  "${CONDA_BIN}" env list | grep -q "^${ENV_NAME} " && env_exists=1 || true

  if [[ "${RECREATE_ENV}" == "1" && "${env_exists}" == "1" ]]; then
    log_info "Removing existing env ${ENV_NAME}"
    run_cmd "${CONDA_BIN}" env remove -n "${ENV_NAME}" -y || true
    env_exists=0
  fi

  if [[ "${env_exists}" == "0" ]]; then
    log_info "Creating conda env ${ENV_NAME} (python ${PYTHON_VERSION})"
    run_cmd "${CONDA_BIN}" create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"
  else
    log_ok "Conda env ${ENV_NAME} exists"
  fi

  ENV_PREFIX="$("${CONDA_BIN}" env list | awk -v n="${ENV_NAME}" '$1==n {print $2}')"
  PYTHON_BIN="${ENV_PREFIX}/bin/python"
  PIP_BIN="${ENV_PREFIX}/bin/pip"
  PYTEST_BIN="${ENV_PREFIX}/bin/pytest"
  log_ok "Python: ${PYTHON_BIN}"
}
