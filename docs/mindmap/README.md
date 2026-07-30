# Selma — Project Phases

Development phases and artifact inventory for the Selma rule governance platform.

## Phases

| Phase | Artifacts | Status |
| :--- | :--- | :--- |
| **Vision** | Project goals, domain scope | Complete |
| **Specification** | Contract tree (`docs/spec/contracts/`), `rule_schema.json`, `policy_doctrine.yaml` | Complete |
| **Semantic Design** | State machines, workflows, data/API contracts, identity & versioning | Complete |
| **Architecture Documentation** | C4 diagrams, package layout, class model | Complete |
| **Implementation** | Runtime code, tests, deployment | Not Started |

## Architecture Documentation deliverables

| Area | Location |
| :--- | :--- |
| C4 Architecture | [`../c4-model/`](../c4-model/) |
| Package architecture | [`../package/`](../package/) |
| Class diagrams | [`../class/`](../class/) |
| Sequence diagrams | [`../sequence/`](../sequence/) |
| Use-case diagrams (human index) | [`../usecase/`](../usecase/) |

## Entry criteria (satisfied)

- Normative behavioral source: `docs/spec/contracts/`
- Archives: `docs/spec/ARCHIVE_*` (2026-07-29)
- Schemas v1.0.0 universal (detection / guidance split)
- C4 dual-document + guidance_only edges
- State machines linked to contracts

## Next major task

**Implementation** — follow C4 Model + contracts. No redesign of bounded contexts without contract change control.