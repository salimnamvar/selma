#!/usr/bin/env bash
# exit_door_check.sh — SC-001/SC-002/SC-006: Function Exit Door Audit.
#
# Comprehensive check: detects ALL function exit mechanisms.
# Under the Safe Coding Doctrine, every function SHALL have exactly ONE
# exit door (the single return at the end). All exceptions SHALL be
# caught locally and converted to Result.failure().
#
# Detects:
#   1. return — normal function completion
#   2. raise — exception-based exit (SC-002 zero-raise)
#   3. sys.exit() — raises SystemExit
#   4. os._exit() — immediate process termination
#   5. raise StopIteration — iterator completion signal
#   6. raise SystemExit — same as sys.exit()
#   7. raise StopAsyncIteration — async iterator completion
#   8. yield / yield from — generator suspension (exempt per SC-001)
#
# Exemptions (per SC-001/SC-002):
#   - Python dunder methods (__init__, __enter__, __exit__, etc.)
#   - Framework Boundary Adapters (translate Result[T] → HTTPException)
#   - Generator functions (yield is a suspension, not an exit)
#
# Scope handling:
#   - Nested functions: pushed onto a state stack; outer function
#     analysis resumes after the inner function ends.
#   - Multi-line signatures: tracked via paren_depth.
#   - Multi-line constructs in body (dicts, tuples, calls): @decorator
#     lines and blank/comment lines are skipped before the indent check,
#     preventing false function-end signals on `}` brackets.
#
# Limitations: AWK cannot fully parse Python AST. Edge cases like
# match/case, walrus (:=), or pathological single-line defs may slip
# through. For full enforcement, consider a Ruff plugin.

