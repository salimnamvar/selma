# Contracts Directory

Dual-schema architecture for universal rule governance. Two independent contracts, one thin connection.

## Architecture

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│  human_rule_doctrine.yaml   │         │  machine_rule_schema.json   │
│  (The Societal Lens)        │         │  (The Mechanical Lens)      │
│                             │         │                             │
│  - Writing Principles       │         │  - Data Structure           │
│  - Document Sections        │         │  - Lifecycle States         │
│  - Governance & Amendment   │◄───────►│  - Dependencies             │
│  - Sanctions & Remedies     │  Label  │  - Evaluator Routing        │
│  - Directive Tables         │  Only   │  - Parameters & Conditions  │
│                             │         │                             │
│  FORBIDDEN: parameters,     │         │  FORBIDDEN: preamble,       │
│  conditions, evaluator_hint,│         │  governance, definitions,   │
│  weight, depends_on, etc.   │         │  principles, sanctions, etc.│
└─────────────────────────────┘         └─────────────────────────────┘
```

## The Separation Principle

**Human Contract** defines *why* and *how* humans write rules:
- Prose structure, editorial standards, governance processes, social consequences
- A diplomat can edit this without knowing what a "regex" is

**Machine Contract** defines *what* a machine executes:
- Data structure, lifecycle, dependencies, evaluator routing hints
- A kernel developer can extend this without caring about the "Governance" section

## The Traceability Bond

The contracts connect in exactly **one** way:

- **Human → Machine**: Directive tables contain a `Machine ID` column (cross-reference label)
- **Machine → Human**: Each rule has an `anchor_ref` field (link back to human document section)

This forms a strict bidirectional pointer:
- Human says: *"This paragraph is about Rule `R-001`."*
- Machine says: *"Rule `R-001` points back to `section:directives`."*

## Contamination Guards

Each contract explicitly lists what it MUST NOT contain:

### Human Contract Forbidden Fields
`parameters`, `conditions`, `evaluator_hint`, `weight`, `depends_on`, `conflicts_with`, `status`, `created_at`, `expires_at`, `remediation`, `target`, `technical_hints`

### Machine Contract Forbidden Root Fields
`preamble`, `governance`, `definitions`, `principles`, `sanctions`, `references`, `writing_principles`, `sections`, `guidance`, `columns`

## Version Synchronization

Both contracts reference each other's version:
- `human_rule_doctrine.yaml` → `doctrine.machine_contract_version`
- `machine_rule_schema.json` → `human_contract_version` + `human_contract_id`

Update both when either contract changes.

## Usage

1. **Edit Human YAML** → Define prose, governance, sanctions for your domain
2. **Edit Machine JSON** → Define data structure, lifecycle, evaluator routing
3. **Cross-reference** → Human tables use `Machine ID` column; Machine rules use `anchor_ref`
4. **Validate** → Ensure no contamination (human has no machine fields, machine has no human fields)
