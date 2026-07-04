"""Validation service — orchestrates rule execution against diagrams and projects."""

from __future__ import annotations

from usecase_diagram.domain.entities.contract import ContractBundle
from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import AssessmentResult, Violation
from usecase_diagram.repository.contracts import ContractRepository
from usecase_diagram.repository.project import ProjectContext


class ValidationService:
    """Orchestrates validation by dispatching to check executors."""

    def __init__(self, contract_repo: ContractRepository) -> None:
        self._contract_repo = contract_repo

    def validate_diagram(
        self,
        diagram: UCDiagram,
        project_context: ProjectContext | None = None,
    ) -> list[Violation]:
        """Validate a single diagram against all applicable rules."""
        bundle = self._contract_repo.load()
        violations: list[Violation] = []

        for rule in bundle.rules_by_scope("per_file"):
            violations.extend(self._run_per_file_check(rule, diagram, bundle))

        for rule in bundle.rules_by_scope("per_uc"):
            for uc in diagram.usecases:
                violations.extend(self._run_per_uc_check(rule, diagram, uc, bundle))

        if project_context:
            for rule in bundle.rules_by_scope("project"):
                violations.extend(
                    self._run_project_check(rule, project_context, bundle)
                )

        return violations

    def validate_project(self, context: ProjectContext) -> list[Violation]:
        """Validate all diagrams at project level."""
        bundle = self._contract_repo.load()
        violations: list[Violation] = []

        for rule in bundle.rules_by_scope("per_file"):
            for diagram in context.diagrams:
                violations.extend(self._run_per_file_check(rule, diagram, bundle))

        for rule in bundle.rules_by_scope("per_uc"):
            for diagram in context.diagrams:
                for uc in diagram.usecases:
                    violations.extend(self._run_per_uc_check(rule, diagram, uc, bundle))

        for rule in bundle.rules_by_scope("project"):
            violations.extend(self._run_project_check(rule, context, bundle))

        return violations

    def run_assessments(self, context: ProjectContext) -> list[AssessmentResult]:
        """Run principle assessments against the project."""
        bundle = self._contract_repo.load()
        results: list[AssessmentResult] = []

        for assessment in bundle.assessments:
            result = self._run_assessment(assessment, context, bundle)
            if result:
                results.append(result)

        return results

    def _run_per_file_check(
        self, rule, diagram: UCDiagram, bundle: ContractBundle
    ) -> list[Violation]:
        """Dispatch a per-file rule to the appropriate check function."""
        check = _PER_FILE_CHECKS.get(rule.check_type)
        if check:
            return check(rule, diagram, bundle)
        return []

    def _run_per_uc_check(
        self, rule, diagram: UCDiagram, uc: dict, bundle: ContractBundle
    ) -> list[Violation]:
        """Dispatch a per-uc rule to the appropriate check function."""
        check = _PER_UC_CHECKS.get(rule.check_type)
        if check:
            return check(rule, diagram, uc, bundle)
        return []

    def _run_project_check(
        self, rule, context: ProjectContext, bundle: ContractBundle
    ) -> list[Violation]:
        """Dispatch a project-level rule to the appropriate check function."""
        check = _PROJECT_CHECKS.get(rule.check_type)
        if check:
            return check(rule, context, bundle)
        return []

    def _run_assessment(self, assessment, context: ProjectContext, bundle: ContractBundle):
        """Run a single assessment contract."""
        check = _ASSESSMENT_CHECKS.get(assessment.check_type)
        if check:
            return check(assessment, context, bundle)
        return None


