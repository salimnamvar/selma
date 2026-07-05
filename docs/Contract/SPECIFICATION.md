# Universal Rule Governance Specification

**Version:** 2.0.0  
**Status:** Draft Standard  
**Date:** 2026-07-05

---

## 1. Introduction

### 1.1 Purpose

This specification defines a universal framework for creating, maintaining, and enforcing rules across any domain. It establishes two independent but interconnected contracts:

1. **Policy Doctrine** — The human-readable contract governing how rules are written
2. **Rule Schema** — The machine-readable contract defining how rules are executed

Together with the Control Derivation Layer and Inspection Authority, these contracts form a complete **Regulatory Operating System (RegOS)**.

### 1.2 Scope

This standard applies to:
- Policy documents (prose rules, governance documents, standards)
- Machine-executable rules (automated enforcement, validation, compliance)
- Control derivation (translating directives into testable conditions)
- Inspection execution (evaluating targets against controls)
- Finding lifecycle (detection, disposition, remediation, closure)
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

### 2.4 The Control Derivation Layer

Between the Rule Schema and the Inspection Authority sits the **Control Derivation Layer**:

```
Directive (Rule Schema)
    ↓
Control Mapping Function: f(directive, scope, semantics) → ControlSet
    ↓
Controls (testable conditions)
    ↓
Executable Representation (normalized constraint graph)
    ↓
Inspection Authority (evaluation engine)
```

**Control Derivation Rules:**

| Derivation Type | Description | Reversible |
| :--- | :--- | :--- |
| **Deterministic** | Directive fields map directly to control conditions via fixed rules | Yes |
| **AI-Assisted** | LLM interprets natural language directive and proposes control conditions | Yes (with human review) |
| **Hybrid** | Deterministic extraction + AI inference for ambiguous cases | Partially |

Each derivation produces a **Control Version** that is independent of the Directive Revision. This allows control logic to evolve without editing the directive text.

### 2.5 The Inspection Execution Pipeline

The Inspection Authority processes targets through a defined pipeline:

```
Target
  → Normalize (parse, extract, standardize)
  → Classify (determine domain, jurisdiction, scope)
  → Select Controls (apply directive scope filters)
  → Evaluate (apply evaluation semantics per control)
  → Aggregate Findings (collect, deduplicate, severity-rank)
  → Generate Report (render findings in requested format)
```

**Pipeline Invariants:**
- Each inspection pins the exact Ruleset Version used
- Normalization is idempotent (same target + same ruleset = same findings)
- Control evaluation order respects dependency graph
- Findings are produced atomically (all or none for a single inspection)

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

## 6. Control Model

### 6.1 Control Definition

A **Control** is a testable condition derived from a directive. Controls are the atomic units evaluated during inspection.

| Field | Type | Description |
|-------|------|-------------|
| `control_id` | String | Unique identifier (e.g., `CTRL-REG-024-01`) |
| `directive_id` | String | Parent directive identifier |
| `directive_revision` | String | Revision of the directive this control was derived from |
| `control_version` | String | Version of this control's evaluation logic |
| `description` | String | Human-readable description of the testable condition |
| `evaluation_semantics` | Enum | How this control resolves: `deterministic`, `probabilistic`, `human_review` |
| `scope` | Object | Applicability context (domain, jurisdiction, filters) |
| `severity_default` | Enum | Default severity if evaluation fails: `critical`, `high`, `medium`, `low`, `informational` |
| `depends_on` | Array | Control IDs that must pass before this control is evaluated |
| `status` | Enum | `draft`, `active`, `deprecated` |

### 6.2 Control Derivation Function

```
ControlSet = f(directive, directive_revision, scope) → [Control]
```

The derivation function is **versioned independently** of the directive. This means:
- A directive can remain unchanged while its control logic evolves
- A control version can change without a directive revision
- The Ruleset Version pins both directive versions and control versions

### 6.3 Evaluation Semantics

Each control defines how it resolves against a target:

| Outcome | Meaning | Required Action |
| :--- | :--- | :--- |
| **Pass** | Target complies with the control | None |
| **Fail** | Target violates the control | Generate Finding |
| **Partial** | Target partially complies | Generate Finding with partial disposition |
| **Needs Review** | Control cannot be evaluated automatically | Escalate to human reviewer |
| **Ambiguous** | Evaluation is uncertain | Apply confidence threshold or escalate |

**Resolution Rules:**
- `Ambiguous` outcomes with confidence ≥ threshold → resolve to Pass/Fail
- `Ambiguous` outcomes below threshold → escalate to Regulatory Official
- `Needs Review` → always escalate to Regulatory Official
- `Partial` → generate Finding with severity proportional to deviation magnitude

### 6.4 Ruleset Version

A **Ruleset Version** is an immutable snapshot of all active directives and their derived controls at a point in time.

| Field | Type | Description |
|-------|------|-------------|
| `ruleset_version` | String | Semantic version (e.g., `3.2.0`) |
| `created_at` | DateTime | Timestamp of snapshot creation |
| `directive_versions` | Map | `{ directive_id: revision }` for all included directives |
| `control_versions` | Map | `{ control_id: version }` for all included controls |
| `scope_filter` | Object | Optional scope filter applied to the snapshot |

