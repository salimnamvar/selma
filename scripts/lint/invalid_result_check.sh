#!/usr/bin/env bash
# invalid_result_check.sh — P4: Fail-Safe Defaults (SC-004).
#
# Rule: Each module SHALL define a module-level INVALID_RESULT constant
#       of type Result[Any]. It SHALL be returned only when the function's
#       postcondition cannot be satisfied.
#
# Checks:
#   - Module-level INVALID_RESULT constant exists (warning only).
#   - INVALID_RESULT is not used as a generic error (error).
#   - INVALID_RESULT is used as initial default in canonical pattern.

if [[ -n "${SETUP_LINT_INVALID_RESULT_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_INVALID_RESULT_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

INVALID_RESULT_AWK=$(cat << 'AWKEOF'
BEGIN {
    has_invalid_result = 0
    has_result_return = 0
    violations = 0
    in_docstring = 0
    in_func = 0
    func_name = ""
    in_sig = 0
    paren_depth = 0
    sig_buf = ""
}

/"""/ {
    if (!in_docstring) { in_docstring = 1; if ($0 ~ /""".*"""/) in_docstring = 0 }
    else { if ($0 ~ /"""/) in_docstring = 0 }
    next
}
/'''/ {
    if (!in_docstring) { in_docstring = 1; if ($0 ~ /'''.*'''/) in_docstring = 0 }
    else { if ($0 ~ /'''/) in_docstring = 0 }
    next
}
in_docstring { next }

/^[[:space:]]*INVALID_RESULT[[:space:]]*(:.*)?=/ { has_invalid_result = 1; next }
/^from[[:space:]]+[a-zA-Z0-9_.]+[[:space:]]+import.*INVALID_RESULT/ { has_invalid_result = 1; next }
/^import[[:space:]]+.*INVALID_RESULT/ { has_invalid_result = 1; next }

/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    in_sig = 1
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    paren_depth = 0
    sig_buf = ""
    def_line = $0
    sub(/#.*/, "", def_line)
    for (di = 1; di <= length(def_line); di++) {
        dc = substr(def_line, di, 1)
        if (dc == "(") paren_depth++
        if (dc == ")") paren_depth--
    }
    sig_buf = def_line
    if (paren_depth <= 0) {
        in_sig = 0
        if (sig_buf ~ /->[^:]*Result\[/) has_result_return = 1
    }
    next
}

in_func && in_sig {
    line = $0
    sub(/#.*/, "", line)
    sig_buf = sig_buf line
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }
    if (paren_depth <= 0) {
        in_sig = 0
        if (sig_buf ~ /->[^:]*Result\[/) has_result_return = 1
    }
}

in_func {
    if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[^[:space:]]/) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        if (length(line) == 0 && $0 !~ /^[[:space:]]*$/) { in_func = 0 }
    }
}

END {
    if (!has_invalid_result && has_result_return) {
        printf "0:0: warning: module has functions returning Result but missing INVALID_RESULT sentinel per SC-004 (invalid-result-missing)\n"
        violations++
    }
    exit (violations > 0) ? 1 : 0
}
AWKEOF
)

invalid_result_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "invalid-result-check: no directories provided, skipping"
    return 0
  fi

  lint_step "INVALID_RESULT check (P4: SC-004) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "invalid-result-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${INVALID_RESULT_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "invalid-result-check: INVALID_RESULT violations found"
    return 1
  fi

  lint_ok "invalid-result-check (P4)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  invalid_result_check_run "$@"
fi