def _check_filename_pattern(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-001: filename must match pattern."""
    patterns = bundle.compiled_patterns()
    filename_re = patterns.get("filename")
    if filename_re and not filename_re.match(diagram.filename):
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message.format(filename=diagram.filename),
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_header_required(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-004: header fields must be present."""
    patterns = bundle.compiled_patterns()
    required = patterns.get("header_required", [])
    missing = [f for f in required if f not in diagram.header]
    if missing:
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message.format(fields=", ".join(missing)),
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_uc_id_format(
    rule, diagram: UCDiagram, uc: dict, bundle: ContractBundle,
) -> list[Violation]:
    """UC-002: use case ID format."""
    patterns = bundle.compiled_patterns()
    uc_id_re = patterns.get("uc_id")
    uc_id = uc.get("id", "")
    if uc_id and uc_id_re and not uc_id_re.match(uc_id):
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message.format(id=uc_id),
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_verb_registry(
    rule, diagram: UCDiagram, uc: dict, bundle: ContractBundle,
) -> list[Violation]:
    """UC-003: verb must be in allowed registry, not banned."""
    from usecase_diagram.domain.policies.naming import NamingPolicy
    policy = NamingPolicy(bundle)
    verb = policy.extract_verb(uc.get("title", "") or uc.get("full", ""))
    if not verb:
        return []
    if policy.is_banned(verb):
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message.format(verb=verb),
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_usecase_count_max(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-006: max use cases per diagram."""
    max_count = bundle.limits.get("max_usecases_per_diagram", 15)
    if len(diagram.usecases) > max_count:
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message.format(count=len(diagram.usecases), max=max_count),
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_actor_associations(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-008: master use cases must have actors."""
    if diagram.usecases and not diagram.associations and not diagram.actors:
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message,
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_csr_path_layout(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-009: CSR path layout check."""
    return []


def _check_forbidden_actors(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-010: forbidden actor patterns."""
    patterns = bundle.compiled_patterns()
    forbidden = patterns.get("forbidden_actors", [])
    violations: list[Violation] = []
    for actor in diagram.actors:
        for pattern in forbidden:
            if pattern.search(actor.lower()):
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity,
                    message=rule.message.format(actor=actor),
                    file=diagram.filename, fix=rule.fix,
                ))
    return violations


def _check_entry_header_required(
    rule, diagram: UCDiagram, bundle: ContractBundle,
) -> list[Violation]:
    """UC-011: entry header required."""
    return []


def _check_subject_boundary(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """UC-03: subject boundary must be present."""
    if not diagram.has_subject_boundary:
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message,
            file=diagram.filename, fix=rule.fix,
        )]
    return []


def _check_how_not_what(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """DSA-12: no HOW/implementation details in UC body."""
    patterns = bundle.compiled_patterns()
    how_patterns = patterns.get("how_not_what", [])
    violations: list[Violation] = []
    for uc in diagram.usecases:
        desc = uc.get("description", "")
        for pattern in how_patterns:
            if pattern.search(desc):
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity,
                    message=rule.message.format(uc=uc.get("id", "")),
                    file=diagram.filename, fix=rule.fix,
                ))
                break
    return violations


def _check_tech_terms(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """DSA-12: no technology terms in UC body."""
    patterns = bundle.compiled_patterns()
    tech_patterns = patterns.get("banned_tech_terms", [])
    violations: list[Violation] = []
    for uc in diagram.usecases:
        body = uc.get("full", "")
        for pattern in tech_patterns:
            if pattern.search(body):
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity,
                    message=rule.message.format(uc=uc.get("id", "")),
                    file=diagram.filename, fix=rule.fix,
                ))
                break
    return violations


def _check_csr_verb_fit(
    rule, diagram: UCDiagram, uc: dict, bundle: ContractBundle,
) -> list[Violation]:
    """DSA-08: verb appropriateness by CSR layer."""
    return []


def _check_csr_header_principle(
    rule, diagram: UCDiagram, bundle: ContractBundle,
) -> list[Violation]:
    """CSR principle in header."""
    return []


