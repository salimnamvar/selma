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
| `DirectiveRepository` | Directives Adapter | `directive_store` | `data_stores/directive_store` |
| `CgIrRepository` | Compiled Rules Adapter | `cgir_store` | `data_stores/cgir_store` |
| `EventStore` | Findings & Audit Trail Adapter | `event_store` | `data_stores/event_store` |
| `ArtifactRepository` | Inspection Snapshots Adapter | `artifact_store` | `data_stores/artifact_store` |
| `TargetGateway` | Target Adapter | `regulated_systems` | inspection target schema |
| `PolicyDoctrineReader` | file/object reader (read-only) | governance policy YAML | `policy_doctrine.yaml` |
| `RuleDatasetReader` | rule JSON loader | governance rule JSON | `rule_schema.json` |
| `DetectionEngine` | adapter registry + pure evaluators | in-process | compilation + inspection |
| `AuditReplicator` | Findings/Snapshots adapters | `audit_platform` | replication only |
| `RemediationNotifier` | optional notifier | `remediation_systems` | notify only, no remote mutate |
| `Clock` / `HlcClock` | system clock + HLC | — | event ordering |
| `HashService` | SHA-256 (or versioned algo) | — | node/snapshot/event hashes |
| `CapabilitySource` | authn/authz provider | claims / RBAC map | `authorization/*` |

## Port catalog (design signatures)

Names are design-level; languages may map to protocols/ABCs.

### DirectiveRepository

```
load(execution_id) -> Directive
load_by_lineage(lineage_id) -> list[DirectiveRevision]
save(directive, expected_version) -> void  # optimistic or lock-aware
acquire_write_lock(scope) / release_write_lock
list_active() -> list[DirectiveSummary]
```

### CgIrRepository

```
publish(snapshot) -> cg_ir_snapshot_hash  # content-addressed; idempotent
get(snapshot_hash) -> CgIrSnapshot
get_latest_for_graph(graph_version) -> CgIrSnapshot | None
find_node_by_hash(node_hash) -> ControlNode | None  # incremental reuse
```

### EventStore

```
append(event) -> void  # fail if hash/HLC invariant broken
read_stream(finding_id) -> list[Event]
read_since(hlc) -> list[Event]
```

### ArtifactRepository

```
put_inspection(snapshot) -> inspection_id
get_inspection(inspection_id) -> InspectionSnapshot
put_conflict(artifact) -> id
put_certification(run) -> id
```

### TargetGateway

```
fetch(target_ref) -> TargetPayload  # schema-validated
```

### PolicyDoctrineReader (**guidance_only**)

```
get(paired_policy_ref) -> PolicyDoctrine
```

**Consumers:** `finding_analyzer` only for guidance resolution after findings exist.  
**Forbidden consumers:** `rule_inspector` evaluation path, `lifecycle_finder` transition logic, `hermetic_compiler` evaluation (compile may validate structure of rules only).

### DetectionEngine

```
validate(rule.detection) -> ValidationResult   # compile-time
evaluate(node, target, context) -> DetectionOutcome  # pure, no I/O
```

## Relationship styles (C4 alignment)

| Edge | Style meaning |
| :--- | :--- |
| Application → core components | command / query dispatch |
| Core → adapters | port calls |
| `finding_analyzer` → doctrine reader | **guidance_only** |
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
- Global mutable “current policy” used by evaluators
- Finding FSM transition helpers that accept policy prose
