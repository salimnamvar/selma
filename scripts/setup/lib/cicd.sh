#!/usr/bin/env bash
# CI quality gates for nasim (lint + test when present).

if [[ -n "${SETUP_CICD_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_CICD_SH=1

run_cicd_gates() {
  [[ "${SKIP_CICD}" == "1" ]] && { log_info "Skipping cicd gates"; return 0; }

  if [[ -x "${PROJECT_ROOT}/scripts/lint.sh" ]]; then
    run_cmd "${PROJECT_ROOT}/scripts/lint.sh" || true
  else
    log_warn "lint.sh not found"
  fi

  if [[ -x "${PYTEST_BIN}" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log_info "Would run pytest"
    else
      "${PYTEST_BIN}" --tb=short || true
    fi
  fi
  log_ok "cicd gates executed (non-fatal in setup)"
}
