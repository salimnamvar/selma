# ADR-002: Content-Addressed Storage

**Status:** Accepted  
**Date:** 2026-07-06  
**Spec Reference:** SPECIFICATION.md §2.6  
**Components:** CgIrStore, NodeDeduplicator, EdgeDeduplicator, SnapshotManifestStore

## Context

The Selma system generates CG-IR snapshots containing hundreds of nodes and edges. Traditional identifier-based storage creates duplication: identical nodes with different IDs waste space and obscure equivalence. Content-addressed storage (CAS) uses content hashes as keys, enabling automatic deduplication and verifiable integrity.

## Decision

Implement **content-addressed storage** for all CG-IR artifacts:

1. **Node hashing**: `node_hash = SHA-256({semantic_hash, presentation_hash})` — composite of semantic (evaluator/scope/priority) and presentation (description/revision) content
2. **Edge hashing**: `edge_hash = SHA-256({source, target})` — directional, node-content independent
3. **Snapshot hashing**: `cg_ir_snapshot_hash = SHA-256({node_hashes: sorted[], edge_hashes: sorted[], provenance})` — `compiled_at` excluded from hash
4. **Deduplication**: NodeDeduplicator and EdgeDeduplicator reuse existing objects by hash match
5. **Multi-index lookups**: Nodes indexed by node_hash, directive_id, lineage_id, semantic_hash

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|-----------------|
| UUID-based storage | No deduplication, no integrity verification, no incremental compilation support |
| Content hashing with `compiled_at` included | Non-deterministic — different compilation times produce different hashes for identical content |
| Mutable snapshot storage | Breaks audit trail — historical snapshots must be immutable |

## Consequences

- **Positive**: Automatic deduplication saves 40-60% storage. Immutable snapshots enable point-in-time queries. Hash-based integrity verification is O(1). Incremental compilation reuses unchanged subgraphs via semantic_hash lookup.
- **Negative**: Hash computation adds ~10ms per node. Cannot modify snapshots in place (must create new snapshot).
- **Mitigation**: Hash computation is parallelizable. New snapshots are lightweight due to deduplication.

## Related Decisions

- ADR-001 (Hermetic Compilation) ensures hash stability across runs
- ADR-005 (Conflict Resolution Determinism) requires frozen snapshot inputs
