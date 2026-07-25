#!/usr/bin/env bash
# Comprehensive lint + format + type check for *this service only*.
# Operates on src/, tests/, and scripts/ relative to the service dir.
# Run from anywhere, or via: bash scripts/lint.sh
#
# Checks (in order):
#   --- Tool-based checks ---
#   1.  ruff check           — lint for errors and style
#   2.  ruff format          — enforce formatting (120 chars, double quotes)
#   3.  pylint               — Google pylintrc for naming and style
#   4.  pyright              — strict static type checking
#
#   --- Project convention checks ---
#   5.  a-prefix check       — all args must start with a_
#   6.  import check         — no imports inside functions
#   7.  return check         — single return per function (no early returns)
#   8.  global check         — no mutable global state (SC-070)
#   9.  google style         — docstrings, TODOs, mutable defaults
#
#   --- Safe Coding Doctrine checks (modular) ---
#   10. determinism check    — P1: no datetime.now/random without injection (SC-071)
#   11. zero-raise check     — P2: no raise statements in non-dunder functions (SC-002)
#   12. result return check  — P3: Result[T] returns, no tuples, return types, no star imports (SC-003/005/024/025)
#   13. INVALID_RESULT check — P4: module-level INVALID_RESULT sentinel (SC-004)
#   14. assert validation    — P5: no assert for input validation (SC-007/SC-113)
#   15. resource check       — P6: context managers for resources (SC-080/082)
#   16. function length      — SC-010: max 60 executable lines per function
#   17. b_continue check     — SC-011: b_continue one-way transition rules
#   18. error handling       — SC-041/042/052: specific exceptions, no silent failures, no re-raise
#   19. security check       — SC-100/101/104: no secrets, parameterized queries, no eval/exec
#   20. contract check       — SC-013: function docstring contracts
#
# Used by:
#   - developers (manual)
#   - setup.sh --steps cicd  (via cicd.sh)
#   - .githooks/pre-commit (if present)
#
# Requires the conda env activated (or full path to the tools in env).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LINT_DIR="${SCRIPT_DIR}/lint"

# Allow caller to override (e.g. from cicd.sh)
: "${RUFF:=$(command -v ruff || echo ruff)}"
: "${PYRIGHT:=$(command -v pyright || echo pyright)}"
: "${PYLINT:=$(command -v pylint || echo pylint)}"

SRC_DIR="${SERVICE_ROOT}/src"
TESTS_DIR="${SERVICE_ROOT}/tests"
SCRIPTS_DIR="${SERVICE_ROOT}/scripts"

# Source modular lint scripts (shared helpers)
# shellcheck source=lint/common.sh
source "${LINT_DIR}/common.sh"
# shellcheck source=lint/ruff_check.sh
source "${LINT_DIR}/ruff_check.sh"
# shellcheck source=lint/ruff_format.sh
source "${LINT_DIR}/ruff_format.sh"
# shellcheck source=lint/a_prefix_check.sh
source "${LINT_DIR}/a_prefix_check.sh"
# shellcheck source=lint/import_check.sh
source "${LINT_DIR}/import_check.sh"
# shellcheck source=lint/return_check.sh
source "${LINT_DIR}/return_check.sh"
# shellcheck source=lint/global_check.sh
source "${LINT_DIR}/global_check.sh"
# shellcheck source=lint/google_style_check.sh
source "${LINT_DIR}/google_style_check.sh"
# shellcheck source=lint/pylint_check.sh
source "${LINT_DIR}/pylint_check.sh"
# shellcheck source=lint/pyright.sh
source "${LINT_DIR}/pyright.sh"

# Source Safe Coding Doctrine lint scripts (modular per principle)
# shellcheck source=lint/determinism_check.sh
source "${LINT_DIR}/determinism_check.sh"
# shellcheck source=lint/zero_raise_check.sh
source "${LINT_DIR}/zero_raise_check.sh"
# shellcheck source=lint/result_return_check.sh
source "${LINT_DIR}/result_return_check.sh"
# shellcheck source=lint/invalid_result_check.sh
source "${LINT_DIR}/invalid_result_check.sh"
# shellcheck source=lint/assert_validation_check.sh
source "${LINT_DIR}/assert_validation_check.sh"
# shellcheck source=lint/resource_check.sh
source "${LINT_DIR}/resource_check.sh"
# shellcheck source=lint/function_length_check.sh
source "${LINT_DIR}/function_length_check.sh"
# shellcheck source=lint/b_continue_check.sh
source "${LINT_DIR}/b_continue_check.sh"
# shellcheck source=lint/error_handling_check.sh
source "${LINT_DIR}/error_handling_check.sh"
# shellcheck source=lint/security_check.sh
source "${LINT_DIR}/security_check.sh"
# shellcheck source=lint/contract_check.sh
source "${LINT_DIR}/contract_check.sh"

# Start from a clean slate (removes stale caches, egg-info, pyc etc.)
if [[ -x "${SERVICE_ROOT}/scripts/clean.sh" ]]; then
  "${SERVICE_ROOT}/scripts/clean.sh"
fi

# Collect existing directories
dirs=()
while IFS= read -r d; do
  dirs+=("${d}")
done < <(lint_existing_dirs "${SRC_DIR}" "${TESTS_DIR}" "${SCRIPTS_DIR}")

if [[ ${#dirs[@]} -eq 0 ]]; then
  lint_warn "No src/ or tests/ directories found, nothing to lint"
  exit 0
fi

# Helper to run a check and capture its exit status without dying immediately
run_lint_check() {
  local check_name="$1"
  shift
  if "$@"; then
    return 0
  else
    return 1
  fi
}

# --- Tool-based checks ---
failed=0
run_lint_check "ruff check" ruff_check_run "${RUFF}" "${dirs[@]}" || failed=1
run_lint_check "ruff format" ruff_format_run "${RUFF}" "${dirs[@]}" || failed=1
run_lint_check "pylint" pylint_run "${PYLINT}" "${SERVICE_ROOT}" || failed=1
run_lint_check "pyright" pyright_run "${PYRIGHT}" "${SERVICE_ROOT}" || failed=1

# --- Project convention checks ---
# Run independent AWK checks in parallel to improve performance
custom_checks=(
    "a_prefix_check_run ${SRC_DIR}"
    "import_check_run ${SRC_DIR}"
    "return_check_run ${SRC_DIR}"
    "global_check_run ${SRC_DIR}"
    "google_style_check_run ${SRC_DIR}"
    "determinism_check_run ${SRC_DIR}"
    "zero_raise_check_run ${SRC_DIR}"
    "result_return_check_run ${SRC_DIR}"
    "invalid_result_check_run ${SRC_DIR}"
    "assert_validation_check_run ${SRC_DIR}"
    "resource_check_run ${SRC_DIR}"
    "function_length_check_run ${SRC_DIR}"
    "b_continue_check_run ${SRC_DIR}"
    "error_handling_check_run ${SRC_DIR}"
    "security_check_run ${SRC_DIR}"
    "contract_check_run ${SRC_DIR}"
    "safe_coding_compliance_check_run ${SRC_DIR}"
)

echo "Running custom doctrine checks in parallel..."
for check in "${custom_checks[@]}"; do
    ( $check ) &
done

# Wait for all background checks to complete and capture exit status
for pid in $(jobs -p); do
    wait "$pid" || failed=1
done

if [[ "${failed}" -eq 1 ]]; then
  lint_fail "Some lint checks failed. Please fix the violations above."
  exit 1
fi

lint_ok "all checks passed"
