# C4 Diagram

Design knowledge service for C4 architecture diagrams.

Validates and repairs PlantUML C4 diagrams (Context, Container, Component levels).

## Usage

```bash
cd services/c4-diagram
pip install -e ".[dev]"

# Lint
python c4_lint.py docs/C4/

# Fix
python c4_fix.py docs/C4/ --in-place
```
