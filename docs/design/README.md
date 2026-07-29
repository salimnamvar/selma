# Selma — Design Freeze

Design Freeze documents the **application architecture** that implements the
normative contracts. Structure and behavior sources remain authoritative:

| Concern | Authoritative location |
| :--- | :--- |
| Behavioral contracts | [`../spec/contracts/`](../spec/contracts/) |
| Data shapes | [`../schema/`](../schema/) |
| Structural architecture (C4) | [`../c4-model/`](../c4-model/) |
| Behavioral FSMs / pipelines | [`../state-machine/`](../state-machine/) |
| Use-case catalog | [`../usecase/`](../usecase/) |
| **Design Freeze (this tree)** | `docs/design/` |

## Documents

| # | Document | Purpose |
| :--- | :--- | :--- |
| 01 | [Design Freeze status](01-design-freeze.md) | Entry/exit criteria, freeze scope, open decisions |
| 02 | [DDD model](02-ddd-model.md) | Bounded contexts, aggregates, entities, VOs, domain events |
| 03 | [Ports & adapters](03-ports-and-adapters.md) | Hexagonal ports, adapters, dependency rules |
| 04 | [Package architecture](04-package-architecture.md) | Target package layout, ownership, forbidden deps |
| 05 | [Application use cases](05-application-use-cases.md) | Application services mapped to contracts + capabilities |
| 06 | [Domain events & stores](06-domain-events-and-stores.md) | Event types, store roles, immutability rules |
| 07 | [Component class design](07-component-class-design.md) | Core classes/interfaces per C4 component (design-level) |
| 08 | [Implementation gap map](08-implementation-gap-map.md) | Current scaffold vs Design Freeze target (docs only) |

## Non-goals (this phase)

- No production code changes under `src/`
- No runtime wiring, migrations, or tests as deliverables of Design Freeze docs
- No inventing behavior that contradicts `docs/spec/contracts/`

## How to use these docs

1. **Implementers** start from packages + ports + use cases.
2. **Reviewers** check that PRs cite a contract ID and a design section.
3. **Auditors** use certification gates ([`certification/gates.yaml`](../spec/contracts/certification/gates.yaml)) against the architecture described here.
