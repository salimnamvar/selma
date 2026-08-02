# Selma — Deployment Documentation

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **View concerns:** [`../standards/view_concerns.md`](../standards/view_concerns.md)  
> **design_contract_version:** `1.1.0` · Structural SSoT for **peers:** [`../c4-model/`](../c4-model/README.md)

## View concern (this directory owns)

| | |
| :--- | :--- |
| **Answers** | *Where* does Selma run, and how is it **operated** in production? |
| **Owns 100%** | Network zones, nodes, TLS/mTLS hops, store failure domains, sizing, backup/RPO/RTO, observability, HA, edge rate limits, process model (StatefulSet/PVC), compile CPU isolation as **ops** |
| **Does not own** | Peer inventing / Component use-case graph (C4) · package trees / ports / domain services (package/class) · FSM tables / locks / capability catalog (spec) |
| **Join key** | C4 container IDs (`clients`, `application`) and store IDs (`*_store`); v1 one Application process hosts all C4 components |

DEP-001 is a **topology** diagram: Clients → LB → Application → stores / optional `target_sources` / monitoring.  
Internals of Application: [C4 Component](../c4-model/c4_selma_component.puml). Code layout: [package](../package/README.md). Behavior: [spec](../spec/README.md) / [state](../state/README.md).

## Diagram index

| ID | Title | File | Description |
|:---|:------|:-----|:------------|
| **DEP-001** | Production Deployment | [`dep_001_production.puml`](dep_001_production.puml) | Zones, nodes, separate PG failure domains, S3-compatible CAS/artifacts, TLS hops |

## Network zones

| Zone | Purpose | Deployed elements (C4 IDs) |
|:-----|:--------|:-----------|
| **External User** | Driving adapters outside Selma deployables | `clients` |
| **Public** | Edge entry | Load balancer (managed multi-AZ or active/standby) |
| **Application** | C4 `application` process (v1 **StatefulSet**) | One runtime co-locating all C4 components (`api`, `compilation_application` / package `compiled_rules_*`, other `*_application`, `*_repository` adapters, `*_gateway`). HLC node state on PVC. |
| **Data** | Four C4 `*_store` | PG cluster A: `directives_store`; PG cluster B: `finding_events_store`; object store: `compiled_rules_store` + `artifacts_store`. Store I/O only via `*_repository` — never direct `api` → store. |
| **External** | Optional pull only | `target_sources` |
| **Monitoring** | Observability | Prometheus/Grafana, ELK/Loki, Jaeger |

**Not deploy peers:** CI/CD, long-term audit export, remediation ticketing, offline `certification_tool` (AA-01…AA-09). Production CI uploads certification results via authenticated API (`CertificationArtifactPort` / artifacts resource) — not direct network ingress from CI into the Data Zone object store. Local/dev offline write to `artifacts_store` kind=certification remains allowed under operator control.

## Environment requirements

### Runtime

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11+ | Application runtime |
| Docker | 24+ | Container runtime |
| PostgreSQL | 15+ | Directives + Finding Events (**production MUST use separate instances or clusters**) |
| Nginx / Traefik | latest | TLS termination at edge |
| Object store | S3-compatible | Artifacts; CAS backend for Compiled Rules |

### Compute resources (per Application replica)

| Resource | Minimum | Recommended |
|:---------|:--------|:------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB (local Compiled Rules / Artifacts cache) |

#### CPU isolation and compile backpressure (production MUST)

v1 co-locates `api` and `compilation_application` in one process. Production MUST prevent compile CPU from starving REST handlers:

| Control | Requirement |
|:--------|:------------|
| Process/cgroup CPU | **MUST** pin or cgroup-limit hermetic compile workers (e.g. 50% of container CPU to compile pool). |
| Worker pool | Fixed-size compile pool (default 2 concurrent workers per replica; environment-configurable). No unbounded fan-out. |
| Outbox depth backpressure | When `compile_outbox_depth` exceeds soft limit (default **1000**), new directive mutations that would enqueue MUST fail fast with **503 CompileQueueFull** (Retry-After). Normative depths: `directives_store.yaml` `compile_coordination.backpressure`. |
| Metrics | Alert on `compile_outbox_depth`, `compile_duration_seconds` p99 vs lease duration, API p99 during compile bursts. |

### Data store sizing

| C4 store | Storage type | Scaling |
|:---------|:-------------|:--------|
| `directives_store` | PostgreSQL | Vertical + read replicas; revisions referenced by `paired_policy_ref` retained indefinitely (INV-DS-007) |
| `compiled_rules_store` | Filesystem (dev) or S3-compatible CAS (production) | Horizontal object store; snapshots indefinite |
| `finding_events_store` | PostgreSQL (append-only table) | Partition by time; events indefinite |
| `artifacts_store` | S3-compatible object store | Horizontal |

