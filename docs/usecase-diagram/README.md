# Selma — Use Case Diagrams

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

## Diagram Index

| ID | Bounded Context | Primary Actor(s) | Key Component | File |
|----|-----------------|-------------------|---------------|------|
| UC-001 | Governance Authoring | Regulatory Official | `directives_adapter`, `application_service` | [uc_001_governance.puml](uc_001_governance.puml) |
| UC-002 | Compilation | CI/CD Pipeline, Regulatory Official (indirect) | `hermetic_compiler` | [uc_002_compilation.puml](uc_002_compilation.puml) |
| UC-003 | Inspection | Compliance Representative | `rule_inspector` | [uc_003_inspection.puml](uc_003_inspection.puml) |
| UC-004 | Finding Lifecycle | Regulatory Official, Compliance Representative | `lifecycle_finder` | [uc_004_findings.puml](uc_004_findings.puml) |
| UC-005 | Conflict | Regulatory Official | `conflict_resolver` | [uc_005_conflict.puml](uc_005_conflict.puml) |
| UC-006 | Authorization | Both actors | `application_service` | [uc_006_authorization.puml](uc_006_authorization.puml) |
| UC-007 | Guidance & Analytics | Both actors | `finding_analyzer` | [uc_007_guidance.puml](uc_007_guidance.puml) |
| UC-008 | Certification | CI/CD Pipeline | `architectural_auditor` | [uc_008_certification.puml](uc_008_certification.puml) |

## Actor Legend

| Actor | Type | Description |
|-------|------|-------------|
| Regulatory Official | Human / AI agent | Regulatory authority with full directive lifecycle capabilities |
| Compliance Representative | Human / AI / Programmatic service | Regulated entity; submits targets, acknowledges findings |
| CI/CD Pipeline | System | Triggers certification and compliance checks |
| External Systems | System | Governance Contracts, Target Systems, Audit Platform, Remediation Systems |

## Conventions

- `-->` solid arrow = association (actor participates in use case)
- `..>` dashed arrow = `<<include>>` (mandatory sub-flow) or `<<extend>>` (optional/conditional sub-flow)
- Notes contain **Pre** (precondition) and **Post** (postcondition) for each use case
- System boundary rectangles group use cases by bounded context
- All diagrams share styling from `common/uc_styles.puml`
