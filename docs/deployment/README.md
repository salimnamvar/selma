# Selma — Deployment Documentation

Infrastructure and deployment architecture for the Selma Rule Regularity Platform.

## Diagram Index

| ID | Title | File | Description |
|:---|:------|:-----|:------------|
| **DEP-001** | Production Deployment | [`dep_001_production.puml`](dep_001_production.puml) | Full production topology: network zones, containers, data stores, external systems, monitoring |

## Network Zones

| Zone | Purpose | Components |
|:-----|:--------|:-----------|
| **Public** | User-facing entry point | Load Balancer, Selma Interface |
| **Application** | Core business logic | Selma Application container |
| **Data** | Persistent storage | PostgreSQL, CGIR Store, Event Store, Artifact Store |
| **External** | Third-party integrations | Governance Contracts, CI/CD, Target Systems, Audit Platform, Remediation |
| **Monitoring** | Observability stack | Prometheus/Grafana, ELK/Loki, Jaeger |

## Environment Requirements

### Runtime

| Requirement | Version | Notes |
|:------------|:--------|:------|
| Python | 3.11+ | Runtime for Selma Application |
| Docker | 24+ | Container runtime |
| PostgreSQL | 15+ | Directive Store, Event Store |
| Nginx / Traefik | latest | Load balancer and TLS termination |

### Compute Resources (per Selma Application container)

| Resource | Minimum | Recommended |
|:---------|:--------|:------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB | 50 GB (for local CGIR/artifact cache) |

### Data Store Sizing

| Store | Storage Type | Scaling Strategy |
|:------|:-------------|:-----------------|
| Directive Store | PostgreSQL (managed or self-hosted) | Vertical + read replicas |
| CGIR Store | Filesystem or S3-compatible | Horizontal (object store) |
| Event Store | PostgreSQL (append-only) or Kafka | Partition by time |
| Artifact Store | S3-compatible object store | Horizontal (object store) |

## Deployment Notes

### Hermetic Compiler

The Hermetic Compiler operates in a **network-isolated environment** during rule compilation. This ensures:

- Deterministic compilation output (no external fetches mid-compile)
- Security guarantee: compiled rules cannot exfiltrate data during compilation
- Governance Contracts (Git) are cloned **before** entering the hermetic boundary

### TLS Termination

TLS is terminated at the load balancer. Internal traffic between zones uses plain HTTP within the trusted network. For zero-trust environments, enable mTLS between zones.

### Connection Pooling

Use PgBouncer or equivalent connection pooler in front of PostgreSQL to manage:

- Directive Store connections (read/write with locking)
- Event Store connections (append-only writes)

### Backup & Recovery

| Store | Backup Strategy | RPO | RTO |
|:------|:----------------|:----|:----|
| Directive Store | Automated PITR (point-in-time recovery) | < 5 min | < 1 hour |
| CGIR Store | None required (reconstructable from Governance Contracts) | N/A | < 30 min (recompile) |
| Event Store | Replicated + archived to Audit Platform | < 1 min | < 1 hour |
| Artifact Store | Cross-region replication | < 15 min | < 2 hours |

### Horizontal Scaling

The Selma Application supports horizontal scaling via multiple container replicas behind the load balancer. State is fully externalized to the data stores. The Hermetic Compiler does not require sticky sessions.

### Monitoring Endpoints

| Stack | Protocol | Purpose |
|:------|:---------|:--------|
| Prometheus | HTTP `/metrics` | Application and infrastructure metrics |
| ELK / Loki | OTLP or stdout | Structured application logs |
| Jaeger | OTLP / Jaeger agent | Distributed request tracing |

## Security Considerations

1. **Network segmentation**: Data zone is not directly accessible from Public zone; all traffic routes through Application zone
2. **Hermetic boundary**: No network egress during compile phase
3. **Write-once artifacts**: Artifact Store enforces WORM (write once, read many) semantics
4. **Append-only events**: Event Store is append-only; no mutation or deletion of events
5. **Immutable CGIR**: Compiled rule snapshots are content-addressed and immutable
6. **Capability enforcement**: All user actions are gated by capability checks at the Application Service boundary
