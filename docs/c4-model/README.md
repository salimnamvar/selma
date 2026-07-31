# Selma — C4 Architecture Diagrams

Three-level C4 model using **Clean Architecture** layering and **resource-oriented** entity IDs/names. Every structural ID carries a **layer postfix** (or role token) so its Clean Architecture ring is obvious.

**Contract version:** 1.1.0 (aligned across all diagrams)

## C4 levels (layer by layer)

| Level | File | What it shows | What it must not show |
| :--- | :--- | :--- | :--- |
| **Context** | `c4_selma_context.puml` | People, the Selma system, optional external systems | Containers, components, databases, tech stacks |
| **Container** | `c4_selma_container.puml` | Deployable/process units inside Selma: Clients, Application, four `*_store` | Internal classes, use-case wiring, repository adapters |
| **Component** | `c4_selma_component.puml` | Clean Architecture inside **Application**: `api` → `*_application` → `*_repository` / `*_gateway` | Domain service peers, every class, package modules |

Zoom rule: each level expands one element of the level above without renaming it. IDs and display names for the same entity are identical across levels.

## Layer postfix conventions (strict)

| Kind | ID pattern | Display name pattern | Examples |
| :--- | :--- | :--- | :--- |
| Actor / system / external | `snake_case` role | Title Case | `selma`, `target_sources` |
| Container | role token | Title Case | `clients`, `application` |
| Store (frameworks & drivers) | `{resource}_store` | `{Resource} Store` | `directives_store` |
| Use-case cluster (application) | `{resource\|process}_application` | `{Name} Application` | `findings_application`, `compilation_application` |
| Driven store adapter | `{resource}_repository` | `{Resource} Repository` | `directives_repository` |
| Driven external adapter | `{external}_gateway` | `{External} Gateway` | `target_sources_gateway` |
| Driving gate | `api` | `API` | `api` |

**Dependency rule**

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Entity ID map (canonical)

| ID | Kind | Display name | CA role |
| :--- | :--- | :--- | :--- |
| `regulatory_official` | Actor | Regulatory Official | — |
| `compliance_representative` | Actor | Compliance Representative | — |
| `selma` | System | Selma | System boundary |
| `target_sources` | External (optional) | Target Sources | External system |
| `clients` | Container | Clients | Driving adapters (outer ring) |
| `application` | Container | Application | Runtime process |
| `directives_store` | Store | Directives Store | Frameworks & drivers |
| `compiled_rules_store` | Store | Compiled Rules Store | Frameworks & drivers |
| `finding_events_store` | Store | Finding Events Store | Frameworks & drivers |
| `artifacts_store` | Store | Artifacts Store | Frameworks & drivers |
| `api` | Component (gate) | API | Interface adapter (driving) |
| `directives_application` | Component (use case) | Directives Application | Application layer |
| `compilation_application` | Component (hermetic use case) | Compilation Application | Application layer |
| `inspections_application` | Component (use case) | Inspections Application | Application layer |
| `findings_application` | Component (use case) | Findings Application | Application layer |
| `directives_repository` | Component (infra) | Directives Repository | Interface adapter (driven) |
| `compiled_rules_repository` | Component (infra) | Compiled Rules Repository | Interface adapter (driven) |
| `finding_events_repository` | Component (infra) | Finding Events Repository | Interface adapter (driven) |
| `artifacts_repository` | Component (infra) | Artifacts Repository | Interface adapter (driven) |
| `target_sources_gateway` | Component (infra, optional) | Target Sources Gateway | Interface adapter (driven) |

### Naming notes

- **`compilation_application`** — hermetic compile process; publishes `compiled_rules_store` (not named `compiled_rules_application` in C4 so the hermetic process stays explicit; packages may still use `compiled_rules_*`).
- **`findings_application` vs `finding_events_store`** — findings is the resource/use-case projection; finding events is the append-only system of record.
- **`{resource}_repository`** pairs with `{resource}_store` (e.g. `directives_repository` → `directives_store`).

## Clean Architecture mapping

| CA ring | C4 entities |
| :--- | :--- |
| Frameworks & drivers (outer) | `*_store`; optional `target_sources` |
| Interface adapters (driving) | `clients`, `api` |
| Application use cases | `*_application` |
| Domain | Aggregates and domain services in class/package diagrams only (e.g. `ResolveConflict`) |
| Interface adapters (driven) | `*_repository`, `*_gateway` |

