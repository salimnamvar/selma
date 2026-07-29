# Selma — Use Case Catalog

Human- and system-facing use cases for Implementation planning.
**Normative acceptance criteria** live as `stories:` inside
[`../spec/contracts/`](../spec/contracts/) (`US-DOMAIN-NNN`).
This catalog is a navigational index only.

## Actors

| Actor | C4 ID | Summary |
| :--- | :--- | :--- |
| Regulatory Official | `regulatory_official` | Full directive lifecycle, dispositions, conflict resolution |
| Compliance Representative | `compliance_rep` | Submit targets, acknowledge findings, submit evidence |
| System | — | Automatic FSM edges, compilation, inspection evaluation |
| CI/CD | `cicd` | Architectural certification trigger |
| AI Agent | (acts as official or rep) | Same capabilities as human principal |

## Epic index

| Epic | Use cases | Primary contracts |
| :--- | :--- | :--- |
| [UC-G Governance](UC-G-governance.md) | Create/modify/retire/fork/merge/split/restore directives | `directive/*`, compilation |
| [UC-C Compilation](UC-C-compilation.md) | Validate & publish CG-IR | `compilation/*` |
| [UC-I Inspection](UC-I-inspection.md) | Submit/reinspect targets, explain | `inspection/*` |
| [UC-F Findings](UC-F-findings.md) | FSM transitions + views | `finding_lifecycle/*` |
| [UC-X Conflict](UC-X-conflict.md) | Detect/resolve conflicts | `conflict/*` |
| [UC-A Authz](UC-A-authorization.md) | Capability & SoD enforcement | `authorization/*`, sod |
| [UC-N Guidance](UC-N-guidance.md) | Guidance resolution & analytics | policy doctrine, analyzer |
| [UC-Z Certification](UC-Z-certification.md) | AA-01…AA-07 | `certification/gates.yaml` |

## Design mapping

Application-layer orchestration detail:
[`../design/05-application-use-cases.md`](../design/05-application-use-cases.md).
