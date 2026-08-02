# Selma — State Machine Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.3.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *How state evolves* inside owned components and pipelines |
| **Owns 100%** | State machine **visualization**: states, transitions, guards, stream events; full-word filenames; shared `common/` styles and identities |
| **Does not own** | Peer inventing (C4) · package trees/ports invent (package) · zones/TLS/RPO (deployment) · normative prose (spec) |
| **Join key** | C4 peer IDs + package module names in headers; non-peers labeled `(domain)` / `(offline)` |

**No PlantUML `note` blocks.** No short-form names in filenames, titles, state labels, or transition text (no `sm_`, `SM-`, `SoD`, `CG-IR`, `HLC`, `CAS`, `RO`, `CR` as labels). Formal contract IDs (`INV-*`, `TR-*`, `US-*`, `AA-01`…) may appear as catalog references.

## Source layout (like C4 `common/` and package `common/`)

| Path | Role | Edit when… |
| :--- | :--- | :--- |
| [`common/state_styles.puml`](common/state_styles.puml) | Skinparams + **semantic color macros** shared with C4 palette | Visual language / harmony |
| [`common/state_identities.puml`](common/state_identities.puml) | C4 owner strings, actor full names, diagram titles | Rename labels / owners |
| [`state_machine_NNN_*.puml`](.) | One machine per file (orchestrates includes only at top) | Behavior extracted from contracts |

**Include order:** `state_styles` → `state_identities` → diagram body.

## Color harmony (CA MACRO + state MICRO)

**SSoT:** [`../standards/common/ca_palette.puml`](../standards/common/ca_palette.puml)  
State styles include the palette and re-export `$STATE_COLOR_*` as **lifecycle micro** aliases of CA layers:

| `$STATE_COLOR_*` (micro) | CA MACRO | Hex | Typical state use |
| :--- | :--- | :--- | :--- |
| `RESOURCE` | Interface | `#0288D1` | Durable resource hubs (Created, Open) |
| `PROCESS` | Application | `#00897B` | Pure pipelines, automated stages |
| `STORE` | Frameworks | `#2E7D32` | Published, Verified, durable success |
| `PENDING` | Infrastructure | `#EF6C00` | Draft, Queued, awaits human |
| `DOMAIN` | Domain | `#7B1FA2` | ResolveConflict path (not a C4 peer) |
| `GATE` | Gate (micro) | `#C62828` | Denied, Failed, Rejected |
| `TERMINAL` | Terminal (micro) | `#37474F` | Closed, Dismissed, Archived |
| `EXTERNAL` | External | `#607D8B` | Offline certification tool |
| `ACTOR` | Actors | `#3F51B5` | Rare actor emphasis |

**Rule:** never invent hex in diagram bodies — only `$STATE_COLOR_*` macros.

## Naming (full words only)

| View | File pattern | Example |
| :--- | :--- | :--- |
| C4 | `c4_selma_{level}.puml` | `c4_selma_component.puml` |
| Package | `pkg_NNN_*.puml` | `pkg_001_clean_architecture.puml` |
| Deployment | `dep_NNN_*.puml` | `dep_001_production.puml` |
| **State** | `state_machine_NNN_*.puml` | `state_machine_001_finding_lifecycle.puml` |

| Element | Convention |
| :--- | :--- |
| Diagram ID | `State Machine NNN` in `@startuml`, title, footer |
| Title | `**State Machine NNN — {Full Name}**` + `C4: {owners}` |
| States | PascalCase full words (`PendingVerification`, not `PV`) |
| Events | PascalCase past-tense full words (`FindingCreated`, `CompiledRulesPublished`) |
| Guards / actions | lowerCamelCase full words (`[actorNotInCreatorProvenance]`) |
| Actors | `Regulatory Official`, `Compliance Representative` (never short roles) |
| C4 IDs | registry peers only (`findings_application`) |

## Catalog

