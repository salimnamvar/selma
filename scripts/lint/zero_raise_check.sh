#!/usr/bin/env bash
# zero_raise_check.sh — P2: Localized Failure Handling (SC-002, SC-052).
#
# Rule: Every function SHALL contain zero raise statements. All exceptions
#       SHALL be caught within the function and converted to structured results.
#
# Exceptions:
#   - Python dunder methods (__init__, __enter__, __exit__, etc.)

if [[ -n "${SETUP_LINT_ZERO_RAISE_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_ZERO_RAISE_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_ZERO_RAISE_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = 0
    paren_depth = 0
    violations = 0
    in_docstring_dbl = 0
    in_docstring_sgl = 0
    sig_closed = 0
    sq = sprintf("%c", 39)
    sq_re = sprintf("%s([^%s\\\\]|\\\\.)*%s", sq, sq, sq)
    triple_sq = sq sq sq
}

# Track triple-double-quoted docstrings
/"""/ {
    if (!in_docstring_dbl) {
        in_docstring_dbl = 1
        if ($0 ~ /""".*"""/) in_docstring_dbl = 0
    } else {
        if ($0 ~ /"""/) in_docstring_dbl = 0
    }
    next
}
in_docstring_dbl { next }

# Track triple-single-quoted docstrings
{
    if (index($0, triple_sq) > 0) {
        if (!in_docstring_sgl) {
            in_docstring_sgl = 1
            first = index($0, triple_sq)
            rest = substr($0, first + 3)
            if (index(rest, triple_sq) > 0) in_docstring_sgl = 0
        } else {
            in_docstring_sgl = 0
        }
        next
    }
}
in_docstring_sgl { next }

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    sig_closed = 0
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_indent = length(line)
    func_line = NR
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    paren_depth = 0
    if (func_name ~ /^__.*__$/) next
    next
}

# Track function scope via indentation
in_func && paren_depth <= 0 {
    if ($0 ~ /^[[:space:]]*$/) next
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    current_indent = length(line)
    if (!sig_closed) {
        if (current_indent <= func_indent && $0 ~ /\):[[:space:]]*$/) {
            sig_closed = 1
        }
    }
    if (sig_closed && current_indent <= func_indent && $0 !~ /^[[:space:]]*$/) {
        in_func = 0
    }
}

# Detect raise statements inside functions
in_func && /raise[[:space:]]/ || in_func && /raise$/ {
    check_line = $0
    gsub(/#.*/, "", check_line)
    gsub(/"([^"\\]|\\.)*"/, "", check_line)
    gsub(sq_re, "", check_line)
    if (check_line ~ /raise[[:space:]]/ || check_line ~ /raise$/) {
        if (func_name ~ /^__.*__$/) next
        if ($0 ~ /^[[:space:]]*#/) next

        printf "%d:0: error: raise statement in function \"%s\" — handle locally and return Result.failure() (zero-raise)\n", NR, func_name
        violations++
    }
}

# Detect re-raise (raise inside except block)
in_func && /^[[:space:]]*raise$/ {
    check_line = $0
    if (check_line ~ /^[[:space:]]*raise[[:space:]]*$/) {
        if (func_name !~ /^__.*__$/) {
            printf "%d:0: error: re-raise in function \"%s\" — convert to Result.failure() (zero-raise-reraise)\n", NR, func_name
            violations++
        }
    }
}

END { exit (violations > 0) ? 1 : 0 }
'

zero_raise_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "zero-raise-check: no directories provided, skipping"
    return 0
  fi

  lint_step "zero-raise check (P2: SC-002) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "zero-raise-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_ZERO_RAISE_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "zero-raise-check: raise statements found"
    return 1
  fi

  lint_ok "zero-raise-check (P2)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  zero_raise_check_run "$@"
fi
