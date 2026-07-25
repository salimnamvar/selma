#!/usr/bin/env bash
# return_check.sh — Enforce single return per function.
#
# Rule: Every function/method must have exactly ONE return statement.
# No early returns, no guard clauses, no exceptions.
#
# Uses awk to track function boundaries and count return statements.

if [[ -n "${SETUP_LINT_RETURN_CHECK_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_RETURN_CHECK_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_RETURN_CHECK_AWK='
BEGIN {
    in_func = 0
    func_indent = 0
    func_line = 0
    func_name = ""
    return_count = 0
    paren_depth = 0
    buf = ""
    violations = 0
    has_yield = 0
    nested_indent = 0
    stack_depth = 0
    in_docstring = 0
    nested_in_sig = 0
}

function push_state() {
    stack_depth++
    s_func_indent[stack_depth] = func_indent
    s_func_name[stack_depth] = func_name
    s_func_line[stack_depth] = func_line
    s_return_count[stack_depth] = return_count
    s_has_yield[stack_depth] = has_yield
    s_paren_depth[stack_depth] = paren_depth
    s_buf[stack_depth] = buf
}

function pop_state() {
    func_indent = s_func_indent[stack_depth]
    func_name = s_func_name[stack_depth]
    func_line = s_func_line[stack_depth]
    return_count = s_return_count[stack_depth]
    has_yield = s_has_yield[stack_depth]
    paren_depth = s_paren_depth[stack_depth]
    buf = s_buf[stack_depth]
    stack_depth--
}

function strip_strings(s,    r) {
    r = s
    gsub(/#.*/, "", r)
    gsub(/"([^"\\]|\\.)*"/, "", r)
    gsub(/\047\047\047([^\047]|\047[^\047\047])*\047\047\047/, "", r)
    gsub(/\047([^\047\\]|\\.)*\047/, "", r)
    return r
}

function strip_parens(s,    r, prev) {
    r = s
    prev = ""
    while (prev != r) {
        prev = r
        gsub(/\([^()]*\)/, "", r)
    }
    return r
}

# Detect function/method definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    current_indent = length(line)

    if (nested_indent > 0 && current_indent <= nested_indent) {
        pop_state()
        nested_indent = 0
    }

    if (in_func && return_count > 1) {
        printf "%d:0: error: function \"%s\" has %d return statements (single-return)\n", func_line, func_name, return_count
        violations++
    }

    if (in_func && current_indent > func_indent && nested_indent == 0) {
        push_state()
        nested_indent = current_indent
        sig_check = $0
        sub(/#.*/, "", sig_check)
        nested_in_sig = (sig_check ~ /\)/) ? 0 : 1
    }

    in_func = 1
    func_indent = current_indent
    func_line = NR
    in_docstring = 0

    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname

    if (func_name ~ /^__.*__$/) {
        if (nested_indent > 0) {
            pop_state()
            nested_indent = 0
        } else {
            in_func = 0
        }
        next
    }

    return_count = 0
    paren_depth = 0
    buf = ""
    has_yield = 0
    next
}

# Inside function body
in_func {
    if (nested_indent > 0) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        blank = ($0 ~ /^[[:space:]]*$/)
        if (blank) {
            next
        } else if (current_indent < nested_indent) {
            pop_state()
            nested_indent = 0
        } else if (current_indent == nested_indent) {
            if (nested_in_sig) {
                sig_line = $0
                if (sig_line ~ /\)/) {
                    nested_in_sig = 0
                }
                next
            } else {
                pop_state()
                nested_indent = 0
            }
        }
        # current_indent > nested_indent: fall through to body processing
    }

    if (in_docstring) {
        if (in_docstring == 1 && $0 ~ /"""/) {
            in_docstring = 0
        } else if (in_docstring == 2 && $0 ~ /\047\047\047/) {
            in_docstring = 0
        }
        next
    }

    if (return_count == 0 && paren_depth <= 0) {
        stripped = $0
        gsub(/^[[:space:]]+/, "", stripped)
        if (stripped ~ /^"""/) {
            rest = stripped
            sub(/^"""/, "", rest)
            if (rest !~ /"""/) {
                in_docstring = 1
                next
            }
        } else if (stripped ~ /^\047\047\047/) {
            rest = stripped
            sub(/^\047\047\047/, "", rest)
            if (rest !~ /\047\047\047/) {
                in_docstring = 2
                next
            }
        }
    }

    line = $0
    sub(/#.*/, "", line)
    buf = buf line

    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }

    check_yield = strip_strings($0)
    if (check_yield ~ /yield/) {
        has_yield = 1
    }

    if (paren_depth <= 0 && !has_yield) {
        check_line = strip_strings($0)

        if (check_line ~ /^[[:space:]]*return[[:space:]]/ ||
            check_line ~ /^[[:space:]]*return$/) {
            return_count++
        }

        if (check_line ~ /^[[:space:]]*return[[:space:]]/) {
            after_return = check_line
            sub(/^[[:space:]]*return[[:space:]]+/, "", after_return)
            after_return = strip_parens(after_return)
            if (after_return ~ /,/) {
                printf "%d:0: error: function \"%s\" has a tuple return (single-return)\n", NR, func_name
                violations++
            }
        }
    }
}

END {
    while (stack_depth > 0) {
        if (return_count > 1) {
            printf "%d:0: error: function \"%s\" has %d return statements (single-return)\n", func_line, func_name, return_count
            violations++
        }
        pop_state()
    }

    if (in_func && return_count > 1) {
        printf "%d:0: error: function \"%s\" has %d return statements (single-return)\n", func_line, func_name, return_count
        violations++
    }
    exit (violations > 0) ? 1 : 0
}
'

return_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "return-check: no directories provided, skipping"
    return 0
  fi

  lint_step "single-return check ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "return-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_RETURN_CHECK_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "return-check: multiple return statements found"
    return 1
  fi

  lint_ok "return-check"
}

# When executed directly (not sourced), run with provided arguments.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  return_check_run "$@"
fi
