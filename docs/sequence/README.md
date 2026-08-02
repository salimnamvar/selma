# Selma Sequence Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.2.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

PlantUML sequence diagrams for core resource workflows.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime

## Usage

```bash
plantuml docs/sequence/*.puml
plantuml -tsvg docs/sequence/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| SEQ-001 | [seq_001_directive_crud.puml](seq_001_directive_crud.puml) | Directive resource lifecycle |
| SEQ-002 | [seq_002_compilation_pipeline.puml](seq_002_compilation_pipeline.puml) | Compilation → Compiled Rules |
| SEQ-003 | [seq_003_inspection_pipeline.puml](seq_003_inspection_pipeline.puml) | Inspection pipeline |
| SEQ-004 | [seq_004_finding_lifecycle.puml](seq_004_finding_lifecycle.puml) | Findings resource FSM |
| SEQ-005 | [seq_005_conflict_resolution.puml](seq_005_conflict_resolution.puml) | `ResolveConflict` domain service (not C4 peer) + artifact-backed human review |
| SEQ-006 | [seq_006_guidance_resolution.puml](seq_006_guidance_resolution.puml) | Finding guidance via `findings_application` + doctrine |
| SEQ-007 | [seq_007_certification_gates.puml](seq_007_certification_gates.puml) | Offline/CI `certification_tool` (not C4 peer) → artifacts |
| SEQ-008 | [seq_008_authorization_check.puml](seq_008_authorization_check.puml) | JWT authN + CapabilityEnforcer + DenialAuditPort |

## Cross-cutting sequence notes

- **SEQ-001:** durable directive mutation inserts `compile_request` outbox; short read locks released before hermetic CPU compile.
- **SEQ-006:** guidance resolves **revision-pinned** `paired_policy_ref` only (never latest doctrine head).
- **SEQ-008:** authentication via JWT; denials append through application-owned **DenialAuditPort**.

## Participants (C4 1.1.0)

| ID | Technology | Role |
|----|------------|------|
| `clients` | CLI/Web/Desktop/Mobile | Driving adapters |
| `api` | FastAPI/Pydantic | Resource API gate |
| `directives_application` | Python/Pydantic | Directive resource use cases |
| `compilation_application` | Python/JSON Schema/SHA-256 | Compile use cases (hermetic) |
| `inspections_application` | Python/RE2/SHA-256 | Inspection use cases |
| `findings_application` | Python/Pydantic | Findings lifecycle + guidance reads |
| `ResolveConflict` | domain service | Precedence algorithm (not a C4 peer) |
| `directives_repository` | SQLAlchemy/PostgreSQL | Directives port |
| `compiled_rules_repository` | CAS | Compiled Rules port |
| `finding_events_repository` | Append-Only | Finding Events port |
| `artifacts_repository` | Object Store | Artifacts port |
| `target_sources_gateway` | HTTP client | Optional remote targets |
| `certification_tool` | offline/CI | AA gates (not in-process peer) |

## Resource stores

| C4 ID | Type | Purpose |
|-------|------|---------|
| `directives_store` | PostgreSQL | Dual-document directives |
| `compiled_rules_store` | CAS | Immutable CG-IR snapshots |
| `finding_events_store` | Append-Only Log | Finding lifecycle events |
| `artifacts_store` | Object Store | Write-once evidence blobs |
