# Selma — Use Case Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.2.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *What actor goals* the product fulfills and how they **group** |
| **Owns 100%** | Actor catalog (C4 persons); use-case **groups** by `{resource}_application` / gate / offline tool; **ROD use-case names** identical to package leaves and class `<<Use Case>>` types; actor associations; `<<include>>` / `<<extend>>` among use cases; shared `common/uc_*` styles and identities |
| **Does not own** | Peer inventing (C4) · package trees/ports (package/) · method signatures (class/) · zones/TLS/RPO (deployment/) · FSM states/transitions (state/) · capability catalog / pre-post acceptance (spec/) · pipeline stage inventories (state/activity) |
| **Join key** | C4 peer IDs + package module names + ROD use-case PascalCase names (identical strings across package / class / use case) |

**No PlantUML `note` blocks.** Preconditions, postconditions, and stories live under [`../spec/contracts/`](../spec/contracts/) (`stories:` / `US-*`). No short-form actor labels (`RO`, `CR`).

## Source layout (like package / class / state `common/`)

| Path | Role | Edit when… |
| :--- | :--- | :--- |
| [`common/uc_styles.puml`](common/uc_styles.puml) | Skinparams + **CA palette** aliases | Visual language / harmony |
| [`common/uc_identities.puml`](common/uc_identities.puml) | Actors, group titles, ROD names, diagram IDs | Rename labels / peers / use cases |
| [`common/uc_section_*.puml`](common/) | Use-case ovals + include edges by group | Inventory of goals per package |
| [`uc_NNN_*.puml`](.) | Orchestrators only (actors + associations) | Actor participation |

**Include order:** `uc_styles` → `uc_identities` → declare **only connected** C4/System actors → `uc_section_*` → associations in orchestrator.

```bash
plantuml docs/usecase/uc_*.puml
python scripts/check_design_alignment.py
```

## Color harmony (CA MACRO)

**SSoT:** [`../standards/common/ca_palette.puml`](../standards/common/ca_palette.puml) via [`common/uc_styles.puml`](common/uc_styles.puml).

| Element | CA MACRO | Fill / border |
| :--- | :--- | :--- |
| Actors | Actors | `#E8EAF6` / `#3F51B5` |
| Application use cases / groups | Application | `#E0F2F1` / `#00897B` |
| Interface gate group | Interface | `#E1F5FE` / `#0288D1` |
| Domain service group | Domain | `#F3E5F5` / `#7B1FA2` |
| Offline / system / external actors | External | `#ECEFF1` / `#607D8B` |
| Gate use cases (deny / segregation) | Gate (micro) | `#FFEBEE` / `#C62828` |
| Hermetic validation use case | Hermetic (micro) | `#FFFDE7` / `#F9A825` |

**Rule:** never invent hex in diagram bodies — only palette macros / `$UC_*` aliases.

## Identity binding (groups — identical across views)

**SSoT for group display titles:** [`../package/common/pkg_identities.puml`](../package/common/pkg_identities.puml)  
Use-case identities **include** that file. Do not invent group strings.

| UC | Group rectangle (macro) | Package package | Class package box | C4 component |
| :--- | :--- | :--- | :--- | :--- |
| UC-001 | `$TITLE_APP_DIR` | `directives_application` + C4 dual | same | `directives_application` |
| UC-002 | `$TITLE_APP_CR` | `compiled_rules_application` + C4 dual | same | `compilation_application` |
| UC-003 | `$TITLE_APP_INS` | `inspections_application` + C4 dual | same | `inspections_application` |
| UC-004 / UC-007 | `$TITLE_APP_FIND` | `findings_application` + C4 dual | same | `findings_application` |
| UC-005 | `$TITLE_DOM_CON` + `$TITLE_APP_FIND` | `conflicts_domain` + findings app | same | domain not peer · `findings_application` |
| UC-006 | `$TITLE_IF_REST` | `rest_interface (C4: api)` | same | `api` |
| UC-008 | `$TITLE_OFFLINE_CERT` | offline (not a CA ring) | — | offline · not peer |
| Outer ring | `$TITLE_APPLICATION` | `<<application>> *_application` | application layer | container `application` |

**Oval names** = package application leaves = class `<<Use Case>>` type names (ROD Verb+Resource).

## Naming (ROD + Clean Architecture)

