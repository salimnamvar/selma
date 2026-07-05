# Selma — Rule Regularity Platform

**A universal governance steward that maintains a perfect, bidirectional bond between human-readable policies and machine-executable rules.**

Selma is domain-agnostic. It serves financial compliance, environmental standards, organizational governance, software engineering, or any regulatory domain where policy intent must map to verifiable machine behavior.

---

## What is Selma?

Selma is a **rule governance platform** designed to provide **regularity** — the state where rules are consistently defined, uniformly enforced, logically coherent, and predictably evolved across time and domains.

It achieves this through three core tenets:

1. **Strict separation** between human governance intent and machine-executable logic.
2. **Hermetic, deterministic compilation** that produces content-addressed, immutable execution artifacts.
3. **Auditable, append-only event streams** that track every finding and remediation.

Selma is **domain-agnostic** — it can be instantiated for regulatory compliance, internal corporate policies, technical standards, or any context requiring rule-based enforcement.

---

## Current Status

| Artifact | Status | Version |
| :--- | :--- | :--- |
| Normative Specification (`SPECIFICATION.md`) | Complete | 8.2.4 |
| Structural Schema (`rule_schema.json`) | Complete | 8.2.4 |
| Governance Doctrine (`policy_doctrine.yaml`) | Complete | 8.2.4 |
| User Stories (32 stories, 7 epics) | Complete | 8.2.4 |
| C4 Architecture Diagrams | Complete | 1.0.0 |
| Contract Validators | Complete | — |
| **Implementation** | **Not started** | — |

> Selma is in the **design phase**. All architectural artifacts, specifications, schemas, and user stories are complete, cross-validated, and audit-verified (98/100 architectural soundness). Runtime implementation has not yet begun.

**Next step:** Use-case diagrams → sequence diagrams → ERD → class diagrams → contracts → code.

---

## Architecture

Selma enforces a strict **three-layer dominance hierarchy**:

| Layer | Document | Role | Runtime Authority |
| :--- | :--- | :--- | :--- |
| **Normative** | `SPECIFICATION.md` | System behaviors, algorithms, invariants | **Highest** — sole source of runtime semantics |
| **Structural** | `rule_schema.json` | JSON Schema projection of spec invariants | **Data carrier** — no executable logic |
| **Governance** | `policy_doctrine.yaml` | Human authoring guidance | **None** — prohibited at runtime |

### The Policy Runtime Prohibition

The governance layer (`policy_doctrine.yaml`) is **never read at runtime**. It influences execution only through human authoring constraints enforced at compile time. The engine operates purely on structured schema fields and the compiled intermediate representation (CG-IR).

### Three Runtime Primitives

1. **Directive Graph** — human-authored, structured source of truth (versioned, mutable).
2. **Compiled Control DAG (CG-IR)** — content-addressed, immutable executable intermediate representation.
3. **Finding Event Stream** — append-only, HLC-ordered audit log of all compliance findings and state transitions.

### Four-Pillar Pipeline

```
Directive Graph → Definition → Maintenance → Mechanical Linting → Reasoning → CG-IR
```

| Pillar | Engine | Responsibility |
| :--- | :--- | :--- |
| 1 | **Definition** | Generates Machine IDs, drafts rule entries for both human and machine formats |
| 2 | **Maintenance** | CRUD operations, SemVer bumping, deprecation, refactoring |
| 3 | **Mechanical Linting** | Syntax, schema, contamination guard — hard fail on violations |
| 4 | **Reasoning** | Conflict detection, priority enforcement, soft warnings (Conflict Artifacts) |

---

## Project Structure

```
selma/
├── docs/
│   ├── Regulation/              # Three-layer contract architecture
│   │   ├── SPECIFICATION.md         # Normative behavioral source (8.2.4)
│   │   ├── rule_schema.json         # Structural JSON Schema (8.2.4)
│   │   ├── policy_doctrine.yaml     # Governance intent (8.2.4)
│   │   └── README.md                # Cross-layer binding & compatibility matrix
│   ├── User-Story/
│   │   └── User_Stories.md          # 32 user stories across 7 epics
│   └── C4-Design/                   # Architecture diagrams (PlantUML)
│       ├── c4_selma_context.puml
│       ├── c4_selma_container.puml
│       ├── c4_selma_component.puml
│       ├── common/c4_styles.puml
│       └── README.md                # Diagram conventions & rendering guide
├── src/selma/                   # Source scaffold (runtime not yet implemented)
├── tests/                       # Contract validation tests
├── scripts/
│   ├── validate_contracts.py        # Cross-layer contract validators
│   └── setup/                       # Environment provisioning
├── pyproject.toml
└── LICENSE                      # Apache-2.0
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

### Verify Contracts

```bash
python scripts/validate_contracts.py
pytest
```

`validate_contracts.py` checks version synchronization, the policy runtime prohibition, and audit-clarification traceability across the five-document corpus. `pytest` runs the same validators as an automated test suite.

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
| **Dual Identity** | Each rule has an immutable **Lineage ID** (audit root) and a mutable **Execution ID** (active node identity). |
| **Content-Addressed Storage** | CG-IR nodes are deduplicated by hash; identical rule content shares storage. |
| **Incremental Compilation** | Unchanged subgraphs are reused via `semantic_hash`; only dirty nodes are recompiled. |
| **Hermetic Reproducibility** | All non-deterministic factors are pinned in a frozen environment; identical inputs produce identical CG-IR. |
| **Finding FSM** | Strict state machine: `Created → Open → Acknowledged → … → Closed`. |
| **Capability Model** | Role → Capability → Action, enforced at request ingress and stage gates. |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver. |

---

## Documentation

| Document | Description |
| :--- | :--- |
| [SPECIFICATION.md](docs/Regulation/SPECIFICATION.md) | Normative system behavior, algorithms, and invariants |
| [rule_schema.json](docs/Regulation/rule_schema.json) | Machine-readable JSON Schema projection |
| [policy_doctrine.yaml](docs/Regulation/policy_doctrine.yaml) | Human authoring guidance (governance intent) |
| [Regulation README](docs/Regulation/README.md) | Cross-layer binding, version compatibility matrix, audit corpus |
| [User_Stories.md](docs/User-Story/User_Stories.md) | 32 behavioral user stories with traceability to spec invariants |
| [C4 Design](docs/C4-Design/) | Context, container, and component diagrams (PlantUML) |

---

## Design Chain

Selma follows a structured design-then-implementation workflow:

```
Specification → User Stories → C4 Diagrams → Use Cases → Sequence Diagrams
    → ERD → Class Diagrams → Contracts → Code
```

All steps through **C4 Diagrams** are complete and validated. **Use-case diagrams** are the current focus.

---

## Contributing

This project is in the **design phase**. Contributions are welcome as reviews, suggestions, and refinements to the specification, schema, user stories, or architecture diagrams. Runtime implementation is not yet open.

Please open an issue or submit a pull request with your proposed changes.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).