if [[ -n "${SETUP_LINT_EXIT_DOOR_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_EXIT_DOOR_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_EXIT_DOOR_AWK=$(cat << 'AWK_PROGRAM'
BEGIN {
    violations = 0
    in_docstring = 0
    docstring_char = ""
    in_func = 0
    func_line = 0
    func_name = ""
    func_indent = -1
    paren_depth = 0
    stack_top = 0

    # Counters
    return_count = 0
    raise_count = 0
    sys_exit_count = 0
    os_exit_count = 0
    stop_iter_count = 0
    sys_exit_raise_count = 0
    stop_async_count = 0
    has_yield = 0
    is_dunder = 0
    is_generator = 0
    has_noqa = 0
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
    st_func_line[stack_top] = func_line
    st_func_name[stack_top] = func_name
    st_func_indent[stack_top] = func_indent
    st_return_count[stack_top] = return_count
    st_raise_count[stack_top] = raise_count
    st_sys_exit_count[stack_top] = sys_exit_count
    st_os_exit_count[stack_top] = os_exit_count
    st_stop_iter_count[stack_top] = stop_iter_count
    st_sys_exit_raise_count[stack_top] = sys_exit_raise_count
    st_stop_async_count[stack_top] = stop_async_count
    st_has_yield[stack_top] = has_yield
    st_is_dunder[stack_top] = is_dunder
    st_is_generator[stack_top] = is_generator
    st_has_noqa[stack_top] = has_noqa
}

function pop_state() {
    if (stack_top <= 0) { in_func = 0; return }
    func_line = st_func_line[stack_top]
    func_name = st_func_name[stack_top]
    func_indent = st_func_indent[stack_top]
    return_count = st_return_count[stack_top]
    raise_count = st_raise_count[stack_top]
    sys_exit_count = st_sys_exit_count[stack_top]
    os_exit_count = st_os_exit_count[stack_top]
    stop_iter_count = st_stop_iter_count[stack_top]
    sys_exit_raise_count = st_sys_exit_raise_count[stack_top]
    stop_async_count = st_stop_async_count[stack_top]
    has_yield = st_has_yield[stack_top]
    is_dunder = st_is_dunder[stack_top]
    is_generator = st_is_generator[stack_top]
    has_noqa = st_has_noqa[stack_top]
    stack_top--
    in_func = 1; paren_depth = 0
}

function count_str(line, target,    n, tmp) {
    n = 0; tmp = line
    while (sub(target, "", tmp)) n++
    return n
}

function strip_code(line) {
    gsub(/[fFrRuUbB]{0,2}"([^"\\]|\\.)*"/, " ", line)
    gsub(/[fFrRuUbB]{0,2}\047([^\047\\]|\\.)*\047/, " ", line)
    gsub(/#.*/, "", line)
    return line
}

function report_violations() {
    if (!in_func) return
    if (is_dunder || is_generator || has_yield || has_noqa) return

    total_exits = return_count + raise_count + sys_exit_count + os_exit_count + \
                  stop_iter_count + sys_exit_raise_count + stop_async_count

    if (total_exits > 1) {
        msg = sprintf("function \"%s\" has %d exit doors", func_name, total_exits)
        if (return_count > 0) msg = msg sprintf(" (return=%d", return_count)
        if (raise_count > 0) msg = msg sprintf(" raise=%d", raise_count)
        if (sys_exit_count > 0) msg = msg sprintf(" sys.exit=%d", sys_exit_count)
        if (os_exit_count > 0) msg = msg sprintf(" os._exit=%d", os_exit_count)
        if (stop_iter_count > 0) msg = msg sprintf(" StopIteration=%d", stop_iter_count)
        if (sys_exit_raise_count > 0) msg = msg sprintf(" SystemExit=%d", sys_exit_raise_count)
        if (stop_async_count > 0) msg = msg sprintf(" StopAsyncIteration=%d", stop_async_count)
        msg = msg ")"
        printf "%d:0: error: %s — use b_continue pattern for single exit (exit-door)\n", func_line, msg
        violations++
    } else if (raise_count > 0) {
        printf "%d:0: error: function \"%s\" has %d raise statement(s) — handle locally with Result.failure() (exit-door-raise)\n", func_line, func_name, raise_count
        violations++
    } else if (sys_exit_count > 0) {
        printf "%d:0: error: function \"%s\" has sys.exit() — convert to Result.failure() (exit-door-sys-exit)\n", func_line, func_name
        violations++
    } else if (os_exit_count > 0) {
        printf "%d:0: error: function \"%s\" has os._exit() — convert to Result.failure() (exit-door-os-exit)\n", func_line, func_name
        violations++
    }
    
    in_func = 0
}

# --- Function definition detection (Rule priority: def > docstring) ---
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    _indent = calc_indent($0)
    
    if (in_func) {
        if (_indent > func_indent) {
            push_state()
        } else {
            report_violations()
            while (stack_top > 0) {
                pop_state()
                if (func_indent >= _indent) {
                    report_violations()
                } else {
                    break
                }
            }
        }
    }
    
    _fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", _fname)
    sub(/[[:space:]]*\(.*$/, "", _fname)
    
    in_func = 1
    func_line = NR
    func_name = _fname
    func_indent = _indent
    
    is_dunder = (_fname ~ /^__.*__$/) ? 1 : 0
    has_noqa = 0
    
    # Reset counters
    paren_depth = 0
    return_count = 0; raise_count = 0; sys_exit_count = 0; os_exit_count = 0
    stop_iter_count = 0; sys_exit_raise_count = 0; stop_async_count = 0
    has_yield = 0; is_generator = 0
    
    _check = strip_code($0)
    for (_i = 1; _i <= length(_check); _i++) {
        _c = substr(_check, _i, 1)
        if (_c == "(") paren_depth++
        if (_c == ")") paren_depth--
    }
    next
}

# --- Docstring tracking ---
{
    n_tqd = count_str($0, "\"\"\"")
    n_tqs = count_str($0, "\047\047\047")
    
    if (!in_docstring) {
        if (n_tqd % 2 != 0) { in_docstring = 1; docstring_char = "\"" }
        else if (n_tqs % 2 != 0) { in_docstring = 1; docstring_char = "\047" }
    } else {
        if (docstring_char == "\"" && n_tqd % 2 != 0) { in_docstring = 0 }
        else if (docstring_char == "\047" && n_tqs % 2 != 0) { in_docstring = 0 }
    }
    if (in_docstring) next
}

# --- Inside function body ---
in_func {
    if (paren_depth > 0) {
        _sig = strip_code($0)
        for (_i = 1; _i <= length(_sig); _i++) {
            _c = substr(_sig, _i, 1)
            if (_c == "(") paren_depth++
            if (_c == ")") paren_depth--
        }
        next
    }
    
    if ($0 !~ /^[[:space:]]*$/ && $0 !~ /^[[:space:]]*#/) {
        _cur_indent = calc_indent($0)
        if (_cur_indent != -1 && _cur_indent <= func_indent) {
            report_violations()
            while (stack_top > 0) {
                pop_state()
                if (func_indent >= _cur_indent) {
                    report_violations()
                } else {
                    break
                }
            }
            if (!in_func) next
        }
    }
    
    _cl = strip_code($0)
    if (_cl ~ /^[[:space:]]*$/) next
    
    # 1. Detect return statements (Word boundary)
    if (_cl ~ /(^|[^a-zA-Z0-9_])return([[:space:]]|$)/) return_count++
    
    # 2. Detect raise statements (Word boundary)
    if (_cl ~ /(^|[^a-zA-Z0-9_])raise([[:space:]]|$)/) {
        raise_count++
        if (_cl ~ /raise[[:space:]]+StopIteration/) stop_iter_count++
        if (_cl ~ /raise[[:space:]]+SystemExit/) sys_exit_raise_count++
        if (_cl ~ /raise[[:space:]]+StopAsyncIteration/) stop_async_count++
    }
    
    # 3. Detect sys.exit()
    if (_cl ~ /(^|[^a-zA-Z0-9_])sys\.exit[[:space:]]*\(/) sys_exit_count++
    
    # 4. Detect os._exit()
    if (_cl ~ /(^|[^a-zA-Z0-9_])os\._exit[[:space:]]*\(/) os_exit_count++
    
    # 8. Detect yield / yield from
    if (_cl ~ /(^|[^a-zA-Z0-9_])yield([^a-zA-Z0-9_]|$)/) {
        has_yield = 1
        is_generator = 1
    }
}

END {
    while (in_func) {
        report_violations()
        if (stack_top > 0) pop_state()
        else in_func = 0
    }
    exit (violations > 0) ? 1 : 0
}
AWK_PROGRAM
)

exit_door_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "exit-door-check: no directories provided, skipping"
    return 0
  fi

  lint_step "exit door audit (SC-001/002/006) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "exit-door-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_EXIT_DOOR_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "exit-door-check: exit door violations found"
    return 1
  fi

  lint_ok "exit-door-check (SC-001/002/006)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  exit_door_check_run "$@"
fi
