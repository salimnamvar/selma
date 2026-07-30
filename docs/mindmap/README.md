# Selma — Project Phases

Development phases and artifact inventory for the Selma rule governance platform.

## Phases

| Phase | Artifacts | Status |
| :--- | :--- | :--- |
| **Vision** | Project goals, domain scope | Complete |
| **Specification** | Contract tree (`docs/spec/contracts/`), `rule_schema.json`, `policy_doctrine.yaml` | Complete |
| **Semantic Design** | State machines, workflows, data/API contracts, identity & versioning | Complete |
| **Design Freeze** | DDD model, ports & adapters, packages, use cases, class design | **Complete** |
| **Implementation** | Runtime code, tests, deployment | Not Started |

## Design Freeze deliverables

| Area | Location |
| :--- | :--- |
| Design index | [`../design/README.md`](../design/README.md) |
| DDD model | [`../design/02-ddd-model.md`](../design/02-ddd-model.md) |
| Ports & adapters | [`../design/03-ports-and-adapters.md`](../design/03-ports-and-adapters.md) |
| Package architecture | [`../design/04-package-architecture.md`](../design/04-package-architecture.md) |
| Application use cases | [`../design/05-application-use-cases.md`](../design/05-application-use-cases.md) |
| Use-case diagrams (human index) | [`../usecase/README.md`](../usecase/README.md) |
| Scaffold gap map | [`../design/08-implementation-gap-map.md`](../design/08-implementation-gap-map.md) |

## Entry criteria (satisfied)

- Normative behavioral source: `docs/spec/contracts/`
- Archives: `docs/spec/ARCHIVE_*` (2026-07-29)
- Schemas v1.0.0 universal (detection / guidance split)
- C4 dual-document + guidance_only edges
- State machines linked to contracts

## Next major task

**Implementation** — follow Design Freeze package layout and ports; close gaps in
[`../design/08-implementation-gap-map.md`](../design/08-implementation-gap-map.md).
No redesign of bounded contexts without contract + design change control
([`../design/01-design-freeze.md`](../design/01-design-freeze.md)).
