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
| **Public** | User-facing entry | Load balancer |
| **Application** | Core process | Application (`api`, compilation, inspection, findings) |
| **Data** | Resource stores | Directives, Compiled Rules, Finding Events, Artifacts |
| **External** | Optional only | Target Sources (pull by reference) |
| **Monitoring** | Observability | Prometheus/Grafana, ELK/Loki, Jaeger |

**Note:** Clients are external to Selma. They are not part of the Selma deployment. The network flow is: Clients → Load Balancer → Application.

CI/CD, long-term audit export, and remediation ticketing are **optional clients/exports**, not required topology peers.

## Environment Requirements

### Runtime

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11+ | Application runtime |
| Docker | 24+ | Container runtime |
| PostgreSQL | 15+ | Directives + Finding Events |
| Nginx / Traefik | latest | TLS termination |

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

## Deployment Notes

### Compilation (hermetic)

- Deterministic compile; no network egress mid-compile
- Executable documents read from **Directives** under read-lock before hermetic boundary
- Policy doctrines are not loaded for evaluation

### TLS

TLS terminates at the load balancer. Internal zone traffic may use plain HTTP in a trusted network; mTLS optional for zero-trust.

### Connection pooling

PgBouncer (or equivalent) for Directives and Finding Events.

### Backup & Recovery

| C4 store | Backup | RPO | RTO |
|:---------|:-------|:----|:----|
| Directives | PITR | < 5 min | < 1 hour |
| Compiled Rules | Rebuild by recompile from Directives | N/A | < 30 min |
| Finding Events | Replicated append log | < 1 min | < 1 hour |
| Artifacts | Cross-region replication | < 15 min | < 2 hours |

### Horizontal scaling

Application replicas behind the load balancer; state externalized to the four stores.

## Security Considerations

1. Network segmentation: Data zone not reachable from Public without Application
2. Hermetic boundary during compile
3. Write-once Artifacts; append-only Finding Events; immutable Compiled Rules
4. Capability enforcement at `api`
