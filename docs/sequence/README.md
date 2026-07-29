# Selma Sequence Diagrams

PlantUML sequence diagrams documenting the core workflows of the Selma compliance platform.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime (for PlantUML rendering)

## Usage

```bash
# Render all diagrams
plantuml docs/sequence/*.puml

# Render a single diagram
plantuml docs/sequence/seq_001_directive_crud.puml

# Render to SVG (recommended for docs)
plantuml -tsvg docs/sequence/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| SEQ-001 | [seq_001_directive_crud.puml](seq_001_directive_crud.puml) | Directive CRUD lifecycle (Create/Modify/Retire/Fork/Merge/Split/Restore) |
| SEQ-002 | [seq_002_compilation_pipeline.puml](seq_002_compilation_pipeline.puml) | Hermetic compilation of directive graph to CG-IR |
| SEQ-003 | [seq_003_inspection_pipeline.puml](seq_003_inspection_pipeline.puml) | 6-stage inspection pipeline (normalize, classify, select, evaluate, aggregate, report) |
| SEQ-004 | [seq_004_finding_lifecycle.puml](seq_004_finding_lifecycle.puml) | Finding state transitions through 10-state FSM |
| SEQ-005 | [seq_005_conflict_resolution.puml](seq_005_conflict_resolution.puml) | Deterministic + human conflict resolution |
| SEQ-006 | [seq_006_guidance_resolution.puml](seq_006_guidance_resolution.puml) | Resolve paired policy doctrine for finding guidance |
| SEQ-007 | [seq_007_certification_gates.puml](seq_007_certification_gates.puml) | 7-gate architectural certification (AA-01 through AA-07) |
| SEQ-008 | [seq_008_authorization_check.puml](seq_008_authorization_check.puml) | Capability-based access control with Segregation of Duties |

## Shared Styles

Common styling definitions are in [`common/seq_styles.puml`](common/seq_styles.puml). All diagrams include this file via `!include common/seq_styles.puml`.

## Participants (Components)

| Component | Technology | Role |
|-----------|-----------|------|
| selma_interface | CLI/WebApp/DesktopApp/MobileApp | User-facing interface |
| application_service | FastAPI/Pydantic | API gateway and orchestration |
| directives_adapter | Python/SQLAlchemy/PostgreSQL | Directive persistence |
| hermetic_compiler | Python/JSON Schema/SHA-256 | Deterministic CG-IR compilation |
| compiled_rules_adapter | Python/SHA-256/CAS | Compiled rule storage (CAS) |
| rule_inspector | Python/RE2/SHA-256 | 6-stage inspection engine |
| lifecycle_finder | Python/Pydantic | Finding FSM lifecycle management |
| conflict_resolver | Python/Pydantic | Conflict detection and resolution |
| finding_analyzer | Python/Pydantic | Guidance and policy analysis |
| architectural_auditor | Python | 7-gate certification auditor |
| snapshots_adapter | Python/Object Store | Inspection snapshot persistence |
| findings_audit_adapter | Python/SHA-256/Append-Only | Finding audit trail (append-only) |
| target_adapter | Python/HTTP Client | Target data retrieval |
| policy_doctrine | YAML files, read-only | Governance policy definitions |

## Data Stores

| Store | Type | Purpose |
|-------|------|---------|
| directive_store | PostgreSQL | Directive records with versioned revisions |
| cgir_store | Content-Addressed Storage | CG-IR nodes, edges, and snapshots |
| event_store | Append-Only Log | Finding events and audit trail |
| artifact_store | Object Store | Inspection snapshots and certification artifacts |
