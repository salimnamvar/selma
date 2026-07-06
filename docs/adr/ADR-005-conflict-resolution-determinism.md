# ADR-005: Conflict Resolution Determinism

**Status:** Accepted  
**Date:** 2026-07-06  
**Spec Reference:** SPECIFICATION.md §2.15  
**Components:** ConflictResolver, ScopeSpecificityScorer, ConflictPairGenerator

## Context

Multiple directives may conflict on the same target aspect. Without deterministic resolution, the same CG-IR snapshot could produce different conflict outcomes across runs, breaking audit trails, content-addressed storage, and regulatory compliance. Conflict resolution must be a pure function of frozen inputs.

## Decision

Implement **deterministic conflict resolution** with a strict precedence chain:

1. **Explicit override**: `conflict_resolution` field in directive (highest priority)
2. **Compatible overrides**: `compatible_overrides()` for symmetric pairs (`{always_wins, never_wins}`, identical `defer_to` targets)
3. **Priority level**: Integer comparison (regulatory > statutory > advisory)
4. **Specificity score**: `scope_specificity_score × 100 + count_bound_fields` — quantifies scope narrowness
5. **Created_at recency**: Later timestamp wins (frozen in node_body, not wall clock)
6. **ConflictArtifact**: Escalation for unresolvable conflicts (requires human review via `conflict.resolve`)

### Determinism Guarantees

- All inputs frozen in CG-IR snapshot at compile time
- `compiled_at` excluded from snapshot hash (not a resolution input)
- DFS cycle detection for `defer_to` chains
- Runtime ConflictResolverRuntime applies same precedence chain to concurrent findings

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|-----------------|
| First-come-first-served | Non-deterministic — depends on request ordering |
| Random selection | Non-deterministic — violates audit requirements |
| Manual-only resolution | Doesn't scale — hundreds of conflicts per compilation |
| Priority-only resolution | Too coarse — multiple directives at same priority level |

## Consequences

- **Positive**: Identical CG-IR snapshot + target → byte-identical conflict outcomes. Audit trail is reproducible. Content-addressed storage works correctly for conflict artifacts. AA-05 gate provides certification traceability.
- **Negative**: Specificity scoring adds ~5ms per conflict pair. Complex precedence chain requires thorough testing.
- **Mitigation**: Specificity scoring is O(1) per pair. Precedence chain is well-defined and testable via §9.9 AA-05 gate.

## Related Decisions

- ADR-001 (Hermetic Compilation) ensures frozen inputs for determinism
- ADR-002 (Content-Addressed Storage) depends on deterministic outputs
- AA-05 gate in ArchitecturalAuditEngine validates determinism