**CAS backend (production):** `compiled_rules_store` MUST be S3-compatible (not single-node filesystem) so snapshots survive node loss. API contract: `compiled_rules_store.yaml`. Local disk remains cache only.

**Finding Events technology note (ops):** PostgreSQL append-only keeps the stack consistent with Directives; migration path to a log stream if throughput demands it is environment-owned.

**Failure-domain separation (production):** `directives_store` and `finding_events_store` MUST NOT share a single PostgreSQL primary as the only production topology. Prefer separate instances/clusters. Separate DB names on one cluster is non-prod only (or documented risk acceptance).

**Directive revision retention (ops implication of store contract):** Unreferenced historical revisions MAY be GC'd under environment policy; any revision still referenced by a finding's `paired_policy_ref` MUST be retained. Authority: `directives_store.yaml` `retention_policy`.

## Deployment notes

### Compilation process model (ops)

- Deterministic compile; no network egress mid-compile (normative hermeticity: [`../spec/contracts/compilation/`](../spec/contracts/compilation/)).
- **v1 process model:** compile runs **in-process** with the Application container (same C4 `application`; package prefix `compiled_rules_*`). Dedicated compile worker (same image, different entrypoint) is a future deployment option and does **not** change C4 peer IDs.
- **CPU isolation:** production MUST apply the CPU isolation table above.
- **Split compile/inspect deployables:** both MUST load the **same versioned** `conflicts_domain` library from a single release train; pin `conflicts_domain_version` in `frozen_environment` / `frozen_env_hash`. Forking private copies is non-conformant. Structural non-peer: C4; package edges: package README.

### TLS and transport

| Hop | Requirement |
|:----|:------------|
| Clients → Load balancer | **TLS required** (HTTPS) |
| Load balancer → Application | **TLS required** in production; plain HTTP only for local/dev |
| Application → Data zone stores | **TLS required** for PostgreSQL and object-store APIs in production |
| Application → Target Sources | **HTTPS required** |

**mTLS** between Application and stores **SHOULD be deployed** for zero-trust data zones. Any production deviation **MUST** be risk-accepted in the environment runbook with compensating controls.

### Encryption at rest and secrets

- **At rest:** PostgreSQL volumes and object-store buckets MUST use encryption at rest in production (AES-256 or cloud CMK/PMK). Document KMS key ID in runbook.
- **In transit:** TLS 1.2+ (TLS 1.3 preferred) on all production hops.
- **Secrets:** DB credentials, object-store keys, JWT validation material from secrets manager or sealed mount — not baked into image layers.
- **JWT:** schemes in [`../api/components/security.yaml`](../api/components/security.yaml); authn contract: [`../spec/contracts/authorization/authentication.yaml`](../spec/contracts/authorization/authentication.yaml). Enforcement only at `api` (C4 gate).

### Connection pooling

PgBouncer (or equivalent) for Directives and Finding Events, with **separate pools** per store role.

### Backup & recovery

| C4 store | Backup | RPO | RTO (store alone) |
|:---------|:-------|:----|:------------------|
| `directives_store` | PostgreSQL PITR | < 5 min | < 1 hour |
| `compiled_rules_store` | Rebuild by recompile from Directives | N/A (derived) | < 30 min (assumes Directives available) |
| `finding_events_store` | PostgreSQL PITR **plus** streaming/replica append durability | < 1 min | < 1 hour |
| `artifacts_store` | Cross-region object replication | < 15 min | < 2 hours |

#### Composed system recovery

| Scenario | Effective RTO | Notes |
|:---------|:--------------|:------|
| Finding Events only | < 1 hour | Independent of compile |
| Directives only | < 1 hour | Compiled Rules still serve last CAS snapshots until rebuild |
| Directives **and** Compiled Rules | Directives RTO + recompile RTO ≤ ~1.5 hours | Recompile waits on Directives |
| Full data-zone loss | max(Directives+recompile, Events, Artifacts) ≈ ≤ 2 hours | Often dominated by Artifacts restore |

#### RPO / RTO (production defaults)

| Component | RPO | RTO | Notes |
|:----------|:----|:----|:------|
| `finding_events_store` | **0** | ≤ 15 min | Synchronous replication; regulatory event log |
| `directives_store` | ≤ 5 min | ≤ 15 min | Sync preferred |
| `compiled_rules_store` / `artifacts_store` | ≤ 15 min | ≤ 30 min | CAS + Object Lock/WORM; multi-AZ |
| Application StatefulSet | n/a | ≤ 5 min | PVC reattach; HLC resync before traffic |

### Horizontal scaling

Application replicas behind the load balancer; state externalized to the four stores.

#### HLC node state persistence (required)

Append path uses Hybrid Logical Clock ordering (`INV-ES-003` in `finding_events_store.yaml`). Production:

