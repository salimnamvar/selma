"""Validator for RoD-CSR-SQ combined rules.

Checks CSR compliance, RoD compliance, and SQ structural integrity.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation

from .ir import RodCsrSqDiagram


def _check_csr(d: RodCsrSqDiagram) -> list[Violation]:
    """Check CSR layer interaction rules."""
    violations: list[Violation] = []

    # CSR-1: Must have actor
    if not d.csr.has_actor:
        violations.append(Violation(
            rule_id="RCSR-001", severity="critical",
            message="Diagram must have an actor (User, HTTPClient, etc.)",
            location=d.filename,
            fix_suggestion="Add 'actor \"User\" as user' at diagram start",
        ))

    # CSR-2: Must have controller layer
    if not d.csr.has_controller:
        violations.append(Violation(
            rule_id="RCSR-002", severity="critical",
            message="Diagram must include a Controller layer participant",
            location=d.filename,
            fix_suggestion="Add participant for Controller (e.g., '{Resource}Controller')",
        ))

    # CSR-3: Should have service layer (high, not critical)
    # Service layer is a design choice: business-logic-heavy flows MUST have it,
    # but pure orchestration/routing, infrastructure-access, and protocol-adaptation
    # flows may legitimately omit it. Declare @csr-exempt service in header
    # to explicitly opt out and reduce severity to info.
    if not d.csr.has_service:
        if d.csr.is_infra_access:
            violations.append(Violation(
                rule_id="RCSR-003", severity="info",
                message="Infrastructure-access flow — Service layer omitted (advisory: verify business logic doesn't need it)",
                location=d.filename,
                fix_suggestion="Add 'Service' participant if business logic exists, or keep @csr-exempt service for intentional omission",
            ))
        else:
            violations.append(Violation(
                rule_id="RCSR-003", severity="high",
                message="Diagram should include a Service layer participant",
                location=d.filename,
                fix_suggestion="Add participant for Service (e.g., '{Resource}Service') or declare '@csr-exempt service' if intentionally omitted",
            ))

    # CSR-4: Must have repository layer
    # Exemption: pure output-rendering flows (e.g., CLI-03 stream output) that
    # only display data without persistence operations are exempt from Repository
    # requirement. These flows render pre-existing data, not fetch/store it.
    if not d.csr.has_repository:
        violations.append(Violation(
            rule_id="RCSR-004", severity="high",
            message="Diagram should include a Repository layer participant",
            location=d.filename,
            fix_suggestion="Add participant for Repository (e.g., '{Resource}Repository')",
        ))

    # CSR-5: Controller must NOT call Repository directly
    # Infrastructure-access flows are exempt — direct Controller→Repository calls
    # are acceptable when there is no Service layer performing business logic.
    if d.csr.controller_to_repo_calls:
        if d.csr.is_infra_access:
            violations.append(Violation(
                rule_id="RCSR-005", severity="medium",
                message=f"Controller directly calls Repository in infra-access flow ({len(d.csr.controller_to_repo_calls)} violation(s))",
                location=d.filename,
                fix_suggestion="Route Controller calls through Service layer unless this is an intentional infra-access pattern",
            ))
        else:
            violations.append(Violation(
                rule_id="RCSR-005", severity="critical",
                message=f"Controller directly calls Repository ({len(d.csr.controller_to_repo_calls)} violation(s))",
                location=d.filename,
                fix_suggestion="Route Controller calls through Service layer",
            ))

    # CSR-6: Repository must NOT call Service upward
    if d.csr.repo_to_service_calls:
        violations.append(Violation(
            rule_id="RCSR-006", severity="critical",
            message=f"Repository calls Service upward ({len(d.csr.repo_to_service_calls)} violation(s))",
            location=d.filename,
            fix_suggestion="Repository should never call Service; remove upward calls",
        ))

    return violations


def _check_rod(d: RodCsrSqDiagram) -> list[Violation]:
    """Check Resource-Oriented Design rules."""
    violations: list[Violation] = []

    # ROD-1: Must identify a resource
    if not d.rod.method_type:
        violations.append(Violation(
            rule_id="RROD-001", severity="high",
            message="Diagram does not identify a RoD method type (Get/List/Create/Update/Delete/Custom)",
            location=d.filename,
            fix_suggestion="Title or source must indicate the RoD method (e.g., 'Create Book', 'List Orders')",
        ))

    # ROD-2: Must not use verb-as-path
    if d.rod.verb_as_path:
        violations.append(Violation(
            rule_id="RROD-002", severity="high",
            message=f"Verb-as-path anti-pattern detected: {d.rod.verb_as_path}",
            location=d.filename,
            fix_suggestion="Use noun resources with standard/custom methods instead of verb paths",
        ))

    # ROD-3: List must have pagination
    if d.rod.method_type == "List" and not d.rod.has_pagination:
        violations.append(Violation(
            rule_id="RROD-003", severity="high",
            message="List operation missing pagination fields (page_size, page_token)",
            location=d.filename,
            fix_suggestion="Add page_size, page_token parameters and nextPageToken response per AIP-158",
        ))

    # ROD-4: Update should show update_mask
    if d.rod.method_type == "Update" and not d.rod.has_update_mask:
        violations.append(Violation(
            rule_id="RROD-004", severity="medium",
            message="Update operation missing update_mask field",
            location=d.filename,
            fix_suggestion="Add update_mask parameter per AIP-134 for partial updates",
        ))

    # ROD-5: State transitions should be explicit
    if d.rod.has_state_transition and not d.rod.state_from:
        violations.append(Violation(
            rule_id="RROD-005", severity="medium",
            message="State transition detected but from/to states not specified",
            location=d.filename,
            fix_suggestion="Use format 'State: FROM_STATE → TO_STATE' in note",
        ))

    # ROD-6: Resource names should use full form (collection/id)
    for name in d.rod.resource_names_in_messages:
        if re.match(r'^\d+$', name):
            violations.append(Violation(
                rule_id="RROD-006", severity="medium",
                message=f"Bare numeric ID '{name}' in resource name — use full resource name format",
                location=d.filename,
                fix_suggestion="Use full resource name: 'collection/{id}' per AIP-122",
            ))

    return violations


def _check_sq_structure(d: RodCsrSqDiagram) -> list[Violation]:
    """Check SQ diagram structural requirements.

    Note: RSQ-001 through RSQ-005 (intro/summary notes) are disabled per
    project rule 'No Notes in SQ'. Diagrams must speak for themselves
    through structure, ROD method names, combined fragments, and hnote
    only on real state changes.
    """
    violations: list[Violation] = []

    # SQ-5: Must have activation bars
    if not d.sq.has_activation_bars:
        violations.append(Violation(
            rule_id="RSQ-006", severity="medium",
            message="No activation bars detected — layers should show active processing",
            location=d.filename,
            fix_suggestion="Add 'activate' / 'deactivate' for each layer during processing",
        ))

    return violations


def validate_rod_csr_sq(d: RodCsrSqDiagram) -> list[Violation]:
    """Run all RoD-CSR-SQ validation checks."""
    violations: list[Violation] = []
    violations.extend(_check_csr(d))
    violations.extend(_check_rod(d))
    violations.extend(_check_sq_structure(d))
    return violations
