#!/usr/bin/env bash
# assert_validation_check.sh — P5: Validation as Entry Contract (SC-007, SC-113).
#
# Rule: assert SHALL NOT be used for input validation or runtime checks.
#       assert SHALL be used exclusively for internal invariants — conditions
#       that, if false, indicate a defect in the function's own logic.
#
# Enforcement: Every assert in src/ is flagged. Test files are excluded.
# Exceptions: None per SC-007.

if [[ -n "${SETUP_LINT_ASSERT_VALIDATION_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_ASSERT_VALIDATION_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_ASSERT_VALIDATION_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    violations = 0
    in_docstring = 0
    docstring_char = ""
    dq = sprintf("%c%c%c", 34, 34, 34)
    sq = sprintf("%c%c%c", 39, 39, 39)
}

# Track docstrings (triple double or single quotes)
{
    has_dq = (index($0, dq) > 0)
    has_sq = (index($0, sq) > 0)
    if (has_dq || has_sq) {
        if (!in_docstring) {
            in_docstring = 1
            if (has_dq) docstring_char = dq
            else docstring_char = sq
            if (index($0, docstring_char) > 0) {
                n = gsub(docstring_char, docstring_char, $0)
                if (n % 2 == 0) in_docstring = 0
            }
        } else {
            if (index($0, docstring_char) > 0) in_docstring = 0
        }
        next
    }
}
in_docstring { next }

# Skip comments
/^[[:space:]]*#/ { next }

# Detect assert statements (with or without space after assert)
/^[[:space:]]*assert([[:space:]]|\()/ {
    # Determine context: function name if inside one
    context = "module-level"
    if (in_func) context = func_name
    printf "%d:0: error: assert in %s — use explicit validation with if-check and Result.failure() (no-assert-validation)\n", NR, context
    violations++
}

# Detect function definition (for context reporting only)
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    next
}

# Detect function end by indentation
in_func {
    if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[^[:space:]]/) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent == 0 && $0 !~ /^[[:space:]]*$/) {
            in_func = 0
        }
    }
}

END { exit (violations > 0) ? 1 : 0 }
'

assert_validation_check_run() {
  local src_dir="${1:-.}"

  lint_step "assert validation check (P5: SC-007/SC-113) ${src_dir}"

  local py_files=()
  while IFS= read -r -d '' f; do
    py_files+=("$f")
  done < <(find "${src_dir}" -name "*.py" -not -name 'test_*.py' -not -name '*_test.py' -type f -print0 2>/dev/null)

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "assert-validation-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_ASSERT_VALIDATION_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "assert-validation-check: assert statements found in src/"
    return 1
  fi

  lint_ok "assert-validation-check (P5)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  assert_validation_check_run "$@"
fi
