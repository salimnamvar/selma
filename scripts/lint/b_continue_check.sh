#!/usr/bin/env bash
# b_continue_check.sh — SC-011 b_continue Rules Linter (Enhanced v2)
#
# Enforces the following rules for b_continue error-gating variables:
#   1. b_continue SHALL be function-local only (no parameters, global, nonlocal).
#   2. Initialized to True at function start (first executable statement).
#   3. Transitions only True -> False (never False -> True).
#   4. b_continue = False appears at most once per error condition (approximate).
#   5. After initialization, b_continue = True SHALL NOT appear again.
#   6. Workflow functions MAY use b_continue for error gating (not tied to Result[T]).
#   7. b_continue SHALL NOT be deleted (del b_continue forbidden).
#   8. After init, b_continue SHALL only be assigned True or False (no aliases).
#   9. External mutation forbidden: no self.x.b_continue, no getattr(x, "b_continue").
#  10. b_continue SHALL NOT appear in global/nonlocal statements.
#
# Violation codes:
#   b_continue-scope        -- b_continue is not function-local (Rules 1,9,10)
#   b_continue-param        -- b_continue is a function parameter (Rule 1)
#   b_continue-init         -- first assignment is not True (Rule 2)
#   b_continue-transition   -- False -> True transition detected (Rule 3)
#   b_continue-reset        -- b_continue re-initialized to True (Rule 5)
#   b_continue-missing      -- Result[T] function lacks b_continue (Rule 6, info)
#   b_continue-unused       -- b_continue initialized but never used (Rule 6, info)
#   b_continue-multi-false  -- multiple b_continue = False (Rule 4, warning)
#   b_continue-alias        -- assigned to non-bool value (Rule 8)
#   b_continue-delete       -- del b_continue (Rule 7)
#
# Scope: Workflow/orchestration functions only. Dunder methods excluded.
# Support: # noqa: sc-011 on def line exempts the function.
#
# Limitations: AWK cannot fully parse Python AST. This catches common patterns.
#   Edge cases like walrus operators, match/case, or complex multiline
#   expressions may slip through. For full enforcement, consider a Ruff plugin.

