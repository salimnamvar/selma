# State Machine Diagram

Design knowledge service for PlantUML state machine (lifecycle) diagrams.

## Usage

```bash
cd services/state-machine-diagram
pip install -e ".[dev]"

# Lint
python sm_lint.py docs/SM/

# Fix
python sm_fix.py docs/SM/ --in-place

# Scaffold
python scaffold_states.py docs/SM/
```
