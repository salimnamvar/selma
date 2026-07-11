# Selma 8.2.4 — Design Mindmap & Visual Architecture

I'll give you three things: (1) a master mindmap, (2) key design diagrams the corpus *doesn't* have but implementers need, and (3) a recommendation for what artifact to build next.

---

## 1. Master Mindmap

```mermaid
mindmap
  root((Selma 8.2.4))
    Document Architecture
      Normative Layer
        SPECIFICATION.md
          System behavior
          Algorithms
          Invariants
          Contracts
      Structural Layer
        rule_schema.json
          Data structure
          JSON Schema Draft-07
          x-* annotations informative
      Governance Layer
        policy_doctrine.yaml
          Writing principles
          Priority intent
          Section templates
          NO runtime authority
      Behavioral Layer
        User_Stories.md
          35 stories across 7 epics
          Acceptance criteria
          Traceability matrix
      Index Layer
        README.md
          Audit corpus checklist
          Compatibility matrix
          Cross-layer binding index
    Runtime Primitives
      Directive Graph
        Human-authored
        Mutable
        Semantic versioned
        Contains prose + directive tables
      CG-IR Compiled Control DAG
        Immutable snapshots
        Content-addressed SHA-256
        Dual hash model
          semantic_hash - compilation cache
          presentation_hash - audit drift
          node_hash - storage key
        Incremental compilation
        Edge hashing - directional node-independent
        Snapshot hash - sorted nodes + edges + provenance
        compiled_at EXCLUDED from hash
      Finding Event Stream
        Append-only
        HLC-ordered total order
        Read-only analytics
        Finding FSM enforced
      Execution Artifacts
        Inspection snapshots
        Pipeline traces
        System state hashes
    Identity Model
      Lineage ID
        Immutable root
        Pattern: XX999
        Audit trail anchor
        Policy: Machine ID maps here
        Unique per root
        Shared after fork/split
      Execution ID
        Active node identity
        Pattern: XX999-SUFFIX
        Changes on fork/merge/split
        Globally unique
        CG-IR: directive_id
      Lifecycle Operations
        Revision - same lineage same id
        Fork - shared lineage two new ids
        Merge - lexmin lineage new id
        Split - shared lineage multiple new ids
        Rename - same lineage same id
        Retire - same lineage status=deprecated
      Lineage DAG
        Acyclic - DFS validated
        Max depth 64
        No self-reference
        Temporal ordering
        Operation consistency
    Compilation Pipeline
      Hermetic Boundary
        Frozen environment
          Engine version
          Toolchain hash
          AI model hashes if applicable
          frozen_env_hash computed
        Read lock on Directive Graph
        Reproducible
      Pipeline Stages
        Normalize
        Classify
        Select controls
        Evaluate
        Aggregate
        Report
      Validators
        JSON Schema structural - first pass
        AST discriminator walker - normative gate
        Evaluator complexity walker
        Lineage DAG validator
        Reference validator
          RE2 canary vectors
          UTC-only timestamps
          Finite numerics
          NFC strings
        Policy version check
    Evaluator System
      Types
        regex - pattern matching
        field_check - structured field validation
        threshold - numeric comparison
        composite - boolean combination
      Contract
        Pure functions
        No IO no randomness
        Deterministic
        Same inputs same outputs
      Portability
        RE2 regex only
        IEEE 754 doubles
        UTC timestamps
        NFC-normalized strings
        No locale collation
      Complexity Limits
        Depth <= 32
        Nodes <= 256
        Width <= 64
        Pattern <= 4096 chars
        Metadata <= 16384 bytes
      Outcome Mapping
        Pass - no finding
        Fail - finding at severity_default
        Partial - finding downgraded one level
        NeedsReview - finding informational only
      Deontic Semantics
        Obligation fail = violation
        Prohibition fail = violation
        Permission fail = advisory only
    Conflict Resolution
      Precedence Chain
        1 Explicit override - schema field
        2 Compatible overrides - symmetric pairs
        3 Priority level - integer 1-5
        4 Specificity score - composite
        5 Recency - created_at frozen
        6 Conflict Artifact - human review
      Specificity Score
        scope_specificity_score x 100
        Plus count_bound_fields
        Normative algorithm in Section 2.15
      Override Strategies
        always_wins
        never_wins
        defer_to - with DFS cycle detection
      Scope
        Within-lineage - deterministic
        Cross-lineage - advisory only
      Temporal Binding
        All inputs frozen in CG-IR
        Snapshot-bound not evaluation-time
    Finding Lifecycle
      FSM States
        Created
        Open
        Acknowledged
        Evidence Submitted
        Pending Verification
        Verified
        Rejected
        Dismissed
        Waived
        Closed terminal
        Dismissed terminal
      Human Transitions
        Open to Acknowledged - S-12
        Open to Dismissed - S-25
        Open to Waived - S-29
        Pending Verification to Verified - S-14a
        Pending Verification to Rejected - S-14b
        Rejected to Open - S-14c
      System Transitions
        Created to Open - automatic
        Evidence Submitted to Pending Verification - automatic
        Verified to Closed - automatic
        Waived to Closed - automatic
      Event Stream
        Append-only
        event_hash per event
        HLC total order
    Capability Model
      Actors
        Regulatory Official
          directive.create modify retire fork merge restore
          finding.view dismiss waive approve_remediation reject_remediation supersede
          analytics.view
          conflict.resolve
        Compliance Representative
          inspection.submit reinspect
          finding.view acknowledge
          evidence.submit
          analytics.view
        System
          inspection.submit
          finding.view
          analytics.view
      Gates
        Request ingress - API Gateway
        Compilation Engine - directive mutations
        Pipeline entry - inspection
        Finding FSM Engine - transitions
        Conflict resolution
      Segregation of Duties
        Creator cannot waive own findings
        Evidence submitter cannot approve own remediation
        creator_provenance inherited through lineage
      Enforcement
        Hard deny - 403 CapabilityDenied
        No partial mutation
        Audit logged
    Cross-Cutting Concerns
      Policy Runtime Prohibition
        Never read at inspection
        Never read at evaluation
        Never read at FSM transitions
        Never read at conflict resolution
        CI scans runtime source
        Boot-time assertion recommended
      Version Synchronization
        MAJOR must match across all layers
        floor S equals floor P
        MINOR PATCH may differ
        Compile-time rejection on mismatch
      Deterministic Serialization
        Canonical JSON sorted keys
        SHA-256 hashing
        NaN Infinity prohibited
        UTC timestamps only
        Ordered vs unordered arrays
      Concurrency
        Compilation = read lock
        Modification = write lock
        Writer-preference FIFO queue
        Deadlock prevention
      Mediated Feedback
        Analytics read-only
        No analytics to CG-IR write path
        Humans close the loop
```

