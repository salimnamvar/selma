# Selma — C4 Architecture Diagrams

Three-level C4 model using **Clean Architecture** layering and **resource-oriented** entity IDs/names.

## Diagrams

| Level | File | Scope |
| :--- | :--- | :--- |
| **Context** | `c4_selma_context.puml` | Actors, Selma, optional Target Sources |
| **Container** | `c4_selma_container.puml` | Clients, Application, four resource stores |
| **Component** | `c4_selma_component.puml` | API, use-case clusters, repositories, optional gateway |

## Entity ID map (canonical)

| ID | Kind | Display name |
| :--- | :--- | :--- |
| `regulatory_official` | Actor | Regulatory Official |
| `compliance_representative` | Actor | Compliance Representative |
| `selma` | System | Selma |
| `target_sources` | External (optional) | Target Sources |
| `clients` | Container | Clients |
| `application` | Container | Application |
| `directives` | Store | Directives |
| `compiled_rules` | Store | Compiled Rules |
| `finding_events` | Store | Finding Events |
| `artifacts` | Store | Artifacts |
| `api` | Component (gate) | API |
| `compilation` | Component (hermetic) | Compilation |
| `inspection` | Component | Inspection |
| `findings` | Component | Findings |
| `directives_repository` | Component (infra) | Directives Repository |
| `compiled_rules_repository` | Component (infra) | Compiled Rules Repository |
| `finding_events_repository` | Component (infra) | Finding Events Repository |
| `artifacts_repository` | Component (infra) | Artifacts Repository |
| `target_sources_gateway` | Component (infra, optional) | Target Sources Gateway |

## Not C4 peers (by design)

| Concern | Where it lives instead |
| :--- | :--- |
| Conflict resolution algorithm | Domain service `ResolveConflict` used by Compilation / Inspection |
| Guidance & analytics | Findings resource reads (`guidance_only` via Directives Repository) |
| AA-01…AA-07 certification | Offline/CI tool suite; writes Artifacts only when run |
| CI/CD | Optional client of API / certify tool |
| Long-term audit export | Ops export from Finding Events / Artifacts (not a product peer) |
| Remediation ticketing | Optional notify after finding transitions (not a product peer) |
| Governance Contracts Git corpus | Removed; instances only in Directives |

## Clean Architecture mapping

| CA ring | C4 entities |
| :--- | :--- |
| Interface adapters (driving) | `clients`, `api` |
| Application use cases | `compilation`, `inspection`, `findings` (+ directive use cases via `api` → `directives_repository`) |
| Domain | Aggregates/services in design class diagrams (not all drawn as C4 components) |
| Interface adapters (driven) | `*_repository`, `target_sources_gateway` |
| Frameworks & drivers | Store containers `directives`, `compiled_rules`, `finding_events`, `artifacts` |

## Resource-oriented resources (API surface alignment)

| Resource collection | Store / component |
| :--- | :--- |
| `/directives` | `directives` + `directives_repository` |
| `/compiled-rules` (or compile side-effect) | `compiled_rules` + `compilation` |
| `/inspections` | `inspection` + `artifacts` |
| `/findings` (+ `/findings/{id}/guidance`) | `findings` + `finding_events` |
| `/artifacts` | `artifacts` |

## Design principles

- **Dual-document directives** in `directives` only; `directives_repository` owns both documents
- **Compile/runtime split**: Compilation → `compiled_rules`; Inspection never reads doctrines
- **Guidance only after findings**: Findings → doctrine via `directives_repository` (`guidance_only`)
- **Four stores by mutability**: mutable directives · immutable CG-IR · append-only events · write-once artifacts
- **Primary target path is inline**; Target Sources is optional pull

## Canonical registry

IDs, names, tech, and descriptions: `common/c4_identities.puml`.
Styles: `common/c4_styles.puml`.

## Rendering

```bash
plantuml docs/c4-model/c4_selma_context.puml
plantuml docs/c4-model/c4_selma_container.puml
plantuml docs/c4-model/c4_selma_component.puml
```

Behavior FSMs: [`../state/`](../state/README.md).
Application design freeze: [`../design/`](../design/README.md).
