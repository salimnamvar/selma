# ADR-001: Hermetic Compilation Boundary

**Status:** Accepted  
**Date:** 2026-07-06  
**Spec Reference:** SPECIFICATION.md §2.7  
**Components:** FrozenEnvManager, CompilationEngine

## Context

The Selma system compiles human-authored directives into immutable CG-IR snapshots. Reproducibility is essential: the same directive graph + environment must produce byte-identical CG-IR snapshots across runs. Without hermetic boundaries, environmental drift (engine version, toolchain, AI models, OS/runtime) could cause non-deterministic compilation outcomes, breaking audit trails and content-addressed storage guarantees.

## Decision

Implement a **hermetic compilation boundary** that pins all environment dimensions at compile time:

1. **FrozenEnvManager** captures: engine version, toolchain hash, AI model hashes, OS/runtime fingerprint
2. A `frozen_env_hash` is computed from all pinned dimensions (SHA-256 of canonical JSON)
3. The frozen_env_hash is recorded in CG-IR snapshot provenance
4. Any environment change produces a new frozen_env_hash, triggering full recompilation
5. Incremental compilation reuses subgraphs only when `frozen_env_hash` matches

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|-----------------|
| Runtime environment detection | Non-deterministic — environment changes between runs |
| External config file without hashing | No integrity guarantee — config could be modified silently |
| Docker/container-based hermetic builds | Adds deployment complexity; doesn't address AI model versioning |

## Consequences

- **Positive**: Byte-identical snapshots for same inputs. Content-addressed storage works correctly. Incremental compilation cache is trustworthy.
- **Negative**: Any environment change forces full recompilation. FrozenEnvManager adds compile-time overhead (~50ms).
- **Mitigation**: FrozenEnvManager runs once per compilation trigger; hash computation is O(1) for cached environments.

## Related Decisions

- ADR-002 (Content-Addressed Storage) depends on hermetic boundaries for hash stability
- ADR-005 (Conflict Resolution Determinism) requires frozen inputs
