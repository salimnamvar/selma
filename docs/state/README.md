# Selma — State Machine Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *How state evolves* inside owned components and pipelines |
| **Owns 100%** | FSM/pipeline **visualization**: states, transitions, guards, stream events; `SM-NNN` filenames; headers (`Source`, `C4`, `Package`, `Contract`) |
| **Does not own** | Peer inventing (C4) · package trees/ports invent (package) · zones/TLS/RPO (deployment) · normative prose (spec) |
| **Join key** | C4 peer IDs + package module names in headers; non-peers labeled `(domain)` / `(offline)` |

**No PlantUML `note` blocks.** Anything that would be a note is encoded as state body fields, transition guards/actions, or lives only in the **Source** contract. Notes mean unfinished design.

## Naming (aligned with other views)

| View | File pattern | Example |
| :--- | :--- | :--- |
| C4 | `c4_selma_{level}.puml` | `c4_selma_component.puml` |
| Package | `pkg_NNN_*.puml` | `pkg_001_clean_architecture.puml` |
| Deployment | `dep_NNN_*.puml` | `dep_001_production.puml` |
| **State** | `sm_NNN_*.puml` | `sm_001_finding_lifecycle.puml` |

| Element | Convention |
| :--- | :--- |
| Diagram ID | `SM-NNN` in `@startuml`, title, footer |
| Title | `**SM-NNN — {Name}**` + `C4: {owners}` subtitle |
| States | PascalCase conditions (`Open`, `Queued`) |
| Events | PascalCase past-tense (`FindingCreated`, `WaiverGranted`) |
| Guards / actions | lowerCamelCase `[guard]` / `/ action()` |
| C4 IDs | registry peers only (`findings_application`, not engines) |

## Catalog

| ID | File | Machine | C4 owners | Package | Spec authority | Normative? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **SM-001** | [`sm_001_finding_lifecycle.puml`](sm_001_finding_lifecycle.puml) | Finding Lifecycle | `findings_application` → `finding_events_repository` → `finding_events_store` | `findings_*` · `FindingFsm` | [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) | **Yes** |
| **SM-002** | [`sm_002_directive_lifecycle.puml`](sm_002_directive_lifecycle.puml) | Directive Lifecycle | `api` → `directives_application` → `directives_repository` → `directives_store` | `directives_*` | [`directive/`](../spec/contracts/directive/) | Extracted |
| **SM-003** | [`sm_003_compilation_pipeline.puml`](sm_003_compilation_pipeline.puml) | Compilation / CG-IR | `compilation_application` → `compiled_rules_repository` → `compiled_rules_store` | `compiled_rules_*` | [`compilation/`](../spec/contracts/compilation/) | Extracted |
| **SM-004** | [`sm_004_inspection_pipeline.puml`](sm_004_inspection_pipeline.puml) | Inspection Execution | `inspections_application` → `artifacts_repository`; `FindingOpenPort` | `inspections_*` | [`inspection/`](../spec/contracts/inspection/) | Extracted |
| **SM-005** | [`sm_005_conflict_resolution.puml`](sm_005_conflict_resolution.puml) | Conflict Resolution | `ResolveConflict` (domain · not peer) | `conflicts_domain` | [`conflict/`](../spec/contracts/conflict/) | Extracted |
| **SM-006** | [`sm_006_architecture_certification.puml`](sm_006_architecture_certification.puml) | Architectural Certification | `certification_tool` (offline) → `artifacts_repository` | offline tool | [`certification/gates.yaml`](../spec/contracts/certification/gates.yaml) AA-01…AA-09 | Extracted |
| **SM-007** | [`sm_007_authorization.puml`](sm_007_authorization.puml) | Capability Authorization | `api`; denials → `finding_events_repository` | `*_interface` · `CapabilityEnforcer` | [`authorization/`](../spec/contracts/authorization/) | Extracted |
| **SM-008** | [`sm_008_artifact_lifecycle.puml`](sm_008_artifact_lifecycle.puml) | Artifact Lifecycle | `artifacts_repository` → `artifacts_store` | `artifacts_infrastructure` | [`data_stores/artifacts_store.yaml`](../spec/contracts/data_stores/artifacts_store.yaml) | Extracted |
| **SM-009** | [`sm_009_hlc_clock.puml`](sm_009_hlc_clock.puml) | Hybrid Logical Clock | `finding_events_repository` → `finding_events_store` | `platform_infrastructure` | [`finding_events_store.yaml`](../spec/contracts/data_stores/finding_events_store.yaml) | Detail |
| **SM-010** | [`sm_010_cgir_hash_chain.puml`](sm_010_cgir_hash_chain.puml) | CG-IR Hash Composition | `compilation_application` → `compiled_rules_repository` | `compiled_rules_*` | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) | Detail |
| **SM-011** | [`sm_011_machine_interaction.puml`](sm_011_machine_interaction.puml) | Machine Interaction Overview | handoffs among SM-001…SM-010 | — | contracts + C4 | Overview |
| — | [`common/sm_styles.puml`](common/sm_styles.puml) | Shared theme | — | — | — | — |

## View rules

- **Contract dominance** — diagrams extract contracts; they never supersede them  
- **Header schema** — `Title` / `Source` / `C4` / `Package` / `Contract: 1.1.0`  
- **No notes** — invariants appear as `**entry**` / `**forbidden**` / guards / actions  
- **No structural redraw** — do not invent containers, packages, or zones as state boxes  

## Rendering

```bash
plantuml docs/state/sm_*.puml
```

## Related

- [Spec contracts](../spec/contracts/) · [C4](../c4-model/README.md) · [Package](../package/README.md) · [Deployment](../deployment/README.md)  
- [View concerns](../standards/view_concerns.md)
