#!/usr/bin/env bash
# determinism_check.sh — P1: Determinism Over Cleverness (SC-071).
#
# Rule: Business logic SHALL NOT depend on datetime.now(), time.time(),
#       random.random() without fixed seed, uuid.uuid4() without
#       deterministic mode, or any other source of non-determinism.
#
# Exceptions:
#   - Cryptographic randomness (secrets module) for token/password use.
#   - Database drivers, logging frameworks, metric emitters.
#   - Functions with injected timestamp/seed parameters.

if [[ -n "${SETUP_LINT_DETERMINISM_SH:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
SETUP_LINT_DETERMINISM_SH=1

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

_DETERMINISM_AWK='
BEGIN {
    in_func = 0
    func_line = 0
    func_name = ""
    paren_depth = 0
    violations = 0
    in_docstring = 0
    in_comment = 0
    in_signature = 0
    sig_buf = ""
    has_signature_injection = 0
    docstring_quote = ""
}

# Track docstrings (skip them)
/("""|\047\047\047)/ {
    if (!in_docstring) {
        in_docstring = 1
        if ($0 ~ /"""/) docstring_quote = "\"\"\""
        else docstring_quote = "\047\047\047"
        rest = $0
        gsub(/^[[:space:]]*("""|\047\047\047)/, "", rest)
        if (rest ~ docstring_quote) in_docstring = 0
    } else {
        if ($0 ~ docstring_quote) in_docstring = 0
    }
    next
}

in_docstring { next }

# Skip comments
/^[[:space:]]*#/ { next }

# Detect function definition
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    in_func = 1
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
    in_signature = 1
    sig_buf = ""
    has_signature_injection = 0

    # Track parens on def line for signature detection
    def_check = $0
    sub(/#.*/, "", def_check)
    for (di = 1; di <= length(def_check); di++) {
        dc = substr(def_check, di, 1)
        if (dc == "(") paren_depth++
        if (dc == ")") paren_depth--
    }
    sig_buf = def_check

    # If single-line signature, check for injection now
    if (paren_depth <= 0) {
        in_signature = 0
        if (sig_buf ~ /timestamp/ || sig_buf ~ /a_timestamp/ || sig_buf ~ /a_time/ || sig_buf ~ /seed/ || sig_buf ~ /a_seed/) {
            has_signature_injection = 1
        }
    }

    next
}

# Track function body and parentheses
in_func {
    line = $0
    sub(/#.*/, "", line)
    buf = buf line
    for (i = 1; i <= length(line); i++) {
        c = substr(line, i, 1)
        if (c == "(") paren_depth++
        if (c == ")") paren_depth--
    }

    # Accumulate signature lines and detect end of signature
    if (in_signature) {
        sig_buf = sig_buf line
        if (paren_depth <= 0) {
            in_signature = 0
            if (sig_buf ~ /timestamp/ || sig_buf ~ /a_timestamp/ || sig_buf ~ /a_time/ || sig_buf ~ /seed/ || sig_buf ~ /a_seed/) {
                has_signature_injection = 1
            }
        }
    }

    if (paren_depth <= 0 && buf != "") {
        check_line = $0
        gsub(/#.*/, "", check_line)
        gsub(/"([^"\\]|\\.)*"/, "", check_line)
        gsub(/\047([^\\\047\n]|\\.)*\047/, "", check_line)

        if (!has_signature_injection) {
            # datetime.now() or datetime.utcnow()
            if (check_line ~ /datetime\.now\(\)/ || check_line ~ /datetime\.utcnow\(\)/) {
                printf "%d:0: error: non-deterministic datetime.now() — inject timestamp parameter (determinism-datetime)\n", NR
                violations++
            }
            # time.time()
            if (check_line ~ /time\.time\(\)/) {
                printf "%d:0: error: non-deterministic time.time() — inject timestamp parameter (determinism-time)\n", NR
                violations++
            }
            # time.monotonic(), time.localtime(), time.gmtime()
            if (check_line ~ /time\.monotonic\(\)/) {
                printf "%d:0: error: non-deterministic time.monotonic() — inject timestamp parameter (determinism-time)\n", NR
                violations++
            }
            if (check_line ~ /time\.localtime\(\)/) {
                printf "%d:0: error: non-deterministic time.localtime() — inject timestamp parameter (determinism-time)\n", NR
                violations++
            }
            if (check_line ~ /time\.gmtime\(\)/) {
                printf "%d:0: error: non-deterministic time.gmtime() — inject timestamp parameter (determinism-time)\n", NR
                violations++
            }
            # random.random(), random.randint(), random.choice(), random.shuffle(), random.gauss(), etc. without seed
            if (check_line ~ /random\.random\(\)/ || check_line ~ /random\.randint\(/ ||
                check_line ~ /random\.choice\(/ || check_line ~ /random\.sample\(/ ||
                check_line ~ /random\.shuffle\(/ || check_line ~ /random\.gauss\(/) {
                printf "%d:0: error: non-deterministic random usage — inject seed or use deterministic mode (determinism-random)\n", NR
                violations++
            }
            # uuid.uuid4()
            if (check_line ~ /uuid\.uuid4\(\)/) {
                printf "%d:0: warning: uuid.uuid4() is non-deterministic — consider uuid5() with fixed namespace (determinism-uuid)\n", NR
            }
        }

        buf = ""
    }
}

END { exit (violations > 0) ? 1 : 0 }
'

determinism_check_run() {
  local dirs=("$@")

  if [[ ${#dirs[@]} -eq 0 ]]; then
    lint_warn "determinism-check: no directories provided, skipping"
    return 0
  fi

  lint_step "determinism check (P1: SC-071) ${dirs[*]}"

  local py_files=()
  local d
  for d in "${dirs[@]}"; do
    while IFS= read -r -d '' f; do
      py_files+=("$f")
    done < <(find "${d}" -name "*.py" -type f -print0 2>/dev/null)
  done

  if [[ ${#py_files[@]} -eq 0 ]]; then
    lint_warn "determinism-check: no .py files found"
    return 0
  fi

  local has_violations=0
  local f
  for f in "${py_files[@]}"; do
    local output
    output=$(awk "${_DETERMINISM_AWK}" "${f}" 2>/dev/null) || true
    if [[ -n "${output}" ]]; then
      while IFS= read -r line; do
        printf "%s:%s\n" "${f}" "${line}"
      done <<< "${output}"
      has_violations=1
    fi
  done

  if [[ "${has_violations}" -eq 1 ]]; then
    lint_fail "determinism-check: non-deterministic patterns found"
    return 1
  fi

  lint_ok "determinism-check (P1)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  determinism_check_run "$@"
fi
