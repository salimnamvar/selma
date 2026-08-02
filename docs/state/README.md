# Selma — State Machine Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *How state evolves* inside owned components and pipelines |
| **Owns 100%** | FSM/pipeline **visualization**: states, transitions, guards, stream events; diagram headers (`Source`, `C4`, `Contract`); machine interaction overview |
| **Does not own** | Peer inventing / dependency graph (C4) · package trees / ports (package) · zones / TLS / RPO (deployment) · normative text (spec owns; diagrams extract only) |
| **Join key** | C4 peer IDs in headers; non-peers labeled `(domain)` / `(offline)` |

**Authority:** diagrams are extracted views of [`../spec/contracts/`](../spec/contracts/) (and schema shapes where cited). They must not invent behavior that contradicts contracts.  
**Not design principles of this view:** dual-document split, hermeticity, SoD rules, capability matrix — those live in **spec**; machines only show the resulting transitions.

## Catalog

| File | Machine | C4 owners (header) | Spec authority | Normative? |
| :--- | :--- | :--- | :--- | :---: |
| `selma_finding_lifecycle.puml` | Finding Lifecycle | `findings_application` → `finding_events_repository` → `finding_events_store` | [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) | **Yes** |
| `selma_directive_lifecycle.puml` | Directive Lifecycle | `api` → `directives_application` → `directives_repository` → `directives_store` | [`directive/lifecycle.yaml`](../spec/contracts/directive/lifecycle.yaml), [`identity.yaml`](../spec/contracts/directive/identity.yaml) | Extracted |
| `selma_compilation_pipeline.puml` | Compilation / CG-IR | `compilation_application` → `compiled_rules_repository` → `compiled_rules_store` | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml), [`hermetic_boundary.yaml`](../spec/contracts/compilation/hermetic_boundary.yaml) | Extracted |
| `selma_inspection_pipeline.puml` | Inspection Execution | `inspections_application` → `artifacts_repository` → `artifacts_store`; birth via `findings_application` | [`inspection/pipeline.yaml`](../spec/contracts/inspection/pipeline.yaml), [`finding_contract.yaml`](../spec/contracts/inspection/finding_contract.yaml) | Extracted |
| `selma_conflict_resolution.puml` | Conflict Resolution | `ResolveConflict` (domain · not peer); used by `compilation_application` \| `inspections_application` | [`conflict/detection.yaml`](../spec/contracts/conflict/detection.yaml), [`precedence.yaml`](../spec/contracts/conflict/precedence.yaml) | Extracted |
| `selma_architecture_certification.puml` | Architectural Certification | `certification_tool` (offline · not peer) → `artifacts_repository` → `artifacts_store` | [`certification/gates.yaml`](../spec/contracts/certification/gates.yaml) **AA-01…AA-09** | Extracted |
| `selma_authorization.puml` | Capability Authorization | `api` gate; denials → `finding_events_repository` → `finding_events_store` | [`authorization/capabilities.yaml`](../spec/contracts/authorization/capabilities.yaml), [`role_matrix.yaml`](../spec/contracts/authorization/role_matrix.yaml) | Extracted |
| `selma_artifact_lifecycle.puml` | Artifact Lifecycle | `artifacts_repository` → `artifacts_store` (+ CAS/events peers as producers) | [`data_stores/`](../spec/contracts/data_stores/) | Extracted |
| `selma_hlc_clock.puml` | HLC Event Ordering | `finding_events_repository` / `finding_events_store` | [`finding_events_store.yaml`](../spec/contracts/data_stores/finding_events_store.yaml) | Detail |
| `selma_cgir_hash_chain.puml` | CG-IR Hash & Reuse | `compilation_application` → `compiled_rules_repository` → `compiled_rules_store` | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) | Detail |
| `selma_machine_interaction.puml` | Machine Interaction Overview | handoffs among machines above (C4 IDs on states) | contracts + C4 structure (overview only) | Overview |
| `common/sm_styles.puml` | Shared theme | — | — | — |

**Normative note:** Only the Finding FSM under [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) is an explicit normative state machine in contracts. All other machines are extracted and must stay consistent with their Source contracts.

## View rules (not product design principles)

- **Contract dominance** — diagrams visualize contracts; they do not supersede them  
- **Header schema** — every machine file uses `Title` / `Source` / `C4` / `Contract: 1.1.0` per [`../standards/diagram_header.schema.md`](../standards/diagram_header.schema.md)  
- **C4 IDs only** — peer IDs from registry; non-peers labeled `(domain)` / `(offline)`  
- **No structural redraw** — do not invent containers, packages, or zones here  

## Rendering

```bash
plantuml docs/state/*.puml
```

Shared styles: `common/sm_styles.puml`.

## Related documents

- [Specification Contracts](../spec/contracts/) — normative behavior  
- [C4 Architecture](../c4-model/README.md) — structural peers  
- [Schema](../schema/) — rule + policy data shapes  
- [Package](../package/README.md) · [Deployment](../deployment/README.md)  
- [View concerns](../standards/view_concerns.md)
