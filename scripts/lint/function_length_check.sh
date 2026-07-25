#!/usr/bin/env bash
# function_length_check.sh — Function Design: SC-010 Function Length Limit.
#
# Rule: No function SHALL exceed 60 lines of executable code (excluding
#       docstrings, comments, blank lines, and function signature).
#
# Exceptions:
#   - Generated code (protocol buffers, ORM models).
#   - Boilerplate from canonical pattern (SC-012).
#   - Nested function definitions count toward enclosing function.

if [[ -n "${SETUP_LINT_FUNCTION_LENGTH_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_FUNCTION_LENGTH_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_FUNCTION_LENGTH_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = 0
    paren_depth = 0
    body_lines = 0
    in_docstring = 0
    in_multiline_sig = 0
    violations = 0
    stack_top = 0
}

# Track triple-single-quote docstrings
/\047\047\047/ {
    if (!in_docstring) {
        in_docstring = 1
        if ($0 ~ /\047\047\047.*\047\047\047/) in_docstring = 0
    } else {
        if ($0 ~ /\047\047\047/) in_docstring = 0
    }
    next
}

# Track triple-double-quote docstrings
/"""/ {
    if (!in_docstring) {
        in_docstring = 1
        if ($0 ~ /""".*"""/) in_docstring = 0
    } else {
        if ($0 ~ /"""/) in_docstring = 0
    }
    next
}
in_docstring { next }

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # Get indent of this def
    def_line = $0
    gsub(/[^[:space:]].*$/, "", def_line)
    def_indent = length(def_line)

    if (in_func) {
        if (def_indent > func_indent) {
            # Nested function - push current state
            stack_top++
            stack_func_name[stack_top] = func_name
            stack_func_line[stack_top] = func_line
            stack_body_lines[stack_top] = body_lines
            stack_func_indent[stack_top] = func_indent
        } else {
            # Not nested - check current function
            if (body_lines > 60) {
                printf "%d:0: error: function \"%s\" is %d executable lines (max 60) (function-length)\n", func_line, func_name, body_lines
                violations++
            }
            # Pop stacked functions that are also ending
            while (stack_top > 0 && def_indent <= stack_func_indent[stack_top]) {
                func_name = stack_func_name[stack_top]
                func_line = stack_func_line[stack_top]
                body_lines = stack_body_lines[stack_top]
                func_indent = stack_func_indent[stack_top]
                stack_top--
                if (body_lines > 60) {
                    printf "%d:0: error: function \"%s\" is %d executable lines (max 60) (function-length)\n", func_line, func_name, body_lines
                    violations++
                }
            }
        }
    }

    # Start tracking new function
    in_func = 1
    func_indent = def_indent
    func_line = NR
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    paren_depth = 0
    body_lines = 0

    # Check if signature is complete on this line
    sig_line = $0
    sub(/#.*/, "", sig_line)
    for (i = 1; i <= length(sig_line); i++) {
        c = substr(sig_line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }
    next
}

# Track function body
in_func {
    # Count parens to detect end of multi-line signature
    if (paren_depth > 0) {
        sig_line = $0
        sub(/#.*/, "", sig_line)
        for (i = 1; i <= length(sig_line); i++) {
            c = substr(sig_line, i, 1)
            if (c == "(") paren_depth++
            if (c == ")") paren_depth--
        }
        next
    }

    # Skip blank lines and comments
    if ($0 ~ /^[[:space:]]*$/) next
    if ($0 ~ /^[[:space:]]*#/) next

    # Skip docstring lines
    if (in_docstring) next

    # Check if nested function ended (indent dropped)
    while (stack_top > 0) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent <= func_indent) {
            # Check current function
            if (body_lines > 60) {
                printf "%d:0: error: function \"%s\" is %d executable lines (max 60) (function-length)\n", func_line, func_name, body_lines
                violations++
            }
            # Pop
            func_name = stack_func_name[stack_top]
            func_line = stack_func_line[stack_top]
            body_lines = stack_body_lines[stack_top]
            func_indent = stack_func_indent[stack_top]
            stack_top--
        } else {
            break
        }
    }

    # Count executable lines
    body_lines++
}

END {
    if (in_func && body_lines > 60) {
        printf "%d:0: error: function \"%s\" is %d executable lines (max 60) (function-length)\n", func_line, func_name, body_lines
        violations++
    }
    # Check remaining functions on the stack
    while (stack_top > 0) {
        func_name = stack_func_name[stack_top]
        func_line = stack_func_line[stack_top]
        body_lines = stack_body_lines[stack_top]
        stack_top--
        if (body_lines > 60) {
            printf "%d:0: error: function \"%s\" is %d executable lines (max 60) (function-length)\n", func_line, func_name, body_lines
            violations++
        }
    }
    exit (violations > 0) ? 1 : 0
}
'

function_length_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "function-length-check: no directories provided, skipping"
    return 0
  fi

  lint_step "function length check (SC-010: max 60 lines) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "function-length-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_FUNCTION_LENGTH_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "function-length-check: functions exceeding 60 lines"
    return 1
  fi

  lint_ok "function-length-check (SC-010)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  function_length_check_run "$@"
fi
