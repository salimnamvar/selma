# Selma — Rule Regularity Platform

A universal governance steward that maintains a perfect, bidirectional bond between human-readable policies and machine-executable rules.

Selma is domain-agnostic. It serves financial compliance, environmental standards, organizational governance, software engineering, or any regulatory domain where policy intent must map to verifiable machine behavior.

---

## Current State

| Artifact | Status | Version |
| :--- | :--- | :--- |
| Specification (`SPECIFICATION.md`) | Complete | 8.2.4 |
| Rule Schema (`rule_schema.json`) | Complete | 8.2.4 |
| Policy Doctrine (`policy_doctrine.yaml`) | Complete | 8.2.4 |
| User Stories (32 stories, 7 epics) | Complete | 8.2.4 |
| C4 Architecture Diagrams | Complete | 1.0.0 |
| Contract Validators | Complete | — |
| Implementation | Not started | — |

**Next step:** C4 diagram → use-case → sequence → ERD → class → contract → code.

---

## Architecture

Selma enforces a strict **three-layer dominance hierarchy**:

| Layer | Document | Role | Runtime Authority |
| :--- | :--- | :--- | :--- |
| **Normative** | `SPECIFICATION.md` | System behaviors, algorithms, invariants | Highest — sole source of runtime semantics |
| **Structural** | `rule_schema.json` | JSON Schema projection of spec invariants | Data carrier — no executable logic |
| **Governance** | `policy_doctrine.yaml` | Human authoring guidance | None — prohibited at runtime |

### The Policy Runtime Prohibition

The governance layer (`policy_doctrine.yaml`) is **never read at runtime**. It influences execution only through human authoring constraints enforced at compile time. The engine operates purely on structured schema fields and the compiled intermediate representation (CG-IR).

### Three Runtime Primitives

1. **Directive Graph** — human-authored, structured source of truth
2. **Compiled Control DAG (CG-IR)** — content-addressed, immutable executable IR
3. **Finding Event Stream** — append-only, HLC-ordered audit log

### Four-Pillar Pipeline

```
Directive Graph → Definition → Maintenance → Mechanical Linting → Reasoning → CG-IR
```

| Pillar | Engine | Responsibility |
| :--- | :--- | :--- |
| 1 | Definition | Generates Machine IDs, drafts rules |
| 2 | Maintenance | CRUD, SemVer bumping, deprecation, refactoring |
| 3 | Mechanical Linting | Syntax, schema, contamination guard — hard fail |
| 4 | Reasoning | Conflict detection, priority enforcement, soft warnings |

---

## Project Structure

```
selma/
├── docs/
│   ├── Regulation/          # Three-layer contract architecture
│   │   ├── SPECIFICATION.md     # Normative behavioral source (8.2.4)
│   │   ├── rule_schema.json     # Structural JSON Schema (8.2.4)
│   │   ├── policy_doctrine.yaml # Governance intent (8.2.4)
│   │   └── README.md            # Cross-layer binding & compatibility matrix
│   ├── User-Story/
│   │   └── User_Stories.md      # 32 user stories across 7 epics
│   └── C4-Design/               # Architecture diagrams (PlantUML)
│       ├── c4_selma_context.puml
│       ├── c4_selma_container.puml
│       ├── c4_selma_component.puml
│       └── common/c4_styles.puml
├── src/selma/               # Source code (not yet implemented)
├── tests/                   # Contract validation tests
├── scripts/
│   ├── validate_contracts.py    # Cross-layer contract validators
│   └── setup/                   # Environment provisioning
├── pyproject.toml
└── LICENSE                  # Apache-2.0
```

---

## Quick Start

### Prerequisites

- Python >= 3.11
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)

### Setup

```bash
bash scripts/setup/setup_env.sh
```

This provisions a conda environment, installs dependencies, configures VS Code, and runs verification gates.

### Manual Setup

```bash
conda create -n selma python=3.11 -y
conda activate selma
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Contract Validators

```bash
python scripts/validate_contracts.py
```

### Render C4 Diagrams

Requires [PlantUML](https://plantuml.com/) and [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) v2.13.0:

```bash
plantuml docs/C4-Design/c4_selma_context.puml
plantuml docs/C4-Design/c4_selma_container.puml
plantuml docs/C4-Design/c4_selma_component.puml
```

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Dual Identity** | Lineage ID (immutable root) + Execution ID (active node identity) |
| **Content-Addressed Storage** | CG-IR nodes deduplicated by hash; identical content shares storage |
| **Incremental Compilation** | Unchanged subgraphs reused via `semantic_hash`; only dirty nodes recompiled |
| **Hermetic Reproducibility** | Frozen environment pins all non-deterministic factors |
| **Finding FSM** | Strict state machine: Created → Open → Acknowledged → … → Closed |
| **Capability Model** | Role → Capability → Action, enforced at request ingress and stage gates |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver |

---

## Design Chain

```
Specification → User Stories → C4 Diagrams → Use Cases → Sequence Diagrams
    → ERD → Class Diagrams → Contracts → Code
```

---

## Contributing

This project is in the design phase. Implementation has not yet started. See the specification and user stories in `docs/` for the full behavioral contract.

## License

Apache 2.0 — see [LICENSE](LICENSE).
