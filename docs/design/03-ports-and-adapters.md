# 03 — Ports & Adapters (Hexagonal / Clean Architecture)

## Dependency rule

```
clients (CLI / Web / Desktop / Mobile)
        │
        ▼
api (resource-oriented ingress)
        │
        ▼
application use cases (compilation, inspection, findings, directives)
        │
        ▼
domain (aggregates, VOs, domain services)
        ▲
        │ implements ports
infrastructure (*_repository, *_gateway)
```

- **Domain** depends on nothing inside the app.
- **Application** depends on domain + port interfaces only.
- **Infrastructure** implements ports; may use frameworks.
- **Clients** call the API; never domain repositories directly.

## Driving adapters (primary / inbound)

| Adapter | C4 | Protocol | Use cases |
| :--- | :--- | :--- | :--- |
| REST / channel clients | `clients` → `api` | HTTPS / resource JSON | All mutating + query families |
| CLI / TUI | `clients` | argv / interactive | inspect, findings, certify subset |

## Driven adapters (secondary / outbound)

| Port (application) | Adapter (infrastructure) | C4 store / system | Contract |
| :--- | :--- | :--- | :--- |
| `DirectiveRepository` | Directives Repository | `directives` | `data_stores/directive_store` |
| `CgIrRepository` | Compiled Rules Repository | `compiled_rules` | `data_stores/cgir_store` |
| `EventStore` | Finding Events Repository | `finding_events` | `data_stores/event_store` |
| `ArtifactRepository` | Artifacts Repository | `artifacts` | `data_stores/artifact_store` |
| `TargetGateway` | Target Sources Gateway (optional) | `target_sources` | inspection target schema |
| `DetectionEngine` | adapter registry + pure evaluators | in-process | compilation + inspection |
| `Clock` / `HlcClock` | system clock + HLC | — | event ordering |
| `HashService` | SHA-256 (or versioned algo) | — | node/snapshot/event hashes |
| `CapabilitySource` | authn/authz provider | claims / RBAC map | `authorization/*` |

## Port catalog

| Port | C4 owner | Contract |
| :--- | :--- | :--- |
| `DirectiveRepository` | `directives_repository` | dual-document `directives` |
| `CgIrRepository` | `compiled_rules_repository` | `compiled_rules` |
| `EventStore` | `finding_events_repository` | `finding_events` |
| `ArtifactRepository` | `artifacts_repository` | `artifacts` |
| `TargetGateway` | `target_sources_gateway` | optional remote targets |
| `DetectionEngine` | infrastructure.detection | compilation + inspection |

**Dual-document `DirectiveRepository`:** `readExecutable` (compile path) and `readPolicyDoctrine` (guidance path via `paired_policy_ref`).

**`readPolicyDoctrine` consumers:** `findings` guidance reads only after findings exist (`guidance_only`).  
**Forbidden:** `inspection` evaluate path, finding FSM transition logic. `compilation` uses `readExecutable` only (may check pairing/version).

## Explicit non-ports / non-components

- Separate `PolicyDoctrineReader` or filesystem doctrine adapter
- Peer C4 components for Conflict Resolver, Finding Analyzer, Architectural Auditor
- External Governance Contracts / CI/CD / audit platform / remediation as required runtime peers
- Direct SQL from use cases
- Finding FSM helpers that accept policy prose

## Relationship styles (C4 alignment)

| Edge | Style |
| :--- | :--- |
| `api` → use-case components | command / query dispatch |
| Use cases → repositories | port calls |
| `findings` → `directives_repository.readPolicyDoctrine` | **guidance_only** |
| Repositories → stores | persistence |

## Testing ports

| Test type | Doubles |
| :--- | :--- |
| Domain unit | pure aggregates/services |
| Application | in-memory fakes for driven ports |
| Adapter contract | testcontainers / CAS fixtures |
| Certification | AA gate suite as offline tool against fixtures |
