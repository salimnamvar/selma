# Selma — C4 Architecture Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.3.0` · This directory is the **structural SSoT** (product peers only)

Three-level C4 model using Clean Architecture layering and resource-oriented entity IDs.  
IDs MUST match [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml). Diagrams include `Contract: 1.3.0` headers.

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *What* product peers exist and how they **depend** |
| **Owns 100%** | Peer IDs, display names, tech tags, structural descriptions, containers/components/stores, dependency rule, system/process boundaries, non-peer **placement** (not algorithm) |
| **Does not own** | Package trees / ports / classes · network zones / TLS / RPO / HA · FSM tables / locks / capability matrix · dual-document or hermetic **behavior** text |
| **Join key** | Registry peer IDs only |

**Do not restate** design principles owned by package, deployment, state, or `spec/contracts/`. Link instead — see [`view_concerns.md`](../standards/view_concerns.md).

| Sibling view | Owns |
| :--- | :--- |
| [`../package/`](../package/README.md) | *How* code modules and ports implement peers |
| [`../deployment/`](../deployment/README.md) | *Where* peers run (zones, TLS, failure domains, RPO) |
| [`../state/`](../state/README.md) | *How state evolves* (FSMs extracted from contracts) |
| [`../spec/contracts/`](../spec/README.md) | Normative behavior |

## C4 levels

| Level | File | Shows | Must not show |
| :--- | :--- | :--- | :--- |
| **Context** | `c4_selma_context.puml` | People, Selma system, optional external systems | Containers, components, databases, tech stacks |
| **Container** | `c4_selma_container.puml` | Clients, Application, four `*_store` | Internal classes, use-case wiring, repository adapters |
| **Component** | `c4_selma_component.puml` | Inside Application: `api` → `*_application` → `*_repository` / `*_gateway`; stores inside Selma, outside Application process | Domain service peers, every class, package modules |

Zoom rule: each level expands one element of the level above **without renaming it**. IDs and display names for the same entity are identical across levels.

**Boundary encoding:** Component nests `Container_Boundary(application)` inside `System_Boundary(selma)`. Stores are `ContainerDb` peers of the Application process. Only `*_repository` / `*_gateway` connect to stores or `target_sources`.

## Layer postfix conventions

| Kind | ID pattern | Display name pattern | Examples |
| :--- | :--- | :--- | :--- |
| Actor / system / external | `snake_case` role | Title Case | `selma`, `target_sources` |
| Container | role token | Title Case | `clients`, `application` |
| Store | `{resource}_store` | `{Resource} Store` | `directives_store` |
| Use-case cluster | `{resource\|process}_application` | `{Name} Application` | `findings_application`, `compilation_application` |
| Driven store adapter | `{resource}_repository` | `{Resource} Repository` | `directives_repository` |
| Driven external adapter | `{external}_gateway` | `{External} Gateway` | `target_sources_gateway` |
| Driving gate | `api` | `API` | `api` |

**Dependency rule**

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

Narrow structural exceptions (edges only; behavior in contracts / package):

1. `api` → `finding_events_repository` for **DenialAuditPort** path (capability-denial audit only).
2. `inspections_application` → `findings_application` via **FindingOpenPort** (peer application port; not a separate C4 box).
3. Compile coupling is **store-mediated**: `directives_application` enqueues `compile_request` outbox; `compilation_application` drains it — **no** direct app→app compile edge on the Component diagram.

Never: `api` → `*_store`; repository → use case; store → component.

## Entity ID map (canonical)

Canonical names/tech/descriptions: [`common/c4_identities.puml`](common/c4_identities.puml). Registry: [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml).

| ID | Kind | Display name | CA role |
| :--- | :--- | :--- | :--- |
| `regulatory_official` | Actor | Regulatory Official | — |
| `compliance_representative` | Actor | Compliance Representative | — |
| `selma` | System | Selma | System boundary |
| `target_sources` | External (optional) | Target Sources | External system |
| `clients` | Container | Clients | Driving UX surfaces |
| `application` | Container | Application | Runtime process |
| `directives_store` | Store | Directives Store | Frameworks & drivers |
| `compiled_rules_store` | Store | Compiled Rules Store | Frameworks & drivers |
| `finding_events_store` | Store | Finding Events Store | Frameworks & drivers |
| `artifacts_store` | Store | Artifacts Store | Frameworks & drivers |
| `api` | Component (gate) | API | Interface adapter (driving) |
| `directives_application` | Component | Directives Application | Application |
| `compilation_application` | Component (hermetic) | Compilation Application | Application |
| `inspections_application` | Component | Inspections Application | Application |
| `findings_application` | Component | Findings Application | Application |
| `directives_repository` | Component | Directives Repository | Interface adapter (driven) |
| `compiled_rules_repository` | Component | Compiled Rules Repository | Interface adapter (driven) |
| `finding_events_repository` | Component | Finding Events Repository | Interface adapter (driven) |
| `artifacts_repository` | Component | Artifacts Repository | Interface adapter (driven) |
| `target_sources_gateway` | Component (optional) | Target Sources Gateway | Interface adapter (driven) |

