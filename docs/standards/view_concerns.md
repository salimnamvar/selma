# Structural & behavioral view concerns (exclusive ownership)

**Purpose:** Each documentation view owns **one question** and **one concern set**.  
Views **reference** each other by **C4 peer IDs** only. They must not restate another view’s design principles.

**Join key (all structural views):** peer IDs from [`c4_registry.yaml`](c4_registry.yaml).  
**Behavior authority:** [`../spec/contracts/`](../spec/contracts/) + [`../schema/`](../schema/).  
**design_contract_version:** `1.1.0`

## Exclusive ownership matrix

| View | Answers | Owns 100% | Must not own / restate |
| :--- | :--- | :--- | :--- |
| **C4** [`../c4-model/`](../c4-model/README.md) | *What* product peers exist and how they **depend** | Peer/system/container/component **IDs**, display names, tech tags, structural descriptions, dependency rule, system boundaries, non-peer **placement** (where it lives, not how it works) | Package trees, port/class method shapes, network zones, TLS/mTLS, RPO/RTO, HA, sizing, FSM tables, lock algorithms, capability matrix, authn flows |
| **Package** [`../package/`](../package/README.md) | *How* source modules are layered (Clean Architecture) | `{resource}_{layer}` packages, ISP **port ownership**, use-case/module edges, domain-lib placement, adapter class names, composition root | Peer inventing, Component Rel semantics as product graph, zones/TLS/RPO, normative FSM/lock/capability text |
| **Deployment** [`../deployment/`](../deployment/README.md) | *Where* it runs and how it is **operated** | Zones, nodes, process model (StatefulSet/PVC), TLS hops, store failure domains, sizing, backup/RPO/RTO, observability signals, edge admission, compile CPU isolation as **ops** | Component use-case graph, package module trees, domain services as product peers, redefining store mutability semantics (spec owns) |
| **State** [`../state/`](../state/README.md) | *How state evolves* inside owned components | FSM/pipeline **visualization** of contract behavior: states, transitions, guards, stream events; headers cite **Source** contracts + **C4** owners | Inventing peers, package layout, zones/TLS/RPO, restating dual-document / hermetic / SoD **principles** as if owned here (contracts own; diagrams only extract) |

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

1. **C4** defines IDs; package and deployment **map** to those IDs; state **annotates** machines with those IDs in headers.
2. **Package** may name ports (`DenialAuditPort`, `FindingOpenPort`); C4 Component may show only the **peer edge** (e.g. `api` → `finding_events_repository` for denial audit path).
3. **Deployment** names zones and nodes using C4 container/store IDs; it does not redraw Component Rel graphs.
4. **State** headers MUST use the diagram header schema (`Title`, `Source`, `C4`, `Contract: 1.1.0`). Non-peers labeled `(domain)` / `(offline)`.
5. If two views need the same fact, put it once under the **authority** column above and link from the others.

## Check

```bash
python scripts/check_design_alignment.py
```
