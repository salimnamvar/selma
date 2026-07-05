# Contracts Directory

Dual-schema architecture for universal rule governance. Two independent contracts, one thin connection.

## Architecture

```
+-------------------------------+         +-------------------------------+
|    policy_doctrine.yaml       |         |     rule_schema.json          |
|  (The Societal Lens)          |         |  (The Mechanical Lens)        |
|                               |         |                               |
|  - Writing Principles         |         |  - Data Structure             |
|  - Document Sections          |         |  - Lifecycle States           |
|  - Governance & Amendment     |<------->|  - Dependencies               |
|  - Sanctions & Remedies       |  Label  |  - Evaluator Routing          |
|  - Directive Tables           |  Only   |  - Parameters & Conditions    |
|  - Priority Hierarchy         |         |  - Complexity Limits          |
|                               |         |  - Priority Reference         |
|  FORBIDDEN: parameters,       |         |  FORBIDDEN: preamble,         |
|  conditions, evaluator_hint,  |         |  governance, definitions,     |
|  weight, depends_on, etc.     |         |  principles, sanctions, etc.  |
+-------------------------------+         +-------------------------------+
```

## The Separation Principle

**Policy Contract** defines *why* and *how* humans write rules:
- Prose structure, editorial standards, governance processes, social consequences
- A diplomat can edit this without knowing what a "regex" is

**Rule Contract** defines *what* a machine executes:
- Data structure, lifecycle, dependencies, evaluator routing hints
- A kernel developer can extend this without caring about the "Governance" section

## The Traceability Bond

The contracts connect in exactly **one** way:

- **Policy → Rule**: Directive tables contain a `Machine ID` column (cross-reference label)
- **Rule → Policy**: Each rule has an `anchor_ref` field (link back to policy document section)

This forms a strict bidirectional pointer:
- Policy says: *"This paragraph is about Rule `R-001`."*
- Rule says: *"Rule `R-001` points back to `section:directives`."*

## Contamination Guards

Each contract explicitly lists what it MUST NOT contain:

### Policy Contract Forbidden Fields
`parameters`, `conditions`, `evaluator_hint`, `weight`, `depends_on`, `conflicts_with`, `status`, `created_at`, `expires_at`, `remediation`, `target`, `technical_hints`

### Rule Contract Forbidden Root Fields
`preamble`, `governance`, `definitions`, `principles`, `sanctions`, `references`, `writing_principles`, `sections`, `guidance`, `columns`

## Version Synchronization

Both contracts reference each other's version:
- `policy_doctrine.yaml` → `doctrine.rule_contract_version` + `doctrine.rule_contract_id`
- `rule_schema.json` → `policy_contract_version` + `policy_contract_id`

Update both when either contract changes.

## Priority Hierarchy

Rules exist at different authority levels. When two rules conflict, the higher-priority rule wins:

1. **Constitutional** - Core principles that cannot be overridden
2. **Statutory** - Rules enacted by authorized governing bodies
3. **Regulatory** - Rules created by agencies to implement statutory requirements
4. **Operational** - Day-to-day procedures implementing higher-level rules
5. **Advisory** - Recommendations that are not mandatory

## Versioning Strategy

Both contracts follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR** - Breaking changes requiring migration
- **MINOR** - New backward-compatible features
- **PATCH** - Bug fixes and clarifications

## Specification

See [SPECIFICATION.md](SPECIFICATION.md) for the full universal rule governance specification.
