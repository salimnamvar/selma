# Structural & behavioral view concerns (exclusive ownership)

**Purpose:** Each documentation view owns **one question** and **one concern set**.  
Views **reference** each other by **join keys** only. They must not restate another view’s design principles.

**Join keys:**
| Layer | Key | SSoT |
| :--- | :--- | :--- |
| Structural peers | C4 peer IDs | [`c4_registry.yaml`](c4_registry.yaml) |
| Modules / use-case names | Package titles + ROD PascalCase | [`../package/common/pkg_identities.puml`](../package/common/pkg_identities.puml) |
| HTTP surface | `api_resources` paths + `operationId` | [`c4_registry.yaml`](c4_registry.yaml) `api_resources` + [`../api/`](../api/README.md) |

**Behavior authority:** [`../spec/contracts/`](../spec/contracts/) + [`../schema/`](../schema/).  
**design_contract_version:** [`docs/standards/VERSION`](VERSION) (sole SemVer SSoT; whole-design freeze line — never embed the number here)

## Exclusive ownership matrix

| View | Answers | Owns 100% | Must not own / restate |
| :--- | :--- | :--- | :--- |
| **C4** [`../c4-model/`](../c4-model/README.md) | *What* product peers exist and how they **depend** | Peer/system/container/component **IDs**, display names, tech tags, structural descriptions, dependency rule, system boundaries, non-peer **placement** (where it lives, not how it works); high-level resource→peer **map** only (link to `api_resources` / API) | Package trees, port/class method shapes, **HTTP paths / OpenAPI / operationIds / wire schemas**, network zones, TLS/mTLS, RPO/RTO, HA, sizing, FSM tables, lock algorithms, capability matrix, authn flows, use-case catalogs, ERD columns |
| **Package** [`../package/`](../package/README.md) | *How* source modules are layered (Clean Architecture) | `{resource}_{layer}` packages, ISP **port ownership**, use-case/module edges, domain-lib placement, adapter **class names**, composition root | Peer inventing, Component Rel as product graph, zones/TLS/RPO, normative FSM/lock/capability text, full method signatures (class owns), actor associations (use case owns), **HTTP paths / OpenAPI / status codes / error envelopes** (API owns) |
| **Class** [`../class/`](../class/README.md) | *What types and methods* realize each package | Aggregate/entity/VO/event **members**, domain service signatures, ISP **port method shapes**, ROD use-case classes, **application DTOs**, adapter **implements**, driving adapter **type names** (e.g. `DirectiveRouter`), composition-root types; shared `common/cd_*` identities & C4-aligned archetype colors | Package dependency edges as layout authority, peer inventing, zones/TLS/RPO, normative FSM tables / capability catalog / store mutability (spec/state), actor–use-case associations (use case owns), **OpenAPI path inventory as SSoT**, Redocly layout, JSON Schema wire files, AIP-136 URI catalog (API owns; class routers **mirror** API paths only) |
| **Deployment** [`../deployment/`](../deployment/README.md) | *Where* it runs and how it is **operated** | Zones, nodes, process model (StatefulSet / persistent volume claim), TLS hops, store failure domains, sizing, backup/RPO/RTO, observability signals, edge admission, compile CPU isolation as **ops**; shared `common/dep_*` identities & C4-aligned colors | Component use-case graph, package module trees, domain services as product peers, redefining store mutability (spec owns), **resource collections / REST methods / wire schemas** (API owns) |
| **State** [`../state/`](../state/README.md) | *How state evolves* inside owned components | FSM/pipeline **visualization** of contract behavior: states, transitions, guards, stream events; headers cite **Source** contracts + **C4** owners | Inventing peers, package layout, class method catalogs, zones/TLS/RPO, restating dual-document / hermetic / SoD **principles** as if owned here (contracts own; diagrams only extract), actor goal catalogs (use case owns), **HTTP operation catalogs / OpenAPI** (API owns), **message-order collaborations** (sequence owns), **procedural swim-lane flows** (activity owns) |
| **Sequence** [`../sequence/`](../sequence/README.md) | *In what order* do peers / packages collaborate for a ROD use case or API operation | Time-ordered **message collaborations** among C4 peers and CA layers; participants labeled with C4 IDs / package titles; messages use **ROD use-case names**, class methods, and **API paths/operationIds** identical to `docs/api/`; alt/opt/loop/group for gate deny, SoD deny, and contract branches; shared `common/seq_*` styles (CA palette) + identities | Peer inventing, package dependency trees as layout SSoT, class full member catalogs, zones/TLS/RPO, FSM state charts (state owns), actor goal catalogs as ovals (use case owns), ERD tables, OpenAPI wire schema definitions (API owns schemas; sequence only **names** paths/operationIds), restating capability catalog or lock algorithms as prose (contracts own), **PlantUML `note` blocks** (forbidden — encode as messages/groups/alt) |
| **Activity** [`../activity/`](../activity/README.md) | *What procedural control flow* (decisions, fork/join, swim-lanes) realizes a ROD use case or API operation | Swim-lane **partitions** by CA layer / C4 peer / package; actions named with ROD use cases + class methods; decisions for schema/capability/SoD/status guards (labels only — norms in contracts); fork/join where contracts allow concurrency; API path/operationId on ingress actions; shared `common/act_*` styles (CA palette) + identities | Peer inventing, package trees, class member catalogs, zones/TLS/RPO, FSM state charts as the primary model (state owns), sequence message order as SSoT (sequence owns timing), OpenAPI schema bodies (API owns), capability catalog tables, ERD DDL, inventing pipeline stages not in contracts/state, **PlantUML `note` blocks** (forbidden) |
| **Use Case** [`../usecase/`](../usecase/README.md) | *What actor goals* the product fulfills and how they **group** | Actor catalog (C4 persons), use-case **groups** by `{resource}_application` / gate / offline tool, **ROD use-case names** identical to package components and class `<<Use Case>>` types, actor associations, `<<include>>` / `<<extend>>` among use cases only; shared `common/uc_*` identities & CA palette styles | Peer inventing, package trees/ports, class method signatures, zones/TLS/RPO, FSM states/transitions, store mutability, capability catalog text, **pipeline stage inventories and swim-lane procedures** (state/activity own), sequence message catalogs (sequence owns), re-drawing C4 Rel graphs, **HTTP paths, verbs, status codes, request/response bodies, operationIds as wire catalog** (API owns; UC names are the join key only) |
| **ERD** [`../erd/`](../erd/README.md) | *What durable tables and relationships* each C4 `*_store` holds | Per-store **entities/tables**, columns and types, primary/foreign/unique keys, indexes required for store ops, enum value sets that are **column domains**, mutability stereotype (`mutable` / `append_only` / `immutable` / `write_once` / `projection` / `outbox` / `secondary_index` / `content_addressed`); shared `common/erd_*` identities & CA palette; one diagram file per C4 store peer | Peer inventing, package trees, class method signatures, actor–use-case graphs, zones/TLS/RPO/HA, FSM transition tables and guards (state owns visualization; contracts own norms), capability catalog prose, locking algorithm narrative, retention policy prose, network topology, **REST resources as HTTP collections, OpenAPI schemas, pagination tokens** (API owns; column domains may align with wire enums by name only), sequence/activity flows |
| **API** [`../api/`](../api/README.md) | *What HTTP resources, methods, and wire schemas* the product exposes | Path inventory (AIP-121 standard + AIP-136 custom methods); HTTP methods; `operationId`s (camelCase of ROD use-case names); request/response **wire** schemas and JSON Schema resource views; shared path/query/header **parameters** as wire names; shared **error response** components and error envelope shape; OpenAPI security **scheme declaration**; multi-file OpenAPI layout + Redocly config; registry `api_resources` path list **must match** this view | Peer inventing (C4), package trees/ports (package), domain algorithms / full domain method catalogs (class/domain), zones/TLS/RPO (deployment), FSM transition **tables and guards** (state + contracts), capability **catalog** / SoD rules (contracts), store mutability / locks / retention / HLC (contracts), dual-document **principles** (contracts + schema), certification gate **criteria** (contracts), actor catalogs and include/extend graphs (use case), ERD physical keys/indexes (ERD), sequence message order and activity swim-lanes (behavior views own visualization). **Must not invent** resources or use cases that do not exist in C4 / use case / class. **Must not restate** normative behavior prose owned by `spec/contracts/` — **link** only |

