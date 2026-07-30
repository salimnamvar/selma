# Selma — Activity Diagrams

Activity diagrams showing process flows and decision logic across Selma's key workflows. Complements the [state machines](../state-machine/README.md) (which model state *transitions*) with a focus on *procedural flow*, parallelism, and swim-lane partitioning.

Read with [`contracts/`](../spec/contracts/) for the full behavioral contracts.

## Catalog

| File | Activity | Spec authority | Key participants |
| :--- | :--- | :--- | :--- |
| `act_001_inspection_pipeline.puml` | Inspection Pipeline (6-stage) | [`inspection/pipeline.yaml`](../spec/contracts/inspection/pipeline.yaml) | `api`, `inspection`, `findings`, `artifacts_repository` |
| `act_002_finding_disposition.puml` | Finding Disposition | [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) | Regulatory Official, Compliance Rep, `findings` |
| `act_003_directive_amendment.puml` | Directive Amendment | [`directive/lifecycle.yaml`](../spec/contracts/directive/lifecycle.yaml) | `api`, `directives_repository`, `compilation` |
| `common/act_styles.puml` | Shared theme | — | — |

## Design Principles

- **Contract dominance** — diagrams illustrate contract behavior; they do not invent new flows
- **Swim-lane partitioning** — each partition maps to a C4 component or logical layer
- **Parallel fork/join** — used where the contract explicitly allows concurrent execution
- **Capability gates** — every human-initiated action shows capability check before mutation
- **SoD enforcement** — Separation of Duties checks shown where creator ≠ actor constraint applies
- **Error paths** — abort, skip, and retry paths are explicit; no silent failures

## Relationship to State Machines

| Activity Diagram | Corresponding State Machine |
| :--- | :--- |
| `act_001_inspection_pipeline.puml` | [`selma_inspection_pipeline.puml`](../state-machine/selma_inspection_pipeline.puml) |
| `act_002_finding_disposition.puml` | [`selma_finding_lifecycle.puml`](../state-machine/selma_finding_lifecycle.puml) |
| `act_003_directive_amendment.puml` | [`selma_directive_lifecycle.puml`](../state-machine/selma_directive_lifecycle.puml) + [`selma_compilation_pipeline.puml`](../state-machine/selma_compilation_pipeline.puml) |

## Rendering

Requires [PlantUML](https://plantuml.com/):

```bash
plantuml docs/activity/*.puml
```

Shared styles: `common/act_styles.puml`.

## Related Documents

- [Specification Contracts](../spec/contracts/) — normative behavioral contracts
- [State Machines](../state-machine/README.md) — FSMs and pipeline state transitions
- [C4 Architecture](../c4-model/README.md) — structural architecture
- [Design Freeze](../design/README.md) — DDD, ports & adapters, package layout
