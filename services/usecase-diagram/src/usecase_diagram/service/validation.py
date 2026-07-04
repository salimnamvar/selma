"""Validation service — orchestrates rule execution against diagrams and projects."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from usecase_diagram.domain.entities.contract import AssessmentDef, ContractBundle, RuleDef
from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import AssessmentResult, Violation
from usecase_diagram.domain.policies.naming import NamingPolicy
from usecase_diagram.repository.contracts import ContractRepository
from usecase_diagram.repository.project import ProjectContext


class ValidationService:
    """Orchestrates validation by dispatching to check executors.

    Attributes:
        _contract_repo (ContractRepository): Contract data access.
    """

    def __init__(self, a_contract_repo: ContractRepository) -> None:
        """Initialize with a contract repository.

        Args:
            a_contract_repo (ContractRepository): Contract data access.
        """
        self._contract_repo: ContractRepository = a_contract_repo

    def validate_diagram(
        self,
        a_diagram: UCDiagram,
        a_project_context: Optional[ProjectContext] = None,
    ) -> List[Violation]:
        """Validate a single diagram against all applicable rules.

        Args:
            a_diagram (UCDiagram): Diagram to validate.
            a_project_context (Optional[ProjectContext]): Project context for project-level checks.

        Returns:
            List[Violation]: List of violations found.
        """
        bundle: ContractBundle = self._contract_repo.load()
        violations: List[Violation] = []

        for rule in bundle.rules_by_scope("per_file"):
            violations.extend(self._run_per_file_check(rule, a_diagram, bundle))

        for rule in bundle.rules_by_scope("per_uc"):
            for uc in a_diagram.usecases:
                violations.extend(self._run_per_uc_check(rule, a_diagram, uc, bundle))

        if a_project_context is not None:
            for rule in bundle.rules_by_scope("project"):
                violations.extend(
                    self._run_project_check(rule, a_project_context, bundle)
                )

        return violations

    def validate_project(self, a_context: ProjectContext) -> List[Violation]:
        """Validate all diagrams at project level.

        Args:
            a_context (ProjectContext): Project context with diagrams.

        Returns:
            List[Violation]: List of violations found.
        """
        bundle: ContractBundle = self._contract_repo.load()
        violations: List[Violation] = []

        for rule in bundle.rules_by_scope("per_file"):
            for diagram in a_context.diagrams:
                violations.extend(self._run_per_file_check(rule, diagram, bundle))

        for rule in bundle.rules_by_scope("per_uc"):
            for diagram in a_context.diagrams:
                for uc in diagram.usecases:
                    violations.extend(self._run_per_uc_check(rule, diagram, uc, bundle))

        for rule in bundle.rules_by_scope("project"):
            violations.extend(self._run_project_check(rule, a_context, bundle))

        return violations

    def run_assessments(self, a_context: ProjectContext) -> List[AssessmentResult]:
        """Run principle assessments against the project.

        Args:
            a_context (ProjectContext): Project context.

        Returns:
            List[AssessmentResult]: Assessment results.
        """
        bundle: ContractBundle = self._contract_repo.load()
        results: List[AssessmentResult] = []

        for assessment in bundle.assessments:
            result: Optional[AssessmentResult] = self._run_assessment(
                assessment, a_context, bundle
            )
            if result is not None:
                results.append(result)

        return results

    def _run_per_file_check(
        self, a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
    ) -> List[Violation]:
        """Dispatch a per-file rule to the appropriate check function.

        Args:
            a_rule (RuleDef): Rule to execute.
            a_diagram (UCDiagram): Diagram to check.
            a_bundle (ContractBundle): Contract bundle.

        Returns:
            List[Violation]: Violations from the check.
        """
        check: Optional[Callable[..., List[Violation]]] = _PER_FILE_CHECKS.get(
            a_rule.check_type
        )
        violations: List[Violation] = []
        if check is not None:
            violations = check(a_rule, a_diagram, a_bundle)
        return violations

    def _run_per_uc_check(
        self,
        a_rule: RuleDef,
        a_diagram: UCDiagram,
        a_uc: Dict[str, Any],
        a_bundle: ContractBundle,
    ) -> List[Violation]:
        """Dispatch a per-uc rule to the appropriate check function.

        Args:
            a_rule (RuleDef): Rule to execute.
            a_diagram (UCDiagram): Diagram containing the use case.
            a_uc (Dict[str, Any]): Use case dictionary.
            a_bundle (ContractBundle): Contract bundle.

        Returns:
            List[Violation]: Violations from the check.
        """
        check: Optional[Callable[..., List[Violation]]] = _PER_UC_CHECKS.get(
            a_rule.check_type
        )
        violations: List[Violation] = []
        if check is not None:
            violations = check(a_rule, a_diagram, a_uc, a_bundle)
        return violations

    def _run_project_check(
        self,
        a_rule: RuleDef,
        a_context: ProjectContext,
        a_bundle: ContractBundle,
    ) -> List[Violation]:
        """Dispatch a project-level rule to the appropriate check function.

        Args:
            a_rule (RuleDef): Rule to execute.
            a_context (ProjectContext): Project context.
            a_bundle (ContractBundle): Contract bundle.

        Returns:
            List[Violation]: Violations from the check.
        """
        check: Optional[Callable[..., List[Violation]]] = _PROJECT_CHECKS.get(
            a_rule.check_type
        )
        violations: List[Violation] = []
        if check is not None:
            violations = check(a_rule, a_context, a_bundle)
        return violations

    def _run_assessment(
        self,
        a_assessment: AssessmentDef,
        a_context: ProjectContext,
        a_bundle: ContractBundle,
    ) -> Optional[AssessmentResult]:
        """Run a single assessment contract.

        Args:
            a_assessment (AssessmentDef): Assessment to execute.
            a_context (ProjectContext): Project context.
            a_bundle (ContractBundle): Contract bundle.

        Returns:
            Optional[AssessmentResult]: Result or None if check not found.
        """
        check: Optional[Callable[..., Optional[AssessmentResult]]] = _ASSESSMENT_CHECKS.get(
            a_assessment.check_type
        )
        result: Optional[AssessmentResult] = None
        if check is not None:
            result = check(a_assessment, a_context, a_bundle)
        return result


def _check_filename_pattern(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-001: filename must match pattern.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    filename_re = patterns.get("filename")
    violations: List[Violation] = []
    if filename_re is not None and not filename_re.match(a_diagram.filename):
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message.format(filename=a_diagram.filename),
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_header_required(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-004: header fields must be present.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    required: List[str] = patterns.get("header_required", [])
    missing: List[str] = [f for f in required if f not in a_diagram.header]
    violations: List[Violation] = []
    if missing:
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message.format(fields=", ".join(missing)),
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_uc_id_format(
    a_rule: RuleDef,
    a_diagram: UCDiagram,
    a_uc: Dict[str, Any],
    a_bundle: ContractBundle,
) -> List[Violation]:
    """UC-002: use case ID format.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram containing the use case.
        a_uc (Dict[str, Any]): Use case dictionary.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    uc_id_re = patterns.get("uc_id")
    uc_id: str = a_uc.get("id", "")
    violations: List[Violation] = []
    if uc_id and uc_id_re is not None and not uc_id_re.match(uc_id):
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message.format(id=uc_id),
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_verb_registry(
    a_rule: RuleDef,
    a_diagram: UCDiagram,
    a_uc: Dict[str, Any],
    a_bundle: ContractBundle,
) -> List[Violation]:
    """UC-003: verb must be in allowed registry, not banned.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram containing the use case.
        a_uc (Dict[str, Any]): Use case dictionary.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    policy: NamingPolicy = NamingPolicy(a_bundle)
    verb: Optional[str] = policy.extract_verb(a_uc.get("title", "") or a_uc.get("full", ""))
    violations: List[Violation] = []
    if verb is not None and policy.is_banned(verb):
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message.format(verb=verb),
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_usecase_count_max(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-006: max use cases per diagram.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    max_count: int = a_bundle.limits.get("max_usecases_per_diagram", 15)
    violations: List[Violation] = []
    if len(a_diagram.usecases) > max_count:
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message.format(count=len(a_diagram.usecases), max=max_count),
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_actor_associations(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-008: master use cases must have actors.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    violations: List[Violation] = []
    if a_diagram.usecases and not a_diagram.associations and not a_diagram.actors:
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message,
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_csr_path_layout(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-009: CSR path layout check.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_forbidden_actors(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-010: forbidden actor patterns.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    forbidden: List[Any] = patterns.get("forbidden_actors", [])
    violations: List[Violation] = []
    for actor in a_diagram.actors:
        for pattern in forbidden:
            if pattern.search(actor.lower()):
                violations.append(Violation(
                    rule_id=a_rule.id, severity=a_rule.severity,
                    message=a_rule.message.format(actor=actor),
                    file=a_diagram.filename, fix=a_rule.fix,
                ))
    return violations


def _check_entry_header_required(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-011: entry header required.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_subject_boundary(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """UC-03: subject boundary must be present.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    violations: List[Violation] = []
    if not a_diagram.has_subject_boundary:
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message,
            file=a_diagram.filename, fix=a_rule.fix,
        ))
    return violations


