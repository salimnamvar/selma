#!/usr/bin/env bash
# Comprehensive lint + format + type check for *this service only*.
#
# Thin wrapper around: python -m scripts.lint
#
# Usage:
#   bash scripts/lint.sh                      # run all checks
#   bash scripts/lint.sh --skip-tools         # AST rules only
#   bash scripts/lint.sh --only ruff-check    # single check
#   bash scripts/lint.sh --codes SC001 SC002  # specific rules
#
# Checks orchestrated by the Python linter:
#   1. ruff check       — lint for errors and style
#   2. ruff format      — enforce formatting
#   3. pylint           — Google pylintrc
#   4. pyright          — strict type checking
#   5. AST rules        — SC-001..SC-104, a-prefix, contracts, imports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${SERVICE_ROOT}"
exec python -m scripts.lint "$@"