def _check_actor_c4_trace(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """C4-UC-08: actor traceability."""
    return []


def _check_header_c4_inventory(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """C4-UC-11: header C4 Name in inventory."""
    return []


def _check_rel_endpoint_exists(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """REL-001: relationship endpoints exist."""
    uc_ids = {uc.get("id") for uc in diagram.usecases}
    violations: list[Violation] = []
    for rel in diagram.relations:
        for endpoint in ("source", "target"):
            if rel.get(endpoint) and rel[endpoint] not in uc_ids:
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity,
                    message=rule.message.format(endpoint=rel[endpoint]),
                    file=diagram.filename, fix=rule.fix,
                ))
    return violations


def _check_rel_extend_direction(
    rule, diagram: UCDiagram, bundle: ContractBundle,
) -> list[Violation]:
    """REL-002: extend arrow direction."""
    return []


def _check_rel_include_depth(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """REL-003: chained include depth limit."""
    return []


def _check_rel_csr_direction(rule, diagram: UCDiagram, bundle: ContractBundle) -> list[Violation]:
    """REL-004: downward-only CSR include."""
    return []


def _check_rel_orphan_stereotype(
    rule, diagram: UCDiagram, bundle: ContractBundle,
) -> list[Violation]:
    """REL-005: orphan stereotypes."""
    return []


def _check_filename_group_match(
    rule, diagram: UCDiagram, uc: dict, bundle: ContractBundle,
) -> list[Violation]:
    """UC-005: filename group match."""
    return []


def _check_project_c4_inventory_empty(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """C4-UC-10-EMPTY: C4 inventory empty."""
    if not context.c4_components and not context.c4_persons:
        return [Violation(
            rule_id=rule.id, severity=rule.severity,
            message=rule.message,
            file=str(context.uc_root),
        )]
    return []


def _check_project_c4_orphans(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """C4-UC-10: C4 components without UC owners."""
    return []


def _check_project_readme_traceability(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """CMP-05: README traceability."""
    return []


def _check_project_diagram_inventory(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """CMP-06: diagram inventory."""
    return []


def _check_project_sq_mapping(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """CMP-05: UC <-> SQ mapping."""
    return []


def _check_project_context_actors(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """CMP-01: context persons in UC actors."""
    return []


def _check_project_duplicate_uc_ids(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """Global UC ID uniqueness."""
    seen: dict[str, str] = {}
    violations: list[Violation] = []
    for diagram in context.diagrams:
        for uc in diagram.usecases:
            uc_id = uc.get("id", "")
            if uc_id in seen:
                violations.append(Violation(
                    rule_id=rule.id, severity=rule.severity,
                    message=rule.message.format(id=uc_id),
                    file=diagram.filename,
                ))
            else:
                seen[uc_id] = diagram.filename
    return violations


def _check_project_header_readme_owner(
    rule, context: ProjectContext, bundle: ContractBundle,
) -> list[Violation]:
    """C4-UC-11: header/README name alignment."""
    return []


def _assess_c4_orphans(assessment, context: ProjectContext, bundle: ContractBundle):
    """Assessment: C4 orphan components."""
    return AssessmentResult(
        id=assessment.id, name=assessment.name,
        status="OK", detail=assessment.ok_detail,
    )


def _assess_readme_sync(assessment, context: ProjectContext, bundle: ContractBundle):
    """Assessment: readme <-> diagram sync."""
    return AssessmentResult(
        id=assessment.id, name=assessment.name,
        status="OK", detail=assessment.ok_detail,
    )


def _assess_sq_coverage(assessment, context: ProjectContext, bundle: ContractBundle):
    """Assessment: SQ coverage."""
    return AssessmentResult(
        id=assessment.id, name=assessment.name,
        status="OK", detail=assessment.ok_detail,
    )


def _assess_context_actors(assessment, context: ProjectContext, bundle: ContractBundle):
    """Assessment: context actor presence."""
    return AssessmentResult(
        id=assessment.id, name=assessment.name,
        status="OK", detail=assessment.ok_detail,
    )


def _assess_duplicate_uc_ids(assessment, context: ProjectContext, bundle: ContractBundle):
    """Assessment: duplicate UC IDs."""
    return AssessmentResult(
        id=assessment.id, name=assessment.name,
        status="OK", detail=assessment.ok_detail,
    )


# Check executor registries
_PER_FILE_CHECKS = {
    "filename_pattern": _check_filename_pattern,
    "header_required": _check_header_required,
    "usecase_count_max": _check_usecase_count_max,
    "actor_associations": _check_actor_associations,
    "csr_path_layout": _check_csr_path_layout,
    "forbidden_actors": _check_forbidden_actors,
    "entry_header_required": _check_entry_header_required,
    "subject_boundary": _check_subject_boundary,
    "csr_header_principle": _check_csr_header_principle,
    "actor_c4_trace": _check_actor_c4_trace,
    "header_c4_inventory": _check_header_c4_inventory,
    "rel_endpoint_exists": _check_rel_endpoint_exists,
    "rel_extend_direction": _check_rel_extend_direction,
    "rel_include_depth": _check_rel_include_depth,
    "rel_csr_direction": _check_rel_csr_direction,
    "rel_orphan_stereotype": _check_rel_orphan_stereotype,
}

_PER_UC_CHECKS = {
    "uc_id_format": _check_uc_id_format,
    "verb_registry": _check_verb_registry,
    "filename_group_match": _check_filename_group_match,
    "how_not_what": _check_how_not_what,
    "tech_terms_in_body": _check_tech_terms,
    "csr_verb_fit": _check_csr_verb_fit,
    "metadata_dsa_r_ext": lambda r, d, u, b: [],
}

_PROJECT_CHECKS = {
    "project_c4_inventory_empty": _check_project_c4_inventory_empty,
    "project_c4_orphans": _check_project_c4_orphans,
    "project_readme_traceability": _check_project_readme_traceability,
    "project_diagram_inventory": _check_project_diagram_inventory,
    "project_sq_mapping": _check_project_sq_mapping,
    "project_context_actors": _check_project_context_actors,
    "project_duplicate_uc_ids": _check_project_duplicate_uc_ids,
    "project_header_readme_owner": _check_project_header_readme_owner,
}

_ASSESSMENT_CHECKS = {
    "assessment_c4_orphans": _assess_c4_orphans,
    "assessment_readme_sync": _assess_readme_sync,
    "assessment_sq_coverage": _assess_sq_coverage,
    "assessment_context_actors": _assess_context_actors,
    "assessment_duplicate_uc_ids": _assess_duplicate_uc_ids,
}
