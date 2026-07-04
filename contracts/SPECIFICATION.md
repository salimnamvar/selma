# Universal Rule Governance Specification

**Version:** 1.3.0
**Status:** Draft Standard
**Date:** 2026-07-04

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. It establishes two independent but interconnected contracts:

1. **Policy Doctrine** — The human-readable contract governing how rules are written
2. **Rule Schema** — The machine-readable contract defining how rules are executed

### 1.2 Scope

This standard applies to:
- Policy documents (prose rules, governance documents, standards)
- Machine-executable rules (automated enforcement, validation, compliance)
- Systems that bridge human understanding and machine execution

### 1.3 Audience

- Policy authors and governance bodies
- Software engineers building rule engines
- Compliance officers and auditors
- Standards organizations

---

## 2. Architecture

### 2.1 The Dual-Contract Model

The system employs a strict separation between human and machine concerns:

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│    policy_doctrine.yaml     │         │     rule_schema.json        │
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

### 2.2 The Separation Principle

**Policy Contract** defines *why* and *how* humans write rules:
- Prose structure, editorial standards, governance processes, social consequences
- A diplomat can edit this without knowing what a "regex" is

**Rule Contract** defines *what* a machine executes:
- Data structure, lifecycle, dependencies, evaluator routing hints
- A kernel developer can extend this without caring about the "Governance" section

### 2.3 The Traceability Bond

The contracts connect in exactly **one** way:

- **Policy → Rule**: Directive tables contain a `Machine ID` column (cross-reference label)
- **Rule → Policy**: Each rule has an `anchor_ref` field (link back to policy document section)

This forms a strict bidirectional pointer:
- Policy says: *"This paragraph is about Rule `R-001`."*
- Rule says: *"Rule `R-001` points back to `section:directives`."*

---

## 3. Contamination Guards

### 3.1 Principle

Each contract MUST NOT contain fields that belong to the other contract. This prevents:
- Human documents becoming machine configuration files
- Machine schemas becoming governance documents
- Confusion about which contract governs what

### 3.2 Policy Contract Forbidden Fields

The following fields are FORBIDDEN in policy documents:

| Field | Reason |
|-------|--------|
| `parameters` | Machine configuration, not human prose |
| `conditions` | Activation logic, not governance |
| `evaluator_hint` | Implementation detail |
| `weight` | Machine priority, not human importance |
| `depends_on` | Machine dependency graph |
| `conflicts_with` | Machine conflict resolution |
| `status` | Lifecycle state, not governance |
| `created_at` | Machine metadata |
| `expires_at` | Machine lifecycle |
| `remediation` | Implementation detail |
| `target` | Machine targeting |
| `technical_hints` | Implementation detail |

**Allowed machine references:** Only `Machine ID` columns in directive tables (cross-reference labels).

### 3.3 Rule Contract Forbidden Root Fields

The following fields are FORBIDDEN at the root level of rule schemas:

| Field | Reason |
|-------|--------|
| `preamble` | Human prose, not machine data |
| `governance` | Human process, not machine logic |
| `definitions` | Human terminology, not machine data |
| `principles` | Human values, not machine rules |
| `sanctions` | Human consequences, not machine actions |
| `references` | Human citations, not machine data |
| `writing_principles` | Human standards, not machine config |
| `sections` | Document structure, not machine data |
| `guidance` | Human advice, not machine instructions |
| `columns` | Table layout, not machine data |

**Allowed human references:** `anchor_ref` (traceability link) and `message` (human-readable output).

---

## 4. Policy Doctrine Contract

### 4.1 Structure

A policy document MUST contain the following sections:

| Section | Required | Content Type | Purpose |
|---------|----------|--------------|---------|
| Preamble | Yes | Prose | Explain the existential need for these rules |
| Governance & Amendment | Yes | Prose | Define how this doctrine is changed |
| Definitions | Yes | Table | Define all terms used in the document |
| Foundational Principles | Yes | Prose or Table | State high-level morals or axioms |
| Directives | Yes | Mixed | List all rules and standards |
| Sanctions & Remedies | Yes | Table | State consequences of non-compliance |
| References & Annexes | No | Prose or Table | External sources and supplementary data |

### 4.2 Directive Tables

#### Specific Directives Table

| Column | Type | Description |
|--------|------|-------------|
| Type | Enum | Obligation, Prohibition, Permission |
| Description | String | Human-readable rule description |
| Machine ID | String | Cross-reference label (e.g., TRAF-001) |
| Context / Conditions | String | When this rule applies |

#### Flexible Standards Table

| Column | Type | Description |
|--------|------|-------------|
| Description | String | Human-readable standard description |
| Machine ID | String | Cross-reference label (e.g., STND-001) |
| Factors to Consider | String | Variables affecting interpretation |
| Examples | String | Concrete instances of the standard |

### 4.3 Writing Principles

| ID | Title | Description |
|----|-------|-------------|
| WP-001 | Precision over Ambiguity | Use exact, imperative language |
| WP-002 | Definitions First | Define every atomic term before use |
| WP-003 | Structural Integrity | Do not exceed 3 levels of nested sections |
| WP-004 | Traceability | Every substantive paragraph must link to a Machine ID |
| WP-005 | Hierarchy of Authority | Declare how conflicts are resolved |

### 4.4 Priority Hierarchy

Rules exist at different authority levels:

