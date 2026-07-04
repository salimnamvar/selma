# Data Contract

Design knowledge service for ODCS v3 data contracts.

## Usage

```bash
cd services/data-contract
pip install -e ".[dev]"

# Lint
python odcs_lint.py docs/CT/

# Fix
python odcs_fix.py docs/CT/ --in-place
```