**Invariants:**
- Once created, a Ruleset Version is immutable
- Historical inspections reference the exact Ruleset Version used
- A new Ruleset Version is created whenever directives or controls change

---

## 7. Inspection Model

### 7.1 Inspection Record

| Field | Type | Description |
|-------|------|-------------|
| `inspection_id` | String | Unique identifier |
| `target_id` | String | Reference to the submitted target |
| `ruleset_version` | String | Exact ruleset version used for evaluation |
| `inspector` | String | Actor who initiated the inspection |
| `started_at` | DateTime | When evaluation began |
| `completed_at` | DateTime | When evaluation finished |
| `status` | Enum | `pending`, `in_progress`, `completed`, `failed` |
| `finding_count` | Integer | Total findings produced |

**Invariant:** Once `completed`, an inspection record is never modified.

### 7.2 Inspection Report

An Inspection Report is a **renderable artifact** produced from inspection findings. Reports can be:
- Regenerated without rerunning the inspection
- Formatted for different audiences (legal, technical, executive)
- Filtered by severity, disposition, or control type

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | String | Unique identifier |
| `inspection_id` | String | Reference to the inspection |
| `format` | Enum | `legal`, `technical`, `executive`, `json` |
| `generated_at` | DateTime | When the report was rendered |
| `findings` | Array | Findings included in this report |

---

## 8. Finding Model

### 8.1 Finding Record

A Finding is an **immutable record** of a deviation detected during inspection.

| Field | Type | Description |
|-------|------|-------------|
| `finding_id` | String | Unique identifier |
| `inspection_id` | String | Reference to the inspection that produced this finding |
| `control_id` | String | The control that was evaluated |
| `directive_id` | String | The directive that produced the control |
| `directive_revision` | String | Revision of the directive at time of inspection |
| `control_version` | String | Version of the control at time of inspection |
| `ruleset_version` | String | Ruleset version at time of inspection |
| `target_id` | String | The target that was inspected |
| `description` | String | What was observed |
| `evidence` | String | Relevant portions of the target |
| `reasoning` | String | Why this finding was raised |
| `created_at` | DateTime | When the finding was created |
| `lifecycle_status` | Enum | `open`, `closed` |
| `disposition` | Enum | `valid`, `invalid`, `waived` |
| `severity` | Enum | `critical`, `high`, `medium`, `low`, `informational` |

**Invariant:** Once created, a Finding is never modified. Disposition changes are recorded as events on the finding's event log.

### 8.2 Finding Causal Chain

Every finding must be traceable through its causal chain:

```
Finding → Control → Directive → Revision → Scope
```

This chain enables:
- **Explainability:** "Why was this finding raised?" (S-16)
- **Impact Analysis:** "Which findings are affected by a rule change?"
- **Reinspection Diffs:** "What changed between inspection v1 and v2?"

### 8.3 Finding Severity Model

| Severity | Description | Remediation SLA |
| :--- | :--- | :--- |
| **Critical** | Immediate risk, requires urgent action | 24 hours |
| **High** | Significant non-compliance | 7 days |
| **Medium** | Moderate deviation | 30 days |
| **Low** | Minor deviation | 90 days |
| **Informational** | Observation, not a violation | None |

### 8.4 Finding Lifecycle

```
Finding Created (immutable)
    ↓
Lifecycle: Open
    ↓
Disposition: Valid | Invalid | Waived
    ↓
Remediation (mutable, attached to finding)
    ↓
Lifecycle: Closed
```

**Two independent dimensions:**
- **Lifecycle Status:** Open / Closed (whether action is needed)
- **Disposition:** Valid / Invalid / Waived (whether the finding is legitimate)

---

## 9. Remediation Model

### 9.1 Remediation Record

Remediation is a **mutable process** attached to an immutable finding.

| Field | Type | Description |
|-------|------|-------------|
| `remediation_id` | String | Unique identifier |
| `finding_id` | String | Reference to the finding |
| `status` | Enum | `in_progress`, `evidence_submitted`, `pending_verification`, `verified`, `closed` |
| `actor` | String | Who initiated remediation |
| `started_at` | DateTime | When remediation began |
| `evidence` | Array | Submitted evidence records |
| `verified_by` | String | Who verified the remediation |
| `verified_at` | DateTime | When verification occurred |
| `resolution` | Enum | `fixed`, `waived`, `rejected` |

### 9.2 Evidence Record

| Field | Type | Description |
|-------|------|-------------|
| `evidence_id` | String | Unique identifier |
| `remediation_id` | String | Reference to the remediation |
| `submitted_by` | String | Who submitted the evidence |
| `submitted_at` | DateTime | When submitted |
| `content` | String | The evidence itself (text, link, artifact reference) |
| `type` | Enum | `document`, `code_change`, `configuration`, `process_change` |

---

## 10. Authorization Model

### 10.1 Role-Permission Matrix

