# ADR-004: Policy Runtime Prohibition

**Status:** Accepted  
**Date:** 2026-07-06  
**Spec Reference:** SPECIFICATION.md §1.2 Rule 7  
**Components:** PolicyAccessBlocker, AAGateValidator, CI/CD Pipeline

## Context

`policy_doctrine.yaml` describes governance intent in human prose. If runtime engines read this file during inspection, evaluation, FSM transitions, or conflict resolution, they could introduce non-determinism (prose interpretation varies), violate the normative hierarchy (spec is authoritative, policy is descriptive), and create security risks (untrusted input at runtime).

## Decision

Implement **strict policy runtime prohibition** with three enforcement layers:

1. **Compile-time validation**: PolicyAccessBlocker validates that policy_doctrine.yaml is not referenced in runtime data paths. PolicyVersionChecker ensures major version alignment.
2. **Boot-time assertions**: Runtime modules assert policy file absence from data paths. Any runtime access triggers immediate failure.
3. **CI/CD static analysis**: Automated scans of runtime source code for policy_doctrine.yaml references. AA-02 gate in ArchitecturalAuditEngine.

### Policy Influence Channels (Authoring-Time Only)

- Human authors read policy when writing directives
- Compile-time validators check schema fields conform to spec (not policy)
- Policy prose never interpreted as executable logic

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|-----------------|
| Runtime policy caching | Still allows runtime access — violates prohibition |
| Policy-as-code (executable policy) | Conflates governance intent with normative behavior |
| Sandboxed policy reader | Adds complexity; prohibition is simpler and more secure |

## Consequences

- **Positive**: Deterministic runtime behavior. Clean separation of governance intent from executable logic. AA-02 gate provides certification traceability. CI/CD enforcement catches violations before deployment.
- **Negative**: Authors cannot preview runtime behavior from policy alone. Policy changes require re-validation through compilation pipeline.
- **Mitigation**: Compilation pipeline provides dry-run mode (S-09) for impact preview without policy runtime access.

## Related Decisions

- ADR-001 (Hermetic Compilation) — policy is compile-time input, not runtime input
- AA-02 gate in ArchitecturalAuditEngine validates prohibition enforcement
