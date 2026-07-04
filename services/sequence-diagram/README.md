# Sequence Diagram

Design knowledge service for PlantUML sequence diagrams.

## Usage

```bash
cd services/sequence-diagram
pip install -e ".[dev]"

# Lint
python sq_lint.py docs/SQ/

# Fix
python sq_fix.py docs/SQ/ --in-place
```