1. **StatefulSet with PVCs** — stable `node_id` per ordinal; HLC state on PVC; DEP-001 shows the PVC.
2. **DB watermark** — on startup, effective state = `max(PVC, DB_watermark)`; pure PVC-only without watermark is non-conformant when PVC may be stale.
3. **Fence and retire** — corrupted PVC → retire old `node_id`; reject appends from retired nodes.

HLC state machine detail: [`../state/selma_hlc_clock.puml`](../state/selma_hlc_clock.puml).

#### Object store immutability

Production `compiled_rules_store` and `artifacts_store` MUST enable S3 Object Lock (or equivalent WORM).

#### certification_tool authentication (ops)

Offline/CI `certification_tool` uses **scoped credentials** limited to certification object prefix — not JWT SoD, not anonymous store access. Credentials MUST NOT write directives/events stores.

#### Compile sandbox (same pod)

Hermetic compile CPU work MUST use process/netns sandbox or compile sidecar with NetworkPolicy egress deny (HERM / INV-HB-011).

**Denial spool replay (ops):** CapabilityDenied / SoDDenied events spooled during store outage MUST be replayed with HLC timestamps at **replay time** (see finding_events_store + SoD contracts).

### Load balancer high availability

| Mode | When |
|:-----|:-----|
| Cloud-managed LB (multi-AZ) | Preferred in public cloud |
| Active/standby (keepalived / VRRP) | Self-hosted |
| DNS active-active | Only with health-checked endpoints |

A single non-HA LB node is **not** a production topology.

### Target Sources gateway resilience

| Control | Default (production) |
|:--------|:---------------------|
| Connect / read timeout | ≤ 5 s |
| Retries | ≤ 2 on idempotent GET; exponential backoff |
| Circuit breaker | Per-source open after consecutive failures |
| Bulkhead | Dedicated pool separate from store pools |
| Method allowlist | GET (HEAD probes only) |
| SSRF | Allowlist hosts/CIDRs; block link-local/metadata/RFC1918 |
| NetworkPolicy | Egress restricted to allowlisted destinations |
| Body limits | max_body_bytes / max_json_depth |

Normative limits: [`../spec/contracts/inspection/pipeline.yaml`](../spec/contracts/inspection/pipeline.yaml). Primary path remains **inline target body**.

### Edge admission control

Load balancer / edge gateway MUST enforce a **global, identity-independent** admission limit in production (e.g. Nginx `limit_req`). Starting point: 200 rps per client IP (environment-owned). Edge 429s do not write `DenialAuditPort`. Per-actor limits remain application-tier (capabilities contract).

### Idempotency (ops reminder)

Mutating POSTs require client `Idempotency-Key` scoped to `(actor, key)`. Normative: [`../spec/contracts/interfaces/rest_api.yaml`](../spec/contracts/interfaces/rest_api.yaml).

### Observability (required signals)

| Signal | Why |
|:-------|:----|
| `compile_outbox_depth` / drain lag | Stuck outbox / compile backlog |
| `compile_outbox_failed_total{reason}` | Poison rows |
| `compile_outbox_lease_steal_total` | Multi-replica reclaim |
| `directive_lock_wait_seconds` | Writer-preference fairness |
| `compile_duration_seconds` / in-process concurrency | API vs compile CPU |
| `finding_fsm_transition_total` / denial rate | SoD / authz health |
| `finding_events_append_latency` / denial_append_rate | Denial-audit vs lifecycle volume |
| `denied_actions` volume | SOC two-channel model |
| `hlc_counter_reset_total` / node_id restart | HLC persistence health |
| Per-endpoint request rate & error ratio | Incident triage |
| `directive_modify_rate_limited_total` | Per-actor 429 before write-queue 503 |

Logs MUST include `lineage_id`, `revision`, `finding_id`, `event_id`, `actor_id`, outbox `worker_id` where applicable. Traces SHOULD span `api` → `*_application` → repository.

## Security considerations (ops surface)

1. Network segmentation: Data zone not reachable from Public without Application  
2. Hermetic boundary during compile (no mid-compile egress)  
3. Write-once Artifacts; append-only Finding Events; immutable Compiled Rules (store contracts)  
4. Capability enforcement at `api` only — catalog in authorization contracts  
5. Denial audit via **DenialAuditPort** path (C4 edge; package port ownership) — never skip on deny  
6. Per-actor rate limits on `directive.modify` / `directive.create` — 429 before write lock  
7. TLS on all production hops; encryption at rest for all stores  
8. Offline `certification_tool` is not network-exposed as a product peer  
9. Production JWT revocation per authentication contract  

## Related documents

- [C4 Architecture](../c4-model/README.md) — peers  
- [Package Diagrams](../package/README.md) — modules / ports  
- [State machines](../state/README.md) — FSMs  
- [Spec contracts](../spec/README.md) — behavior  
- [OpenAPI security](../api/components/security.yaml)  
- [View concerns](../standards/view_concerns.md)
