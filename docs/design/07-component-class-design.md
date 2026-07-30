# 07 — Component Class Design

See: [`../class-diagram/`](../class-diagram/) for structure, methods, and fields.

## C4 component → design mapping

| C4 ID | Class / package focus | Contracts |
| :--- | :--- | :--- |
| `api` | REST routers, capability gate, DTO mapping | `interfaces/*`, `authorization/*` |
| `compilation` | CompileDirectives, MaterializeCgIr, PublishSnapshot | `compilation/*` |
| `inspection` | SubmitInspection, pipeline stages | `inspection/*` |
| `findings` | Finding FSM use cases, ResolveGuidance, read models | `finding_lifecycle/*`, guidance |
| `directives_repository` | SqlDirectiveRepository | `data_stores/directives` |
| `compiled_rules_repository` | ContentAddressedCgIrStore | `data_stores/compiled_rules` |
| `finding_events_repository` | AppendOnlyEventLog | `data_stores/finding_events` |
| `artifacts_repository` | ObjectArtifactStore | `data_stores/artifacts` |
| `target_sources_gateway` | HttpTargetGateway (optional) | target schema |

## Domain services (not C4 components)

| Service | Used by | Contract |
| :--- | :--- | :--- |
| `ResolveConflict` | `compilation`, `inspection`, `findings` | `conflict/*` |
| `LineageService` | directive use cases via `api` | `directive/identity` |
| `FindingFsm` | `findings` | `finding_lifecycle/*` |
| `GuidanceResolver` | `findings` | policy doctrine schema |

## Adapter → port mapping

| Adapter class | Port | C4 store / system |
| :--- | :--- | :--- |
| `SqlDirectiveRepository` | `DirectiveRepository` | `directives` |
| `ContentAddressedCgIrStore` | `CgIrRepository` | `compiled_rules` |
| `AppendOnlyEventLog` | `EventStore` | `finding_events` |
| `ObjectArtifactStore` | `ArtifactRepository` | `artifacts` |
| `HttpTargetGateway` | `TargetGateway` | `target_sources` (optional) |

**Constraints:**

- No separate doctrine reader; doctrine only via `DirectiveRepository.readPolicyDoctrine`.
- `findings` must not write `compiled_rules` or mutate directives from analytics.
- `inspection` must not call `readPolicyDoctrine` on evaluate path.
- Certification (AA-01…AA-07) is an offline/CI tool, not an in-process C4 peer.
