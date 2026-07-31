# Selma — State Machine Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

Canonical state machines describing how state evolves inside Selma's components.
**C4** ([`../c4-model/`](../c4-model/README.md)) is the structural source of truth;
this directory describes behavior only. Component names in diagram headers match
C4 IDs (`api`, `*_application`, `*_repository`, `*_gateway`, `*_store`).
Non-peers: `ResolveConflict` (domain), `certification_tool` (offline/CI).

Read with [`contracts/`](../spec/contracts/) for the full behavioral contracts.
The normative finding FSM contract is [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/).

## Catalog

| File | Machine | Spec authority | Normative? |
| :--- | :--- | :--- | :---: |
| `selma_finding_lifecycle.puml` | Finding Lifecycle | [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) | **Yes** |
| `selma_directive_lifecycle.puml` | Directive Lifecycle | [`directive/lifecycle.yaml`](../spec/contracts/directive/lifecycle.yaml) | Extracted |
| `selma_compilation_pipeline.puml` | Compilation / CG-IR | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) | Extracted |
| `selma_inspection_pipeline.puml` | Inspection Execution | [`inspection/pipeline.yaml`](../spec/contracts/inspection/pipeline.yaml) | Extracted |
| `selma_conflict_resolution.puml` | Conflict Resolution | [`conflict/detection.yaml`](../spec/contracts/conflict/detection.yaml) | Extracted |
| `selma_architecture_certification.puml` | Architectural Certification | [`certification/gates.yaml`](../spec/contracts/certification/gates.yaml) | Extracted |
| `selma_authorization.puml` | Capability Authorization | [`authorization/capabilities.yaml`](../spec/contracts/authorization/capabilities.yaml) | Extracted |
| `selma_artifact_lifecycle.puml` | Artifact Lifecycle | [`data_stores/`](../spec/contracts/data_stores/) | Extracted |
| `selma_hlc_clock.puml` | HLC Event Ordering | [`data_stores/finding_events_store.yaml`](../spec/contracts/data_stores/finding_events_store.yaml) | Detail view |
| `selma_cgir_hash_chain.puml` | CG-IR Hash & Reuse | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) | Detail view |
| `selma_machine_interaction.puml` | Machine Interaction Overview | [`../c4-model/c4_selma_component.puml`](../c4-model/c4_selma_component.puml) | Overview |
| `common/sm_styles.puml` | Shared theme | — | — |

**Normative note:** The contract tree defines **one** explicit state machine as normative (Finding FSM in [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/)). All other machines are extracted from their respective contracts and must not invent behavior that contradicts the contracts.

## Design Principles

- **Contract dominance** — diagrams are proposals; Finding FSM in [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) is non-negotiable
- **Compile-time / runtime separation** — executable rules compiled to CG-IR; policy doctrines read at runtime for guidance only, never for finding FSM transitions
- **Capability + SoD before mutation** — every human edge is capability-gated
- **No silent failures** — typed findings, denial audits, or explicit abort states
- **Humans never close findings** — only System after Verified or Waived

## Rendering

Requires [PlantUML](https://plantuml.com/):

```bash
plantuml docs/state/*.puml
```

Shared styles: `common/sm_styles.puml`.

## Related Documents

- [Specification Contracts](../spec/contracts/) — normative behavioral contracts
- [C4 Architecture](../c4-model/README.md) — structural architecture
- [Schema Contracts](../schema/) — data structure contracts
- [Class Diagrams](../class/README.md) — domain model
- [Package Diagrams](../package/README.md) — Clean Architecture layout
