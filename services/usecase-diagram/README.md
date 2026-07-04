# Use Case Diagram

Design knowledge service for PlantUML use case diagrams.

## Usage

```bash
cd services/usecase-diagram
pip install -e ".[dev]"

usecase-diagram lint docs/UC/
usecase-diagram fix docs/UC/ --in-place

# Or run directly
python -m usecase_diagram lint docs/UC/
```
