#!/usr/bin/env bash
# resource_check.sh — P6: Resource Ownership Is Explicit (SC-080, SC-082).
#
# Rule: All resources (file handles, connections, subprocess handles, locks,
#       temporary files) SHALL be managed via context managers (with) or
#       try/finally blocks. Resources SHALL NOT be left for garbage collection.
#
# Checks:
#   - open() without `with` context manager.
#   - socket/connection creation without context manager.
#   - subprocess.Popen without context manager.
#   - threading.Lock/RLock without context manager.

if [[ -n "${SETUP_LINT_RESOURCE_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_RESOURCE_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_RESOURCE_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    violations = 0
    in_docstring = 0
    docstring_char = ""
    dq = sprintf("%c%c%c", 34, 34, 34)
    sq = sprintf("%c%c%c", 39, 39, 39)
}

# Track docstrings (triple double or single quotes)
{
    has_dq = (index($0, dq) > 0)
    has_sq = (index($0, sq) > 0)
    if (has_dq || has_sq) {
        if (!in_docstring) {
            in_docstring = 1
            if (has_dq) docstring_char = dq
            else docstring_char = sq
            if (index($0, docstring_char) > 0) {
                n = gsub(docstring_char, docstring_char, $0)
                if (n % 2 == 0) in_docstring = 0
            }
        } else {
            if (index($0, docstring_char) > 0) in_docstring = 0
        }
        next
    }
}
in_docstring { next }

# Skip comments
/^[[:space:]]*#/ { next }

# Strip inline comments and string literals to avoid false positives
{
    check_line = $0
    # Remove inline comments
    gsub(/#.*/, "", check_line)
    # Remove double-quoted strings
    while (match(check_line, /"[^"]*"/)) {
        check_line = substr(check_line, 1, RSTART - 1) substr(check_line, RSTART + RLENGTH)
    }
    # Remove single-quoted strings
    while (match(check_line, /\x27[^\x27]*\x27/)) {
        check_line = substr(check_line, 1, RSTART - 1) substr(check_line, RSTART + RLENGTH)
    }
    # Remove f-strings and similar prefixed strings
    while (match(check_line, /[fFrRuUbB]?"[^"]*"/)) {
        check_line = substr(check_line, 1, RSTART - 1) substr(check_line, RSTART + RLENGTH)
    }
    while (match(check_line, /[fFrRuUbB]?\x27[^\x27]*\x27/)) {
        check_line = substr(check_line, 1, RSTART - 1) substr(check_line, RSTART + RLENGTH)
    }
}

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
    fname = $0
    sub(/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/, "", fname)
    sub(/[[:space:]]*\(.*$/, "", fname)
    func_name = fname
    next
}

# Detect function end
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

# Check: open() without context manager (not Popen)
in_func && check_line ~ /(^|[^a-zA-Z_.])open\(/ {
    if (check_line ~ /with[[:space:]]+/) next
    printf "%d:0: error: open() without context manager in \"%s\" — use with-statement (resource-open)\n", NR, func_name
    violations++
}

# Check: subprocess.Popen without context manager
in_func && check_line ~ /subprocess\.Popen\(/ {
    if (check_line !~ /with[[:space:]]+/) {
        printf "%d:0: error: subprocess.Popen without context manager in \"%s\" — use with-statement (resource-popen)\n", NR, func_name
        violations++
    }
}

# Check: threading.Lock() or RLock() without context manager
in_func && check_line ~ /threading\.(R?Lock)\(\)/ {
    if (check_line !~ /with[[:space:]]+/) {
        printf "%d:0: error: %s without context manager in \"%s\" — use with-statement (resource-lock)\n", NR, (check_line ~ /RLock/ ? "RLock" : "Lock"), func_name
        violations++
    }
}

# Check: socket.socket() without context manager
in_func && check_line ~ /socket\.socket\(\)/ {
    if (check_line !~ /with[[:space:]]+/) {
        printf "%d:0: error: socket.socket() without context manager in \"%s\" — use with-statement (resource-socket)\n", NR, func_name
        violations++
    }
}

# Check: sqlite3.connect() without context manager
in_func && check_line ~ /sqlite3\.connect\(/ {
    if (check_line !~ /with[[:space:]]+/) {
        printf "%d:0: error: sqlite3.connect() without context manager in \"%s\" — use with-statement (resource-sqlite3)\n", NR, func_name
        violations++
    }
}

# Check: tempfile.NamedTemporaryFile() without context manager
in_func && check_line ~ /tempfile\.NamedTemporaryFile\(\)/ {
    if (check_line !~ /with[[:space:]]+/) {
        printf "%d:0: error: tempfile.NamedTemporaryFile() without context manager in \"%s\" — use with-statement (resource-tempfile)\n", NR, func_name
        violations++
    }
}

END { exit (violations > 0) ? 1 : 0 }
'

resource_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "resource-check: no directories provided, skipping"
    return 0
  fi

  lint_step "resource ownership check (P6: SC-080/082) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "resource-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_RESOURCE_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "resource-check: resource management violations found"
    return 1
  fi

  lint_ok "resource-check (P6)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  resource_check_run "$@"
fi