| Level | ID | Title | Description |
|-------|-----|-------|-------------|
| 1 | constitutional | Constitutional / Foundational | Core principles that cannot be overridden |
| 2 | statutory | Statutory / Legislative | Rules enacted by authorized governing bodies |
| 3 | regulatory | Regulatory / Administrative | Rules created by agencies to implement statutory requirements |
| 4 | operational | Operational / Procedural | Day-to-day procedures implementing higher-level rules |
| 5 | advisory | Advisory / Best Practice | Recommendations that are not mandatory |

**Conflict Resolution:**
1. Higher priority level wins (constitutional > statutory > regulatory > operational > advisory)
2. If same level: more specific rule wins over general rule
3. If same specificity: newer rule wins over older rule
4. If same age: rule with explicit conflict resolution wins

### 4.5 Versioning Strategy

Format: `MAJOR.MINOR.PATCH`

| Component | When to Increment |
|-----------|-------------------|
| MAJOR | Breaking changes that require migration |
| MINOR | New features that are backward-compatible |
| PATCH | Bug fixes and clarifications |

**Synchronization:** Both contracts must maintain synchronized versions.

---

## 5. Rule Schema Contract

### 5.1 Required Fields

Every rule MUST contain:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Stable unique identifier |
| `type` | String | Classification (obligation, prohibition, permission, standard) |
| `message` | String | Human-readable output or description |

### 5.2 Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `target` | String | Who or what this rule applies to |
| `status` | String | Lifecycle state (draft, active, deprecated, superseded) |
| `anchor_ref` | String | Link back to human document section |
| `evaluator_hint` | String | How to evaluate (regex, human_judgment, api_call) |
| `weight` | String | Priority/severity (critical, informative) |
| `depends_on` | Array | IDs of rules that must be evaluated first |
| `conflicts_with` | Array | IDs of rules that cannot coexist |
| `created_at` | DateTime | Timestamp of creation |
| `expires_at` | DateTime | Timestamp after which rule is obsolete |
| `parameters` | Object | Unconstrained key-value store for config |
| `conditions` | Object | Activation logic |
| `rationale` | String | Why this rule exists |
| `remediation` | String | What to do if violated |
| `complexity` | Object | Controls rule nesting and evaluation limits |
| `priority` | Enum | Authority level from policy hierarchy |

### 5.3 Complexity Field

The `complexity` field controls rule nesting and evaluation limits:

```json
{
  "complexity": {
    "max_depth": 3,
    "max_conditions": 5,
    "max_parameters": 10
  }
}
```

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `max_depth` | Integer | 3 | 1-10 | Maximum levels of nested conditions |
| `max_conditions` | Integer | 5 | 1-20 | Maximum number of conditions |
| `max_parameters` | Integer | 10 | 1-50 | Maximum number of parameters |

### 5.4 Priority Field

The `priority` field references the authority level from the policy hierarchy:

```json
{
  "priority": "statutory"
}
```

Valid values: `constitutional`, `statutory`, `regulatory`, `operational`, `advisory`

---

## 6. Validation

### 6.1 Policy Validation

A policy document is valid if:
1. All required sections are present
2. Sections have correct content types
3. No forbidden fields appear as structured data keys
4. Machine IDs are present in directive tables

### 6.2 Rules Validation

A rules file is valid if:
1. It passes JSON Schema validation
2. All required fields are present
3. No forbidden fields appear at root level
4. All rules have valid `anchor_ref` references

### 6.3 Traceability Validation

Traceability is valid if:
1. Every Machine ID in policy exists as an `id` in rules
2. Every rule `id` has a corresponding Machine ID in policy
3. Every `anchor_ref` points to a valid section
4. Versions are synchronized between contracts

### 6.4 Contamination Validation

Contamination is valid if:
1. Policy contains no forbidden fields as structured data keys
2. Rules contain no forbidden fields at root level
3. No human prose appears in machine schemas
4. No machine logic appears in human documents

---

## 7. Implementation Guide

### 7.1 Creating a New Domain

1. Create a policy document (`policy.md`) for your domain:
   - Update Preamble with domain context
   - Define domain-specific terms
   - List domain-specific directives
2. Create a rules file (`rules.yaml`) for your domain:
   - Update metadata (jurisdiction, domain)
   - Create rules with unique IDs
   - Link rules to policy sections via `anchor_ref`
3. Validate using the rule-manager service:
   ```bash
   cd services/rule-manager
   python validate.py your-example/
   ```

### 7.2 Building a Rule Engine

1. Parse `rule_schema.json` to understand the data structure
2. Load `rules.yaml` instances
3. Evaluate rules based on `type`, `conditions`, and `parameters`
4. Use `evaluator_hint` to route to appropriate evaluation logic
5. Respect `priority` hierarchy when rules conflict
6. Enforce `complexity` limits during rule evaluation

### 7.3 Maintaining Governance

1. Follow `policy_doctrine.yaml` writing principles
2. Maintain traceability between policy and rules
3. Use versioning strategy for changes
4. Run validators before publishing changes

---

## 8. References

- `contracts/policy_doctrine.yaml` — The policy contract
- `contracts/rule_schema.json` — The rule schema contract
- `services/rule-manager/validate.py` — Validation tooling

---

## 9. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 1.1.0 | 2026-07-04 | Added complexity field |
| 1.2.0 | 2026-07-04 | Added priority hierarchy |
| 1.3.0 | 2026-07-04 | Added versioning strategy |
