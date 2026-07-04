# Class Diagram

Design knowledge service for PlantUML class diagrams (domain model).

## Usage

```bash
cd services/class-diagram
pip install -e ".[dev]"

# Lint
python cl_lint.py docs/CL/

# Fix
python cl_fix.py docs/CL/ --in-place
```
