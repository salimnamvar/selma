# Selma — C4 Architecture Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · This directory is the structural SSoT (peers only)

Three-level C4 model using **Clean Architecture** layering and **resource-oriented** entity IDs/names. Every structural ID carries a **layer postfix** (or role token) so its Clean Architecture ring is obvious.

**Contract version:** 1.1.0 — IDs MUST match [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml). Diagrams include `Contract: 1.1.0` headers.

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

- **`compilation_application` (C4 ID)** — hermetic compile process; publishes `compiled_rules_store`. **Package prefix is `compiled_rules_*`** (e.g. `compiled_rules_application`, `compiled_rules_infrastructure`) so the resource that is written stays explicit. These are **one concept, two names by design**: C4 emphasizes the hermetic process; packages emphasize the compiled-rules resource. Never invent a C4 peer ID `compiled_rules_application`.
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
2. `api` → `*_application` only  
3. **Capability-denial audit (narrow exception):** `api` may append denials only through application-owned **`DenialAuditPort`** (not via store I/O and not via full findings use cases). On the Component diagram this is drawn as `api` → `finding_events_repository` because that adapter is the sole implementer of `DenialAuditPort`. Package/class diagrams show the port as an application-owned interface implemented by `findings_infrastructure`.  
4. `*_application` → `*_repository` / `*_gateway` (and peer use cases when needed, e.g. `inspections_application` → `findings_application`)  
5. `*_repository` → `*_store`; `*_gateway` → external system  
6. Never: `api` → `*_store`; never: repository → use case; never: store → component; never: `api` → arbitrary repository methods beyond `DenialAuditPort.AppendDenial(...)`

### DenialAuditPort (gate side-effect)

| Item | Rule |
| :--- | :--- |
| Owner | Application layer (declared next to findings ports; see [`../class/cd_002_application_services.puml`](../class/cd_002_application_services.puml)) |
| Implementer | `finding_events_repository` / `findings_infrastructure` |
| Consumer | `api` only (capability gate) |
| Surface | Single write method: append capability-denial event (actor, capability, action, reason, timestamp) |
| Why not full findings use cases | Avoid circular dependency: gate must audit denials even when the denied action would have entered `findings_application` |
| Normative audit content | [`../spec/contracts/finding_lifecycle/sod_contract.yaml`](../spec/contracts/finding_lifecycle/sod_contract.yaml), [`../spec/contracts/interfaces/rest_api.yaml`](../spec/contracts/interfaces/rest_api.yaml) |

## Not C4 peers (by design)

