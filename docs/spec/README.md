# Selma — Specification Contracts

Three-layer architecture for rule governance. Spec is normative; schema and policy conform.

## Documents

| File | Role | Version |
| :--- | :--- | :--- |
| [SPECIFICATION.md](SPECIFICATION.md) | Normative behavioral source | 8.2.4 |
| [rule_schema.json](../schema/rule_schema.json) | Structural JSON Schema projection | 8.2.4 |
| [policy_doctrine.yaml](../schema/policy_doctrine.yaml) | Governance intent, reasoning, and guidance | 1.0.0 |
| [User_Stories.md](User_Stories.md) | Behavioral contract | 8.2.4 |
| [State machines](../state-machine/README.md) | Canonical behavioral FSMs | 8.2.4 |

## Architecture

- **SPECIFICATION.md** defines system behavior — algorithms, invariants, execution semantics. The normative source; all other layers conform to it.
- **policy_doctrine.yaml** defines governance intent, reasoning, and remediation guidance. Read at runtime AFTER evaluation to populate finding guidance for humans and AI agents. NOT used for evaluation or finding FSM transitions.
- **rule_schema.json** defines what the machine executes — data structure, lifecycle, evaluator routing. Derived from spec invariants; structural projection, not standalone algorithm.

**Authority:**
- Evaluation authority: Spec > Schema (rule_schema.json). Policy has zero evaluation authority.
- Guidance authority: Policy (policy_doctrine.yaml) is the authoritative source for finding explanations, remediation steps, and domain examples. Read at runtime after evaluation produces a finding.

## Version Compatibility

All three documents share the same MAJOR version. MINOR and PATCH may differ independently. See [SPECIFICATION.md §5](SPECIFICATION.md) for the normative compatibility rule.

## Related

- [C4 Architecture](../c4-model/README.md) — structural architecture
- [State Machines](../state-machine/README.md) — behavioral FSMs