**Dependency rules on the Component diagram**

1. `clients` → `api` only  
2. `api` → `*_application` only (plus denial audit → `finding_events_repository` as gate side-effect)  
3. `*_application` → `*_repository` / `*_gateway` (and peer use cases when needed, e.g. `inspections_application` → `findings_application`)  
4. `*_repository` → `*_store`; `*_gateway` → external system  
5. Never: `api` → `*_store`; never: repository → use case; never: store → component  

## Not C4 peers (by design)

| Concern | Where it lives instead |
| :--- | :--- |
| Conflict resolution algorithm | Domain service `ResolveConflict` used by Compilation / Inspections Application |
| Guidance & analytics | Findings Application → doctrine via `directives_repository` (`guidance_only`) |
| AA-01…AA-07 certification | Offline/CI tool suite; writes Artifacts Store only when run |
| CI/CD | Optional client of API / certify tool |
| Long-term audit export | Ops export from Finding Events / Artifacts stores (not a product peer) |
| Remediation ticketing | Optional notify after finding transitions (not a product peer) |
| Governance Contracts Git corpus | Removed; instances only in Directives Store |

## Resource-oriented resources (API surface alignment)

| Resource collection | Use-case component | Store / adapter |
| :--- | :--- | :--- |
| `/directives` | `directives_application` | `directives_store` + `directives_repository` |
| `/directives/.../compilations` | `compilation_application` | `compiled_rules_store` + `compiled_rules_repository` |
| `/inspections` | `inspections_application` | evidence in `artifacts_store` + `artifacts_repository` |
| `/findings` (+ `/findings/{id}/guidance`) | `findings_application` | `finding_events_store` + `finding_events_repository` |
| `/artifacts` | (via inspections / findings / certify) | `artifacts_store` + `artifacts_repository` |

## Design principles

- **Dual-document directives** in `directives_store` only; `directives_repository` owns both documents
- **Compile/runtime split**: Compilation Application → `compiled_rules_store`; Inspections Application never reads doctrines
- **Guidance only after findings**: Findings Application → doctrine via `directives_repository` (`guidance_only`)
- **Four stores by mutability**: mutable directives · immutable CG-IR · append-only events · write-once artifacts
- **Primary target path is inline**; Target Sources is optional pull
- **Application layer is mandatory**: resource mutations go through `*_application`, not `api` → repository (except capability-denial audit at the gate)

**Finding vs Finding Events**

- Finding — current resource projection (`findings_application`)
- Finding Events — immutable history stream (`finding_events_store`)
- Finding state is loaded from the event stream for lifecycle enforcement

**Finding Events Store technology**

- Technology: PostgreSQL (append-only table)
- Rationale: consistent with Directives Store, lower operational complexity
- Migration path: can migrate to Kafka if throughput demands it

## Package alignment (`{resource}_{layer}`)

| Package module | C4 component |
| :--- | :--- |
| `directives_application` / `directives_domain` | `directives_application` (+ domain not drawn) |
| `compiled_rules_application` / hermetic compile | `compilation_application` |
| `inspections_application` / `inspections_domain` | `inspections_application` |
| `findings_application` / `findings_domain` | `findings_application` |
| `directives_infrastructure` | `directives_repository` |
| `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `findings_infrastructure` (events) | `finding_events_repository` |
| `artifacts_infrastructure` | `artifacts_repository` |
| `inspections_infrastructure` (targets) | `target_sources_gateway` |
| `rest_interface` / CLI / TUI | `api` + container `clients` |
| `conflicts_domain` | in-process only (not a C4 component) |

## Canonical registry

IDs, names, tech, and descriptions: `common/c4_identities.puml` (Contract: 1.1.0).  
Styles: `common/c4_styles.puml` (Contract: 1.1.0).

All C4 diagrams are aligned to Contract version 1.1.0.

## Rendering

```bash
plantuml docs/c4-model/c4_selma_context.puml
plantuml docs/c4-model/c4_selma_container.puml
plantuml docs/c4-model/c4_selma_component.puml
```

Behavior FSMs: [`../state/`](../state/README.md).  
Implementation structure: [`../class/`](../class/README.md), [`../package/`](../package/README.md).