---

## 2. Missing Design Diagrams

The corpus has flow diagrams for the runtime primitives and compilation boundary, but lacks visual representations for the most implementation-critical state machines and data flows. Here are the five diagrams an implementer needs most:

### 2.1 Finding FSM (UML State Machine)

This is the most complex state machine in the system and exists only as a table. Implementers need the visual.

```mermaid
stateDiagram-v2
    [*] --> Created : System\n(finding raised)

    Created --> Open : System\n(automatic)

    Open --> Acknowledged : finding.acknowledge\n[S-12]
    Open --> Dismissed : finding.dismiss\n[S-25]
    Open --> Waived : finding.waive\n[S-29]\n[actor NOT in creator_provenance]

    Acknowledged --> EvidenceSubmitted : evidence.submit\n[S-13]

    EvidenceSubmitted --> PendingVerification : System\n(automatic)

    PendingVerification --> Verified : finding.approve_remediation\n[S-14a]\n[actor NOT evidence submitter]
    PendingVerification --> Rejected : finding.reject_remediation\n[S-14b]

    Rejected --> Open : finding.reopen\n[S-14c]\n(requires comments)

    Verified --> Closed : System\n(automatic)
    Waived --> Closed : System\n(automatic)

    Closed --> [*]
    Dismissed --> [*]

    note right of Open
        Three possible exits:
        acknowledge, dismiss, waive
        Each gated by capability + SoD
    end note

    note right of PendingVerification
        Segregation of duties:
        approver ≠ evidence submitter
        Gated at FSM Engine before transition
    end note

    note left of Waived
        SoD gate:
        actor ∉ creator_provenance
        for finding's directive
    end note
```

### 2.2 Identity Lifecycle State Diagram

Fork/merge/split semantics are described in prose but the state transitions between identity configurations are never visualized.

