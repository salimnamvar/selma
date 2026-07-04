# design-common

Shared libraries for software-design subprojects.

## Modules

- **puml** — PlantUML parsing utilities (strip comments, extract title/notes, basic diagram IR)
- **report** — Violation and report models shared across linters

## Installation

```bash
pip install -e ../libs/design-common
```

## Usage

```python
from design_common.puml import strip_puml_comments, load_basic_diagram
from design_common.report import Violation, LayerReport
```
