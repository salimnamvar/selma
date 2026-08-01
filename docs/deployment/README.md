# Selma — Deployment Documentation

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

## View concern

| | |
| :--- | :--- |
| **Answers** | *Where* does Selma run, and how is it operated in production? |
| **Owns** | Network zones, nodes, TLS/mTLS hops, store failure domains, sizing, backup/RPO/RTO, observability, HA, edge rate limits |
| **Does not own** | Peer inventing (C4), component use-case graph (C4 Component), package trees / ports / domain services (package/class) |
| **Join key** | C4 container IDs (`clients`, `application`) and store IDs (`*_store`); one Application process hosts all C4 components in v1 |

DEP-001 is a **topology** diagram: Clients → LB → Application → stores / optional `target_sources` / monitoring.  
Internals of Application are defined by [C4 Component](../c4-model/c4_selma_component.puml); code layout by [package](../package/README.md).

## Diagram Index

| ID | Title | File | Description |
|:---|:------|:-----|:------------|
| **DEP-001** | Production Deployment | [`dep_001_production.puml`](dep_001_production.puml) | Zones, nodes, separate PG failure domains, S3-compatible CAS/artifacts, TLS hops |

## Network Zones

| Zone | Purpose | Deployed elements (C4 IDs) |
|:-----|:--------|:-----------|
| **External User** | Driving adapters outside Selma deployables | `clients` |
| **Public** | Edge entry | Load balancer (managed multi-AZ or active/standby) |
| **Application** | C4 `application` process (v1 **StatefulSet** replica set) | One runtime: all C4 components co-located (`api`, `compilation_application` / package `compiled_rules_*`, inspections, findings, repositories). HLC node state on PVC. |
| **Data** | Four C4 `*_store` (frameworks & drivers ring) | PG cluster A: `directives_store`; PG cluster B: `finding_events_store`; object store: `compiled_rules_store` + `artifacts_store`. Store I/O only via `*_repository` adapters — never direct `api` → store. |
| **External** | Optional pull only | `target_sources` |
| **Monitoring** | Observability | Prometheus/Grafana, ELK/Loki, Jaeger |

CI/CD, long-term audit export, and remediation ticketing are **optional clients/exports**, not required topology peers. Offline **`certification_tool`** (AA-01…AA-08) is not a deploy peer. Production CI MUST upload certification results via the authenticated API (`CertificationArtifactPort` / artifacts resource with a system capability) — **not** by opening direct network ingress from CI into the Data Zone object store. Local/dev offline write to `artifacts_store` kind=certification remains allowed when the tool runs co-located with store credentials under operator control.

## Environment Requirements

### Runtime

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11+ | Application runtime |
| Docker | 24+ | Container runtime |
| PostgreSQL | 15+ | Directives + Finding Events (**production MUST use separate instances or clusters**; see Data Store Sizing) |
| Nginx / Traefik | latest | TLS termination at edge |
| Object store | S3-compatible | Artifacts; optional CAS backend for Compiled Rules |

### Compute Resources (per Application replica)

| Resource | Minimum | Recommended |
|:---------|:--------|:------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB (local Compiled Rules / Artifacts cache) |

#### CPU isolation and compile backpressure (production MUST)

v1 co-locates `api` and `compilation_application` in one process. Production
MUST prevent compile CPU from starving REST handlers:

| Control | Requirement |
|:--------|:------------|
| Process/cgroup CPU | **MUST** pin or cgroup-limit hermetic compile workers (e.g. 50% of container CPU to compile pool, remainder to API event loop). `taskset` / cgroup v2 `cpu.max` are conformant. |
| Worker pool | Fixed-size compile pool (default 2 concurrent in-process workers per replica; environment-configurable). No unbounded fan-out. |
| Outbox depth backpressure | When `compile_outbox_depth` exceeds the configured soft limit (default **1000** pending+in_progress rows), new directive mutations that would enqueue a compile_request MUST fail fast with **503 CompileQueueFull** (Retry-After). See `directives_store.yaml` `compile_coordination.backpressure`. |
| Metrics | Alert on `compile_outbox_depth`, `compile_duration_seconds` p99 vs lease duration, and API p99 latency during compile bursts. |

### Data Store Sizing

| C4 store | Storage type | Scaling |
|:---------|:-------------|:--------|
| Directives | PostgreSQL | Vertical + read replicas; revisions referenced by `paired_policy_ref` retained indefinitely (INV-DS-007) |
| Compiled Rules | Filesystem (single node / dev) or S3-compatible CAS (production) | Horizontal object store; snapshots indefinite |