```mermaid
stateDiagram-v2
    state "Single Root\nlineage=L id=L" as SingleRoot

    state "Forked\nlineage=L\nid=L-A, L-B" as Forked {
        [*] --> ChildA : lineage=L id=L-A
        [*] --> ChildB : lineage=L id=L-B
    }

    state "Split\nlineage=L\nid=L-A, L-B, L-C..." as Split {
        [*] --> Child1
        [*] --> Child2
        [*] --> ChildN
    }

    state "Merged\nlineage=MIN(A,B)\nid=MIN-M+HASH" as Merged

    state "Deprecated\nstatus=deprecated" as Deprecated

    SingleRoot --> Forked : fork\n(parent deprecated)
    SingleRoot --> Split : split\n(parent deprecated)
    SingleRoot --> Deprecated : retire

    Forked --> Merged : merge with another rule\n(lexicographic MIN lineage)
    Split --> Merged : merge with another rule
    Forked --> Deprecated : retire all children
    Split --> Deprecated : retire all children

    Merged --> Forked : fork the merged rule
    Merged --> Split : split the merged rule
    Merged --> Deprecated : retire

    Deprecated --> [*]

    note right of Merged
        Non-surviving parent preserved in
        lineage.parent_lineage_ids only.
        Accepted risk: provenance loss.
        Mitigation: merge_provenance metadata.
    end note
```

### 2.3 Compilation Engine Internal Architecture

The spec defines *what* the compiler does but not *how it's structured internally*. This is the most useful diagram for an implementation team.

```mermaid
flowchart TB
    subgraph Input["Input Gate"]
        DG[Directive Graph]
        POL[policy_doctrine.yaml<br/>authoring-time only]
    end

    subgraph V1["Pass 1: Structural Validation"]
        JS[JSON Schema Validator<br/>Draft-07 first pass]
    end

    subgraph V2["Pass 2: Custom Validators"]
        AST[AST Discriminator Walker<br/>evaluator_type ↔ config]
        CMP[Evaluator Complexity Walker<br/>depth/width/nodes]
        LDAG[Lineage DAG Validator<br/>cycles/depth/existence]
        VER[Reference Validator<br/>RE2 canary / UTC / NaN]
        PVER[Policy Version Check<br/>MAJOR match]
    end

    subgraph V3["Pass 3: Semantic Validation"]
        XFLD[Cross-Field Constraints<br/>scope ↔ priority consistency]
        DEP[Dependency Graph Builder<br/>depends_on acyclicity]
    end

    subgraph HB["Hermetic Boundary"]
        FENV[Frozen Environment<br/>engine + toolchain + AI hashes]
    end

    subgraph COMP["Compilation"]
        IDRES[Identity Resolution<br/>lineage_id + execution_id]
        RULEMAP[Rule → CG-IR Node Mapping<br/>§2.8.1 transform table]
        PARAM[Parameter Merge<br/>shallow merge into evaluator.config]
        CR[Conflict Resolution Mapping<br/>candidate pairs from conflicts_with]
        HASH[Hash Computation<br/>semantic + presentation → node_hash]
        EHASH[Edge Hash Computation<br/>directional source→target]
        INC[Incremental Reuse<br/>dirty marking + cache lookup]
    end

    subgraph Output["Output"]
        SNAP[CG-IR Snapshot<br/>immutable content-addressed]
        PROV[Provenance Record<br/>engine + frozen_env + lineage_validation]
    end

    DG --> JS
    POL -.-> V1
    JS -->|PASS| V2
    JS -->|FAIL| REJECT1[Reject: SchemaError]

    V2 -->|ALL PASS| V3
    V2 -->|ANY FAIL| REJECT2[Reject: SchemaError]

    V3 -->|PASS| HB
    V3 -->|FAIL| REJECT3[Reject: SemanticError]

    HB --> COMP
    FENV --> PROV

    IDRES --> RULEMAP
    RULEMAP --> PARAM
    PARAM --> CR
    CR --> HASH
    DEP --> EHASH
    HASH --> INC
    EHASH --> INC
    INC --> SNAP
    SNAP --> PROV

    style POL stroke-dasharray: 5 5
    style REJECT1 fill:#ff6666
    style REJECT2 fill:#ff6666
    style REJECT3 fill:#ff6666
    style HB fill:#e6f3ff,stroke:#0066cc
```

### 2.4 Conflict Resolution Decision Flow

The precedence chain is stated linearly but the branching logic (especially `compatible_overrides` and `defer_to` fall-through) needs a decision tree.

