# Resource-Oriented Design

Design knowledge service for resource-oriented design and CSR validation of sequence diagrams.

## Usage

```bash
cd services/resource-oriented-design
pip install -e ".[dev]"

# Lint
python rod_csr_sq_lint.py docs/SQ/

# Fix
python rod_csr_sq_fix.py docs/SQ/ --in-place
```
