#!/usr/bin/env bash
# a_ prefix argument checker — enforce a_ prefix on all function/method arguments.
#
# Exemptions: self, cls, *args, **kwargs, dunder methods, / (positional-only),
# and anything already starting with a_ or _a_.
#
# Uses awk for reliable multiline function signature parsing.
# All strings are stripped before paren counting and docstring detection
# to prevent false matches from parentheses or triple quotes inside literals.

if [[ -n "${SETUP_LINT_A_PREFIX_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_A_PREFIX_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_A_PREFIX_AWK='
BEGIN {
    in_func = 0
    paren_depth = 0
    buf = ""
    raw_buf = ""
    decorator_buf = ""
    func_line = 0
    func_name = ""
    has_decorator = 0
    violations = 0
    in_tq_dq = 0
    in_tq_sq = 0
    sq = sprintf("%c", 39)
    dq = sprintf("%c", 34)
    tqs = sq sq sq
    tqd = dq dq dq
}

# ---------------------------------------------------------------------------
# Helper: replace string/bytes literals with spaces so parens and triple-quotes
# inside literals are invisible to the rest of the parser.
# ---------------------------------------------------------------------------
function skip_strings(s,    out, i, len, c, esc) {
    out = ""
    len = length(s)
    i = 1
    while (i <= len) {
        c = substr(s, i, 1)
        if (c == "\\") {
            esc = (i < len) ? substr(s, i + 1, 1) : ""
            if (esc == sq || esc == dq) {
                out = out "  "
                i += 2
                continue
            }
            out = out c
            i++
            continue
        }
        if (c == sq) {
            if (i + 2 <= len && substr(s, i, 3) == tqs) {
                out = out "   "
                i += 3
                while (i <= len) {
                    if (substr(s, i, 3) == tqs) {
                        out = out "   "
                        i += 3
                        break
                    }
                    out = out " "
                    i++
                }
                continue
            }
            out = out " "
            i++
            while (i <= len) {
                c = substr(s, i, 1)
                if (c == "\\") { out = out "  "; i += 2; continue }
                if (c == sq) { out = out " "; i++; break }
                out = out " "
                i++
            }
            continue
        }
        if (c == dq) {
            if (i + 2 <= len && substr(s, i, 3) == tqd) {
                out = out "   "
                i += 3
                while (i <= len) {
                    if (substr(s, i, 3) == tqd) {
                        out = out "   "
                        i += 3
                        break
                    }
                    out = out " "
                    i++
                }
                continue
            }
            out = out " "
            i++
            while (i <= len) {
                c = substr(s, i, 1)
                if (c == "\\") { out = out "  "; i += 2; continue }
                if (c == dq) { out = out " "; i++; break }
                out = out " "
                i++
            }
            continue
        }
        out = out c
        i++
    }
    return out
}

# ---------------------------------------------------------------------------
# Helper: strip inline comments that are NOT inside string literals.
# ---------------------------------------------------------------------------
function strip_comments(s,    out, i, len, c, in_sq, in_dq) {
    out = ""
    len = length(s)
    in_sq = 0
    in_dq = 0
    for (i = 1; i <= len; i++) {
        c = substr(s, i, 1)
        if (in_sq) {
            if (c == "\\") { out = out "  "; i++; continue }
            if (c == sq) { out = out " "; in_sq = 0; continue }
            out = out " "
            continue
        }
        if (in_dq) {
            if (c == "\\") { out = out "  "; i++; continue }
            if (c == dq) { out = out " "; in_dq = 0; continue }
            out = out " "
            continue
        }
        if (c == sq) { in_sq = 1; out = out " "; continue }
        if (c == dq) { in_dq = 1; out = out " "; continue }
        if (c == "#") break
        out = out c
    }
    return out
}

# ---------------------------------------------------------------------------
# Helper: update triple-quote docstring state on a string-stripped line.
# ---------------------------------------------------------------------------
function update_docstring_state(line,    i, len, c3) {
    len = length(line)
    for (i = 1; i <= len - 2; i++) {
        c3 = substr(line, i, 3)
        if (!in_tq_dq && !in_tq_sq && c3 == tqd) { in_tq_dq = 1 }
        else if (in_tq_dq && c3 == tqd) { in_tq_dq = 0 }
        else if (!in_tq_dq && !in_tq_sq && c3 == tqs) { in_tq_sq = 1 }
        else if (in_tq_sq && c3 == tqs) { in_tq_sq = 0 }
    }
}

# ---------------------------------------------------------------------------
# split_args: split on commas respecting nested parens/brackets/braces
# and quoted strings (with backslash-escape handling).
# ---------------------------------------------------------------------------
function split_args(str,    out, n, depth, i, c, current, in_sq, in_dq) {
    n = 0
    depth = 0
    in_sq = 0
    in_dq = 0
    current = ""
    for (i = 1; i <= length(str); i++) {
        c = substr(str, i, 1)
        if (in_sq) {
            if (c == "\\") {
                current = current c
                if (i < length(str)) { i++; current = current substr(str, i, 1) }
                continue
            }
            if (c == sq) { in_sq = 0; current = current c; continue }
            current = current c
            continue
        }
        if (in_dq) {
            if (c == "\\") {
                current = current c
                if (i < length(str)) { i++; current = current substr(str, i, 1) }
                continue
            }
            if (c == dq) { in_dq = 0; current = current c; continue }
            current = current c
            continue
        }
        if (c == sq) { in_sq = 1; current = current c; continue }
        if (c == dq) { in_dq = 1; current = current c; continue }
        if (c == "(" || c == "[" || c == "{") depth++
        if (c == ")" || c == "]" || c == "}") depth--
        if (c == "," && depth == 0) {
            n++
            out[n] = current
            current = ""
        } else {
            current = current c
        }
    }
    n++
    out[n] = current
    return n
}

# ===========================================================================
# Rule 1: Accumulate @decorator lines (only when not in a docstring).
# ===========================================================================
/^[[:space:]]*@/ {
    if (in_func) {
        raw_buf = raw_buf $0 "\n"
        buf = buf $0
    } else {
        was_in_docstring = (in_tq_dq || in_tq_sq)
        stripped = skip_strings($0)
        update_docstring_state(stripped)
        if (!was_in_docstring) {
            decorator_buf = decorator_buf $0 "\n"
        }
    }
    next
}

# ===========================================================================
# Rule 2: Detect function / async function definition.
# ===========================================================================
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    paren_depth = 0
    buf = ""
    func_line = NR
    has_decorator = 0

    if (decorator_buf != "") {
        raw_buf = decorator_buf
        decorator_buf = ""
        has_decorator = 1
    }

    line = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", line)
    sub(/[[:space:]]*\(.*$/, "", line)
    func_name = line
}

# ===========================================================================
# Rule 3: Accumulate while inside a function signature.
# ===========================================================================
in_func {
    raw_buf = raw_buf $0 "\n"

    stripped_for_count = skip_strings($0)
    n = gsub(/\(/, "(", stripped_for_count)
    m = gsub(/\)/, ")", stripped_for_count)
    paren_depth += n - m

    buf = buf strip_comments($0)

    if (paren_depth <= 0 && buf != "") {
        if (func_name ~ /^__.*__$/) {
            in_func = 0; buf = ""; raw_buf = ""
            next
        }
        # Skip functions preceded by @decorator — framework convention
        if (has_decorator) {
            in_func = 0; buf = ""; raw_buf = ""
            next
        }
        # Skip well-known inherited method names (logging, ABC, IO, etc.)
        if (func_name == "filter" || func_name == "emit" || func_name == "format" || func_name == "formatTime" || func_name == "formatException" || func_name == "write" || func_name == "read" || func_name == "close" || func_name == "flush" || func_name == "seek" || func_name == "tell" || func_name == "readline" || func_name == "readlines" || func_name == "writelines") {
            in_func = 0; buf = ""; raw_buf = ""
            next
        }
        idx = index(buf, "(")
        if (idx > 0) {
            rest = substr(buf, idx + 1)
            depth = 1
            end = 0
            for (i = 1; i <= length(rest); i++) {
                c = substr(rest, i, 1)
                if (c == "(") depth++
                if (c == ")") { depth--; if (depth == 0) { end = i; break } }
            }
            if (end > 0) {
                argstr = substr(rest, 1, end - 1)
                n_args = split_args(argstr, args)
                for (a = 1; a <= n_args; a++) {
                    arg = args[a]
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", arg)
                    if (arg == "") continue
                    if (arg == "*" || arg == "**") continue
                    if (arg == "/") continue
                    name = arg
                    gsub(/^\*+/, "", name)
                    gsub(/:.*/, "", name)
                    gsub(/=.*/, "", name)
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
                    if (name == "self" || name == "cls" || name == "args" || name == "kwargs") continue
                    if (name ~ /^a_/ || name ~ /^_a_/) continue
                    if (name == "") continue
                    printf "%d:0: error: argument %c%s%c must start with %ca_%c (a-prefix-arg)\n", func_line, 39, name, 39, 39, 39
                    violations++
                }
            }
        }
        in_func = 0
        buf = ""
        raw_buf = ""
    }
}

# ===========================================================================
# Rule 4: Docstring tracking — skip lines inside triple-quoted docstrings
# (after stripping strings so literal triple-quotes are ignored).
# ===========================================================================
{
    if (!in_func) {
        was_in_docstring = (in_tq_dq || in_tq_sq)
        stripped = skip_strings($0)
        update_docstring_state(stripped)
        if (was_in_docstring) next
    }
}

END { exit (violations > 0) ? 1 : 0 }
'

a_prefix_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "a-prefix-check: no directories provided, skipping"
    return 0
  fi

  lint_step "a_ prefix argument check ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "a-prefix-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local awk_stdout awk_stderr
    awk_stdout=$(awk "${_A_PREFIX_AWK}" "${f}" 2>/tmp/ap_awk_err.$$) || true
    awk_stderr=$(cat /tmp/ap_awk_err.$$ 2>/dev/null)
    rm -f /tmp/ap_awk_err.$$
    if [[ -n "${awk_stderr}" ]]; then
      lint_warn "a-prefix-check: AWK error on ${f}: ${awk_stderr}"
    fi
    if [[ -n "${awk_stdout}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${awk_stdout}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "a-prefix-arg: violations found"
    return 1
  fi

  lint_ok "a-prefix-arg"
}

# When executed directly (not sourced), run with provided arguments.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  a_prefix_check_run "$@"
fi
