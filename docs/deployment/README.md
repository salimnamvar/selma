# Selma — Deployment Documentation

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.1.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)

Infrastructure and deployment architecture for the Selma Rule Regularity Platform.

## Diagram Index

| ID | Title | File | Description |
|:---|:------|:-----|:------------|
| **DEP-001** | Production Deployment | [`dep_001_production.puml`](dep_001_production.puml) | Topology aligned with C4 containers and resource stores |

**Note:** Clients are external to Selma. They are not part of the Selma deployment. The network flow is: Clients → Load Balancer → Application.

## Network Zones

| Zone | Purpose | Components |
|:-----|:--------|:-----------|
| **External User** | Client applications | Clients (CLI / Web / Desktop / Mobile) |
| **Public** | User-facing entry | Load balancer (active/standby or managed multi-AZ) |
| **Application** | Core process | Application (`api`, compilation, inspection, findings) |
| **Data** | Resource stores | Directives, Compiled Rules, Finding Events, Artifacts |
| **External** | Optional only | Target Sources (pull by reference) |
| **Monitoring** | Observability | Prometheus/Grafana, ELK/Loki, Jaeger |

**Note:** Clients are external to Selma. They are not part of the Selma deployment. The network flow is: Clients → Load Balancer → Application.

CI/CD, long-term audit export, and remediation ticketing are **optional clients/exports**, not required topology peers. Offline **`certification_tool`** (AA-01…AA-07) is not a deploy peer; when run it may write `artifacts_store` only.

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

### Data Store Sizing

| C4 store | Storage type | Scaling |
|:---------|:-------------|:--------|
| Directives | PostgreSQL | Vertical + read replicas |
| Compiled Rules | Filesystem or S3 CAS | Horizontal object store |
| Finding Events | PostgreSQL (append-only table) | Partition by time |
| Artifacts | S3-compatible object store | Horizontal |

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
- **v1 process model:** compile runs **in-process** with the Application container after durable directive writes (same C4 `application` container). Scale-out to a dedicated compile worker is a future deployment option and does not change C4 peer IDs

### TLS and transport

| Hop | Requirement |
|:----|:------------|
| Clients → Load balancer | **TLS required** (HTTPS) |
| Load balancer → Application | **TLS required** in production (re-encrypt or pass-through); plain HTTP only for local/dev |
| Application → Data zone stores | **TLS required** for PostgreSQL and object-store APIs in production |
| Application → Target Sources | **HTTPS required** |

**mTLS** between Application and stores is **recommended** for regulated / zero-trust deployments and **optional** only when the data zone is a private network with equivalent controls documented in the environment runbook. Production defaults assume encrypted transport on every hop above; plaintext is never the production default.

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

### Idempotency (mutating APIs)

State-changing REST operations (directive mutations, inspections, finding transitions, compile triggers) SHOULD accept client `Idempotency-Key` (or resource-natural keys already unique) so retries do not double-append finding events or double-open findings. Event append uniqueness and FSM guards are normative in finding-lifecycle contracts.

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
| `hlc_counter_reset_total` / node_id restart | HLC persistence health |
| Per-endpoint request rate & error ratio | Incident triage for REST surface |

Application logs MUST include `lineage_id`, `revision`, `finding_id`, `event_id`, `actor_id`, and outbox `worker_id` where applicable. Traces SHOULD span `api` → `*_application` → repository calls.

## Security Considerations

1. Network segmentation: Data zone not reachable from Public without Application
2. Hermetic boundary during compile
3. Write-once Artifacts; append-only Finding Events; immutable Compiled Rules
4. Capability enforcement at `api` only — catalog and SoD: [`../spec/contracts/authorization/`](../spec/contracts/authorization/), [`../spec/contracts/finding_lifecycle/sod_contract.yaml`](../spec/contracts/finding_lifecycle/sod_contract.yaml)
5. Capability denials append via **DenialAuditPort** (see [`../c4-model/README.md`](../c4-model/README.md)); never skip audit on deny; rate-limit/aggregate per finding_events_store
6. TLS on all production hops (see above); encryption at rest for all stores
7. Offline `certification_tool` is not network-exposed as a product peer
8. Production JWT revocation: deny-list and/or short-lived tokens per authentication.yaml

## Related Documents

- [C4 Architecture](../c4-model/README.md)
- [Package Diagrams](../package/README.md)
- [Spec contracts](../spec/README.md)
- [OpenAPI security](../api/components/security.yaml)
