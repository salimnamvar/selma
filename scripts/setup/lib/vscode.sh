#!/usr/bin/env bash
# Generate .vscode/ for nasim from pyproject-derived values.

if [[ -n "${SETUP_VSCODE_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_VSCODE_SH=1

VSCODE_DIR="${PROJECT_ROOT}/.vscode"

_json_escape() {
  local v="$1"; v="${v//\\/\\\\}"; v="${v//\"/\\\"}"; printf '%s' "$v"
}

setup_vscode() {
  [[ "${SETUP_SKIP_VSCODE:-0}" == "1" ]] && { log_info "Skipping VS Code setup"; return 0; }

  local py_bin conda_bin pytest_bin profile analysis
  py_bin="$(_json_escape "${PYTHON_BIN}")"
  conda_bin="$(_json_escape "${CONDA_DIR}/bin/conda")"
  pytest_bin="$(_json_escape "${PYTEST_BIN:-python -m pytest}")"
  profile="$(_json_escape "${TERMINAL_PROFILE_NAME}")"
  analysis="$(_json_escape "${PYTHON_ANALYSIS_PATHS}")"

  if [[ "${DRY_RUN}" == "1" ]]; then
    log_info "Would write .vscode/settings.json + terminal-init.sh"
    return 0
  fi

  mkdir -p "${VSCODE_DIR}"

  cat >"${VSCODE_DIR}/settings.json" <<JSON
{
  "terminal.integrated.profiles.linux": {
    "${profile}": {
      "path": "/bin/bash",
      "args": ["--rcfile", "\${workspaceFolder}/.vscode/terminal-init.sh", "-i"],
      "icon": "beaker"
    },
    "bash": { "path": "/bin/bash", "icon": "terminal-bash" }
  },
  "terminal.integrated.defaultProfile.linux": "${profile}",
  "python.defaultInterpreterPath": "${py_bin}",
  "python.condaPath": "${conda_bin}",
  "python.terminal.activateEnvironment": true,
  "python.terminal.activateEnvInCurrentTerminal": true,
  "python.envFile": "\${workspaceFolder}/.env",
  "python.analysis.extraPaths": [ "\${workspaceFolder}/${analysis}" ],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestPath": "${pytest_bin}",
  "python.testing.pytestArgs": [ "${PYTEST_TESTPATHS}" ],
  "python.testing.cwd": "\${workspaceFolder}",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": { "source.organizeImports": "explicit" }
  },
  "black-formatter.args": [ "--line-length=${BLACK_LINE_LENGTH}" ],
  "isort.args": [ "--profile=${ISORT_PROFILE}", "--line-length=${ISORT_LINE_LENGTH}" ],
  "ruff.enable": true,
  "ruff.lint.args": [ "--line-length=${RUFF_LINE_LENGTH}" ],
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace",
  "files.exclude": {
    "**/__pycache__": true, "**/*.egg-info": true,
    "**/.ruff_cache": true, "**/.pytest_cache": true,
    "**/.mypy_cache": true, "**/.coverage*": true,
    "**/htmlcov": true, "**/build": true, "**/dist": true, "**/.eggs": true
  },
  "search.exclude": {
    "**/__pycache__": true, "**/*.egg-info": true,
    "**/.ruff_cache": true, "**/.pytest_cache": true, "**/.coverage*": true
  }
}
JSON

  cat >"${VSCODE_DIR}/terminal-init.sh" <<'SH'
# Managed by setup_env.sh — do not hand-edit.
source "${HOME}/.bashrc" 2>/dev/null || true
for CAND in \
  "${HOME}/miniconda3/etc/profile.d/conda.sh" \
  "${HOME}/anaconda3/etc/profile.d/conda.sh" \
  "/opt/miniconda3/etc/profile.d/conda.sh"
do
  if [ -f "$CAND" ]; then . "$CAND"; conda activate nasim 2>/dev/null || true; break; fi
done
SH

  log_ok "VS Code config written"
}
