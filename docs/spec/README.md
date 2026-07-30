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
| **Compilation** | `contracts/compilation/` | `compilation` | Defined |
| **Inspection** | `contracts/inspection/` | `inspection` | Defined |
| **Finding Lifecycle** | `contracts/finding_lifecycle/` | `findings` | Defined |
| **Conflict Resolution** | `contracts/conflict/` | `ResolveConflict` (domain service; used by compilation / inspection / findings) | Defined |
| **Authorization** | `contracts/authorization/` | `api` | Defined |
| **Data Stores** | `contracts/data_stores/` | `*_repository` adapters | Defined |
| **Certification** | `contracts/certification/` | `certification_tool` (offline/CI; not an in-process C4 peer) | Defined |
| **Directive** | `contracts/directive/` | `directives_repository` (+ `api` orchestration) | Defined |
| **Interfaces** | `contracts/interfaces/` | `api` / `clients` | Defined |

### Data store contract filenames → C4 store IDs

| Contract file | C4 store ID | Repository component |
| :--- | :--- | :--- |
| `data_stores/directive_store.yaml` | `directives` | `directives_repository` |
| `data_stores/cgir_store.yaml` | `compiled_rules` | `compiled_rules_repository` |
| `data_stores/event_store.yaml` | `finding_events` | `finding_events_repository` |
| `data_stores/artifact_store.yaml` | `artifacts` | `artifacts_repository` |

## Schema Contracts (Separate)

| File | Role | Version |
| :--- | :--- | :--- |
| [`rule_schema.json`](../schema/rule_schema.json) | Executable rule structure | 1.0.0 |
| [`policy_doctrine.yaml`](../schema/policy_doctrine.yaml) | Guidance and reasoning structure | 1.0.0 |

## Contract File Structure

Every contract file follows this template:

```yaml
contract_id: "domain.subdomain"        # e.g., "compilation.pipeline"
schema_version: "1.0.0"                # Must match meta/versioning.yaml
owner_component: "c4_component_id"     # C4 ID from docs/c4-model/
state_machine_ref: "../state-machine/xxx.puml"  # If applicable

invariants:
  - id: "INV-XXX-001"
    statement: "What MUST always be true"
    enforcement: "how_enforced"

stages: / transitions: / rules:        # Domain-specific structure
  ...

stories:                                # Acceptance criteria live HERE
  - story_id: "US-XXX-001"
    as: "actor_or_component"
    i_want: "capability"
    so_that: "benefit"
    acceptance_criteria:
      - "Given ... When ... Then ..."
```

## Cross-References

- **C4 Architecture** — [`../c4-model/`](../c4-model/) (structural source of truth)
- **State Machines** — [`../state-machine/`](../state-machine/) (behavioral FSMs)
- **Schemas** — [`../schema/`](../schema/) (data structure contracts)
- **Design Freeze** — [`../design/`](../design/README.md) (DDD, ports, packages, use cases)
- **Use Case Diagrams** — [`../usecase-diagram/`](../usecase-diagram/README.md) (index only; stories remain in contracts)

## Migration Status

All content from the monolithic specification has been migrated to the
contract tree. Archives have been deleted. The `contracts/` tree is the
sole normative source for behavioral contracts.
