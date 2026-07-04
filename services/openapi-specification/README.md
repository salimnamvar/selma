# OpenAPI Specification

Design knowledge service for OpenAPI specifications.

## Usage

```bash
cd services/openapi-specification
pip install -e ".[dev]"

# Lint
python oas_lint.py docs/CT/

# Fix
python oas_fix.py docs/CT/ --in-place
```
