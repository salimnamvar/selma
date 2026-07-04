#!/usr/bin/env bash
# Post-setup verification for nasim.

if [[ -n "${SETUP_VERIFY_SH:-}" ]]; then return 0 2>/dev/null || exit 0; fi
SETUP_VERIFY_SH=1

_verify_command() {
  local name="$1"; shift
  local binary="${ENV_PREFIX}/bin/${name}"
  if [[ "${DRY_RUN}" == "1" ]]; then log_info "Would verify ${name}"; return 0; fi
  local out; out="$("${binary}" "$@" 2>&1)" || die "verify ${name}: ${out}"
  log_ok "${name}: $(printf '%s' "$out" | head -n1)"
}

verify_setup() {
  [[ -x "${PYTHON_BIN}" ]] || die "python not ready for verify"

  _verify_command python --version
  _verify_command pip --version || true

  if [[ "${DRY_RUN}" == "1" ]]; then
    log_info "Would run: pytest --collect-only -q"
    return 0
  fi

  local rc=0 out
  out="$("${PYTEST_BIN}" --collect-only -q 2>&1)" || rc=$?
  if [[ $rc -ne 0 && $rc -ne 5 ]]; then
    log_warn "pytest collection issues (may be ok if no tests yet): ${out}"
  else
    log_ok "pytest collection ok"
  fi
}
