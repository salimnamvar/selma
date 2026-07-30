# Selma — Use Case Diagrams

Normative acceptance criteria live as `stories:` inside [`../spec/contracts/`](../spec/contracts/) (`US-DOMAIN-NNN`). This file is a navigational index only — no use case prose lives here.

PlantUML use case diagrams for each bounded context. Actors and components
align with [`../c4-model/`](../c4-model/README.md).

## Prerequisites

- PlantUML ≥ 1.2024
- Java 17+ (or the PlantUML Docker image)
- Common styles: `common/uc_styles.puml` (auto-included by each diagram)

## Quick Render

```bash
# Single diagram
plantuml docs/usecase/uc_001_governance.puml

# All diagrams
plantuml docs/usecase/uc_*.puml
```

## Actor Catalog (C4)

| Actor | Type | Description |
|-------|------|-------------|
| Regulatory Official | Human / AI agent | Authors directives; resolves findings; reads guidance |
| Compliance Representative | Human / AI / service | Submits targets and inspections; acknowledges findings; submits evidence; reads guidance |
| AI Agent | (acts as official or rep) | Same capabilities as the human principal it represents |

### Not C4 context peers

| Concern | How it appears |
|---------|----------------|
| CI/CD | Optional **client** of API / `certification_tool` (not a product actor) |
| Certification runner | Offline/CI tool suite (AA-01…AA-07); writes Artifacts when run |
| Target Sources | Optional external pull for inspection targets (primary path is inline) |
| Audit export / remediation ticketing | Ops exports / optional notify — not product peers |

## Diagram & Epic Index

| Epic / ID | Bounded Context | Primary Actor(s) | C4 / design owner | File | Primary contracts |
|-----------|-----------------|-------------------|-------------------|------|-------------------|
| UC-001 | Governance Authoring | Regulatory Official | `api`, `directives_repository` | [uc_001_governance.puml](uc_001_governance.puml) | `directive/*`, `compilation/*` |
| UC-002 | Compilation | Regulatory Official (via directive change); optional compile client | `compilation` | [uc_002_compilation.puml](uc_002_compilation.puml) | `compilation/*` |
| UC-003 | Inspection | Compliance Representative | `inspection` | [uc_003_inspection.puml](uc_003_inspection.puml) | `inspection/*` |
| UC-004 | Finding Lifecycle | Regulatory Official, Compliance Representative | `findings` | [uc_004_findings.puml](uc_004_findings.puml) | `finding_lifecycle/*` |
| UC-005 | Conflict | Regulatory Official | `ResolveConflict` (+ compilation / inspection / findings) | [uc_005_conflict.puml](uc_005_conflict.puml) | `conflict/*` |
| UC-006 | Authorization | Both actors | `api` | [uc_006_authorization.puml](uc_006_authorization.puml) | `authorization/*`, `finding_lifecycle/sod_contract.yaml` |
| UC-007 | Guidance | Both actors | `findings` (doctrine via `directives_repository`, `guidance_only`) | [uc_007_guidance.puml](uc_007_guidance.puml) | `inspection/finding_contract.yaml`, `schema/policy_doctrine.yaml` |
| UC-008 | Certification | Optional CI client | `certification_tool` (not in-process C4 peer) | [uc_008_certification.puml](uc_008_certification.puml) | `certification/gates.yaml` |

## Conventions

- `-->` solid arrow = association (actor participates in use case)
- `..>` dashed arrow = `<<include>>` (mandatory sub-flow) or `<<extend>>` (optional/conditional sub-flow)
- Notes contain **Pre** (precondition) and **Post** (postcondition) for each use case
- System boundary rectangles group use cases by bounded context
- All diagrams share styling from `common/uc_styles.puml`

## Design Reference

- C4 structure: [`../c4-model/README.md`](../c4-model/README.md)
- Application orchestration: [`../design/05-application-use-cases.md`](../design/05-application-use-cases.md)