## What is **not** a structural- or API-view principle

These live under **spec** (and schema where structural data shapes apply). Views may **link**, never **duplicate** as their own design principles:

| Concern | Authority |
| :--- | :--- |
| Authentication (JWT/OIDC validation rules, claims) | `spec/contracts/authorization/authentication.yaml` |
| Capability catalog / roles / SoD rules | `spec/contracts/authorization/`, `finding_lifecycle/sod_contract.yaml` |
| Finding FSM states/transitions/guards (normative) | `spec/contracts/finding_lifecycle/` |
| Hermetic compile + locks + outbox | `spec/contracts/compilation/`, `data_stores/directives_store.yaml` |
| Store mutability / retention / HLC | `spec/contracts/data_stores/` |
| Dual-document + `paired_policy_ref` | `spec/contracts/data_stores/directives_store.yaml`, `docs/schema/` |
| REST **behavior** (idempotency rules, denial audit, error code **semantics**, concurrency rules) | `spec/contracts/interfaces/rest_api.yaml` |
| Certification gates AA-01…AA-09 **criteria** | `spec/contracts/certification/gates.yaml` |

**Split (do not conflate):**

| Concern | Authority |
| :--- | :--- |
| REST **behavior** (what must happen; errors; idempotency; ETag rules) | `spec/contracts/interfaces/rest_api.yaml` |
| REST **surface** (paths, methods, operationIds, wire schemas, OpenAPI) | `docs/api/` only |
| Rule/policy **document** JSON Schema (executable + doctrine content) | `docs/schema/` (mirrored at repo `schema/`) |
| Domain type **members** / DTO field intent | `docs/class/` |
| Durable **table** columns | `docs/erd/` + store contracts |