**CAS backend requirement (production):** `compiled_rules_store` MUST be backed by an S3-compatible object store (S3, MinIO, Ceph RGW, …) — not a single-node filesystem — so snapshots are replicated across failure domains and the head pointer stays recoverable after node loss. A single-node filesystem CAS is a development-only topology (single point of failure). Implementations MUST use the S3-compatible API contract (`compiled_rules_store.yaml`) with CAS semantics (content-addressed keys, idempotent put by content hash); local disk remains only a cache (see Disk row above).
| Finding Events | PostgreSQL (append-only table) | Partition by time; events indefinite |
| Artifacts | S3-compatible object store | Horizontal |

**Directive revision retention:** Unreferenced historical revisions MAY be GC'd under environment policy; any revision still referenced by a finding's `paired_policy_ref` MUST be retained indefinitely so guidance resolution remains valid. See `directives_store.yaml` `retention_policy`.

**Note:** Finding Events uses PostgreSQL with append-only semantics. This provides:
- Consistent technology stack with Directives
- Lower operational complexity
- Query flexibility for finding lookups
- Migration path to Kafka if throughput demands it

**Failure-domain separation (production):** Directives (`directives_store`) and Finding Events (`finding_events_store`) MUST NOT share a single PostgreSQL primary as the only production topology. Prefer separate instances or clusters (independent failover, backup schedules, and connection pools). Separate database names/roles on one cluster is acceptable only for non-production or when an environment runbook explicitly accepts correlated write-path failure and documents compensating controls.

## Deployment Notes

### Compilation (hermetic)

- Deterministic compile; no network egress mid-compile
- Executable documents read from **Directives** under **read-lock** before hermetic boundary (normative: [`../spec/contracts/compilation/pipeline.yaml`](../spec/contracts/compilation/pipeline.yaml) `concurrency_model`)
- Concurrent compilations allowed (shared read locks); directive mutations take exclusive write locks (writer-preference FIFO)
- Policy doctrines are not loaded for evaluation
- **v1 process model:** compile runs **in-process** with the Application container after durable directive writes (same C4 `application` container; package prefix `compiled_rules_*`). Scale-out to a dedicated compile worker (same image, different entrypoint) is a future deployment option and does not change C4 peer IDs
- **CPU isolation:** production MUST apply the CPU isolation table above; "MAY pin" is non-conformant for production
- **Split compile/inspect deployables (DEP-001):** If/when compilation and inspection run in separate processes or images, both deployables MUST load the **same versioned** `conflicts_domain` library artifact (`ResolveConflict`) from a single release train, and `conflicts_domain_version` MUST be pinned in `frozen_environment` / `frozen_env_hash` ([`../spec/contracts/compilation/hermetic_boundary.yaml`](../spec/contracts/compilation/hermetic_boundary.yaml)). Forking private copies of conflict-resolution code is non-conformant (`INV-PR-002` / conflict determinism). Normative structural note: [`../c4-model/README.md`](../c4-model/README.md) "Not C4 peers"; package edges: [`../package/README.md`](../package/README.md)

### TLS and transport

| Hop | Requirement |
|:----|:------------|
| Clients → Load balancer | **TLS required** (HTTPS) |
| Load balancer → Application | **TLS required** in production (re-encrypt or pass-through); plain HTTP only for local/dev |
| Application → Data zone stores | **TLS required** for PostgreSQL and object-store APIs in production |
| Application → Target Sources | **HTTPS required** |

**mTLS** between Application and stores **SHOULD be deployed** in production environments that require a zero-trust data zone (client-certificate verification on both PostgreSQL and object-store APIs). Any production deviation from mTLS — including plain TLS relying only on network isolation — **MUST be explicitly risk-accepted** in the environment runbook with compensating controls documented (e.g. network policy denying all non-Application ingress to the data zone, and per-connection credential checks).

Example (PostgreSQL): `sslmode=verify-full` plus client certificates (`sslcert`/`sslkey` presented by the Application), server certificate pinned via `sslrootcert`; object stores: SigV4/HTTPS with per-deploy short-lived credentials or workload identity. Production defaults assume encrypted, mutually authenticated transport on every Application → Data hop.

### Encryption at rest and secrets

- **At rest:** PostgreSQL volumes and object-store buckets MUST use encryption at rest in production (**AES-256** or cloud equivalent CMK/PMK). Document the KMS key ID in the environment runbook
- **In transit:** TLS 1.2+ (TLS 1.3 preferred) on all production hops (see TLS table)
- **Secrets:** DB credentials, object-store keys, and JWT validation material MUST come from a secrets manager or sealed mount (not image env baked into layers; not plaintext in compose files committed to git). Rotation procedure is environment-owned; Application reads secrets at process start or via sidecar
- **JWT:** Bearer tokens per [`../api/components/security.yaml`](../api/components/security.yaml) and [`../spec/contracts/authorization/authentication.yaml`](../spec/contracts/authorization/authentication.yaml); enforcement only at `api` via shared CapabilityEnforcer

