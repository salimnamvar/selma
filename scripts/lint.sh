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

# Ensure conda is on PATH for hook environments
if [[ -z "${CONDA_PREFIX:-}" && -z "${VIRTUAL_ENV:-}" ]]; then
    for _conda_dir in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/miniforge3" "$HOME/mambaforge" "/opt/conda"; do
        if [[ -x "${_conda_dir}/bin/conda" ]]; then
            export PATH="${_conda_dir}/bin:${_conda_dir}/condabin:${PATH}"
            break
        fi
    done
fi

if [[ -n "${CONDA_PREFIX:-}" ]]; then
    PYTHON="${CONDA_PREFIX}/bin/python"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
    PYTHON="${VIRTUAL_ENV}/bin/python"
elif command -v conda &>/dev/null; then
    _selma_env="$(conda info --base 2>/dev/null)/envs/selma"
    if [[ -x "${_selma_env}/bin/python" ]]; then
        PYTHON="${_selma_env}/bin/python"
    else
        PYTHON="python"
    fi
else
    PYTHON="python"
fi

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
if ! "$PYTHON" -m selma "${SELMA_TARGET}" --skip-tools; then
    echo ""
    echo "✗ Selma AST rule violations found. Commit blocked."
    exit 1
fi

echo "✓ All lint checks passed."
