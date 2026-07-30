# Selma Documentation

| Area | Path | Role |
| :--- | :--- | :--- |
| **Specification contracts** | [`spec/`](spec/README.md) | Normative behavior (`contracts/`) |
| **Schemas** | [`schema/`](schema/) | Rule + policy structure (v1.0.0) |
| **C4 architecture** | [`c4-model/`](c4-model/README.md) | **Source of truth for structure** (context / container / component) |
| **State machines** | [`state-machine/`](state-machine/README.md) | FSMs and pipelines |
| **Design Freeze** | [`design/`](design/README.md) | DDD, ports, packages, use cases |
| **Use case diagrams** | [`usecase/`](usecase/README.md) | Actor / epic index (stories live in contracts) |
| **Sequence diagrams** | [`sequence/`](sequence/README.md) | Resource workflow sequences |
| **Class diagrams** | [`class/`](class/README.md) | Domain / application / infrastructure classes |
| **Package diagrams** | [`package/`](package/README.md) | Clean Architecture package layout |
| **ERDs** | [`erd/`](erd/README.md) | Four resource stores |
| **Activity diagrams** | [`activity/`](activity/README.md) | Procedural swim-lane flows |
| **API** | [`api/`](api/README.md) | OpenAPI + resource schemas |
| **Deployment** | [`deployment/`](deployment/README.md) | Topology aligned with C4 containers |
| **Project phases** | [`mindmap/`](mindmap/README.md) | Phase status |

## Authority

1. `spec/contracts/` — what the system MUST do
2. `schema/` — data shapes
3. **`c4-model/`** — structural architecture (entity IDs, containers, components, stores)
4. `design/` — how Implementation is structured (packages, ports, use cases)
5. `state-machine/` + other diagrams — behavior and detail views; must not contradict C4 or contracts

Diagrams and design prose use C4 resource-oriented IDs from
[`c4-model/README.md`](c4-model/README.md) (e.g. `api`, `compilation`,
`inspection`, `findings`, `*_repository`, stores `directives` /
`compiled_rules` / `finding_events` / `artifacts`).

**Not product peers** (optional clients/exports only): CI/CD, long-term audit
export, remediation ticketing. Conflict resolution and guidance are domain /
findings concerns, not freestanding engines. Certification (AA-01…AA-07) is an
offline/CI tool suite.

## Implementation

Do not start coding from archives. Start from Design Freeze + contracts + C4.
Gap checklist: [`design/08-implementation-gap-map.md`](design/08-implementation-gap-map.md).
