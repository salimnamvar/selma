#!/usr/bin/env bash
# CI quality gates for nasim (lint + test when present).

if [[ -n "${SETUP_CICD_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_CICD_SH=1

run_cicd_gates() {
  [[ "${SKIP_CICD}" == "1" ]] && { log_info "Skipping cicd gates"; return 0; }

  local repo_root
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

  if [[ -x "${PYTEST_BIN}" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log_info "Would run pytest"
    else
      "${PYTEST_BIN}" --tb=short || true
    fi
  fi

  # State-machine architecture gates (notes, capability matrix, catalog)
  if [[ -f "${repo_root}/scripts/validate_state_machines.py" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log_info "Would run validate_state_machines.py"
    else
      python "${repo_root}/scripts/validate_state_machines.py" || true
    fi
  fi

  log_ok "cicd gates executed (non-fatal in setup)"
}
