# Structural & behavioral view concerns (exclusive ownership)

**Purpose:** Each documentation view owns **one question** and **one concern set**.  
Views **reference** each other by **C4 peer IDs** only. They must not restate another view’s design principles.

**Join key (all structural views):** peer IDs from [`c4_registry.yaml`](c4_registry.yaml).  
**Behavior authority:** [`../spec/contracts/`](../spec/contracts/) + [`../schema/`](../schema/).  
**design_contract_version:** `1.2.0` (stamp of [`VERSION`](VERSION); whole-design freeze line)

## Exclusive ownership matrix

| View | Answers | Owns 100% | Must not own / restate |
| :--- | :--- | :--- | :--- |
| **C4** [`../c4-model/`](../c4-model/README.md) | *What* product peers exist and how they **depend** | Peer/system/container/component **IDs**, display names, tech tags, structural descriptions, dependency rule, system boundaries, non-peer **placement** (where it lives, not how it works) | Package trees, port/class method shapes, network zones, TLS/mTLS, RPO/RTO, HA, sizing, FSM tables, lock algorithms, capability matrix, authn flows, use-case catalogs |
| **Package** [`../package/`](../package/README.md) | *How* source modules are layered (Clean Architecture) | `{resource}_{layer}` packages, ISP **port ownership**, use-case/module edges, domain-lib placement, adapter **class names**, composition root | Peer inventing, Component Rel semantics as product graph, zones/TLS/RPO, normative FSM/lock/capability text, full method signatures (class owns), actor associations (use case owns) |
| **Class** [`../class/`](../class/README.md) | *What types and methods* realize each package | Aggregate/entity/VO/event **members**, domain service signatures, ISP **port method shapes**, ROD use-case classes, DTOs, adapter **implements**, driving adapter types, composition-root types; shared `common/cd_*` identities & C4-aligned archetype colors | Package dependency edges as the layout authority, peer inventing, zones/TLS/RPO, normative FSM tables / capability catalog / store mutability (spec/state), actor–use-case associations (use case owns) |
| **Deployment** [`../deployment/`](../deployment/README.md) | *Where* it runs and how it is **operated** | Zones, nodes, process model (StatefulSet / persistent volume claim), TLS hops, store failure domains, sizing, backup/RPO/RTO, observability signals, edge admission, compile CPU isolation as **ops**; shared `common/dep_*` identities & C4-aligned colors | Component use-case graph, package module trees, domain services as product peers, redefining store mutability semantics (spec owns) |
| **State** [`../state/`](../state/README.md) | *How state evolves* inside owned components | FSM/pipeline **visualization** of contract behavior: states, transitions, guards, stream events; headers cite **Source** contracts + **C4** owners | Inventing peers, package layout, class method catalogs, zones/TLS/RPO, restating dual-document / hermetic / SoD **principles** as if owned here (contracts own; diagrams only extract), actor goal catalogs (use case owns) |
| **Use Case** [`../usecase/`](../usecase/README.md) | *What actor goals* the product fulfills and how they **group** | Actor catalog (C4 persons), use-case **groups** by `{resource}_application` / gate / offline tool, **ROD use-case names** identical to package components and class `<<Use Case>>` types, actor associations, `<<include>>` / `<<extend>>` among use cases only; shared `common/uc_*` identities & CA palette styles | Peer inventing, package trees/ports, class method signatures, zones/TLS/RPO, FSM states/transitions, store mutability, capability catalog text, pipeline stage inventories (state/activity own), re-drawing C4 Rel graphs |

## What is **not** a structural-view principle

These live under **spec** (and schema where structural data shapes apply). Structural views may **link**, never **duplicate** as their own design principles:

| Concern | Authority |
| :--- | :--- |
| Authentication (JWT/OIDC) | `spec/contracts/authorization/authentication.yaml` |
| Capability catalog / roles / SoD | `spec/contracts/authorization/`, `finding_lifecycle/sod_contract.yaml` |
| Finding FSM states/transitions | `spec/contracts/finding_lifecycle/` |
| Hermetic compile + locks + outbox | `spec/contracts/compilation/`, `data_stores/directives_store.yaml` |
| Store mutability / retention / HLC | `spec/contracts/data_stores/` |
| Dual-document + `paired_policy_ref` | `spec/contracts/data_stores/directives_store.yaml`, `docs/schema/` |
| REST idempotency / ETag | `spec/contracts/interfaces/rest_api.yaml`, `docs/api/` |
| Certification gates AA-01…AA-09 | `spec/contracts/certification/gates.yaml` |

## Naming dual (one concept, two labels)

| Concept | C4 peer ID | Package prefix |
| :--- | :--- | :--- |
| Hermetic compile → CG-IR | `compilation_application` | `compiled_rules_application` / `compiled_rules_*` |

Never invent C4 peer `compiled_rules_application` (see `forbidden_c4_peer_ids` in registry).

## Cross-view reference rules

