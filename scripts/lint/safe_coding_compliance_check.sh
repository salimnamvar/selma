#!/usr/bin/env bash
# safe_coding_compliance_check.sh — Master check: SC-001/SC-003/SC-011/SC-012.
#
# Every function SHALL:
#   1. Return Result[T] (SC-003)
#   2. Use b_continue for error gating (SC-011)
#   3. Have a single return at the end (SC-001)
#
# This is the ENFORCER linter — it finds functions that do NOT follow
# the safe coding pattern AT ALL, not just functions that misuse it.
#
# Exemptions:
#   - Dunder methods (__init__, __enter__, __exit__, etc.)
#   - @staticmethod factory methods on Result class (success/failure)
#   - Functions with `# noqa: safe-coding` comment

if [[ -n "${SETUP_LINT_SAFE_CODING_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_SAFE_CODING_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_SAFE_CODING_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = 0
    paren_depth = 0
    has_return_type = 0
    has_result_return = 0
    has_b_continue_init = 0
    has_b_continue_use = 0
    return_count = 0
    is_dunder = 0
    is_staticmethod = 0
    has_noqa = 0
    in_docstring = 0
    in_sig = 0
    sig_buf = ""
    dq = sprintf("%c%c%c", 34, 34, 34)
    sq = sprintf("%c%c%c", 39, 39, 39)
    violations = 0
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
in_docstring && /"""/ { in_docstring = 0; next }
in_docstring { next }

# Track triple-single-quote docstrings
{
    has_sq3 = (index($0, sq sq sq) > 0)
    if (has_sq3) {
        if (!in_docstring) {
            in_docstring = 1
            first = index($0, sq sq sq)
            rest = substr($0, first + 3)
            if (index(rest, sq sq sq) > 0) in_docstring = 0
        } else {
            in_docstring = 0
        }
        next
    }
}
in_docstring { next }

# Skip pure comment lines
/^[[:space:]]*#/ { next }

# Detect @staticmethod decorator
/^[[:space:]]*@staticmethod/ {
    is_staticmethod = 1
    next
}

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # Report previous function
    if (in_func && func_line > 0) {
        _report_violations()
    }

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

    # Check exemptions
    is_dunder = (func_name ~ /^__.*__$/)
    has_noqa = 0

    # Reset per-function state
    paren_depth = 0
    has_return_type = 0
    has_result_return = 0
    has_b_continue_init = 0
    has_b_continue_use = 0
    return_count = 0
    sig_buf = ""

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
        if ($0 ~ /->[^:]*Result\[/) has_result_return = 1
    }
    sig_buf = def_check
    next
}

# Inside function signature (multi-line)
in_func && in_sig {
    line = $0
    sub(/#.*/, "", line)
    sig_buf = sig_buf " " line
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }
    if (paren_depth <= 0) {
        in_sig = 0
        if (sig_buf ~ /\)[[:space:]]*->[[:space:]]/) has_return_type = 1
        if (sig_buf ~ /->[^:]*Result\[/) has_result_return = 1
    }
    next
}

# Inside function body
in_func && paren_depth <= 0 {
    # Check function end
    if ($0 !~ /^[[:space:]]*$/) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent <= func_indent) {
            if (func_line > 0) _report_violations()
            in_func = 0
            in_sig = 0
            is_staticmethod = 0
            next
        }
    }

    # Strip comments and strings
    check_line = $0
    gsub(/#.*/, "", check_line)
    gsub(/"[^"]*"/, "", check_line)
    gsub(/\047[^\047]*\047/, "", check_line)

    # Count returns
    if (check_line ~ /^[[:space:]]*return[[:space:]]/ || check_line ~ /^[[:space:]]*return$/) {
        return_count++
    }

    # Detect b_continue = True
    if (check_line ~ /(^|[^.])b_continue[[:space:]]*(:[[:space:]]*[a-zA-Z0-9_.|]+)?[[:space:]]*=[[:space:]]*True/) {
        has_b_continue_init = 1
        has_b_continue_use = 1
    }

    # Detect b_continue = False
    if (check_line ~ /(^|[^.])b_continue[[:space:]]*(:[[:space:]]*[^=]+)?[[:space:]]*=[[:space:]]*False/) {
        has_b_continue_use = 1
    }

    # Detect if b_continue: guard
    if (check_line ~ /(^|[^.])b_continue[[:space:]]*:/) {
        has_b_continue_use = 1
    }
}

function _report_violations(    _msg) {
    if (is_dunder) return
    if (has_noqa) return
    if (is_staticmethod && (func_name == "success" || func_name == "failure")) return
    if (func_line == 0) return

    # Rule 1: Must return Result[T]
    if (!has_result_return) {
        _msg = sprintf("function \"%s\" does not return Result[T]", func_name)
        printf "%d:0: error: %s — add -> Result[T] per SC-003 (safe-coding-no-result)\n", func_line, _msg
        violations++
    }

    # Rule 2: Must have b_continue
    if (!has_b_continue_init) {
        _msg = sprintf("function \"%s\" has no b_continue", func_name)
        printf "%d:0: error: %s — add b_continue per SC-011 (safe-coding-no-b-continue)\n", func_line, _msg
        violations++
    }

    # Rule 3: Single return
    if (return_count > 1) {
        _msg = sprintf("function \"%s\" has %d return statements", func_name, return_count)
        printf "%d:0: error: %s — single exit per SC-001 (safe-coding-multi-return)\n", func_line, _msg
        violations++
    }
}

END {
    if (in_func && func_line > 0) _report_violations()
    exit (violations > 0) ? 1 : 0
}
'

safe_coding_compliance_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "safe-coding-compliance: no directories provided, skipping"
    return 0
  fi

  lint_step "safe coding compliance (SC-001/003/011/012) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "safe-coding-compliance: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_SAFE_CODING_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "safe-coding-compliance: violations found"
    return 1
  fi

  lint_ok "safe-coding-compliance (SC-001/003/011/012)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  safe_coding_compliance_check_run "$@"
fi