### Connection pooling

PgBouncer (or equivalent) for Directives and Finding Events, with **separate pools** per store role.

### Backup & Recovery

| C4 store | Backup | RPO | RTO (store alone) |
|:---------|:-------|:----|:------------------|
| Directives | PostgreSQL PITR | < 5 min | < 1 hour |
| Compiled Rules | Rebuild by recompile from Directives | N/A (derived) | < 30 min (assumes Directives already available) |
| Finding Events | PostgreSQL PITR **plus** streaming/replica append durability (same engine; append-only workload) | < 1 min | < 1 hour |
| Artifacts | Cross-region object replication | < 15 min | < 2 hours |

**Finding Events backup wording:** both Directives and Finding Events use PostgreSQL. Directives emphasize PITR for mutable OLTP recovery; Finding Events emphasize continuous replication of the append-only log **in addition to** PITR-capable base backups. This is not two conflicting engines—it is workload-appropriate recovery emphasis on one technology.

#### Composed system recovery (correlated failure)

| Scenario | Effective RTO | Notes |
|:---------|:--------------|:------|
| Finding Events only | < 1 hour | Independent of compile |
| Directives only | < 1 hour | Compiled Rules still serve last CAS snapshots until rebuild |
| Directives **and** Compiled Rules | **Directives RTO + recompile RTO ≤ ~1.5 hours** | Recompile cannot start until Directives are restored |
| Full data-zone loss | **max(Directives+recompile, Events, Artifacts) ≈ ≤ 2 hours** | Dominated by Artifacts cross-region restore unless Artifacts were multi-region hot |

Runbooks MUST use the composed figures when more than one store is unavailable. Per-store RTOs alone understate outage duration for correlated failures.

### Horizontal scaling

Application replicas behind the load balancer; state externalized to the four stores.

#### HLC node state persistence (required)

The Application appends to `finding_events_store` under Hybrid Logical Clock
ordering (`INV-ES-003`). Causal monotonicity across restarts requires each
replica to persist its `(node_id, physical_time, logical_counter)` state —
a stateless restart that reuses a `node_id` without its HLC state breaks the
total-order and `chain_hash` guarantees (see `finding_events_store.yaml`
`hlc.node_identity`).

**Production mandate:** Application replicas MUST be deployed as a **Kubernetes
StatefulSet (or equivalent) with a PVC per ordinal** for HLC node state:

1. **StatefulSet with PVCs (required production):** one replica identity per
   StatefulSet ordinal; `node_id` (UUID) and HLC `(physical_time, logical_counter)`
   live on the replica's persistent volume and are reloaded on restart before
   accepting appends. Pod rescheduling reattaches the PVC. DEP-001 shows the PVC.
2. **Database-backed `hlc_state` (non-production / emergency only):** a dedicated
   table in `finding_events_store` keyed by `node_id`. **Not** a production
   default: it couples process bootstrap to DB availability (circular dependency
   during store outage) and is unsafe under PITR rollback of the same store
   (stale logical counters can collide with externally observed chain hashes).
   Environments that use it MUST document risk acceptance and a fence-and-retire
   procedure after any PITR.

A stateless `Deployment` that regenerates a fresh `node_id` on every start is
conformant **only if** no events from the previous `node_id` remain in the
stream (fence-and-retire); it MUST NOT reuse a previously retired `node_id`.
If a PVC is lost, treat the ordinal as a **new** node (retire old `node_id`).
Monitor `hlc_counter_reset_total` / node_id restarts (observability catalog)
to detect unpersisted restarts.

**Replay of spooled denials:** CapabilityDenied / SoDDenied events spooled to
disk during store outage MUST be replayed with HLC timestamps assigned at
**replay time** (monotonic with current node state) and MAY carry
`original_denied_at` / `replay_marker` in payload so SOC can reconcile wall
time without violating INV-ES-003 non-decreasing HLC order.

### Load balancer high availability

| Mode | When |
|:-----|:-----|
| Cloud-managed LB (multi-AZ) | Preferred in public cloud |
| Active/standby (keepalived / VRRP) | Self-hosted |
| DNS active-active | Only with health-checked endpoints |

A single non-HA LB node is **not** a production topology. DEP-001 shows the logical LB role; production MUST deploy it as an HA pair or managed service.

### Target Sources gateway resilience

When inspections use remote references (`target_sources_gateway`):

| Control | Default (production) |
|:--------|:---------------------|
| Connect / read timeout | ≤ 5 s (configurable; fail closed to error, not hang) |
| Retries | ≤ 2 retries on idempotent GET; exponential backoff |
| Circuit breaker | Open after consecutive failures; fail inspection fetch with structured error |
| Bulkhead | Dedicated connection pool separate from store pools |