```mermaid
flowchart TD
    START[Pair of conflicting rules A, B] --> CHK_OVR{Either has\nconflict_resolution\nfield?}

    CHK_OVR -->|No| CHK_COMPAT{Symmetric pair?\nalways_wins ↔ never_wins\nor identical defer_to}
    CHK_OVR -->|Yes| CHK_STRAT{Strategy type?}

    CHK_STRAT -->|always_wins| WIN_A[A wins]
    CHK_STRAT -->|never_wins| WIN_B[B wins]
    CHK_STRAT -->|defer_to| CHK_DEFER{Target exists\nand unambiguous?}

    CHK_DEFER -->|Yes, single active| DEFER_WIN[Target wins]
    CHK_DEFER -->|No: missing| FALL1[Fall through\n→ computed factors]
    CHK_DEFER -->|No: ambiguous\npost-fork| ARTIFACT1[Conflict Artifact\nmultiple active children]
    CHK_DEFER -->|Yes, but cycle\ndetected via DFS| FALL2[Fall through\n→ computed factors]

    CHK_COMPAT -->|Yes, symmetric| COMPAT_RES[Resolve per\ncompatible_overrides]
    CHK_COMPAT -->|No| CHK_LINEAGE{Same\nlineage_id?}

    CHK_LINEAGE -->|No| ADVISORY[Advisory Conflict Artifact\n§2.15.2\nno finding modification]
    CHK_LINEAGE -->|Yes| CHK_PRI{Priority level\ndiffers?}

    CHK_PRI -->|Yes| PRI_WIN[Higher priority wins\nlower integer = higher authority]
    CHK_PRI -->|Tie| CHK_SPEC{Specificity score\ndiffers?}

    CHK_SPEC -->|Yes| SPEC_WIN[Higher specificity wins\nscope_score × 100 + bound_fields]
    CHK_SPEC -->|Tie| CHK_REC{created_at\ndiffers?}

    CHK_REC -->|Yes| REC_WIN[Newer rule wins\nlater timestamp]
    CHK_REC -->|Tie| ARTIFACT2[Conflict Artifact\nhuman review required]

    style ARTIFACT1 fill:#ffcc00
    style ARTIFACT2 fill:#ffcc00
    style ADVISORY fill:#ffe0b2
    style WIN_A fill:#c8e6c9
    style WIN_B fill:#c8e6c9
    style PRI_WIN fill:#c8e6c9
    style SPEC_WIN fill:#c8e6c9
    style REC_WIN fill:#c8e6c9
    style DEFER_WIN fill:#c8e6c9
    style COMPAT_RES fill:#c8e6c9
```

### 2.5 Data Model — Entity Relationships

The corpus never shows a unified ERD. This is what an implementation team needs to understand the storage layer.

```mermaid
erDiagram
    RULE_DATASET ||--o{ RULE : contains
    RULE_DATASET {
        string version
        string policy_contract_version
        string policy_contract_id
        object metadata
    }

    RULE {
        string lineage_id PK,FK
        string id PK
        enum type
        string message
        enum status
        string evaluator_type
        object evaluator_config
        object scope
        enum priority
        object conflict_resolution
        datetime created_at
        string anchor_ref
        object lineage
        object metadata
        object parameters
        string weight
        array depends_on
        array conflicts_with
    }

    RULE ||--o{ CGIR_NODE : compiles_to
    CGIR_NODE {
        string node_hash PK
        string directive_id FK
        string lineage_id FK
        enum deontic_type
        object evaluator
        object scope
        enum severity_default
        array depends_on
        enum priority
        object conflict_resolution
        enum status
        datetime created_at
        string description
        string directive_revision
        string control_version
    }

    CGIR_NODE }o--o{ CGIR_NODE : depends_on
    CGIR_NODE ||--o{ CGIR_EDGE : source
    CGIR_NODE ||--o{ CGIR_EDGE : target
    CGIR_EDGE {
        string edge_hash PK
        string source FK
        string target FK
    }

    CGIR_SNAPSHOT ||--o{ CGIR_NODE : contains
    CGIR_SNAPSHOT ||--o{ CGIR_EDGE : contains
    CGIR_SNAPSHOT {
        string snapshot_hash PK
        array node_hashes
        array edge_hashes
        object provenance
    }

    CGIR_SNAPSHOT_PROVENANCE {
        string engine_version
        string frozen_env_hash
        string directive_graph_version
        object lineage_validation
    }

    CGIR_SNAPSHOT ||--|| CGIR_SNAPSHOT_PROVENANCE : has

    TARGET {
        string target_id PK
        string target_type
        string content_hash
        datetime submitted_at
        object content
        object metadata
    }

    INSPECTION {
        string inspection_id PK
        string target_id FK
        string cg_ir_snapshot_hash FK
        string system_state_hash
        object frozen_env_hash
        datetime inspected_at
        array skipped_nodes
        object pipeline_trace
    }

    INSPECTION }o--|| TARGET : evaluates
    INSPECTION }o--|| CGIR_SNAPSHOT : against

    FINDING {
        string finding_id PK
        string inspection_id FK
        string control_id FK
        string lineage_id FK
        enum fsm_state
        enum severity
        enum disposition
        string evidence
        string reasoning
        float confidence
    }

    INSPECTION ||--o{ FINDING : produces
    CGIR_NODE ||--o{ FINDING : raised_by

    FINDING_EVENT {
        string event_id PK
        string finding_id FK
        enum transition
        string from_state
        string to_state
        string actor_id
        string event_hash
        object hlc_timestamp
        datetime wall_clock
    }

    FINDING ||--o{ FINDING_EVENT : stream

    CONFLICT_ARTIFACT {
        string artifact_id PK
        string cg_ir_snapshot_hash FK
        array rule_ids
        string reason
        enum binding_status
        boolean requires_human_action
    }

    CGIR_SNAPSHOT ||--o{ CONFLICT_ARTIFACT : contains

    CREATOR_PROVENANCE {
        string directive_id FK
        array authored_by
    }

    CGIR_NODE ||--|| CREATOR_PROVENANCE : has
```