| Element | Convention | Examples |
| :--- | :--- | :--- |
| Diagram ID | `UC-NNN` / `Use Case NNN` | `UC-001`, `Use Case 001 — Directives` |
| File | `uc_NNN_{resource}.puml` | `uc_004_findings.puml` |
| Group rectangle | **Only** `$TITLE_APP_*` / `$TITLE_IF_*` / `$TITLE_DOM_*` / `$TITLE_OFFLINE_CERT` from package identities | never invent “Selma Application” or bare drifted labels |
| Use-case oval | PascalCase **Verb + Resource** = class / package leaf | `CreateDirective`, `TransitionFinding`, `CompileDirectives` |
| Actors | Full C4 person names only (+ System when connected) | `Regulatory Official`, `Compliance Representative` |
| Non-peers | Domain / offline groups from package macros | `$TITLE_DOM_CON`, `$TITLE_OFFLINE_CERT` |

**Forbidden on this view:** pipeline stage names as use cases (`NormalizeTarget`, `Materialize…`), FSM state names (`PendingVerification`), store mutability prose, capability catalog tables, C4 Rel graphs, short forms (`CG-IR`, `SoD`, `RO`), **invented group names**.

## Actor catalog (identical to C4)

C4 context/registry persons are the **only** product actors. Names match
[`../c4-model/common/c4_identities.puml`](../c4-model/common/c4_identities.puml)
and `c4_registry.yaml` `peers.actors`.

| Actor | C4 peer ID | Type | Rule |
| :--- | :--- | :--- | :--- |
| Regulatory Official | `regulatory_official` | Person | C4 only |
| Compliance Representative | `compliance_representative` | Person | C4 only |
| System | — (not a C4 person) | Automated | Allowed for automated goals only |

**Rules:**

1. Do **not** invent persons (no continuous-integration client, no ops roles).
2. Each diagram declares **only** actors that have at least one association to a use case — no floating actors.
3. `System` is not a C4 person peer; it may appear when the goal is automated (outbox, open findings, offline certification run, domain resolve during pipeline).
4. Target Sources, certification tool, and stores are **not** actors (C4 external/system/offline placement only).

## Diagram & use-case inventory

| ID | File | Group (package) | C4 | ROD use cases (must match package + class) |
| :--- | :--- | :--- | :--- | :--- |
| **UC-001** | [uc_001_directives.puml](uc_001_directives.puml) | `$TITLE_APP_DIR` | `directives_application` | `CreateDirective`, `GetDirective`, `ListDirectives`, `UpdateDirective`, `LifecycleTransitions` (+ `Retire` / `Fork` / `Merge` / `Split` / `Restore`) |
| **UC-002** | [uc_002_compilation.puml](uc_002_compilation.puml) | `$TITLE_APP_CR` | `compilation_application` | `CompileDirectives`, `PublishCompiledRules`, `DrainOutbox`, `ValidateDirectiveDocuments` |
| **UC-003** | [uc_003_inspection.puml](uc_003_inspection.puml) | `$TITLE_APP_INS` | `inspections_application` | `CreateInspection`, `GetInspection`, `RunInspectionPipeline` |
| **UC-004** | [uc_004_findings.puml](uc_004_findings.puml) | `$TITLE_APP_FIND` | `findings_application` | full findings ROD catalog |
| **UC-005** | [uc_005_conflict.puml](uc_005_conflict.puml) | `$TITLE_DOM_CON` + `$TITLE_APP_FIND` | domain + `findings_application` | `ResolveConflict`, `ReviewConflictArtifact` |
| **UC-006** | [uc_006_authorization.puml](uc_006_authorization.puml) | `$TITLE_IF_REST` | `api` | `AuthenticateActor`, `CheckCapability`, `AppendDenial`, `EnforceSegregationOfDuties` |
| **UC-007** | [uc_007_guidance.puml](uc_007_guidance.puml) | `$TITLE_APP_FIND` (slice) | `findings_application` | `GetFindingGuidance`, `ListFindingAggregates` |
| **UC-008** | [uc_008_certification.puml](uc_008_certification.puml) | `$TITLE_OFFLINE_CERT` | offline · not peer | `RunArchitecturalCertification` + AA-01…AA-09 · System only |

## Conventions

| Arrow | Meaning |
| :--- | :--- |
| `-->` solid | Actor participates in use case |
| `..>` dashed `<<include>>` | Mandatory sub-goal |
| `..>` dashed `<<extend>>` | Optional / conditional sub-goal |

## Related views

| View | Relationship |
| :--- | :--- |
| [C4](../c4-model/README.md) | Peer IDs and actor persons |
| [Package](../package/README.md) | Application packages and UC component leaves |
| [Class](../class/README.md) | `<<Use Case>>` types and method shapes |
| [State](../state/README.md) | How lifecycle / pipelines evolve (not actor goals) |
| [Deployment](../deployment/README.md) | Where processes run (not goals) |
| [Spec contracts](../spec/contracts/) | Normative pre/post and stories |
