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

## Migration Status

| Artifact | From | To | Status |
| :--- | :--- | :--- | :--- |
| SPECIFICATION.md | `SPECIFICATION.md` | `contracts/` tree | Archived |
| User_Stories.md | `User_Stories.md` | Embedded in contracts | Archived |
| Schema files | `../schema/` | `../schema/` | Unchanged |
| §2.2–§2.5 Directive | `SPECIFICATION.md §2.2–§2.5` | `contracts/directive/*.yaml` | **Migrated** |
| §2.4–§2.7 Compilation | `SPECIFICATION.md §2.4–§2.7` | `contracts/compilation/*.yaml` | **Migrated** |
| §2.14–§2.16 Event Stream | `SPECIFICATION.md §2.14–§2.16` | `contracts/data_stores/event_store.yaml` | **Migrated** |
| §3.1 Finding FSM | `SPECIFICATION.md §3.1` | `contracts/finding_lifecycle/*.yaml` | **Migrated** |
| §3.2 SoD / Capabilities | `SPECIFICATION.md §3.2` | `contracts/finding_lifecycle/sod_contract.yaml` | **Migrated** |
| §3.3–§3.7 Inspection | `SPECIFICATION.md §3.3–§3.7` | `contracts/inspection/*.yaml` | **Migrated** |
| §3.4–§3.5 Data Stores | `SPECIFICATION.md §3.4–§3.5` | `contracts/data_stores/*.yaml` | **Migrated** |
| §2.15 Conflict Resolution | `SPECIFICATION.md §2.15` | `contracts/conflict/*.yaml` | **Migrated** |
| §7 Metadata / Amendment | `SPECIFICATION.md §7` | `contracts/directive/amendment.yaml` | **Migrated** |
| §9.9 Audit Gates | `SPECIFICATION.md §9.9` | `contracts/certification/gates.yaml` | **Migrated** |
| §2.7 Hermetic Boundary | `SPECIFICATION.md §2.7` | `contracts/compilation/hermetic_boundary.yaml` | **Migrated** |