| Concern | Where it lives instead |
| :--- | :--- |
| Conflict resolution algorithm | Domain service `ResolveConflict` in `conflicts_domain`; invoked **in-process** by `compilation_application` and `inspections_application` (package edges required; not a C4 component). When compile and inspect deployables are split, both MUST load the **same versioned** `conflicts_domain` library artifact (shared package / single release train); forking a private copy is non-conformant |
| Guidance & analytics | Findings Application → doctrine via `directives_repository` (`guidance_only`); revision pinned by `paired_policy_ref` (see Design principles) |
| AA-01…AA-08 certification | Offline/CI **`certification_tool`** (registry non-peer); may write `artifacts_store` kind=certification only when run — not drawn as Context/Container peer |
| Capability catalog / SoD | Enforced at `api`; normative in [`../spec/contracts/authorization/`](../spec/contracts/authorization/) and OpenAPI [`../api/components/security.yaml`](../api/components/security.yaml) |
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
- **Guidance temporal integrity**: guidance loads the doctrine revision identified by the finding’s `paired_policy_ref` (revision-pinned). Implementations MUST NOT resolve “latest doctrine” for a finding created under an older revision. Normative dual-document identity: [`../spec/contracts/data_stores/directives_store.yaml`](../spec/contracts/data_stores/directives_store.yaml)
- **Four stores by mutability**: mutable directives · immutable CG-IR · append-only events · write-once artifacts
- **Primary target path is inline**; Target Sources is optional pull
- **Application layer is mandatory**: resource mutations go through `*_application`. The only gate→driven path is `DenialAuditPort` (above)
- **Compile trigger coupling**: after durable directive mutation, insert **`compile_request` outbox** row (same DB TX); `compilation_application` drains outbox (same Application process in v1; optional separate worker later without changing C4 peer IDs). Edge tagged async on the Component diagram. Clients may also enqueue via `/directives/.../compilations`
- **Compile concurrency**: short **read locks** only while loading executables (then release); mutations take write locks. Normative: [`../spec/contracts/compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml), [`../spec/contracts/data_stores/directives_store.yaml`](../spec/contracts/data_stores/directives_store.yaml)

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
| `compiled_rules_application` / `compiled_rules_domain` | **`compilation_application`** (C4 process name; package keeps resource prefix) |
| `inspections_application` / `inspections_domain` | `inspections_application` |
| `findings_application` / `findings_domain` | `findings_application` |
| `directives_infrastructure` | `directives_repository` |
| `compiled_rules_infrastructure` | `compiled_rules_repository` |
| `findings_infrastructure` (events) | `finding_events_repository` (+ implements `DenialAuditPort`) |
| `artifacts_infrastructure` | `artifacts_repository` |
| `inspections_infrastructure` (targets) | `target_sources_gateway` |
| `rest_interface` / CLI / TUI | `api` + container `clients` |
| `conflicts_domain` (`ResolveConflict`) | in-process only; used by compile + inspect packages (not a C4 component) |

## Security architecture (at the gate)

| Concern | Decision |
| :--- | :--- |
| Authentication | Bearer JWT (OIDC/OAuth2 preferred). Normative: [`../spec/contracts/authorization/authentication.yaml`](../spec/contracts/authorization/authentication.yaml) |
| Authorization | Capability catalog + SoD; enforced only at `api` before use-case dispatch |
| Enforcement module | Shared **CapabilityEnforcer** library used by REST/CLI/TUI — not reimplemented per adapter |
| Denial audit | **DenialAuditPort** → `finding_events_repository` (see above) |
| Wire schemes | [`../api/components/security.yaml`](../api/components/security.yaml) |

### Internal structure of `api` (not separate C4 peers)

Within the driving gate, treat these as **logical sub-responsibilities** of `api` (class/package detail, not Component peers):

1. **Routing** — map HTTP/CLI intent to use-case entry points  
2. **Authentication** — JWT validate (`sub`, `exp`, signature/JWKS)  
3. **CapabilityEnforcer** — capability + SoD checks  
4. **DenialAuditPort client** — append on deny  
5. **Idempotency + ETag filters** — `Idempotency-Key`, `If-Match`

## Tenant model (v1 product decision)

**Selma v1 is single-tenant.** One deployment instance serves one regulatory
organization (one authority boundary). There is **no** `tenant_id` on API
resources, store rows, JWT claims, or idempotency keys.

| Concern | v1 behavior |
| :--- | :--- |
| Isolation | Network / deployment isolation only (one instance per tenant org) |
| `Idempotency-Key` scope | `(actor, key)` — not `(actor, tenant, key)` |
| Capability / roles | Flat actor set within the instance; role matrix is not multi-tenant |
| Multi-tenancy | **Out of scope** for design_contract_version 1.1.0 |

If multi-tenancy is required later, it is a **contract-breaking** change: add
`tenant_id` to stores, scope `Idempotency-Key` to `(actor, tenant, key)`, and
extend capability resolution. Until then, implementors MUST NOT invent a
tenant dimension.

## Distributed coordination decisions

| Path | Decision | Normative ref |
| :--- | :--- | :--- |
| Directive → compile | **Transactional outbox** `compile_request` in `directives_store`; worker = `compilation_application` (same process v1). Eventual consistency until snapshot publish. Failed rows are retriable; **permanently_failed** rows (schema-error poison) require manual intervention or corrective revision. | [`../spec/contracts/data_stores/directives_store.yaml`](../spec/contracts/data_stores/directives_store.yaml) `compile_coordination` |
| Compile locks | Read lock only while loading executables; **release before** hermetic CPU; no write lock during compile. | compilation `concurrency_model` + `lock_implementation` |
| Latest CG-IR per lineage | **`head_snapshot_hash`** on `Directives` + mirrored `LineageHeads` index in `compiled_rules_store`; advanced atomically when outbox → completed. Inspections/`GetLatestCompiledRules` MUST use this pointer — not `compiled_at`. | directives `head_snapshot_pointer`; compiled_rules `lineage_head_index` (INV-CS-006) |
| Finding transitions | Per-`finding_id` serialization (advisory lock or expected chain head) + optional `Idempotency-Key`. | finding_events `append_concurrency` |
| Finding state read | Materialized `finding_projection` cache; stream is SoR. | finding_events `state_hydration` |
| Target Sources | Timeouts, retries, circuit breaker, bulkhead on gateway. | inspection `target_sources_resilience` |

## Interface segregation (application ports)

Ports are owned by application packages (class diagrams). Implementers may be one adapter class:

| Port | Owner package | Implementer |
| :--- | :--- | :--- |
| `DirectiveRepository` (write/lifecycle) | `directives_application` | `directives_infrastructure` |
| `CompilerReadPort` / `read_executable` | `compiled_rules_application` (C4: compilation) | `directives_infrastructure` |
| `GuidanceReadPort` / `read_policy_doctrine` | `findings_application` | `directives_infrastructure` |
| `CompiledRulesRepository` | compile + inspect apps | `compiled_rules_infrastructure` |
| `FindingEventRepository` | `findings_application` | `findings_infrastructure` |
| `DenialAuditPort` | `findings_application` | `findings_infrastructure` |
| `InspectionArtifactPort` / `FindingArtifactPort` | inspections / findings | shared `artifacts_infrastructure` client |
| `TargetSourcesGateway` | `inspections_application` | `inspections_infrastructure` |

## Normative cross-references (behavior not re-specified here)

Structural docs define *what exists and how it depends*. Behavior is owned by contracts:

| Concern | Authority |
| :--- | :--- |
| Authentication (JWT/OIDC) | [`../spec/contracts/authorization/authentication.yaml`](../spec/contracts/authorization/authentication.yaml) |
| Capability catalog, role matrix | [`../spec/contracts/authorization/`](../spec/contracts/authorization/) |
| Hermetic compile + lock model + outbox drain | [`../spec/contracts/compilation/`](../spec/contracts/compilation/) |
| Finding FSM / SoD / denial audit fields | [`../spec/contracts/finding_lifecycle/`](../spec/contracts/finding_lifecycle/) |
| REST surface + idempotency + ETag | [`../spec/contracts/interfaces/rest_api.yaml`](../spec/contracts/interfaces/rest_api.yaml), [`../api/`](../api/README.md) |
| Store mutability, outbox, projections | [`../spec/contracts/data_stores/`](../spec/contracts/data_stores/) |
| Deployment RPO/RTO, TLS, zones | [`../deployment/`](../deployment/README.md) |

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
