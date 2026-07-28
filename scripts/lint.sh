#!/usr/bin/env bash
# SELMA lint: ruff, ruff format, pyright, and selma AST rules.
#
# Usage:
#   bash scripts/lint.sh              # lint all of src/selma
#   bash scripts/lint.sh src/selma/   # lint specific selma target
#
# Used by pre-commit hook and CI/CD.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Resolve the correct python — prefer active env, fall back to selma env
_selma_python=""
if [[ -n "${CONDA_PREFIX:-}" ]]; then
    # CONDA_PREFIX may point to base conda (no selma there); check
    if "$CONDA_PREFIX/bin/python" -c "import selma" 2>/dev/null; then
        _selma_python="$CONDA_PREFIX/bin/python"
    fi
fi
if [[ -z "$_selma_python" && -n "${VIRTUAL_ENV:-}" ]]; then
    if "$VIRTUAL_ENV/bin/python" -c "import selma" 2>/dev/null; then
        _selma_python="$VIRTUAL_ENV/bin/python"
    fi
fi
if [[ -z "$_selma_python" ]]; then
    # Ensure conda is on PATH for hook environments
    for _conda_dir in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/miniforge3" "$HOME/mambaforge" "/opt/conda"; do
        if [[ -x "${_conda_dir}/bin/conda" ]]; then
            export PATH="${_conda_dir}/bin:${_conda_dir}/condabin:${PATH}"
            break
        fi
    done
    if command -v conda &>/dev/null; then
        _selma_env="$(conda info --base 2>/dev/null)/envs/selma"
        if [[ -x "${_selma_env}/bin/python" ]]; then
            _selma_python="${_selma_env}/bin/python"
        fi
    fi
fi
if [[ -z "$_selma_python" ]]; then
    _selma_python="python"
fi

PYTHON="$_selma_python"

if ! "$PYTHON" -c "import selma" 2>/dev/null; then
    echo "✗ Python at '${PYTHON}' does not have selma installed."
    echo "  Activate the selma conda env first: conda activate selma"
    exit 1
fi

SELMA_TARGET="${1:-src/selma}"

echo "▸ Running ruff check…"
if ! "$PYTHON" -m ruff check src/ tests/ 2>/dev/null; then
    echo ""
    echo "✗ Ruff violations found. Commit blocked."
    exit 1
fi

echo "▸ Running ruff format check…"
if ! "$PYTHON" -m ruff format --check src/ tests/ 2>/dev/null; then
    echo ""
    echo "✗ Format violations found. Commit blocked."
    exit 1
fi

echo "▸ Running pyright…"
if ! "$PYTHON" -m pyright src/ 2>/dev/null; then
    echo ""
    echo "✗ Type errors found. Commit blocked."
    exit 1
fi

echo "▸ Running selma self-lint: ${SELMA_TARGET}…"
# Self-lint with full rule set. Process/governance rules SC-120–133 are
# enforced outside AST evaluation. Exit codes:
#   0 — no critical/high findings
#   1 — critical/high findings (report; baseline debt may remain while the
#       catalog is brought into full compliance)
#   2+ — tool/runtime failure (always blocks)
set +e
"$PYTHON" -m selma inspect "${SELMA_TARGET}" --skip-tools
_selma_ec=$?
set -e
if [[ "${_selma_ec}" -ge 2 ]]; then
    echo ""
    echo "✗ Selma failed to run (exit ${_selma_ec}). Commit blocked."
    exit 1
fi
if [[ "${_selma_ec}" -eq 1 ]]; then
    echo ""
    echo "⚠ Selma reported critical/high findings (exit 1)."
    echo "  Ruff/pyright still gate the commit. Resolve findings in follow-up."
fi

echo "✓ All lint checks passed."
