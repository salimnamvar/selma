# Selma — Use Case Catalog

Normative acceptance criteria live as `stories:` inside
[`../spec/contracts/`](../spec/contracts/) (`US-DOMAIN-NNN`).
Visual representation lives in [`../usecase-diagram/`](../usecase-diagram/README.md).
This file is a navigational index only — no use case prose lives here.

## Actors

| Actor | C4 ID | Summary |
| :--- | :--- | :--- |
| Regulatory Official | `regulatory_official` | Full directive lifecycle, dispositions, conflict resolution |
| Compliance Representative | `compliance_representative` | Submit targets, acknowledge findings, submit evidence |
| System | — | Automatic FSM edges, compilation, inspection evaluation |
| Certification runner | offline/CI tool | Optional AA-01…AA-07 gates (not a C4 external peer) |
| AI Agent | (acts as official or rep) | Same capabilities as human principal |

## Epic Index

| Epic | Diagram | Primary contracts |
| :--- | :--- | :--- |
| Governance | [`UC-001`](../usecase-diagram/uc_001_governance.puml) | `directive/*`, `compilation/*` |
| Compilation | [`UC-002`](../usecase-diagram/uc_002_compilation.puml) | `compilation/*` |
| Inspection | [`UC-003`](../usecase-diagram/uc_003_inspection.puml) | `inspection/*` |
| Findings | [`UC-004`](../usecase-diagram/uc_004_findings.puml) | `finding_lifecycle/*` |
| Conflict | [`UC-005`](../usecase-diagram/uc_005_conflict.puml) | `conflict/*` |
| Authorization | [`UC-006`](../usecase-diagram/uc_006_authorization.puml) | `authorization/*`, `finding_lifecycle/sod_contract.yaml` |
| Guidance | [`UC-007`](../usecase-diagram/uc_007_guidance.puml) | `inspection/finding_contract.yaml`, `schema/policy_doctrine.yaml` |
| Certification | [`UC-008`](../usecase-diagram/uc_008_certification.puml) | `certification/gates.yaml` |

## Design Reference

Application-layer orchestration:
[`../design/05-application-use-cases.md`](../design/05-application-use-cases.md).
