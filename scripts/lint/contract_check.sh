#!/usr/bin/env bash
# contract_check.sh — Function Contracts (SC-013).
#
# Rule: Every function SHALL have a docstring documenting:
#   1. Preconditions
#   2. Postconditions
#   3. Side effects
#   4. Resource ownership
#   5. Failure modes
#
# Enforcement: Functions in src/ must have docstrings. Functions with
# parameters must have docstrings. Dunder methods are exempt.

if [[ -n "${SETUP_LINT_CONTRACT_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_CONTRACT_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_CONTRACT_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = 0
    has_docstring = 0
    paren_depth = 0
    violations = 0
    in_docstring = 0
    in_docstring_single = 0
    line_after_def = 0
    sig_complete = 0
    docstring_text = ""
}

# Track docstrings (both triple-double and triple-single quotes)
/"""/ || $0 ~ "\047\047\047" {
    if (!in_docstring && !in_docstring_single) {
        if ($0 ~ /"""/) {
            in_docstring = 1
            if (in_func && sig_complete && line_after_def) {
                has_docstring = 1
                docstring_text = $0
            }
            tmp = $0; n = gsub(/"""/, "\"\"\"", tmp)
            if (n >= 2) {
                in_docstring = 0
                line_after_def = 0
            }
        }
        if ($0 ~ "\047\047\047") {
            in_docstring_single = 1
            if (in_func && sig_complete && line_after_def) {
                has_docstring = 1
                docstring_text = $0
            }
            tmp = $0; n = gsub(/\047\047\047/, "\047\047\047", tmp)
            if (n >= 2) {
                in_docstring_single = 0
                line_after_def = 0
            }
        }
    } else if (in_docstring && $0 ~ /"""/) {
        in_docstring = 0
        line_after_def = 0
    } else if (in_docstring_single && $0 ~ "\047\047\047") {
        in_docstring_single = 0
        line_after_def = 0
    }
    next
}
in_docstring {
    if (in_func) docstring_text = docstring_text " " $0
    next
}
in_docstring_single {
    if (in_func) docstring_text = docstring_text " " $0
    next
}

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # Check previous function
    if (in_func && !has_docstring && func_name !~ /^__.*__$/) {
        printf "%d:0: warning: function \"%s\" missing docstring — add contract per SC-013 (function-contract)\n", func_line, func_name
    }
    if (in_func && has_docstring && func_name !~ /^__.*__$/) {
        if (docstring_text !~ /[Pp]reconditions?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Preconditions section (sc-013-missing-preconditions)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Pp]ostconditions?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Postconditions section (sc-013-missing-postconditions)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Ss]ide[[:space:]]*[Ee]ffects?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Side Effects section (sc-013-missing-side-effects)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Rr]esource[[:space:]]*[Oo]wnership/) {
            printf "%d:0: warning: function \"%s\" docstring missing Resource Ownership section (sc-013-missing-resource-ownership)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Ff]ailure[[:space:]]*[Mm]odes?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Failure Modes section (sc-013-missing-failure-modes)\n", func_line, func_name
            violations++
        }
    }

    in_func = 1
    line = $0
    gsub(/[^[:space:]].*$/, "", line)
    func_indent = length(line)
    func_line = NR
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    has_docstring = 0
    line_after_def = 1
    paren_depth = 0
    sig_complete = 0
    docstring_text = ""

    # Count parens on the def line (use tmp to avoid destroying $0)
    tmp = $0
    n = gsub(/\(/, "(", tmp)
    paren_depth += n
    n = gsub(/\)/, ")", tmp)
    paren_depth -= n
    if (paren_depth <= 0) {
        sig_complete = 1
    }
    next
}

# While signature is not yet complete, track paren depth on continuation lines
in_func && !sig_complete && line_after_def {
    tmp = $0
    n = gsub(/\(/, "(", tmp)
    paren_depth += n
    n = gsub(/\)/, ")", tmp)
    paren_depth -= n
    if (paren_depth <= 0) {
        sig_complete = 1
    }
    next
}

# Track blank lines between def and docstring
in_func && line_after_def && /^[[:space:]]*$/ {
    next
}

# Non-blank, non-docstring line after def = no docstring
in_func && line_after_def && sig_complete && !/^[[:space:]]*$/ {
    line_after_def = 0
}

# Detect function end
in_func && sig_complete {
    if ($0 ~ /^[[:space:]]*$/ || $0 ~ /^[^[:space:]]/) {
        line = $0
        gsub(/[^[:space:]].*$/, "", line)
        current_indent = length(line)
        if (current_indent == 0 && $0 !~ /^[[:space:]]*$/) {
            in_func = 0
            # Check required sections in docstring before leaving function
            if (has_docstring && func_name !~ /^__.*__$/) {
                if (docstring_text !~ /[Pp]reconditions?/) {
                    printf "%d:0: warning: function \"%s\" docstring missing Preconditions section (sc-013-missing-preconditions)\n", func_line, func_name
                    violations++
                }
                if (docstring_text !~ /[Pp]ostconditions?/) {
                    printf "%d:0: warning: function \"%s\" docstring missing Postconditions section (sc-013-missing-postconditions)\n", func_line, func_name
                    violations++
                }
                if (docstring_text !~ /[Ss]ide[[:space:]]*[Ee]ffects?/) {
                    printf "%d:0: warning: function \"%s\" docstring missing Side Effects section (sc-013-missing-side-effects)\n", func_line, func_name
                    violations++
                }
                if (docstring_text !~ /[Rr]esource[[:space:]]*[Oo]wnership/) {
                    printf "%d:0: warning: function \"%s\" docstring missing Resource Ownership section (sc-013-missing-resource-ownership)\n", func_line, func_name
                    violations++
                }
                if (docstring_text !~ /[Ff]ailure[[:space:]]*[Mm]odes?/) {
                    printf "%d:0: warning: function \"%s\" docstring missing Failure Modes section (sc-013-missing-failure-modes)\n", func_line, func_name
                    violations++
                }
            }
        }
    }
}

END {
    if (in_func && !has_docstring && func_name !~ /^__.*__$/) {
        printf "%d:0: warning: function \"%s\" missing docstring — add contract per SC-013 (function-contract)\n", func_line, func_name
    }
    if (in_func && has_docstring && func_name !~ /^__.*__$/) {
        if (docstring_text !~ /[Pp]reconditions?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Preconditions section (sc-013-missing-preconditions)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Pp]ostconditions?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Postconditions section (sc-013-missing-postconditions)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Ss]ide[[:space:]]*[Ee]ffects?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Side Effects section (sc-013-missing-side-effects)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Rr]esource[[:space:]]*[Oo]wnership/) {
            printf "%d:0: warning: function \"%s\" docstring missing Resource Ownership section (sc-013-missing-resource-ownership)\n", func_line, func_name
            violations++
        }
        if (docstring_text !~ /[Ff]ailure[[:space:]]*[Mm]odes?/) {
            printf "%d:0: warning: function \"%s\" docstring missing Failure Modes section (sc-013-missing-failure-modes)\n", func_line, func_name
            violations++
        }
    }
    exit (violations > 0) ? 1 : 0
}
'

contract_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "contract-check: no directories provided, skipping"
    return 0
  fi

  lint_step "function contract check (SC-013) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -not -name "__init__.py" -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "contract-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_CONTRACT_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "contract-check: missing function contracts"
    return 1
  fi

  lint_ok "contract-check (SC-013)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  contract_check_run "$@"
fi