| Role | Can Create Directive | Can Modify Directive | Can Retire Directive | Can View Findings | Can Acknowledge Finding | Can Submit Evidence | Can Approve Remediation | Can Waive Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Regulatory Official | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Compliance Representative | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |

### 10.2 Segregation of Duties

- The actor who **creates** a directive cannot be the same actor who **waives** a finding derived from it
- The actor who **submits** remediation evidence cannot be the same actor who **approves** it
- These constraints ensure audit integrity

### 10.3 Permission Evaluation Timing

| Action | When Permission Is Checked |
| :--- | :--- |
| Create/Modify/Retire Directive | Pre-execution (before changes are applied) |
| Submit Target for Inspection | Pre-execution (before inspection begins) |
| Acknowledge Finding | Pre-execution (before remediation record is created) |
| Submit Evidence | Pre-execution (before evidence is attached) |
| Approve/Reject Remediation | Pre-execution (before finding status changes) |
| Waive Finding | Pre-execution (before disposition is changed) |

---

## 11. Conflict Resolution Engine

### 11.1 Directive Conflicts

When two directives produce contradictory controls:

1. Apply Priority Hierarchy (Section 4.4)
2. If same priority: more specific directive wins
3. If same specificity: newer directive wins
4. If unresolved: flag for Regulatory Official review

### 11.2 Control Conflicts

When two controls produce contradictory findings for the same target:

1. Check `depends_on` graph for ordering
2. Apply directive priority hierarchy
3. If same priority: generate both findings with `Ambiguous` disposition
4. Escalate to Regulatory Official for resolution

### 11.3 Finding Conflicts

When a finding contradicts a previous finding for the same target + control:

1. If same ruleset version: flag as duplicate (suppress)
2. If different ruleset version: both findings are valid (regulatory change occurred)
3. If different target version: both findings are valid (target changed)

---

## 12. System Invariants

These rules must never be violated:

| Invariant | Description |
| :--- | :--- |
| **Finding Immutability** | Once created, a finding is never modified. Disposition changes are recorded as events. |
| **Inspection Immutability** | Once completed, an inspection record is never modified. Reinspection creates a new inspection. |
| **Directive ID Immutability** | A directive's identifier never changes across revisions. Only the revision number increments. |
| **Ruleset Version Anchoring** | Every inspection references the exact ruleset version used. Historical inspections are never retroactively updated. |
| **Causal Traceability** | Every finding must be traceable: Finding → Control → Directive → Revision → Scope. |
| **Segregation of Duties** | The actor who creates a directive cannot waive findings derived from it. |
| **Control Version Independence** | Control versions are independent of directive revisions. |
| **Pipeline Atomicity** | An inspection either produces all findings or fails entirely. No partial results. |

---

## 13. Validation

### 13.1 Policy Validation

A policy document is valid if:
1. All required sections are present
2. Sections have correct content types
3. No forbidden fields appear as structured data keys
4. Machine IDs are present in directive tables

### 13.2 Rules Validation

A rules file is valid if:
1. It passes JSON Schema validation
2. All required fields are present
3. No forbidden fields appear at root level
4. All rules have valid `anchor_ref` references

### 13.3 Traceability Validation

Traceability is valid if:
1. Every Machine ID in policy exists as an `id` in rules
2. Every rule `id` has a corresponding Machine ID in policy
3. Every `anchor_ref` points to a valid section
4. Versions are synchronized between contracts

### 13.4 Contamination Validation

Contamination is valid if:
1. Policy contains no forbidden fields as structured data keys
2. Rules contain no forbidden fields at root level
3. No human prose appears in machine schemas
4. No machine logic appears in human documents

### 13.5 Control Validation

Controls are valid if:
1. Every control references a valid directive_id
2. Every control has a valid evaluation_semantics value
3. Dependency graph has no cycles
4. Control versions are tracked independently

---

## 14. Implementation Guide

### 14.1 Creating a New Domain

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

### 14.2 Building a Rule Engine

1. Parse `rule_schema.json` to understand the data structure
2. Load `rules.yaml` instances
3. Derive controls from directives using the Control Mapping Function
4. Evaluate controls based on `evaluation_semantics`
5. Respect `priority` hierarchy when rules conflict
6. Enforce `complexity` limits during rule evaluation

### 14.3 Maintaining Governance

1. Follow `policy_doctrine.yaml` writing principles
2. Maintain traceability between policy and rules
3. Use versioning strategy for changes
4. Run validators before publishing changes

---

## 15. References

- `docs/Contract/policy_doctrine.yaml` — The policy contract
- `docs/Contract/rule_schema.json` — The rule schema contract
- `docs/User_Story/User_Stories.md` — User stories defining the system behavior

---

## 16. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-04 | Initial specification |
| 1.1.0 | 2026-07-04 | Added complexity field |
| 1.2.0 | 2026-07-04 | Added priority hierarchy |
| 1.3.0 | 2026-07-04 | Added versioning strategy |
| 2.0.0 | 2026-07-05 | Added Control Model, Inspection Pipeline, Finding Model, Remediation Model, Authorization Model, Conflict Resolution Engine, System Invariants |
