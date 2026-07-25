#!/usr/bin/env bash
# SELMA pre-commit hook: run linter on entire project.
# Blocks commit if any ruff or AST rule violations found.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "▸ Running SELMA linter on entire project…"

# Run ruff check
if ! python -m ruff check src/ tests/ 2>/dev/null; then
    echo ""
    echo "✗ Ruff violations found. Commit blocked."
    exit 1
fi

# Run ruff format check
if ! python -m ruff format --check src/ tests/ 2>/dev/null; then
    echo ""
    echo "✗ Format violations found. Commit blocked."
    exit 1
fi

echo "✓ All lint checks passed."
