#!/usr/bin/env bash
# Self-lint: Selma lints its own source code.
#
# Usage:
#   bash scripts/self_lint.sh              # lint all of src/selma
#   bash scripts/self_lint.sh src/selma/   # lint specific path
#
# Selma MUST follow every rule it enforces on others.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

# Default: lint src/selma
TARGET="${1:-src/selma}"

echo "Selma self-lint: ${TARGET}"
echo "────────────────────────────────────────"

python -m selma "${TARGET}"
