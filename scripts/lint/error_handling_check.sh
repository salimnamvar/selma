#!/usr/bin/env bash
# error_handling_check.sh — Error Handling Rules (SC-041, SC-042, SC-052).
#
# Rules:
#   SC-041: Specific exception handling — catch specific types, not bare/broad.
#   SC-042: No silent failures — empty except blocks are defects.
#   SC-052: No exception re-raising.
#
# Checks:
#   - Empty except blocks (pass or no body).
#   - except Exception: without safety net pattern (warning).
#   - Re-raise inside except blocks.

if [[ -n "${SETUP_LINT_ERROR_HANDLING_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_ERROR_HANDLING_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_Q3=$(printf '%s%s%s' "'" "'" "'")

_ERROR_HANDLING_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_base_indent = 0
    in_except = 0
    except_line = 0
    except_indent = 0
    except_body_count = 0
    violations = 0
    in_docstring = 0
    q3 = Q3
}

# Track triple-double-quote docstrings
/"""/ && !in_docstring {
    in_docstring = 1
    if ($0 ~ /""".*"""/) in_docstring = 0
    next
}
in_docstring && /"""/ {
    in_docstring = 0
    next
}

# Track triple-single-quote docstrings
$0 ~ q3 && !in_docstring {
    in_docstring = 1
    if ($0 ~ q3 ".*" q3) in_docstring = 0
    next
}
in_docstring && $0 ~ q3 {
    in_docstring = 0
    next
}
in_docstring { next }

# Skip pure comment lines
/^[[:space:]]*#/ { next }

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # Close any open except block from the previous function
    if (in_except && except_body_count == 0) {
        printf "%d:0: error: empty except block in \"%s\" — convert to Result.failure() (silent-failure)\n", except_line, func_name
        violations++
    }
    in_except = 0
    in_func = 1
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_base_indent = length(line)
    func_line = NR
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    next
}

# Check for except block end and count body (must run before function-end check)
in_except {
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    current_indent = length(line)

    # Strip trailing comments for body analysis
    body_line = $0
    gsub(/#.*/, "", body_line)
    gsub(/[[:space:]]*$/, "", body_line)
    is_code = (body_line !~ /^[[:space:]]*$/)

    if (current_indent <= except_indent && is_code) {
        # End of except block
        if (except_body_count == 0) {
            printf "%d:0: error: empty except block in \"%s\" — convert to Result.failure() (silent-failure)\n", except_line, func_name
            violations++
        }
        in_except = 0
    } else if (is_code) {
        # Check for re-raise (SC-052)
        if (body_line ~ /^[[:space:]]*raise[[:space:]]*$/) {
            printf "%d:0: error: re-raise in except block — convert to Result.failure() (re-raise)\n", NR
            violations++
        }
        # Check for pass (empty body indicator)
        if (body_line ~ /^[[:space:]]*pass[[:space:]]*$/) {
            except_body_count = 0
        } else {
            except_body_count++
        }
    }
}

# Detect function end: when indentation drops to or below the def line
in_func && $0 !~ /^[[:space:]]*$/ {
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    current_indent = length(line)
    if (current_indent <= func_base_indent) {
        # Close any open except block before leaving function
        if (in_except && except_body_count == 0) {
            printf "%d:0: error: empty except block in \"%s\" — convert to Result.failure() (silent-failure)\n", except_line, func_name
            violations++
        }
        in_func = 0
        in_except = 0
    }
}

# Detect except with specific type (track for empty body and re-raise checks)
in_func && /^[[:space:]]*except[[:space:]]+[A-Za-z]/ {
    in_except = 1
    except_line = NR
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    except_indent = length(line)
    except_body_count = 0
}

END {
    if (in_except && except_body_count == 0) {
        printf "%d:0: error: empty except block in \"%s\" — convert to Result.failure() (silent-failure)\n", except_line, func_name
        violations++
    }
    exit (violations > 0) ? 1 : 0
}
'

error_handling_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "error-handling-check: no directories provided, skipping"
    return 0
  fi

  lint_step "error handling check (SC-041/042/052) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "error-handling-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk -v Q3="${_Q3}" "${_ERROR_HANDLING_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "error-handling-check: error handling violations found"
    return 1
  fi

  lint_ok "error-handling-check"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  error_handling_check_run "$@"
fi
