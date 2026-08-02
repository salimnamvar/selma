# Structural & behavioral view concerns (exclusive ownership)

**Purpose:** Each documentation view owns **one question** and **one concern set**.  
Views **reference** each other by **C4 peer IDs** only. They must not restate another view’s design principles.

**Join key (all structural views):** peer IDs from [`c4_registry.yaml`](c4_registry.yaml).  
**Behavior authority:** [`../spec/contracts/`](../spec/contracts/) + [`../schema/`](../schema/).  
**design_contract_version:** `1.1.0` (stamp of [`VERSION`](VERSION); whole-design freeze line)

## Exclusive ownership matrix

| View | Answers | Owns 100% | Must not own / restate |
| :--- | :--- | :--- | :--- |
| **C4** [`../c4-model/`](../c4-model/README.md) | *What* product peers exist and how they **depend** | Peer/system/container/component **IDs**, display names, tech tags, structural descriptions, dependency rule, system boundaries, non-peer **placement** (where it lives, not how it works) | Package trees, port/class method shapes, network zones, TLS/mTLS, RPO/RTO, HA, sizing, FSM tables, lock algorithms, capability matrix, authn flows |
| **Package** [`../package/`](../package/README.md) | *How* source modules are layered (Clean Architecture) | `{resource}_{layer}` packages, ISP **port ownership**, use-case/module edges, domain-lib placement, adapter **class names**, composition root | Peer inventing, Component Rel semantics as product graph, zones/TLS/RPO, normative FSM/lock/capability text, full method signatures (class owns) |
| **Class** [`../class/`](../class/README.md) | *What types and methods* realize each package | Aggregate/entity/VO/event **members**, domain service signatures, ISP **port method shapes**, ROD use-case classes, DTOs, adapter **implements**, driving adapter types, composition-root types; shared `common/cd_*` identities & C4-aligned archetype colors | Package dependency edges as the layout authority, peer inventing, zones/TLS/RPO, normative FSM tables / capability catalog / store mutability (spec/state) |
| **Deployment** [`../deployment/`](../deployment/README.md) | *Where* it runs and how it is **operated** | Zones, nodes, process model (StatefulSet / persistent volume claim), TLS hops, store failure domains, sizing, backup/RPO/RTO, observability signals, edge admission, compile CPU isolation as **ops**; shared `common/dep_*` identities & C4-aligned colors | Component use-case graph, package module trees, domain services as product peers, redefining store mutability semantics (spec owns) |
| **State** [`../state/`](../state/README.md) | *How state evolves* inside owned components | FSM/pipeline **visualization** of contract behavior: states, transitions, guards, stream events; headers cite **Source** contracts + **C4** owners | Inventing peers, package layout, class method catalogs, zones/TLS/RPO, restating dual-document / hermetic / SoD **principles** as if owned here (contracts own; diagrams only extract) |

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

1. **C4** defines IDs; package, class, and deployment **map** to those IDs; state **annotates** machines with those IDs in headers.
2. **Package** owns which modules own which ports and adapter **names**; **class** owns full port/use-case/adapter **method signatures**. C4 Component may show only the **peer edge** (e.g. `api` → `finding_events_repository` for denial audit path).
3. **Deployment** names zones and nodes using C4 container/store IDs from `dep_identities.puml` (same peer strings as C4/package/state); zone colors use the shared C4 hex palette in `dep_styles.puml`. It does not redraw Component Rel graphs or class catalogs.
4. **State** files use `state_machine_NNN_*.puml` / diagram ID `State Machine NNN` (full words; parallel numbering to `pkg_NNN`, `dep_NNN`, `cd_NNN`). Shared includes: `state/common/state_styles.puml` + `state_identities.puml`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract` (= `docs/standards/VERSION`). Non-peers labeled `(domain)` / `(offline)`.
5. **Class** files use `cd_NNN_*.puml` / `CLS-NNN`. Headers: `Title`, `Source`, `C4`, `Package`, `Contract`. Structure: `common/cd_styles.puml` + `cd_identities.puml` + `cd_section_*` + `*_connections` (same maintenance pattern as package/deployment/state). Domain types group by `*_domain` package names; application by `*_application`; infrastructure by `*_infrastructure`. Archetype colors use the shared C4 hex palette (store / container / process / gate / hermetic / domain).
6. **No PlantUML `note` blocks** on state, package topology, class, C4, or deployment diagrams — unfinished design smell. Encode as type fields, stereotypes, guards, actions, or keep only in the Source contract. **No short-form names** in state filenames or diagram text (`sm_`, `SoD`, `CG-IR`, `HLC`, …); use full words where prose appears. Color fills only via shared style macros (C4-harmonized).
7. If two views need the same fact, put it once under the **authority** column above and link from the others.

## Check

```bash
python scripts/check_design_alignment.py
```