Normative inspection pipeline: [`../spec/contracts/inspection/pipeline.yaml`](../spec/contracts/inspection/pipeline.yaml). Primary path remains **inline target body** on the inspection resource.

### Edge admission control (global rate limiting)

Per-actor limits (`directive.modify`/`directive.create`, 429) are the first
application-tier backpressure signal, but they are keyed by JWT identity and
cannot stop a botnet of unique actors or an unauthenticated flood. The Load
Balancer / edge gateway MUST therefore enforce a **global, identity-independent
admission limit** in production — e.g. Nginx `limit_req`, Traefik RateLimit
middleware, or a managed WAF/CDN rule — keyed by IP/network and per-endpoint.
**Production default starting point:** 200 requests/second per client IP
(environment-owned; tune below Application write-queue and outbox depth bounds).
The edge limit MUST be configured below the Application's write-queue bounds so
it trips before store 503s / CompileQueueFull, and MUST return 429 with
`Retry-After` without reaching the Application (no `DenialAuditPort` write for
edge-level rejection). Production MUST document chosen values and alert on
edge-limit rejections.

### Idempotency (mutating APIs)

All mutating POST operations (directive creation and lifecycle, inspections, finding transitions, conflict resolutions, compile triggers) **MUST require** a client `Idempotency-Key` scoped to `(actor, key)` so network retries cannot double-append finding events, double-open findings, or double-create directives. Store-level uniqueness constraints (e.g. `(inspection_id, control_id, target_hash)` for `FindingCreated`) remain mandatory fallbacks — the key is the primary mechanism, not a substitute. Event append uniqueness and FSM guards are normative in finding-lifecycle contracts; REST behavior is normative in [`../spec/contracts/interfaces/rest_api.yaml`](../spec/contracts/interfaces/rest_api.yaml) (`idempotency`).

### Observability (required signals)

Monitoring tools named in DEP-001 (Prometheus/Grafana, ELK/Loki, Jaeger) MUST export at least the following architecture-owned signals. Thresholds and alert routing are environment-owned (not fixed in this design).

| Signal | Why |
|:-------|:----|
| `compile_outbox_depth` / drain lag | Detect stuck outbox rows and compile backlog |
| `compile_outbox_failed_total{reason}` | Permanently failed outbox rows (schema-error poison rows) |
| `compile_outbox_lease_steal_total` | Detect multi-replica reclaim after lease expiry |
| `directive_lock_wait_seconds` / write-queue depth | Writer-preference fairness (directives_store concurrency_model) |
| `compile_duration_seconds` / in-process compile concurrency | v1 API vs compile CPU contention |
| `finding_fsm_transition_total` / denial rate by capability | SoD friction and authorization health |
| `finding_events_append_latency` / denial_append_rate | Denial-audit amplification vs lifecycle appends |
| `denied_actions` volume (sum of payload.count by channel) | SOC reconciliation of CapabilityDenied + SoDDenied two-channel model |
| `hlc_counter_reset_total` / node_id restart | HLC persistence health |
| Per-endpoint request rate & error ratio | Incident triage for REST surface |
| `directive_modify_rate_limited_total` / per-actor quota remaining | Backpressure for `directive.modify` (INV-CA-004); 429 before write-queue 503 |

Application logs MUST include `lineage_id`, `revision`, `finding_id`, `event_id`, `actor_id`, and outbox `worker_id` where applicable. Traces SHOULD span `api` → `*_application` → repository calls.

## Security Considerations

1. Network segmentation: Data zone not reachable from Public without Application
2. Hermetic boundary during compile
3. Write-once Artifacts; append-only Finding Events; immutable Compiled Rules
4. Capability enforcement at `api` only — catalog and SoD: [`../spec/contracts/authorization/`](../spec/contracts/authorization/), [`../spec/contracts/finding_lifecycle/sod_contract.yaml`](../spec/contracts/finding_lifecycle/sod_contract.yaml)
5. Capability denials append via **DenialAuditPort** (see [`../c4-model/README.md`](../c4-model/README.md)); never skip audit on deny; rate-limit/aggregate per finding_events_store
6. Per-actor rate limits on `directive.modify` / `directive.create` (capabilities.yaml `rate_limits`) — 429 before write lock; distinct from store queue 503
7. TLS on all production hops (see above); encryption at rest for all stores
8. Offline `certification_tool` is not network-exposed as a product peer
9. Production JWT revocation: deny-list and/or short-lived tokens per authentication.yaml

## Related Documents

- [C4 Architecture](../c4-model/README.md)
- [Package Diagrams](../package/README.md)
- [Spec contracts](../spec/README.md)
- [OpenAPI security](../api/components/security.yaml)
