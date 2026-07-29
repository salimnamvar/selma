# Selma — State Machine Diagrams

Canonical state machines describing how state evolves inside Selma's components. C4 describes structure; this directory describes behavior.

Read with [SPECIFICATION.md](../spec/SPECIFICATION.md) for the full behavioral contract.

## Catalog

| File | Machine | Spec authority | Normative? |
| :--- | :--- | :--- | :---: |
| `selma_finding_lifecycle.puml` | Finding Lifecycle | §3.1 | **Yes** |
| `selma_directive_lifecycle.puml` | Directive Lifecycle | §2.2, §2.2.4, §2.3 | Extracted |
| `selma_compilation_pipeline.puml` | Compilation / CG-IR | §2.4–§2.9, §3.4–§3.5 | Extracted |
| `selma_inspection_pipeline.puml` | Inspection Execution | §2.10–§2.13, §3.3, §3.6–§3.7 | Extracted |
| `selma_conflict_resolution.puml` | Conflict Resolution | §2.15, §2.15.2 | Extracted |
| `selma_architecture_certification.puml` | Architectural Certification | §9.9 AA-01…AA-07 | Extracted |
| `selma_authorization.puml` | Capability Authorization | §3.2, §3.2.1 | Extracted |
| `selma_artifact_lifecycle.puml` | Artifact Lifecycle | §2.1, §2.6, §3.5–§3.6 | Extracted |
| `selma_hlc_clock.puml` | HLC Event Ordering | §2.14 | Detail view |
| `selma_cgir_hash_chain.puml` | CG-IR Hash & Reuse | §2.6 | Detail view |
| `selma_machine_interaction.puml` | Machine Interaction Overview | C4 + ownership | Overview |
| `common/sm_styles.puml` | Shared theme | — | — |

**Normative note:** The specification defines **one** explicit state machine (Finding FSM §3.1). All other machines are extracted from normative pipeline prose and must not invent behavior that contradicts the spec.

## Design Principles

- **Specification dominance** — diagrams are proposals; §3.1 Finding FSM is non-negotiable
- **Compile-time / runtime separation** — executable rules compiled to CG-IR; policy doctrines read at runtime for guidance only, never for finding FSM transitions
- **Capability + SoD before mutation** — every human edge is capability-gated
- **No silent failures** — typed findings, denial audits, or explicit abort states
- **Humans never close findings** — only System after Verified or Waived

## Rendering

Requires [PlantUML](https://plantuml.com/):

```bash
plantuml docs/state-machine/*.puml
```

Shared styles: `common/sm_styles.puml`.

## Related Documents

- [SPECIFICATION.md](../spec/SPECIFICATION.md) — normative behavioral contract
- [User_Stories.md](../spec/User_Stories.md) — story bindings
- [C4 Architecture](../c4-model/README.md) — structural architecture