---

## 3. Recommendation: What to Build Next

You now have:
- ✅ **Normative spec** (SPECIFICATION.md)
- ✅ **Structural schema** (rule_schema.json)
- ✅ **Governance intent** (policy_doctrine.yaml)
- ✅ **Behavioral contract** (User_Stories.md)
- ✅ **Cross-layer index** (README.md)
- ✅ **Mindmap** (this response)
- ✅ **5 key diagrams** (this response)

**The single highest-value next artifact is an OpenAPI 3.1 specification.** Here's why:

1. The corpus defines *capabilities* and *gates* but never defines the actual HTTP/gRPC surface. An implementer currently has to guess the request/response shapes.
2. Every user story maps to exactly one or two API operations — the mapping is mechanical.
3. OpenAPI schemas can reference `rule_schema.json` via `$ref`, creating a single source of truth for data shapes.
4. The segregation-of-duties constraints and capability gates can be expressed as `security` requirements and `x-gate` extensions.

**Suggested API surface (from the stories):**

| Endpoint | Method | Story | Gate |
|---|---|---|---|
| `/directives` | POST | S-01 | Compilation Engine |
| `/directives/{id}` | PUT | S-02 | Compilation Engine |
| `/directives/{id}/retire` | POST | S-03 | Compilation Engine |
| `/directives/{id}/fork` | POST | S-19 | Compilation Engine |
| `/directives/{id}/merge` | POST | S-20 | Compilation Engine |
| `/directives/{id}/split` | POST | S-26 | Compilation Engine |
| `/directives/{id}/restore` | POST | S-08 | Compilation Engine |
| `/directives` | GET | S-04 | Read |
| `/directives/{id}/history` | GET | S-07 | Read |
| `/directives/conflicts` | POST | S-05 | Compilation Engine |
| `/directives/audit` | POST | S-06 | Read |
| `/directives/impact-preview` | POST | S-09 | Read |
| `/inspections` | POST | S-10 | Pipeline Entry |
| `/inspections/{id}/reinspect` | POST | S-15 | Pipeline Entry |
| `/findings` | GET | S-11 | Read |
| `/findings/{id}/acknowledge` | POST | S-12 | FSM Engine |
| `/findings/{id}/evidence` | POST | S-13 | FSM Engine |
| `/findings/{id}/approve` | POST | S-14a | FSM Engine + SoD |
| `/findings/{id}/reject` | POST | S-14b | FSM Engine |
| `/findings/{id}/reopen` | POST | S-14c | FSM Engine |
| `/findings/{id}/dismiss` | POST | S-25 | FSM Engine |
| `/findings/{id}/waive` | POST | S-29 | FSM Engine + SoD |
| `/findings/{id}/explain` | GET | S-16 | Read |
| `/analytics` | GET | S-17 | Read |
| `/conflicts/{id}/resolve` | POST | S-28 | Conflict Resolution |
| `/audits/portability` | POST | S-21 | Read |
| `/audits/provenance` | POST | S-22 | Read |
| `/audits/complexity` | POST | S-27 | Read |
| `/audits/determinism` | POST | S-23 | Read |
| `/audits/edge-hashes` | POST | S-24 | Read |
| `/audits/gates` | POST | S-30 | Read |
| `/validation/reference` | POST | S-31 | Compilation Engine |

That's ~30 endpoints, each with a direct story mapping. Want me to generate the OpenAPI spec?