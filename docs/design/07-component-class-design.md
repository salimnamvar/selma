# 07 — Component Class Design

See: [`../class-diagram/`](../class-diagram/) for component class structure, methods, and fields.

## Component → class diagram mapping

| C4 Component | Class diagram | Contracts |
| :--- | :--- | :--- |
| `application_service` | `cd_001_domain_model.puml` | `interfaces/*`, `authorization/*` |
| `hermetic_compiler` | `cd_001_domain_model.puml` | `compilation/*` |
| `rule_inspector` | `cd_001_domain_model.puml` | `inspection/*` |
| `conflict_resolver` | `cd_001_domain_model.puml` | `conflict/*` |
| `lifecycle_finder` | `cd_001_domain_model.puml` | `finding_lifecycle/*` |
| `finding_analyzer` | `cd_001_domain_model.puml` | `inspection/finding_contract.yaml`, `schema/policy_doctrine.yaml` |
| `architectural_auditor` | `cd_001_domain_model.puml` | `certification/gates.yaml` |

## Adapter → port mapping

| Adapter class | Port | Store / system |
| :--- | :--- | :--- |
| `SqlDirectiveRepository` | `DirectiveRepository` | `directive_store` (executable rule + policy doctrine dual documents) |
| `ContentAddressedCgIrStore` | `CgIrRepository` | `cgir_store` |
| `AppendOnlyEventLog` | `EventStore` | `event_store` |
| `ObjectArtifactStore` | `ArtifactRepository` | `artifact_store` |
| `HttpTargetGateway` | `TargetGateway` | `regulated_systems` |

**Constraints:**
- There is **no** separate `PolicyDoctrineReader` / filesystem doctrine adapter.
- `finding_analyzer` must not write CG-IR, directives, or FSM state; guidance uses `DirectiveRepository.readPolicyDoctrine` only.
- `rule_inspector` must not call `readPolicyDoctrine` on the evaluate path.
- Language-specific code (e.g. Python AST) lives only behind adapters referenced from `detection.adapters[]`, not in domain.

Gate definitions: `certification/gates.yaml` (including AA-02 guidance_only interpretation).