if [[ -n "${SETUP_LINT_B_CONTINUE_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_B_CONTINUE_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

# AWK program stored via heredoc for readability (no \047 escaping needed).
_B_CONTINUE_AWK=$(cat << 'AWK_PROGRAM'
    BEGIN {
        violations = 0
        in_docstring = 0
        in_func = 0
        in_sig = 0
        is_dunder = 0
        is_noqa = 0
        func_line = 0
        func_name = ""
        func_indent = -1
        paren_depth = 0
        func_sig = ""
        func_sig_raw = ""
        b_state = 0
        false_count = 0
        has_result_return = 0
        has_guard_use = 0
        stack_top = 0
    }

# --- Helpers ---

function calc_indent(line,    _t) {
    if (line ~ /^[[:space:]]*$/) return -1
    _t = line
    gsub(/[^[:space:]].*$/, "", _t)
    return length(_t)
}

function push_state() {
    stack_top++
    st_func_line[stack_top]         = func_line
    st_func_name[stack_top]         = func_name
    st_func_indent[stack_top]       = func_indent
    st_b_state[stack_top]           = b_state
    st_false_count[stack_top]       = false_count
    st_has_result_return[stack_top] = has_result_return
    st_has_guard_use[stack_top]     = has_guard_use
    st_is_dunder[stack_top]         = is_dunder
    st_is_noqa[stack_top]           = is_noqa
}

function pop_state() {
    if (stack_top <= 0) { in_func = 0; return }
    func_line         = st_func_line[stack_top]
    func_name         = st_func_name[stack_top]
    func_indent       = st_func_indent[stack_top]
    b_state           = st_b_state[stack_top]
    false_count       = st_false_count[stack_top]
    has_result_return = st_has_result_return[stack_top]
    has_guard_use     = st_has_guard_use[stack_top]
    is_dunder         = st_is_dunder[stack_top]
    is_noqa           = st_is_noqa[stack_top]
    stack_top--
    in_func = 1; in_sig = 0; paren_depth = 0
    func_sig = ""; func_sig_raw = ""
}

# Strip strings BEFORE comments (# inside string literal must not truncate line).
function strip_code(line) {
    gsub(/"[^"\\]*(\\.[^"\\]*)*"/, " ", line)
    gsub(/\047([^\047\\]|\\.)*\047/, " ", line)
    gsub(/#.*/, "", line)
    return line
}

# Check for Result[ in return type -- extract everything after -> to handle
# complex types like dict[str, Result[...]].
function check_result_return(sig,    _a) {
    if (sig !~ /->/) return 0
    _a = sig
    sub(/.*->/, "", _a)
    return (_a ~ /Result\[/) ? 1 : 0
}

function finalize_sig() {
    in_sig = 0
    if (!is_dunder && !is_noqa) {
        if (func_sig ~ /[(,][[:space:]]*b_continue[[:space:]]*([:=,)])/) {
            printf "%d:0: error: b_continue must be function-local, not a parameter in \"%s\" (b_continue-param)\n", func_line, func_name
            violations++
        }
        if (check_result_return(func_sig) || check_result_return(func_sig_raw)) {
            has_result_return = 1
        }
    }
    func_sig = ""; func_sig_raw = ""; paren_depth = 0
}

function report_func() {
    if (!in_func) return
    if (has_result_return && !is_dunder && !is_noqa) {
        if (b_state == 0) {
            printf "%d:0: info: function \"%s\" returns Result[T] but has no b_continue -- workflow functions may use b_continue (b_continue-missing)\n", func_line, func_name
        } else if (b_state == 1 && !has_guard_use) {
            printf "%d:0: info: function \"%s\" initializes b_continue but never uses it for error gating (b_continue-unused)\n", func_line, func_name
        }
    }
    in_func = 0; b_state = 0; false_count = 0
    has_result_return = 0; has_guard_use = 0
    is_dunder = 0; is_noqa = 0
    in_sig = 0; func_sig = ""; func_sig_raw = ""; paren_depth = 0
}

# --- Docstring tracking ---
# Single-quote handler MUST come before double-quote to avoid conflicts.
# Note: def block runs first, so def lines with inline docstrings are handled
# there. These handlers catch standalone docstring lines only.

/\047\047\047/ {
    if (!in_docstring) {
        in_docstring = 1
        if ($0 ~ /\047\047\047.*\047\047\047/) in_docstring = 0
    } else {
        if ($0 ~ /\047\047\047/) in_docstring = 0
    }
    next
}

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

# --- Function definition detection ---

/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    _indent = calc_indent($0)

    if (in_func) {
        if (_indent > func_indent) {
            push_state()
        } else {
            report_func()
            # Unwind stack to the level of this new function
            while (stack_top > 0 && st_func_indent[stack_top] >= _indent) {
                pop_state()
            }
        }
    }

    _fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", _fname)
    sub(/[[:space:]]*\(.*$/, "", _fname)

    in_func = 1
    in_sig = 0
    func_line = NR
    func_name = _fname
    func_indent = _indent
    b_state = 0
    false_count = 0
    has_result_return = 0
    has_guard_use = 0
    paren_depth = 0
    func_sig = ""
    func_sig_raw = ""
    is_dunder = (_fname ~ /^__.*__$/) ? 1 : 0
    is_noqa = 0

    # Handle inline docstring on def line (e.g. def foo(): """doc""")
    if ($0 ~ /\047\047\047/) {
        if (!in_docstring) {
            in_docstring = 1
            if ($0 ~ /\047\047\047.*\047\047\047/) in_docstring = 0
        } else {
            if ($0 ~ /\047\047\047/) in_docstring = 0
        }
    }
    if ($0 ~ /"""/) {
        if (!in_docstring) {
            in_docstring = 1
            if ($0 ~ /""".*"""/) in_docstring = 0
        } else {
            if ($0 ~ /"""/) in_docstring = 0
        }
    }

    _check = strip_code($0)
    func_sig_raw = $0
    func_sig = _check

    if (!is_dunder && !is_noqa) {
        if (_check ~ /[(,][[:space:]]*b_continue[[:space:]]*([:=,)])/) {
            printf "%d:0: error: b_continue must be function-local, not a parameter in \"%s\" (b_continue-param)\n", NR, _fname
            violations++
        }
        if (check_result_return(_check)) has_result_return = 1
    }

    for (_i = 1; _i <= length(_check); _i++) {
        _c = substr(_check, _i, 1)
        if (_c == "(") paren_depth++
        if (_c == ")") paren_depth--
    }
    if (paren_depth <= 0) in_sig = 0
    else in_sig = 1

    next
}

# --- Inside a tracked function (non-dunder, non-noqa) ---

in_func && !is_dunder && !is_noqa {

    # Still collecting multi-line signature
    if (in_sig) {
        _sig = strip_code($0)
        func_sig_raw = func_sig_raw " " $0
        func_sig = func_sig " " _sig
        for (_i = 1; _i <= length(_sig); _i++) {
            _c = substr(_sig, _i, 1)
            if (_c == "(") paren_depth++
            if (_c == ")") paren_depth--
        }
        if (_sig ~ /b_continue[[:space:]]*([:=,)])/) {
            printf "%d:0: error: b_continue must be function-local, not a parameter in \"%s\" (b_continue-param)\n", NR, func_name
            violations++
        }
        if (paren_depth <= 0) finalize_sig()
        next
    }

    # --- Indentation-based scope end ---
    if ($0 !~ /^[[:space:]]*$/ && $0 !~ /^[[:space:]]*#/) {
        _cur_indent = calc_indent($0)
        if (_cur_indent != -1 && _cur_indent <= func_indent) {
            report_func()
            if (stack_top > 0) {
                pop_state()
            }
            next
        }
    }
        next
    }
        }
    }

    # --- Rule 9: External mutation (check raw $0 BEFORE strip_code) ---
    # getattr/setattr checks must use raw $0 because strip_code removes
    # the quoted string argument, e.g. getattr(x, "b_continue") -> getattr(x, )
    if ($0 ~ /getattr[[:space:]]*\([^)]*["\047]b_continue["\047]/) {
        printf "%d:0: error: b_continue accessed via getattr in \"%s\" -- use local variable (b_continue-scope)\n", NR, func_name
        violations++
    }
    if ($0 ~ /setattr[[:space:]]*\([^)]*["\047]b_continue["\047]/) {
        printf "%d:0: error: b_continue mutated via setattr in \"%s\" -- use local variable (b_continue-scope)\n", NR, func_name
        violations++
    }

    # --- Line analysis: strip strings FIRST, then comments ---
    _cl = strip_code($0)
    if (_cl ~ /^[[:space:]]*$/) next

    # --- Rule 10: global/nonlocal b_continue ---
    if (_cl ~ /(global|nonlocal)[[:space:]]+b_continue([^a-zA-Z0-9_]|$)/) {
        printf "%d:0: error: b_continue must be function-local, not global/nonlocal in \"%s\" (b_continue-scope)\n", NR, func_name
        violations++
    }

    # --- Rule 7: del b_continue (use portable boundaries, not \b) ---
    if (_cl ~ /(^|[^a-zA-Z0-9_])del[[:space:]]+b_continue([^a-zA-Z0-9_]|$)/) {
        printf "%d:0: error: del b_continue is forbidden in \"%s\" (b_continue-delete)\n", NR, func_name
        violations++
    }

    # --- Rule 9 continued: attribute access (on stripped line) ---
    if (_cl ~ /\.[[:space:]]*b_continue[[:space:]]*=/) {
        printf "%d:0: error: b_continue must be function-local, not an attribute in \"%s\" (b_continue-scope)\n", NR, func_name
        violations++
    }

    # --- Rules 1,2,3,5,8: Assignment analysis ---
    # Consolidated block: match ANY assignment to b_continue, then check RHS.
    # Skips attribute access (self.b_continue = ...) to avoid double-reporting.
    # Uses [^=]+? (non-greedy) for type annotation to handle bool | None, etc.
    if (_cl !~ /\.[[:space:]]*b_continue[[:space:]]*=/ && \
        _cl ~ /(^|[^a-zA-Z0-9_])b_continue([[:space:]]*:[^=]+)?[[:space:]]*=[[:space:]]*/) {

        # Check for True
        if (_cl ~ /(^|[^a-zA-Z0-9_])b_continue([[:space:]]*:[^=]+)?[[:space:]]*=[[:space:]]*True([[:space:];]|$)/) {
            if (b_state == 2) {
                printf "%d:0: error: b_continue transition False->True in \"%s\" -- only True->False allowed (b_continue-transition)\n", NR, func_name
                violations++
            } else if (b_state == 1) {
                printf "%d:0: error: b_continue reset to True in \"%s\" -- may only transition True->False (b_continue-reset)\n", NR, func_name
                violations++
            } else {
                b_state = 1
            }
        }
        # Check for False
        else if (_cl ~ /(^|[^a-zA-Z0-9_])b_continue([[:space:]]*:[^=]+)?[[:space:]]*=[[:space:]]*False([[:space:];]|$)/) {
            if (b_state == 0) {
                printf "%d:0: error: first assignment to b_continue must be True in \"%s\" (b_continue-init)\n", NR, func_name
                violations++
                b_state = 2
            } else if (b_state == 1) {
                b_state = 2
            }
            # Only count valid True->False transitions
            if (b_state == 2) {
                false_count++
                if (false_count > 1) {
                    printf "%d:0: warning: multiple b_continue = False assignments (%d) in \"%s\" -- expected at most one per error condition (b_continue-multi-false)\n", NR, false_count, func_name
                }
            }
        }
        # Anything else is an alias (Rule 8)
        else {
            printf "%d:0: error: b_continue assigned to non-bool value in \"%s\" -- only True/False allowed (b_continue-alias)\n", NR, func_name
            violations++
            b_state = 2
        }
    }

    # --- Guard usage: if/elif/while/and/or/not b_continue ---
    # Word boundary after b_continue to avoid matching b_continue_ready, etc.
    # Also catches: if (b_continue), not(b_continue), ternary ... if b_continue else
    if (_cl ~ /(if|elif|while)[[:space:]]+b_continue([^a-zA-Z0-9_]|$)/ || \
        _cl ~ /(if|elif|while)[[:space:]]*\([[:space:]]*b_continue/ || \
        _cl ~ /(and|or|not)[[:space:]]+b_continue([^a-zA-Z0-9_]|$)/ || \
        _cl ~ /(and|or|not)[[:space:]]*\([[:space:]]*b_continue/ || \
        _cl ~ /b_continue[[:space:]]+else/) {
        has_guard_use = 1
    }
}

# --- Dunder/noqa functions: scope exit only (no rule checks) ---

in_func && (is_dunder || is_noqa) {
    if ($0 !~ /^[[:space:]]*$/ && $0 !~ /^[[:space:]]*#/) {
        _ci = calc_indent($0)
        if (_ci != -1 && _ci <= func_indent) {
            in_func = 0; is_dunder = 0; is_noqa = 0
            next
        }
    }
}

# --- EOF: drain stack ---

END {
    while (in_func) {
        report_func()
        if (stack_top > 0) pop_state()
        else in_func = 0
    }
    exit (violations > 0) ? 1 : 0
}
AWK_PROGRAM
)

b_continue_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "b-continue-check: no directories provided, skipping"
    return 0
  fi

  lint_step "b_continue check (SC-011) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "b-continue-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local awk_stdout awk_stderr
    awk_stdout=$(awk "${_B_CONTINUE_AWK}" "${f}" 2>/tmp/bc_awk_err.$$) || true
    awk_stderr=$(cat /tmp/bc_awk_err.$$ 2>/dev/null)
    rm -f /tmp/bc_awk_err.$$
    if [[ -n "${awk_stderr}" ]]; then
      lint_warn "b-continue-check: AWK error on ${f}: ${awk_stderr}"
    fi
    if [[ -n "${awk_stdout}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${awk_stdout}"
      if echo "${awk_stdout}" | grep -q ': error:'; then
        has_violations=1
      fi
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "b-continue-check: b_continue violations found"
    return 1
  fi

  lint_ok "b-continue-check (SC-011)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  b_continue_check_run "$@"
fi
