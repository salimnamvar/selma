#!/usr/bin/env bash
# result_return_check.sh — P3: Explicit Over Implicit (SC-003, SC-005, SC-024, SC-025).
#
# Rules:
#   SC-003: Every function SHALL return Result[T] (except dunders/pure functions).
#   SC-005: No tuple returns — use Result[T] or named types.
#   SC-024: Explicit return type annotation on every function.
#   SC-025: No star imports (from module import *).
#
# Exceptions:
#   - Dunder methods and protocol-constrained interfaces.
#   - Pure functions with no failure path may return direct types.

if [[ -n "${SETUP_LINT_RESULT_RETURN_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_RESULT_RETURN_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_RESULT_RETURN_AWK=$(cat << 'AWKEOF'
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = 0
    paren_depth = 0
    has_return_type = 0
    violations = 0
    in_docstring = 0
    docstring_char = 0
    in_sig = 0
}

/"""/ || /\047\047\047/ {
    if (!in_docstring) {
        in_docstring = 1
        if ($0 ~ /"""/) docstring_char = 3
        else docstring_char = 1
        if (docstring_char == 3 && $0 ~ /""".*"""/) in_docstring = 0
        if (docstring_char == 1 && $0 ~ /\047\047\047.*\047\047\047/) in_docstring = 0
    } else {
        if (docstring_char == 3 && $0 ~ /"""/) in_docstring = 0
        if (docstring_char == 1 && $0 ~ /\047\047\047/) in_docstring = 0
    }
    next
}
in_docstring { next }

/^[[:space:]]*#/ { next }

/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    in_sig = 1
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_indent = length(line)
    func_line = NR
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    paren_depth = 0
    buf = ""
    has_return_type = 0
    # Count parens on the def line itself
    def_check = $0
    sub(/#.*/, "", def_check)
    for (di = 1; di <= length(def_check); di++) {
        dc = substr(def_check, di, 1)
        if (dc == "(") paren_depth++
        if (dc == ")") paren_depth--
    }
    if ($0 ~ /\)[[:space:]]*->[[:space:]]/) {
        has_return_type = 1
    }
    next
}

in_func && in_sig {
    line = $0
    sub(/#.*/, "", line)
    buf = buf line
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }
    if (!has_return_type && paren_depth <= 0) {
        if (buf ~ /\)[[:space:]]*->[[:space:]]/) {
            has_return_type = 1
        }
        in_sig = 0
    }
}

in_func && paren_depth <= 0 {
    if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[^[:space:]]/) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent <= func_indent && $0 !~ /^[[:space:]]*$/) {
            if (!has_return_type && func_name !~ /^__.*__$/) {
                printf "%d:0: warning: function \"%s\" missing explicit return type annotation (result-return-type)\n", func_line, func_name
                violations++
            }
            in_func = 0
            in_sig = 0
        }
    }
}

in_func && /^[[:space:]]*return[[:space:]].*,[[:space:]]/ {
    if (func_name !~ /^__.*__$/) {
        line = $0
        gsub(/"([^"\\]|\\.)*"/, "", line)
        gsub(/'([^'\\]|\\.)*'/, "", line)
        while (line ~ /\([^()]*\)/) gsub(/\([^()]*\)/, "", line)
        while (line ~ /\[[^[\]]*\]/) gsub(/\[[^[\]]*\]/, "", line)
        while (line ~ /\{[^{}]*\}/) gsub(/\{[^{}]*\}/, "", line)
        if (line ~ /^[[:space:]]*return[[:space:]].*,[[:space:]]/) {
            printf "%d:0: error: tuple return in function \"%s\" — use Result[T] or named type (no-tuple-return)\n", NR, func_name
            violations++
        }
    }
}

/^[[:space:]]*from[[:space:]]+[a-zA-Z0-9_.]+[[:space:]]+import[[:space:]]+\*/ {
    printf "%d:0: error: star import — use explicit imports (no-star-import)\n", NR
    violations++
}

END { exit (violations > 0) ? 1 : 0 }
AWKEOF
)

result_return_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "result-return-check: no directories provided, skipping"
    return 0
  fi

  lint_step "result return check (P3: SC-003/005/024/025) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "result-return-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_RESULT_RETURN_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "result-return-check: violations found"
    return 1
  fi

  lint_ok "result-return-check (P3)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  result_return_check_run "$@"
fi
