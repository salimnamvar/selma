# Selma — Specification Contracts

Bounded-context contract tree. Each contract owns one domain, is machine-readable,
and contains its own acceptance criteria.

## Authority

See [`contracts/meta/authority.yaml`](contracts/meta/authority.yaml) for the
normative hierarchy: Spec Contracts > Schema Contracts > Directive Instances.

## Contract Tree

| Domain | Directory | Owner Component | Status |
| :--- | :--- | :--- | :--- |
| **Meta** | `contracts/meta/` | — | Defined |
| **Compilation** | `contracts/compilation/` | Hermetic Compiler | Defined |
| **Inspection** | `contracts/inspection/` | Rule Inspector | Defined |
| **Finding Lifecycle** | `contracts/finding_lifecycle/` | Finding FSM Engine | Defined |
| **Conflict Resolution** | `contracts/conflict/` | Conflict Resolver | Defined |
| **Authorization** | `contracts/authorization/` | Application Service | Defined |
| **Data Stores** | `contracts/data_stores/` | Adapters | Defined |
| **Certification** | `contracts/certification/` | Architectural Auditor | Defined |
| **Directive** | `contracts/directive/` | Directives Adapter | Defined |
| **Interfaces** | `contracts/interfaces/` | Application Service | Defined |

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
owner_component: "c4_component_id"     # Which C4 component owns this
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

- **C4 Architecture** — [`../c4-model/`](../c4-model/) (structural context)
- **State Machines** — [`../state-machine/`](../state-machine/) (behavioral FSMs)
- **Schemas** — [`../schema/`](../schema/) (data structure contracts)
- **Design Freeze** — [`../design/`](../design/README.md) (DDD, ports, packages, use cases)
- **Use Case Catalog** — [`../usecase/`](../usecase/README.md) (human index; stories remain in contracts)

## Migration Status

All content from the monolithic specification has been migrated to the
contract tree. Archives have been deleted. The `contracts/` tree is the
sole normative source for behavioral contracts.