# Selma — Use Case Diagrams

Normative acceptance criteria live as `stories:` inside [`../spec/contracts/`](../spec/contracts/) (`US-DOMAIN-NNN`). This file is a navigational index only — no use case prose lives here.

PlantUML use case diagrams for each bounded context in the Selma compliance-governance platform.

## Prerequisites

- PlantUML ≥ 1.2024
- Java 17+ (or the PlantUML Docker image)
- Common styles: `common/uc_styles.puml` (auto-included by each diagram)

## Quick Render

```bash
# Single diagram
plantuml docs/usecase-diagram/uc_001_governance.puml

# All diagrams
plantuml docs/usecase-diagram/uc_*.puml
```

## Actor Catalog

| Actor | Type | Description |
|-------|------|-------------|
| Regulatory Official | Human / AI agent | Full directive lifecycle, dispositions, conflict resolution |
| Compliance Representative | Human / AI / Programmatic service | Submit targets, acknowledge findings, submit evidence |
| CI/CD Pipeline | System | Triggers certification and compliance checks |
| Certification runner | offline/CI tool | Optional AA-01…AA-07 gates (not a C4 external peer) |
| External Systems | System | CI/CD, Target Systems, Audit Platform, Remediation Systems |
| AI Agent | (acts as official or rep) | Same capabilities as human principal |

## Diagram & Epic Index

| Epic / ID | Bounded Context | Primary Actor(s) | Key Component | File | Primary contracts |
|-----------|-----------------|-------------------|---------------|------|-------------------|
| UC-001 | Governance Authoring | Regulatory Official | `directives_repository`, `api` | [uc_001_governance.puml](uc_001_governance.puml) | `directive/*`, `compilation/*` |
| UC-002 | Compilation | CI/CD Pipeline, Regulatory Official (indirect) | `compilation` | [uc_002_compilation.puml](uc_002_compilation.puml) | `compilation/*` |
| UC-003 | Inspection | Compliance Representative | `inspection` | [uc_003_inspection.puml](uc_003_inspection.puml) | `inspection/*` |
| UC-004 | Finding Lifecycle | Regulatory Official, Compliance Representative | `findings` | [uc_004_findings.puml](uc_004_findings.puml) | `finding_lifecycle/*` |
| UC-005 | Conflict | Regulatory Official | `ResolveConflict` + `findings` / `compilation` | [uc_005_conflict.puml](uc_005_conflict.puml) | `conflict/*` |
| UC-006 | Authorization | Both actors | `api` | [uc_006_authorization.puml](uc_006_authorization.puml) | `authorization/*`, `finding_lifecycle/sod_contract.yaml` |
| UC-007 | Guidance & Analytics | Both actors | `findings` | [uc_007_guidance.puml](uc_007_guidance.puml) | `inspection/finding_contract.yaml`, `schema/policy_doctrine.yaml` |
| UC-008 | Certification | CI/CD Pipeline | `certification_tool` | [uc_008_certification.puml](uc_008_certification.puml) | `certification/gates.yaml` |

## Conventions

- `-->` solid arrow = association (actor participates in use case)
- `..>` dashed arrow = `<<include>>` (mandatory sub-flow) or `<<extend>>` (optional/conditional sub-flow)
- Notes contain **Pre** (precondition) and **Post** (postcondition) for each use case
- System boundary rectangles group use cases by bounded context
- All diagrams share styling from `common/uc_styles.puml`

## Design Reference

Application-layer orchestration:
[`../design/05-application-use-cases.md`](../design/05-application-use-cases.md).