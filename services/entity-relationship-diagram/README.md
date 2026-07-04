# Entity-Relationship Diagram

Design knowledge service for PlantUML IE entity-relationship diagrams.

## Usage

```bash
cd services/entity-relationship-diagram
pip install -e ".[dev]"

# Lint
python erd_lint.py docs/ERD/

# Fix
python erd_fix.py docs/ERD/ --in-place
```
