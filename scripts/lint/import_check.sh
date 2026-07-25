#!/usr/bin/env bash
# import_check.sh — No imports inside functions/methods.
#
# Rule: All imports must be at module top level.
# Exception: `if TYPE_CHECKING:` blocks are allowed (Google 3.19.12).
#
# Uses awk to track function scope and detect import statements inside them.

if [[ -n "${SETUP_LINT_IMPORT_CHECK_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_IMPORT_CHECK_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_IMPORT_CHECK_AWK='
BEGIN {
    in_func = 0
    func_indent = 0
    func_line = 0
    func_name = ""
    paren_depth = 0
    in_type_checking = 0
    type_checking_indent = 0
    violations = 0
    in_tq_dq = 0
    in_tq_sq = 0
    sq = sprintf("%c", 39)
    dq = "\""
    tqs = sq sq sq
    tqd = dq dq dq
}

# Track triple-quoted docstrings and skip lines inside them
{
    was_in_docstring = (in_tq_dq || in_tq_sq)
    update_docstring_state($0)
    if (was_in_docstring) next
}

# Track TYPE_CHECKING blocks (allowed)
/^[[:space:]]*if[[:space:]]+.*TYPE_CHECKING/ {
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    type_checking_indent = length(line)
    in_type_checking = 1
    next
}

# Detect function/method definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_indent = length(line)
    func_line = NR

    # Extract function name
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname

    paren_depth = 0
    next
}

# Track parentheses for multi-line signatures
in_func && paren_depth >= 0 {
    line = $0
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }
}

# Detect return from function scope
in_func && paren_depth <= 0 {
    # Check indentation to detect end of function
    if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[^[:space:]]/) {
        # Blank line or dedent — might be end of function
        # But only if we are at the same or lower indent level
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent <= func_indent && $0 !~ /^[[:space:]]*$/) {
            in_func = 0
        }
    }
}

# Inside function, check for import statements
in_func && paren_depth <= 0 {
    # Skip TYPE_CHECKING blocks inside functions (rare but possible)
    if (in_type_checking) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent <= type_checking_indent && $0 !~ /^[[:space:]]*$/) {
            in_type_checking = 0
        }
        next
    }

    # Check for import statements (strip strings to avoid false positives)
    stripped = strip_strings($0)
    if (stripped ~ /^[[:space:]]*import[[:space:]]/ || stripped ~ /^[[:space:]]*from[[:space:]]/) {
        printf "%d:0: error: import inside function \"%s\" — move to module top level (import-in-function)\n", NR, func_name
        violations++
    }
}

# update_docstring_state: scan line for triple-quote transitions.
function update_docstring_state(line,    i, len, c3) {
    len = length(line)
    for (i = 1; i <= len - 2; i++) {
        c3 = substr(line, i, 3)
        if (!in_tq_dq && !in_tq_sq && c3 == tqd) { in_tq_dq = 1 }
        else if (in_tq_dq && c3 == tqd) { in_tq_dq = 0 }
        else if (!in_tq_dq && !in_tq_sq && c3 == tqs) { in_tq_sq = 1 }
        else if (in_tq_sq && c3 == tqs) { in_tq_sq = 0 }
    }
}

# strip_strings: replace string literal content with spaces.
function strip_strings(line,    result, i, len, c, in_str, qchar) {
    result = ""
    in_str = 0
    len = length(line)
    for (i = 1; i <= len; i++) {
        c = substr(line, i, 1)
        if (in_str) {
            if (c == qchar) { in_str = 0 }
            result = result " "
        } else {
            if (c == dq || c == sq) { in_str = 1; qchar = c }
            else { result = result c }
        }
    }
    return result
}

END { exit (violations > 0) ? 1 : 0 }
'

import_check_run() {
  local src_dir="${1:-.}"
  local tests_dir="${2:-}"

  lint_step "import-in-function check"

  local dirs=("${src_dir}")
  if [[ -n "${tests_dir}" && -d "${tests_dir}" ]]; then
    dirs+=("${tests_dir}")
  fi

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "import-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_IMPORT_CHECK_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "import-check: imports inside functions found"
    return 1
  fi

  lint_ok "import-check"
}

# When executed directly (not sourced), run with provided arguments.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  import_check_run "$@"
fi
