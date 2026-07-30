# 03 — Ports & Adapters (Hexagonal)

## Dependency rule

```
interfaces (CLI / TUI / REST)
        │
        ▼
application (use cases, ports)
        │
        ▼
domain (aggregates, VOs, domain services)
        ▲
        │ implements ports
infrastructure (adapters, evaluators, parsers, DBs)
```

- **Domain** depends on nothing inside the app.
- **Application** depends on domain + port interfaces only.
- **Infrastructure** implements ports; may use frameworks.
- **Interfaces** call application use cases; never domain repositories directly.

## Driving adapters (primary / inbound)

| Adapter | C4 | Protocol | Use cases invoked |
| :--- | :--- | :--- | :--- |
| REST API | `selma_interface` → `application_service` | HTTP/JSON | All mutating + query families |
| CLI | interface | argv / exit codes | inspect, query, certify (subset) |
| TUI | interface | interactive | inspect, finding workflow (subset) |
| CI/CD hook | external `cicd` | pipeline job | `RunArchitecturalCertification` |

## Driven adapters (secondary / outbound)

| Port (application) | Adapter (infrastructure) | Store / system | Contract |
| :--- | :--- | :--- | :--- |
| `DirectiveRepository` | Directives Adapter (`SqlDirectiveRepository`) | `directive_store` (executable + policy doctrine dual documents) | `data_stores/directive_store`, `rule_schema.json`, `policy_doctrine.yaml` |
| `CgIrRepository` | Compiled Rules Adapter | `cgir_store` | `data_stores/cgir_store` |
| `EventStore` | Findings & Audit Trail Adapter | `event_store` | `data_stores/event_store` |
| `ArtifactRepository` | Inspection Snapshots Adapter | `artifact_store` | `data_stores/artifact_store` |
| `TargetGateway` | Target Adapter | `regulated_systems` | inspection target schema |
| `DetectionEngine` | adapter registry + pure evaluators | in-process | compilation + inspection |
| `AuditReplicator` | Findings/Snapshots adapters | `audit_platform` | replication only |
| `RemediationNotifier` | optional notifier | `remediation_systems` | notify only, no remote mutate |
| `Clock` / `HlcClock` | system clock + HLC | — | event ordering |
| `HashService` | SHA-256 (or versioned algo) | — | node/snapshot/event hashes |
| `CapabilitySource` | authn/authz provider | claims / RBAC map | `authorization/*` |

## Port catalog

See: [`../class-diagram/`](../class-diagram/) for port interface signatures.

| Port | Owner | Contract |
| :--- | :--- | :--- |
| `DirectiveRepository` | `directives_adapter` | `data_stores/directive_store` (dual documents) |
| `CgIrRepository` | `compiled_rules_adapter` | `data_stores/cgir_store` |
| `EventStore` | `findings_audit_adapter` | `data_stores/event_store` |
| `ArtifactRepository` | `snapshots_adapter` | `data_stores/artifact_store` |
| `TargetGateway` | `target_adapter` | inspection target schema |
| `DetectionEngine` | adapter registry | compilation + inspection |
| `AuditReplicator` | `event_adapter` | replication only |
| `RemediationNotifier` | optional notifier | notify only, no remote mutate |
| `Clock` / `HlcClock` | system clock + HLC | event ordering |
| `HashService` | SHA-256 (or versioned algo) | node/snapshot/event hashes |
| `CapabilitySource` | authn/authz provider | `authorization/*` |

**Dual-document `DirectiveRepository`:** persists and loads both the executable rule document and the policy doctrine document for each directive revision. Methods include `readExecutable` (compile path) and `readPolicyDoctrine` (guidance path via `paired_policy_ref`).

**`readPolicyDoctrine` consumers:** `finding_analyzer` / `ResolveGuidance` only after findings exist (**guidance_only**).
**Forbidden consumers of doctrine:** `rule_inspector` evaluation path, `lifecycle_finder` transition logic. Hermetic compiler uses `readExecutable` only (may validate pairing/version consistency, never evaluate doctrine prose).

## Relationship styles (C4 alignment)

| Edge | Style meaning |
| :--- | :--- |
| Application → core components | command / query dispatch |
| Core → adapters | port calls |
| `finding_analyzer` → `directives_adapter.readPolicyDoctrine` | **guidance_only** |
| Adapters → external audit | replicate |
| Analytics → CG-IR / FSM | **forbidden write** (AA-01) |

## Testing ports

| Test type | Doubles |
| :--- | :--- |
| Domain unit | pure aggregates/services; no ports |
| Application | in-memory fakes for all driven ports |
| Adapter contract | testcontainers / filesystem CAS fixtures |
| Certification | AA gate suite against reference fixtures |

## Explicit non-ports

Do **not** expose:

- Direct SQL/session from application use cases
- A separate `PolicyDoctrineReader` or filesystem doctrine adapter (doctrine lives in `directive_store` via `DirectiveRepository`)
- Global mutable “current policy” used by evaluators
- Finding FSM transition helpers that accept policy prose