## Naming dual (one concept, two labels)

| Concept | C4 peer ID | Package prefix |
| :--- | :--- | :--- |
| Hermetic compile → CG-IR | `compilation_application` | `compiled_rules_application` / `compiled_rules_*` |

Never invent C4 peer `compiled_rules_application` (see `forbidden_c4_peer_ids` in registry).

## Cross-view reference rules

1. **C4** defines IDs; package, class, deployment, state, use case, ERD, and API **map** to those IDs; state **annotates** machines with those IDs in headers; use case **groups** by application peers and labels non-peers `(domain)` / `(offline)`; ERD files **one-to-one** with C4 `*_store` peers; API **resource owners** are C4 application/repository peers from `api_resources`.
2. **Package** owns which modules own which ports and adapter **names**; **class** owns full port/use-case/adapter **method signatures** and domain/DTO types. C4 Component may show only the **peer edge** (e.g. `api` → `finding_events_repository` for denial audit path).
3. **Deployment** names zones and nodes using C4 container/store IDs from `dep_identities.puml` (same peer strings as C4/package/state); zone colors use the shared C4 hex palette in `dep_styles.puml`. It does not redraw Component Rel graphs, class catalogs, or OpenAPI path trees.
4. **State** files use `state_machine_NNN_*.puml` / diagram ID `State Machine NNN` (full words; parallel numbering to `pkg_NNN`, `dep_NNN`, `cd_NNN`, `uc_NNN`, `erd_NNN`). Shared includes: `state/common/state_styles.puml` + `state_identities.puml`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract` (= `docs/standards/VERSION`). Non-peers labeled `(domain)` / `(offline)`.
5. **Class** files use `cd_NNN_*.puml` / `CLS-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract`. Structure: `common/cd_styles.puml` + `cd_identities.puml` + `cd_section_*` + `*_connections`. Domain types group by `*_domain` package names; application by `*_application`; infrastructure by `*_infrastructure`. Archetype colors use the shared C4 hex palette. **REST router methods on class diagrams MUST be identical to `docs/api` paths** but class does not own the OpenAPI document.
6. **Use Case** files use `uc_NNN_*.puml` / `UC-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract`. Structure: `common/uc_styles.puml` + `uc_identities.puml` + `uc_section_*`. Use-case **oval names** MUST be PascalCase identical to package application leaves and class `<<Use Case>>` types (Resource-Oriented Design: verb + resource). Groups use the same package titles as package/class. Actors use full C4 person names only. **No pipeline stages, FSM states, store mutability, capability catalog prose, or HTTP path catalogs** on use-case diagrams.
7. **ERD** files use `erd_NNN_*_store.puml` / `ERD-NNN`. Headers: `Title`, `Source` (matching `spec/contracts/data_stores/{store_id}.yaml`), `C4` (store + owning `*_repository`), `Package` (owning `*_infrastructure`), `Contract`. Entity names and column domains MUST be consistent with domain aggregates/value objects in class and with store contracts; **cross-store references are hashes/IDs only**. **No OpenAPI or HTTP paths** on ERD.
8. **API** files live under `docs/api/` (OpenAPI 3.1 multi-file). Entry: `openapi.yaml`. Paths by resource under `paths/`; shared `components/`; primary resource JSON Schema under `schemas/`. Registry `api_resources.paths` **must equal** OpenAPI path keys. **operationId** = camelCase of the ROD use-case oval (or standard Get/List when no separate oval). Wire resource names align with domain aggregates (`Directive`, `Finding`, `Inspection`, `Compilation`/`CgIrSnapshot`, `Artifact`). Enum wire values for FSM states use **storage_id** from finding lifecycle contracts (not display names). **No** FSM guard tables, capability catalogs, lock algorithms, package trees, or deployment zones in API prose — cite contracts/views. Normative: [AIP-121](https://google.aip.dev/121), [AIP-136](https://google.aip.dev/136).
9. **Sequence** files use `seq_NNN_*.puml` / `SEQ-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `API` (paths/operationIds covered), `UseCase` (ROD ovals), `Contract`. Structure: `common/seq_styles.puml` + `seq_identities.puml`. Participants ordered **actors → interface → application → domain → infrastructure → frameworks** (Clean Architecture). Messages cite class use-case/port methods and **exact** API paths from `docs/api/`. Coverage: every client-facing ROD use case and API mutating/read path family has at least one sequence. **No** OpenAPI schema definitions, package dependency graphs, or FSM charts.
10. **Activity** files use `act_NNN_*.puml` / `ACT-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `API`, `UseCase`, `Contract`. Structure: `common/act_styles.puml` + `act_identities.puml`. Swim-lanes = CA layers / C4 peers (same strings as package/C4). Actions = ROD use cases + class methods; ingress labels include API path/operationId. Coverage: every API path family / ROD use-case group has a corresponding activity (or is explicitly covered by a listed activity in the section README). Complements state (states) and sequence (message order) — does not replace them.
11. **No PlantUML `note` blocks** on state, package, class, C4, deployment, use-case, ERD, **sequence**, or **activity** diagrams — unfinished design smell. Encode as type fields, stereotypes, guards, actions, actor associations, include/extend, PK/FK/unique markers, messages, alt/opt groups, decision labels, or keep only in the Source contract. **No short-form names** in state/use-case/ERD/sequence/activity filenames or diagram prose (`sm_`, `SoD`, `CG-IR`, `HLC`, `RO`, `CR`, …); use full words where prose appears (C4 peer IDs remain registry strings).
12. **Colors:** sole SSoT is [`common/ca_palette.puml`](common/ca_palette.puml). **MACRO** tokens are Clean Architecture layers (actors → interface → application → domain → infrastructure → frameworks → external → composition). **MICRO** tokens are cross-cutting concerns (gate, hermetic, terminal) and view-specific aliases (`$STATE_COLOR_*`, `$UC_*`, `$ERD_*`, `$SEQ_*`, `$ACT_*`, type archetypes). Every view styles file includes the palette and re-exports aliases — never invent hex in diagram bodies.
13. If two views need the same fact, put it once under the **authority** column (matrix or “not a structural-view principle”) and **link** from the others.

## Identity duals (must stay identical across views)

### Group dual (use case · package · class · C4)

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

### ROD use case dual (use case · package · class · API)

| Concept | Use-case oval | Package leaf | Class type | API operationId (wire) | C4 peer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Create directive | `CreateDirective` | `CreateDirective` | `<<Use Case>> CreateDirective` | `createDirective` | `directives_application` |
| Compile | `CompileDirectives` | `CompileDirectives` | `<<Use Case>> CompileDirectives` | `compileDirectives` | `compilation_application` |
| Transition finding | `TransitionFinding` | `TransitionFinding` | `<<Use Case>> TransitionFinding` | `transitionFinding` | `findings_application` |
| Attach evidence | `AttachEvidence` | `AttachEvidence` | `<<Use Case>> AttachEvidence` | `attachEvidence` | `findings_application` |
| Conflict review | `ReviewConflictArtifact` | `ReviewConflictArtifact` | `<<Use Case>> ReviewConflictArtifact` | `reviewConflictArtifact` | `findings_application` |
| Capability gate | `CheckCapability` | `CapabilityEnforcer` (interface) | gate types | *(not a resource operation — gate filter)* | `api` |
| Resolve conflict | `ResolveConflict` in `$TITLE_DOM_CON` | `ResolveConflict` | `<<Domain Service>> ResolveConflict` | **no client route** | **not** a peer |
| Certification run | `RunArchitecturalCertification` in `$TITLE_OFFLINE_CERT` | offline | certification payloads | **no client route** (artifact kind only) | offline · not peer |

### Resource dual (API · domain class · ERD · C4 owner)

| API resource (wire) | Domain / class type | Primary store / ERD | C4 owner peer |
| :--- | :--- | :--- | :--- |
| `Directive` | `Directive` aggregate | `erd_001_directives_store` | `directives_application` |
| `Compilation` | `CgIrSnapshot` | `erd_002_compiled_rules_store` | `compilation_application` |
| `Inspection` | `Inspection` aggregate | `erd_004_artifacts_store` (inspection snapshots) | `inspections_application` |
| `Finding` | `Finding` / `FindingProjection` | `erd_003_finding_events_store` | `findings_application` |
| `Artifact` | write-once blobs | `erd_004_artifacts_store` | `artifacts_repository` |

**Forbidden group labels:** invented names (`Selma Application`, “Conflict engine”, “Guidance engine”), bare package ids when the SSoT dual form exists, groups that do not appear in package or C4 (except `$TITLE_OFFLINE_CERT` and `$TITLE_DOM_*`).

**Forbidden API freestanding collections:** `/conflicts`, `/certifications`, `/guidance` as top-level engines — conflict human review and certification results are artifact-backed; guidance is a Finding sub-resource.

Never invent a C4 peer for domain services or the certification tool. Never name use cases after pipeline stages or FSM states (`NormalizeTarget`, `PendingVerification`, …) — state and activity views own those. Never invent API resources or operationIds without a matching use-case oval (except pure standard Get/List on an existing resource collection).

## Violation checklist (separation of concerns)

| If you find… | Wrong owner | Move / fix to… |
| :--- | :--- | :--- |
| Full OpenAPI path list inside C4/package/use case/ERD prose as SSoT | those views | `docs/api/` + `api_resources` |
| FSM transition table inside API or package README | those views | `spec/contracts/finding_lifecycle/` + `state/` extract |
| Capability catalog copied into API path descriptions | API | `spec/contracts/authorization/` |
| Package dependency graph redrawn on C4 Component as module tree | C4 | `package/` |
| Zones/TLS/RPO on class or API | those views | `deployment/` |
| Actor–use-case associations on class or API | those views | `usecase/` |
| ERD inventing columns that contradict store contracts | ERD | `spec/contracts/data_stores/` then ERD |
| API inventing a use case not in package/class/use case | API | add ROD oval everywhere first, then path |
| Class router paths differing from OpenAPI | either | make **identical**; API path inventory is SSoT for HTTP |
| Sequence inventing HTTP path not in OpenAPI | sequence | fix API first or drop message |
| Activity inventing pipeline stage not in contracts/state | activity | `spec/contracts/` + `state/` |
| PlantUML `note` on sequence/activity | those views | encode as message / alt / decision label |
| Sequence and activity missing for a client-facing use case / API path family | sequence/activity | add diagram and catalog row |

## Check

```bash
python scripts/check_design_alignment.py
cd docs/api && npx @redocly/cli lint openapi.yaml
```