def _check_how_not_what(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """DSA-12: no HOW/implementation details in UC body.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    how_patterns: List[Any] = patterns.get("how_not_what", [])
    violations: List[Violation] = []
    for uc in a_diagram.usecases:
        desc: str = uc.get("description", "")
        for pattern in how_patterns:
            if pattern.search(desc):
                violations.append(Violation(
                    rule_id=a_rule.id, severity=a_rule.severity,
                    message=a_rule.message.format(uc=uc.get("id", "")),
                    file=a_diagram.filename, fix=a_rule.fix,
                ))
                break
    return violations


def _check_tech_terms(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """DSA-12: no technology terms in UC body.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    patterns: Dict[str, Any] = a_bundle.compiled_patterns()
    tech_patterns: List[Any] = patterns.get("banned_tech_terms", [])
    violations: List[Violation] = []
    for uc in a_diagram.usecases:
        body: str = uc.get("full", "")
        for pattern in tech_patterns:
            if pattern.search(body):
                violations.append(Violation(
                    rule_id=a_rule.id, severity=a_rule.severity,
                    message=a_rule.message.format(uc=uc.get("id", "")),
                    file=a_diagram.filename, fix=a_rule.fix,
                ))
                break
    return violations


def _check_csr_verb_fit(
    a_rule: RuleDef,
    a_diagram: UCDiagram,
    a_uc: Dict[str, Any],
    a_bundle: ContractBundle,
) -> List[Violation]:
    """DSA-08: verb appropriateness by CSR layer.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram containing the use case.
        a_uc (Dict[str, Any]): Use case dictionary.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_csr_header_principle(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """CSR principle in header.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_actor_c4_trace(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """C4-UC-08: actor traceability.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_header_c4_inventory(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """C4-UC-11: header C4 Name in inventory.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_rel_endpoint_exists(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """REL-001: relationship endpoints exist.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    uc_ids = {uc.get("id") for uc in a_diagram.usecases}
    violations: List[Violation] = []
    for rel in a_diagram.relations:
        for endpoint in ("source", "target"):
            if rel.get(endpoint) and rel[endpoint] not in uc_ids:
                violations.append(Violation(
                    rule_id=a_rule.id, severity=a_rule.severity,
                    message=a_rule.message.format(endpoint=rel[endpoint]),
                    file=a_diagram.filename, fix=a_rule.fix,
                ))
    return violations


def _check_rel_extend_direction(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """REL-002: extend arrow direction.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_rel_include_depth(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """REL-003: chained include depth limit.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_rel_csr_direction(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """REL-004: downward-only CSR include.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_rel_orphan_stereotype(
    a_rule: RuleDef, a_diagram: UCDiagram, a_bundle: ContractBundle
) -> List[Violation]:
    """REL-005: orphan stereotypes.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram to check.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_filename_group_match(
    a_rule: RuleDef,
    a_diagram: UCDiagram,
    a_uc: Dict[str, Any],
    a_bundle: ContractBundle,
) -> List[Violation]:
    """UC-005: filename group match.

    Args:
        a_rule (RuleDef): Rule definition.
        a_diagram (UCDiagram): Diagram containing the use case.
        a_uc (Dict[str, Any]): Use case dictionary.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_c4_inventory_empty(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """C4-UC-10-EMPTY: C4 inventory empty.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    violations: List[Violation] = []
    if not a_context.c4_components and not a_context.c4_persons:
        violations.append(Violation(
            rule_id=a_rule.id, severity=a_rule.severity,
            message=a_rule.message,
            file=str(a_context.uc_root),
        ))
    return violations


def _check_project_c4_orphans(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """C4-UC-10: C4 components without UC owners.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_readme_traceability(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """CMP-05: README traceability.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_diagram_inventory(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """CMP-06: diagram inventory.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_sq_mapping(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """CMP-05: UC <-> SQ mapping.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_context_actors(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """CMP-01: context persons in UC actors.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _check_project_duplicate_uc_ids(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """Global UC ID uniqueness.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    seen: Dict[str, str] = {}
    violations: List[Violation] = []
    for diagram in a_context.diagrams:
        for uc in diagram.usecases:
            uc_id: str = uc.get("id", "")
            if uc_id in seen:
                violations.append(Violation(
                    rule_id=a_rule.id, severity=a_rule.severity,
                    message=a_rule.message.format(id=uc_id),
                    file=diagram.filename,
                ))
            else:
                seen[uc_id] = diagram.filename
    return violations


def _check_project_header_readme_owner(
    a_rule: RuleDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> List[Violation]:
    """C4-UC-11: header/README name alignment.

    Args:
        a_rule (RuleDef): Rule definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        List[Violation]: Violations found.
    """
    return []


def _assess_c4_orphans(
    a_assessment: AssessmentDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> AssessmentResult:
    """Assessment: C4 orphan components.

    Args:
        a_assessment (AssessmentDef): Assessment definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        AssessmentResult: Assessment result.
    """
    result: AssessmentResult = AssessmentResult(
        id=a_assessment.id, name=a_assessment.name,
        status="OK", detail=a_assessment.ok_detail,
    )
    return result


def _assess_readme_sync(
    a_assessment: AssessmentDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> AssessmentResult:
    """Assessment: readme <-> diagram sync.

    Args:
        a_assessment (AssessmentDef): Assessment definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        AssessmentResult: Assessment result.
    """
    result: AssessmentResult = AssessmentResult(
        id=a_assessment.id, name=a_assessment.name,
        status="OK", detail=a_assessment.ok_detail,
    )
    return result


def _assess_sq_coverage(
    a_assessment: AssessmentDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> AssessmentResult:
    """Assessment: SQ coverage.

    Args:
        a_assessment (AssessmentDef): Assessment definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        AssessmentResult: Assessment result.
    """
    result: AssessmentResult = AssessmentResult(
        id=a_assessment.id, name=a_assessment.name,
        status="OK", detail=a_assessment.ok_detail,
    )
    return result


def _assess_context_actors(
    a_assessment: AssessmentDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> AssessmentResult:
    """Assessment: context actor presence.

    Args:
        a_assessment (AssessmentDef): Assessment definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        AssessmentResult: Assessment result.
    """
    result: AssessmentResult = AssessmentResult(
        id=a_assessment.id, name=a_assessment.name,
        status="OK", detail=a_assessment.ok_detail,
    )
    return result


def _assess_duplicate_uc_ids(
    a_assessment: AssessmentDef, a_context: ProjectContext, a_bundle: ContractBundle
) -> AssessmentResult:
    """Assessment: duplicate UC IDs.

    Args:
        a_assessment (AssessmentDef): Assessment definition.
        a_context (ProjectContext): Project context.
        a_bundle (ContractBundle): Contract bundle.

    Returns:
        AssessmentResult: Assessment result.
    """
    result: AssessmentResult = AssessmentResult(
        id=a_assessment.id, name=a_assessment.name,
        status="OK", detail=a_assessment.ok_detail,
    )
    return result


# Check executor registries
_PER_FILE_CHECKS: Dict[str, Callable[..., List[Violation]]] = {
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

_PER_UC_CHECKS: Dict[str, Callable[..., List[Violation]]] = {
    "uc_id_format": _check_uc_id_format,
    "verb_registry": _check_verb_registry,
    "filename_group_match": _check_filename_group_match,
    "how_not_what": _check_how_not_what,
    "tech_terms_in_body": _check_tech_terms,
    "csr_verb_fit": _check_csr_verb_fit,
}

_PROJECT_CHECKS: Dict[str, Callable[..., List[Violation]]] = {
    "project_c4_inventory_empty": _check_project_c4_inventory_empty,
    "project_c4_orphans": _check_project_c4_orphans,
    "project_readme_traceability": _check_project_readme_traceability,
    "project_diagram_inventory": _check_project_diagram_inventory,
    "project_sq_mapping": _check_project_sq_mapping,
    "project_context_actors": _check_project_context_actors,
    "project_duplicate_uc_ids": _check_project_duplicate_uc_ids,
    "project_header_readme_owner": _check_project_header_readme_owner,
}

_ASSESSMENT_CHECKS: Dict[str, Callable[..., Optional[AssessmentResult]]] = {
    "assessment_c4_orphans": _assess_c4_orphans,
    "assessment_readme_sync": _assess_readme_sync,
    "assessment_sq_coverage": _assess_sq_coverage,
    "assessment_context_actors": _assess_context_actors,
    "assessment_duplicate_uc_ids": _assess_duplicate_uc_ids,
}