1. **C4** defines IDs; package, class, deployment, state, and use case **map** to those IDs; state **annotates** machines with those IDs in headers; use case **groups** by application peers and labels non-peers `(domain)` / `(offline)`.
2. **Package** owns which modules own which ports and adapter **names**; **class** owns full port/use-case/adapter **method signatures**. C4 Component may show only the **peer edge** (e.g. `api` → `finding_events_repository` for denial audit path).
3. **Deployment** names zones and nodes using C4 container/store IDs from `dep_identities.puml` (same peer strings as C4/package/state); zone colors use the shared C4 hex palette in `dep_styles.puml`. It does not redraw Component Rel graphs or class catalogs.
4. **State** files use `state_machine_NNN_*.puml` / diagram ID `State Machine NNN` (full words; parallel numbering to `pkg_NNN`, `dep_NNN`, `cd_NNN`, `uc_NNN`). Shared includes: `state/common/state_styles.puml` + `state_identities.puml`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract` (= `docs/standards/VERSION`). Non-peers labeled `(domain)` / `(offline)`.
5. **Class** files use `cd_NNN_*.puml` / `CLS-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract`. Structure: `common/cd_styles.puml` + `cd_identities.puml` + `cd_section_*` + `*_connections` (same maintenance pattern as package/deployment/state). Domain types group by `*_domain` package names; application by `*_application`; infrastructure by `*_infrastructure`. Archetype colors use the shared C4 hex palette (store / container / process / gate / hermetic / domain).
6. **Use Case** files use `uc_NNN_*.puml` / `UC-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract`. Structure: `common/uc_styles.puml` + `uc_identities.puml` + `uc_section_*` (same maintenance pattern as package/class/state). Use-case **oval names** MUST be PascalCase identical to package application leaves and class `<<Use Case>>` types (Resource-Oriented Design: verb + resource). Groups use the same package titles as package/class (`directives_application`, `compiled_rules_application` with C4 dual, …). Actors use full C4 person names only. **No pipeline stages, FSM states, store mutability, or capability catalog prose** on use-case diagrams — those belong to state / class / spec. Domain services and offline tools appear only as non-peer groups when they host actor-visible goals.
7. **No PlantUML `note` blocks** on state, package topology, class, C4, deployment, or use-case diagrams — unfinished design smell. Encode as type fields, stereotypes, guards, actions, actor associations, include/extend, or keep only in the Source contract. **No short-form names** in state/use-case filenames or diagram text (`sm_`, `SoD`, `CG-IR`, `HLC`, `RO`, `CR`, …); use full words where prose appears.
8. **Colors:** sole SSoT is [`common/ca_palette.puml`](common/ca_palette.puml). **MACRO** tokens are Clean Architecture layers (actors → interface → application → domain → infrastructure → frameworks → external → composition). **MICRO** tokens are cross-cutting concerns (gate, hermetic, terminal) and view-specific aliases (`$STATE_COLOR_*`, `$UC_*`, type archetypes). Every view styles file includes the palette and re-exports aliases — never invent hex in diagram bodies.
9. If two views need the same fact, put it once under the **authority** column above and link from the others.

## Use case ↔ structural identity dual

**Group SSoT:** `docs/package/common/pkg_identities.puml` macros `$TITLE_APP_*`, `$TITLE_IF_*`, `$TITLE_DOM_*`, `$TITLE_OFFLINE_CERT`.  
Use-case diagrams **include** that file and draw group rectangles only from those macros. Class package boxes use the same display strings. C4 component IDs appear in the dual subtitle where applicable.

| Use-case group (rectangle) | Package title macro | Class package box | C4 component peer |
| :--- | :--- | :--- | :--- |
| `$TITLE_APP_DIR` | `directives_application` + `(C4: directives_application)` | same | `directives_application` |
| `$TITLE_APP_CR` | `compiled_rules_application` + `(C4: compilation_application)` | same | `compilation_application` |
| `$TITLE_APP_INS` | `inspections_application` + `(C4: inspections_application)` | same | `inspections_application` |
| `$TITLE_APP_FIND` | `findings_application` + `(C4: findings_application)` | same | `findings_application` |
| `$TITLE_IF_REST` | `rest_interface (C4: api)` | same | `api` |
| `$TITLE_DOM_CON` | `conflicts_domain` | same | **not** a peer (domain) |
| `$TITLE_OFFLINE_CERT` | offline (not a CA package ring) | — | `certification_tool` (offline · not peer) |
| Outer `$TITLE_APPLICATION` | `<<application>> *_application` | application layer | C4 container `application` |

| Concept | Use-case oval | Package leaf | Class type | C4 peer |
| :--- | :--- | :--- | :--- | :--- |
| Create directive | `CreateDirective` | `CreateDirective` | `<<Use Case>> CreateDirective` | `directives_application` |
| Compile | `CompileDirectives` | `CompileDirectives` | `<<Use Case>> CompileDirectives` | `compilation_application` |
| Transition finding | `TransitionFinding` | `TransitionFinding` | `<<Use Case>> TransitionFinding` | `findings_application` |
| Capability gate | `CheckCapability` | `CapabilityEnforcer` (interface) | gate types | `api` |
| Resolve conflict | `ResolveConflict` in `$TITLE_DOM_CON` | `ResolveConflict` | `<<Domain Service>> ResolveConflict` | **not** a peer |
| Conflict review | `ReviewConflictArtifact` in `$TITLE_APP_FIND` | `ReviewConflictArtifact` | `<<Use Case>> ReviewConflictArtifact` | `findings_application` |
| Certification run | `RunArchitecturalCertification` in `$TITLE_OFFLINE_CERT` | offline | certification payloads | offline · not peer |

**Forbidden group labels:** invented names (`Selma Application`, “Conflict engine”, “Guidance engine”), bare package ids when the SSoT dual form exists, groups that do not appear in package or C4 (except `$TITLE_OFFLINE_CERT` and `$TITLE_DOM_*`).

Never invent a C4 peer for domain services or the certification tool. Never name use cases after pipeline stages or FSM states (`NormalizeTarget`, `PendingVerification`, …) — state and activity views own those.

## Check

```bash
python scripts/check_design_alignment.py
```
