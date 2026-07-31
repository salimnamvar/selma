# Selma — Specification Contracts

Bounded-context contract tree. Each contract owns one domain, is machine-readable,
and contains its own acceptance criteria.

## Authority

See [`contracts/meta/authority.yaml`](contracts/meta/authority.yaml) for the
normative hierarchy: Spec Contracts > Schema Contracts > Directive Instances.

Structural ownership of contracts maps to **C4 component IDs**
([`../c4-model/README.md`](../c4-model/README.md)).

## Contract Tree

| Domain | Directory | Owner (C4 / design) | Status |
| :--- | :--- | :--- | :--- |
| **Meta** | `contracts/meta/` | — | Defined |
| **Compilation** | `contracts/compilation/` | `compilation_application` | Defined |
| **Inspection** | `contracts/inspection/` | `inspections_application` | Defined |
| **Finding Lifecycle** | `contracts/finding_lifecycle/` | `findings_application` | Defined |
| **Conflict Resolution** | `contracts/conflict/` | `compilation_application` / `inspections_application` (uses ResolveConflict domain service) | Defined |
| **Authorization** | `contracts/authorization/` | `api` | Defined |
| **Data Stores** | `contracts/data_stores/` | `*_repository` adapters + matching `*_store` | Defined |
| **Certification** | `contracts/certification/` | `api` (delegates to external certification_tool) | Defined |
| **Directive** | `contracts/directive/` | `directives_application` (+ `directives_repository`) | Defined |
| **Interfaces** | `contracts/interfaces/` | `api` / `clients` | Defined |

### Data store contract filenames → C4 store IDs

| Contract file | C4 store ID | Repository component |
| :--- | :--- | :--- |
| `data_stores/directives_store.yaml` | `directives_store` | `directives_repository` |
| `data_stores/compiled_rules_store.yaml` | `compiled_rules_store` | `compiled_rules_repository` |
| `data_stores/finding_events_store.yaml` | `finding_events_store` | `finding_events_repository` |
| `data_stores/artifacts_store.yaml` | `artifacts_store` | `artifacts_repository` |

## Schema Contracts (Separate)

| File | Role | Version |
| :--- | :--- | :--- |
| [`rule_schema.json`](../schema/rule_schema.json) | Executable rule structure | 1.0.0 |
| [`policy_doctrine.yaml`](../schema/policy_doctrine.yaml) | Guidance and reasoning structure | 1.0.0 |

## Contract File Structure

```yaml
contract_id: "domain.subdomain"        # e.g., "compilation.pipeline"
schema_version: "1.0.0"
owner_component: "<C4 component ID>"   # e.g., compilation_application
# ... domain-specific normative content ...
acceptance_criteria: [...]
```

## Related

- C4 structure: [`../c4-model/README.md`](../c4-model/README.md)
- State machines: [`../state/`](../state/README.md)