### Naming notes (structural only)

- **`compilation_application` (C4)** vs package prefix **`compiled_rules_*`** — one concept, two names by design. Never invent C4 peer `compiled_rules_application`. See registry `package_aliases` / `forbidden_c4_peer_ids`.
- **`findings_application`** (use-case projection) vs **`finding_events_store`** (append-only SoR).
- **`{resource}_repository`** pairs with **`{resource}_store`**.
- **`clients`** is the external UX container. Package `cli_interface` / `tui_interface` map to `clients` + local gate adapters — package view owns that split.

## Clean Architecture mapping (C4 entities only)

| CA ring | C4 entities |
| :--- | :--- |
| Frameworks & drivers | `*_store`; optional `target_sources` |
| Interface adapters (driving) | `clients`, `api` |
| Application use cases | `*_application` |
| Domain | Not C4 peers — package/class only |
| Interface adapters (driven) | `*_repository`, `*_gateway` |

Port **ownership** and adapter class names: [`../package/`](../package/README.md).  
Port **method shapes**: [`../class/`](../class/README.md).

## Not C4 peers (placement only)

| ID / concern | Kind | Lives in (structure) |
| :--- | :--- | :--- |
| `ResolveConflict` | domain service | `conflicts_domain`; used in-process by `compilation_application` and `inspections_application` |
| `DenialAuditPort` | application port | Owned by findings application layer; consumer `api`; implementer co-located with `finding_events_repository` |
| `FindingOpenPort` | application port | Owned by `findings_application`; consumer `inspections_application` |
| `certification_tool` | offline/CI tool | Not a Context/Container peer; may write `artifacts_store` kind=certification |
| Guidance / analytics read models | findings read models | Inside `findings_application` |
| CI/CD, audit export, remediation ticketing | optional client/export | Not product peers |

Algorithms, SoD rules, gate criteria: **spec contracts** — not restated here.

## API surface alignment (resource → peer)

| Resource | Owner application | Store / adapter |
| :--- | :--- | :--- |
| `/directives` | `directives_application` | `directives_store` + `directives_repository` |
| `/directives/.../compilations` | `compilation_application` | `compiled_rules_store` + `compiled_rules_repository` |
| `/inspections` | `inspections_application` | evidence via `artifacts_repository` → `artifacts_store` |
| `/findings` (+ guidance) | `findings_application` | `finding_events_store` + `finding_events_repository` |
| `/artifacts` | (inspections / findings / certify) | `artifacts_store` + `artifacts_repository` |

Full path list: registry `api_resources` + [`../api/`](../api/README.md).

## Tenant model (v1 product boundary)

**Single-tenant per deployment instance.** No `tenant_id` on API resources, store rows, JWT claims, or idempotency keys. Isolation is deployment-level (see [`../deployment/`](../deployment/README.md)). Multi-tenancy is out of scope for design_contract_version `1.3.0`.

## Normative behavior (do not redefine here)

| Concern | Authority |
| :--- | :--- |
| Authn / capabilities / SoD | [`../spec/contracts/authorization/`](../spec/contracts/authorization/), finding-lifecycle SoD |
| Hermetic compile, locks, outbox | [`../spec/contracts/compilation/`](../spec/contracts/compilation/), `data_stores/directives_store.yaml` |
| Finding FSM | [`../spec/contracts/finding_lifecycle/`](../spec/contracts/finding_lifecycle/) |
| Store mutability, HLC, projections | [`../spec/contracts/data_stores/`](../spec/contracts/data_stores/) |
| Dual-document / schema shapes | [`../schema/`](../schema/), directives store contract |
| Topology, TLS, RPO/RTO | [`../deployment/`](../deployment/README.md) |
| Module/port map | [`../package/`](../package/README.md) |

## Canonical registry & rendering

- IDs: `common/c4_identities.puml` · Styles: `common/c4_styles.puml` · Contract: `1.1.0`
- Check: `python scripts/check_design_alignment.py`

```bash
plantuml docs/c4-model/c4_selma_context.puml
plantuml docs/c4-model/c4_selma_container.puml
plantuml docs/c4-model/c4_selma_component.puml
```
