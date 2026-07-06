# ADR-003: Dual Identity Model

**Status:** Accepted  
**Date:** 2026-07-06  
**Spec Reference:** SPECIFICATION.md §2.2, §2.3  
**Components:** IdentityResolver, LineageTracer

## Context

Directives undergo lifecycle operations (revision, fork, merge, split, rename, retire) that create new execution nodes. Using a single identifier conflates historical lineage with current active state, making it impossible to trace audit trails across operations or distinguish between concurrent branches.

## Decision

Implement a **dual identity model** with two distinct identifier types:

1. **Lineage ID** (`lineage_id`): Immutable root identifier. Never changes across any lifecycle operation. Format: `^[A-Z][A-Z0-9]+-[0-9]+$`. Enables audit trail tracing across fork/merge/split.
2. **Execution ID** (`execution_id`): Active node identity. Changes on fork/merge/split. Format: `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$`. Used for compilation and current-state queries.

### Lifecycle Semantics

| Operation | lineage_id | execution_id | Notes |
|-----------|-----------|-------------|-------|
| Create | Assigned (Machine ID) | Same as lineage_id | Bijective at root level |
| Revision | Unchanged | Unchanged | Same execution_id, new content |
| Fork | Inherited | New (inherited + fork suffix) | Both children share parent lineage_id |
| Merge | Lexicographic min of parents | Deterministic (lineage + SHA-256 of parents + "merge") | Non-surviving parent in `parent_lineage_ids` |
| Split | Inherited | New (inherited + split suffix) | Each child unique execution_id |
| Retire | Unchanged | Unchanged | Status → deprecated |

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|-----------------|
| Single mutable ID | Breaks audit trail — cannot trace lineage across operations |
| UUID-based identity | No semantic meaning, no lexicographic merge semantics |
| Content-addressed identity | Identity should be stable across content changes (revision) |

## Consequences

- **Positive**: Audit trail preserved across all lifecycle operations. Merge identity is deterministic (lexicographic min). Fork/split create clearly traceable branches. Content-addressed storage works with execution_id as directive_id.
- **Negative**: Two ID fields increase schema complexity. Query patterns must specify which ID to use.
- **Mitigation**: IdentityResolver encapsulates all ID logic. External APIs accept either ID type with automatic resolution.

## Related Decisions

- ADR-002 (Content-Addressed Storage) uses execution_id as directive_id in node bodies
- ADR-004 (Policy Runtime Prohibition) — Machine ID maps to lineage_id only
