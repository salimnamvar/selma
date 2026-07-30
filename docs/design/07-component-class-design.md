# 07 — Component Class Design

See: [`../class/`](../class/) for structure, methods, and fields.

Modules use **`{resource}_{layer}`**. Methods use **ROD Verb+Resource** names
(see [03](03-ports-and-adapters.md), [04](04-package-architecture.md), [05](05-application-use-cases.md)).

## C4 → modules

| C4 ID | Modules | Contracts |
| :--- | :--- | :--- |
| `api` | `rest_interface`, `authorization_application` | `interfaces/*`, `authorization/*` |
| `compilation` | `compiled_rules_application` | `compilation/*` |
| `inspection` | `inspections_application` | `inspection/*` |
| `findings` | `findings_application` | `finding_lifecycle/*` |
| `directives_repository` | `directives_infrastructure` | `data_stores/directive_store` |
| `compiled_rules_repository` | `compiled_rules_infrastructure` | `data_stores/cgir_store` |
| `finding_events_repository` | `findings_infrastructure` | `data_stores/event_store` |
| `artifacts_repository` | `artifacts_infrastructure` | `data_stores/artifact_store` |
| `target_sources_gateway` | `inspections_infrastructure` | target schema |

## Domain services (not C4 components)

| Service | Module | Used by |
| :--- | :--- | :--- |
| `ResolveConflict` | `conflicts_domain` | compilation, inspection, findings apps |
| `LineageService` | `directives_domain` | directives_application |
| `FindingFsm` | `findings_domain` | findings_application |
| `GuidanceResolver` | `findings_domain` / application | `GetFindingGuidance` |

## Adapter classes (ROD-aligned)

| Class | Port | Module |
| :--- | :--- | :--- |
| `SqlDirectiveRepository` | `DirectiveRepository` | `directives_infrastructure` |
| `ContentAddressedCompiledRulesRepository` | `CompiledRulesRepository` | `compiled_rules_infrastructure` |
| `AppendOnlyFindingEventRepository` | `FindingEventRepository` | `findings_infrastructure` |
| `ObjectArtifactRepository` | `ArtifactRepository` | `artifacts_infrastructure` |
| `HttpTargetSourcesGateway` | `TargetSourcesGateway` | `inspections_infrastructure` |

**Constraints:**

- No separate doctrine reader; use `GetDirectivePolicyDoctrine`.
- `inspections_application` must not call doctrine getters on evaluate path.
- `findings_application` must not write compiled rules or mutate directives from analytics.
- Certification is offline/CI (`certifications_application`), not an in-process C4 peer.
