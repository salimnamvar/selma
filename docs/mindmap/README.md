# Selma — Project Phases

Development phases and artifact inventory for the Selma rule regularity platform.
Structural source of truth: [`../c4-model/`](../c4-model/README.md) (Contract 1.1.0).

## Phases

| Phase | Artifacts | Status |
| :--- | :--- | :--- |
| **Vision** | Project goals, domain scope | Complete |
| **Specification** | Contract tree (`docs/spec/contracts/`), `rule_schema.json`, `policy_doctrine.yaml` | Complete |
| **Semantic Design** | State machines, workflows, data/API contracts, identity & versioning | Complete |
| **Architecture Documentation** | C4 diagrams, package layout, class model, sequences, ERDs, deployment | Complete |
| **Implementation** | Runtime code, tests, deployment | Not Started |

## Architecture Documentation deliverables

| Area | Location | C4 alignment |
| :--- | :--- | :--- |
| C4 Architecture | [`../c4-model/`](../c4-model/) | Source of truth for structure |
| Specification contracts | [`../spec/`](../spec/) | Behavior owned by C4 components / domain services |
| Schemas | [`../schema/`](../schema/) | Rule + policy shapes |
| State machines | [`../state/`](../state/) | FSMs; no freestanding engine peers |
| Use cases | [`../usecase/`](../usecase/) | Actor index over C4 owners |
| Sequences | [`../sequence/`](../sequence/) | Resource workflows |
| Class / package | [`../class/`](../class/), [`../package/`](../package/) | Implementation structure |
| ERDs | [`../erd/`](../erd/) | Four `*_store` resources |
| Activity | [`../activity/`](../activity/) | Procedural flows |
| API | [`../api/`](../api/) | Resource surface aligned with C4 |
| Deployment | [`../deployment/`](../deployment/) | Containers + four stores |

## C4 product surface (keep in mind)

| In product (C4) | Not freestanding peers |
| :--- | :--- |
| `api`, `*_application`, `*_repository`, `*_gateway`, four `*_store` | `ResolveConflict` (domain), guidance/aggregates (findings reads), `certification_tool` (offline/CI), CI/CD / audit export / ticketing (optional clients) |

## Entry criteria (satisfied)

- Normative behavioral source: `docs/spec/contracts/`
- Schemas v1.0.0 universal (detection / guidance split)
- C4 dual-document + `guidance_only` edges
- State machines linked to contracts
- Non-C4 “engines” removed from diagrams (conflict / guidance / cert as peers)

## Next major task

**Implementation** — follow C4 Model + contracts. No redesign of product peers without contract and C4 change control.
