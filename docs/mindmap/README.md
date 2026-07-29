# Selma — Project Phases

Development phases and artifact inventory for the Selma rule governance platform.

## Phases

| Phase | Artifacts | Status |
| :--- | :--- | :--- |
| **Vision** | Project goals, domain scope | Complete |
| **Specification** | Contract tree (docs/spec/contracts/), rule_schema.json, policy_doctrine.yaml | Complete |
| **Semantic Design** | State machines, business workflows, data/api contracts, ERDs, interaction models, sequence diagrams, business rules, identity & versioning models | Complete |
| **Design Freeze** | DDD model, application architecture, ports & adapters, packages, classes, repositories | READY TO START |
| **Implementation** | Runtime code, tests, deployment | Not Started |

## Design Freeze entry criteria

All of the following are satisfied:

- Normative behavioral source is `docs/spec/contracts/` (archives under `docs/spec/ARCHIVE_*`)
- Universal schemas: `docs/schema/rule_schema.json`, `docs/schema/policy_doctrine.yaml` (v1.0.0)
- State machines catalog linked to contracts (`docs/state-machine/`)
- Dual-document directives (executable rule + guidance_only policy) reflected in C4 and contracts

## Next major task

DDD model + ports & adapters (Design Freeze phase).
