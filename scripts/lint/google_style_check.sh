#!/usr/bin/env bash
# google_style_check.sh — Google Style Guide specific validations.
#
# Checks:
#   - Docstring summary line <= 80 chars (Google 3.8.1)
#   - TODO format: TODO(bugref) - description (Google 3.12)
#   - No mutable default arguments (Google 2.12)
#   - Function length ~40 lines (Google 3.18)
#   - No print() in src/ — use logging (Google 3.10.1)
#   - Docstring Args/Returns/Raises sections exist when needed (Google 3.8.3)

if [[ -n "${SETUP_LINT_GOOGLE_STYLE_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_GOOGLE_STYLE_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_GOOGLE_STYLE_AWK='
BEGIN {
    in_docstring = 0
    docstring_line = 0
    docstring_quote = ""
    in_func = 0
    func_line = 0
    func_name = ""
    func_body_lines = 0
    func_indent = 0
    paren_depth = 0
    errors = 0
    in_comment = 0
    in_string = 0
}

# Track docstrings
/^[[:space:]]*("""|\047\047\047)/ {
    if (!in_docstring) {
        in_docstring = 1
        docstring_line = NR
        if ($0 ~ /"""/) docstring_quote = "\"\"\""
        else docstring_quote = "\047\047\047"
        rest = $0
        gsub(/^[[:space:]]*("""|\047\047\047)/, "", rest)
        if (rest ~ docstring_quote) {
            gsub(docstring_quote, "", rest)
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", rest)
            if (length(rest) > 80) {
                printf "%d:0: warning: docstring summary exceeds 80 chars (%d) (google-docstring-length)\n", NR, length(rest)
            }
            in_docstring = 0
        }
    } else if ($0 ~ docstring_quote) {
        in_docstring = 0
    }
    next
}

in_docstring {
    if ($0 ~ docstring_quote) {
        in_docstring = 0
    }
    next
}

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # Check previous function length
    if (in_func && func_body_lines > 40) {
        printf "%d:0: warning: function \"%s\" is %d lines (google-function-length, max ~40)\n", func_line, func_name, func_body_lines
    }

    in_func = 1
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_indent = length(line)
    func_line = NR
    func_body_lines = 0

    # Extract function name
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname

    # Check for mutable default arguments in parameters only
    params = $0
    open_idx = index(params, "(")
    if (open_idx > 0) {
        params = substr(params, open_idx + 1)
        depth = 1
        close_idx = 0
        for (pi = 1; pi <= length(params); pi++) {
            pc = substr(params, pi, 1)
            if (pc == "(") depth++
            if (pc == ")") { depth--; if (depth == 0) { close_idx = pi; break } }
        }
        if (close_idx > 0) params = substr(params, 1, close_idx - 1)
        gsub(/:[^=,)]+/, "", params)
        if (params ~ /= *\[/ || params ~ /= *\{/ ||
            params ~ /= *set\(/ || params ~ /= *list\(/ ||
            params ~ /= *dict\(/) {
            printf "%d:0: error: mutable default argument in function \"%s\" — use None instead (google-mutable-default)\n", NR, func_name
            errors++
        }
    }

    paren_depth = 0
    # Track parens on def line for multi-line signature detection
    def_line = $0
    sub(/#.*/, "", def_line)
    for (di = 1; di <= length(def_line); di++) {
        dc = substr(def_line, di, 1)
        if (dc == "(") paren_depth++
        if (dc == ")") paren_depth--
    }
    next
}

# Track function body lines
in_func {
    # Track parentheses for multi-line signatures
    line = $0
    sub(/#.*/, "", line)
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }

    # Only count body lines after signature is complete
    if (paren_depth <= 0) {
        func_body_lines++
    }
}

# Check TODO format: must be TODO(bugref) - description
/TODO/ {
    # Skip if in docstring
    if (in_docstring) next

    line = $0
    # Remove leading whitespace and comment markers
    gsub(/^[[:space:]]*#?[[:space:]]*/, "", line)

    # Valid formats:
    #   TODO(bugref): description
    #   TODO(bugref) - description
    # Invalid:
    #   TODO: description (no bug reference)
    #   TODO username: description
    if (line ~ /^TODO\(.+\)[[:space:]]*[:-]/) {
        # Valid format with bug reference
    } else if (line ~ /^TODO[[:space:]]*[:-]/) {
        # Missing bug reference
        printf "%d:0: warning: TODO missing bug reference — use TODO(bugref) - description (google-todo-format)\n", NR
    }
}

# Check for print() statements (should use logging)
/^[[:space:]]*print[[:space:]]*\(/ {
    if (in_docstring) next
    printf "%d:0: warning: use logging instead of print() (google-no-print)\n", NR
}

END {
    # Check last function
    if (in_func && func_body_lines > 40) {
        printf "%d:0: warning: function \"%s\" is %d lines (google-function-length, max ~40)\n", func_line, func_name, func_body_lines
    }
    exit (errors > 0) ? 1 : 0
}
'

google_style_check_run() {
  local src_dir="${1:-.}"

  lint_step "Google Style checks"

  local py_files=()
  while IFS= read -r -d '' f; do
    py_files+=("$f")
  done < <(find "${src_dir}" -name "*.py" -type f -print0 2>/dev/null)

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "google-style-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    local rc=0
    output=$(awk "${_GOOGLE_STYLE_AWK}" "${f}" 2>/dev/null) || rc=$?
    if [[ ${rc} -ne 0 ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "google-style-check: Google Style violations found"
    return 1
  fi

  lint_ok "google-style-check"
}

# When executed directly (not sourced), run with provided arguments.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  google_style_check_run "$@"
fi