| ID | File | Machine | C4 owners | Package | Spec authority | Normative? |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **001** | [`state_machine_001_finding_lifecycle.puml`](state_machine_001_finding_lifecycle.puml) | Finding Lifecycle | `findings_application` → `finding_events_repository` → `finding_events_store` | `findings_application` / `findings_domain` | [`finding_lifecycle/`](../spec/contracts/finding_lifecycle/) | **Yes** |
| **002** | [`state_machine_002_directive_lifecycle.puml`](state_machine_002_directive_lifecycle.puml) | Directive Lifecycle | `api` → `directives_application` → `directives_repository` → `directives_store` | `directives_*` | [`directive/`](../spec/contracts/directive/) | Extracted |
| **003** | [`state_machine_003_compilation_pipeline.puml`](state_machine_003_compilation_pipeline.puml) | Compilation Pipeline | `compilation_application` → `compiled_rules_repository` → `compiled_rules_store` | `compiled_rules_*` | [`compilation/`](../spec/contracts/compilation/) | Extracted |
| **004** | [`state_machine_004_inspection_pipeline.puml`](state_machine_004_inspection_pipeline.puml) | Inspection Execution | `inspections_application` → `artifacts_repository`; `FindingOpenPort` | `inspections_*` | [`inspection/`](../spec/contracts/inspection/) | Extracted |
| **005** | [`state_machine_005_conflict_resolution.puml`](state_machine_005_conflict_resolution.puml) | Conflict Resolution | `ResolveConflict` (domain · not peer) | `conflicts_domain` | [`conflict/`](../spec/contracts/conflict/) | Extracted |
| **006** | [`state_machine_006_architecture_certification.puml`](state_machine_006_architecture_certification.puml) | Architectural Certification | `certification_tool` (offline) → `artifacts_repository` | offline tool | [`certification/gates.yaml`](../spec/contracts/certification/gates.yaml) | Extracted |
| **007** | [`state_machine_007_authorization.puml`](state_machine_007_authorization.puml) | Capability Authorization | `api`; denials → `finding_events_repository` | `rest_interface` · `CapabilityEnforcer` | [`authorization/`](../spec/contracts/authorization/) | Extracted |
| **008** | [`state_machine_008_artifact_lifecycle.puml`](state_machine_008_artifact_lifecycle.puml) | Artifact Lifecycle | `artifacts_repository` → `artifacts_store` | `artifacts_infrastructure` | [`artifacts_store.yaml`](../spec/contracts/data_stores/artifacts_store.yaml) | Extracted |
| **009** | [`state_machine_009_hybrid_logical_clock.puml`](state_machine_009_hybrid_logical_clock.puml) | Hybrid Logical Clock | `finding_events_repository` → `finding_events_store` | `platform_infrastructure` | [`finding_events_store.yaml`](../spec/contracts/data_stores/finding_events_store.yaml) | Detail |
| **010** | [`state_machine_010_compiled_rules_hash_composition.puml`](state_machine_010_compiled_rules_hash_composition.puml) | Compiled Rules Hash Composition | `compilation_application` → `compiled_rules_repository` | `compiled_rules_*` | [`compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) | Detail |
| **011** | [`state_machine_011_machine_interaction.puml`](state_machine_011_machine_interaction.puml) | Machine Interaction Overview | handoffs among 001…010 | — | contracts + C4 | Overview |

## View rules

- **Contract dominance** — diagrams extract contracts; they never supersede them  
- **Header schema** — `Title` / `Source` / `C4` / `Package` / `Contract: 1.3.0`  
- **No notes** — invariants as `**entry**` / `**forbidden**` / guards / actions  
- **No short forms** — full words in filenames and diagram text  
- **Colors only via macros** from `state_styles.puml`  

## Rendering

```bash
plantuml docs/state/state_machine_*.puml
```

## Related

- [Spec contracts](../spec/contracts/) · [C4](../c4-model/README.md) · [Package](../package/README.md) · [Deployment](../deployment/README.md)  
- [View concerns](../standards/view_concerns.md)
