#!/usr/bin/env bash
# security_check.sh — Security Rules (SC-100, SC-101, SC-104).
#
# Rules:
#   SC-100: No secrets in source code.
#   SC-101: Parameterized queries only — no string-formatted SQL.
#   SC-104: No eval() or exec().
#
# Checks:
#   - eval() and exec() calls in production code.
#   - SQL string formatting patterns (f-string, %, .format() with SQL keywords).
#   - Hardcoded secret patterns (API keys, passwords).

if [[ -n "${SETUP_LINT_SECURITY_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_SECURITY_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_SECURITY_AWK='
BEGIN {
    in_func = 0
    func_name = ""
    violations = 0
    in_docstring = 0
    in_docstring_single = 0
    in_comment = 0
}

# Track docstrings (both triple-double and triple-single quotes)
/"""/ || $0 ~ "\047\047\047" {
    if (!in_docstring && !in_docstring_single) {
        if ($0 ~ /"""/) {
            in_docstring = 1
            tmp = $0; n = gsub(/"""/, "\"\"\"", tmp)
            if (n >= 2) in_docstring = 0
        }
        if ($0 ~ "\047\047\047") {
            in_docstring_single = 1
            tmp = $0; n = gsub(/\047\047\047/, "\047\047\047", tmp)
            if (n >= 2) in_docstring_single = 0
        }
    } else if (in_docstring && $0 ~ /"""/) {
        in_docstring = 0
    } else if (in_docstring_single && $0 ~ "\047\047\047") {
        in_docstring_single = 0
    }
    next
}
in_docstring { next }
in_docstring_single { next }

# Skip comments
/^[[:space:]]*#/ { next }

# Detect function definition (for context)
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    next
}

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

# Helper: strip string literals and comments from a line for eval/exec checks
function strip_strings_and_comments(s,    _s, _in_str, _quote, i, c, next1, next2) {
    _s = ""
    _in_str = 0
    _quote = ""
    gsub(/#.*/, "", s)
    for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (_in_str) {
            if (c == _quote) {
                if (i + 2 <= length(s)) {
                    next1 = substr(s, i + 1, 1)
                    next2 = substr(s, i + 2, 1)
                    if (next1 == _quote && next2 == _quote) {
                        _s = _s "   "
                        i += 2
                        _in_str = 0
                        continue
                    }
                }
                _in_str = 0
                _s = _s " "
            } else {
                _s = _s " "
            }
        } else if (c == "\"" || c == "\047") {
            _in_str = 1
            _quote = c
            _s = _s " "
        } else {
            _s = _s c
        }
    }
    return _s
}

# SC-104: Detect eval() and exec()
/[^a-zA-Z_]eval[[:space:]]*\(/ || /[^a-zA-Z_]exec[[:space:]]*\(/ {
    check_line = strip_strings_and_comments($0)
    if (check_line ~ /eval[[:space:]]*\(/) {
        printf "%d:0: error: eval() is forbidden — use ast.literal_eval() or safe alternatives (no-eval)\n", NR
        violations++
    }
    if (check_line ~ /exec[[:space:]]*\(/) {
        printf "%d:0: error: exec() is forbidden — dynamic code execution prohibited (no-exec)\n", NR
        violations++
    }
}

# SC-101: Detect SQL in f-strings — only in .execute() or query-named variables
/\.execute\(.*f["\047]/ || /^[[:space:]]*(query|sql|stmt|sql_query|sql_stmt|sql_statement)[[:space:]]*=.*f["\047]/ {
    check_line = $0
    gsub(/#.*/, "", check_line)
    if (check_line ~ /(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|FROM|WHERE|JOIN|INTO|VALUES)/) {
        printf "%d:0: error: SQL query in f-string — use parameterized queries (no-sql-fstring)\n", NR
        violations++
    }
}

# SC-101: Detect execute() with format
/\.execute\(.*\.format\(/ {
    printf "%d:0: error: SQL in execute(format(...)) — use parameterized queries (no-sql-execute-format)\n", NR
    violations++
}

# SC-101: Detect execute() with % formatting
/\.execute\(.*%/ {
    printf "%d:0: warning: SQL in execute(%% formatting) — verify parameterized queries used (no-sql-execute-percent)\n", NR
}

# SC-100: Detect hardcoded secret patterns — module-level only (no leading whitespace)
/^[a-zA-Z_]*[Ss]ecret[[:space:]]*=[[:space:]]*["\047][^"\047]{8,}/ {
    printf "%d:0: error: hardcoded secret — use environment variables (hardcoded-secret)\n", NR
    violations++
}

/^[a-zA-Z_]*[Aa]pi_?[Kk]ey[[:space:]]*=[[:space:]]*["\047][^"\047]{8,}/ {
    printf "%d:0: error: hardcoded API key — use environment variables (hardcoded-api-key)\n", NR
    violations++
}

/^[a-zA-Z_]*[Pp]assword[[:space:]]*=[[:space:]]*["\047][^"\047]{4,}/ {
    printf "%d:0: error: hardcoded password — use environment variables (hardcoded-password)\n", NR
    violations++
}

END { exit (violations > 0) ? 1 : 0 }
'

security_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "security-check: no directories provided, skipping"
    return 0
  fi

  lint_step "security check (SC-100/101/104) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "security-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_SECURITY_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "security-check: security violations found"
    return 1
  fi

  lint_ok "security-check"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  security_check_run "$@"
fi
