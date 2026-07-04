# Software Design

A collection of independent, deployable services — each a single-responsibility knowledge domain for software design.

## Project Structure

```
software-design/
├── services/                       # Independent, deployable services
│   ├── usecase-diagram/            # Use case diagram design knowledge
│   ├── c4-diagram/                 # C4 diagram design knowledge
│   ├── state-machine-diagram/      # State machine diagram design knowledge
│   ├── sequence-diagram/           # Sequence diagram design knowledge
│   ├── entity-relationship-diagram/ # ERD design knowledge
│   ├── class-diagram/              # Class diagram design knowledge
│   ├── openapi-specification/      # OpenAPI specification design knowledge
│   ├── data-contract/              # ODCS data contract design knowledge
│   └── resource-oriented-design/   # Resource-oriented design knowledge
├── libs/                           # Shared libraries
│   └── design-common/              # PlantUML parsing, report models
├── scripts/                        # Standalone cross-domain tools
├── infrastructure/                 # Deployment configs
└── tools/                          # Tooling configs
```

## Design Principles

- **Fully Independent Services**: Each service is a standalone Python package with its own `pyproject.toml`, source code, and tests. No cross-service dependencies.
- **Single Responsibility**: Each service owns one knowledge domain — it can be developed, deployed, and versioned independently.
- **CSR Pattern**: Each service follows Controller → Service → Repository → Domain layering.
- **Interface-Agnostic Core**: Backend supports CLI, API, desktop, mobile.

## Installation

### Individual service

```bash
cd services/usecase-diagram
pip install -e ".[dev]"
```

### Shared library

```bash
cd libs/design-common
pip install -e .
```

## Usage

```bash
cd services/usecase-diagram
usecase-diagram lint docs/UC/
usecase-diagram fix docs/UC/ --in-place

# Or run directly
python -m usecase_diagram lint docs/UC/
```

## Development

Each service is developed independently:

```bash
cd services/<service-name>
pip install -e ".[dev]"
pytest tests/
ruff check src/ tests/
```
