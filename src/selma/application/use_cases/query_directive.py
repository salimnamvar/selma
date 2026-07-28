"""QueryDirectiveUseCase — reasoning access to the directive catalog.

Agents and humans query policies, rules, and guidance without running inspection.
"""

from __future__ import annotations

from typing import Any
from typing import cast

from selma.application.dto.query_request import QueryKind
from selma.application.dto.query_request import QueryRequest
from selma.application.dto.query_response import QueryResponse
from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.domain.aggregates.directive import Directive
from selma.domain.value_objects.result import Result


class QueryDirectiveUseCase:
    """Application service: queryable catalog for governance reasoning."""

    def __init__(self, a_directive_repository: DirectiveRepository) -> None:
        self._directive_repository = a_directive_repository

    async def execute(self, a_request: QueryRequest) -> Result[QueryResponse]:
        """Execute a catalog query.

        Preconditions: Catalog repository available.
        Postconditions: Ok with QueryResponse or Failure.
        Side Effects: May load directive files.
        Resource: File I/O via repository.
        Failure: Not found or load errors.
        """
        b_continue = True
        result: Result[QueryResponse] = Result.failure("unreachable")

        catalog_result = await self._directive_repository.list_catalog()
        if catalog_result.is_failure():
            b_continue = False
            result = Result.failure(catalog_result.message)

        if b_continue:
            catalog = catalog_result.unwrap()
            kind = a_request.kind

            if kind == QueryKind.LIST:
                items = tuple(
                    self._directive_summary(d)
                    for d in catalog.list_all()[: a_request.limit]
                )
                result = Result.success(
                    QueryResponse(
                        kind=kind.value,
                        summary=f"{len(catalog)} directives in catalog",
                        items=items,
                    )
                )
            elif kind == QueryKind.SEARCH:
                needle = a_request.text.lower()
                matched: list[Directive] = []
                for directive in catalog.list_all():
                    blob = (
                        f"{directive.lineage_id} {directive.rule.message} "
                        f"{directive.title} {directive.rule.rationale}"
                    ).lower()
                    if needle and needle in blob:
                        matched.append(directive)
                items = tuple(
                    self._directive_summary(d) for d in matched[: a_request.limit]
                )
                result = Result.success(
                    QueryResponse(
                        kind=kind.value,
                        summary=f"{len(matched)} match(es) for {a_request.text!r}",
                        items=items,
                    )
                )
            elif kind in {
                QueryKind.POLICY,
                QueryKind.RULE,
                QueryKind.DIRECTIVE,
                QueryKind.GUIDANCE,
            }:
                if not a_request.lineage_id:
                    b_continue = False
                    result = Result.failure("lineage_id is required for this query")
                if b_continue:
                    directive = catalog.find_by_lineage_id(a_request.lineage_id)
                    if directive is None:
                        b_continue = False
                        result = Result.failure(
                            f"Directive not found: {a_request.lineage_id}"
                        )
                    if b_continue and directive is not None:
                        result = Result.success(self._detail_response(kind, directive))
            else:
                result = Result.failure(f"Unsupported query kind: {kind}")

        return result

    def _detail_response(
        self, a_kind: QueryKind, a_directive: Directive
    ) -> QueryResponse:
        """Build a detail response for one directive."""
        payload: dict[str, Any] = {
            "lineage_id": a_directive.lineage_id,
            "execution_id": a_directive.execution_id,
            "title": a_directive.title,
            "active": a_directive.is_active(),
        }
        items: tuple[dict[str, Any], ...] = ()

        if a_kind in {QueryKind.RULE, QueryKind.DIRECTIVE}:
            payload["rule"] = a_directive.rule.model_dump(mode="json")
        if a_kind in {QueryKind.POLICY, QueryKind.DIRECTIVE}:
            if a_directive.policy is not None:
                payload["policy"] = a_directive.policy.model_dump(mode="json")
            else:
                payload["policy"] = None
        if a_kind == QueryKind.GUIDANCE:
            guidance = a_directive.reasoning_guidance()
            payload["guidance"] = (
                guidance.model_dump(mode="json") if guidance is not None else None
            )
            if a_directive.policy is not None:
                guide = a_directive.policy.guidance
                items = (
                    {
                        "reasoning": guide.reasoning,
                        "correct_example": guide.correct_example,
                        "incorrect_example": guide.incorrect_example,
                        "exceptions": guide.exceptions,
                    },
                )

        return QueryResponse(
            kind=a_kind.value,
            summary=f"{a_kind.value} for {a_directive.lineage_id}: {a_directive.title}",
            items=items,
            payload=payload,
        )

    @staticmethod
    def _directive_summary(a_directive: Directive) -> dict[str, Any]:
        """Compact catalog row for list/search."""
        return {
            "lineage_id": a_directive.lineage_id,
            "execution_id": a_directive.execution_id,
            "title": a_directive.title,
            "message": a_directive.rule.message,
            "type": a_directive.rule.type.value,
            "severity": a_directive.rule.weight.value,
            "status": a_directive.rule.status.value,
            "evaluator_type": a_directive.rule.evaluator_type,
            "has_policy": a_directive.has_policy(),
            "active": a_directive.is_active(),
        }

    async def get_policy_text(self, a_lineage_id: str) -> Result[str]:
        """Convenience: return a human-readable policy brief."""
        b_continue = True
        result: Result[str] = Result.failure("unreachable")
        if b_continue and not a_lineage_id:
            b_continue = False
            result = Result.failure("lineage_id is required")
        if b_continue:
            query = QueryRequest(kind=QueryKind.GUIDANCE, lineage_id=a_lineage_id)
            response = await self.execute(query)
            if response.is_failure():
                b_continue = False
                result = Result.failure(response.message)
            if b_continue:
                body = response.unwrap()
                guidance_obj = body.payload.get("guidance")
                guidance: dict[str, Any] = (
                    cast("dict[str, Any]", guidance_obj)
                    if isinstance(guidance_obj, dict)
                    else {}
                )
                lines = [
                    body.summary,
                    "",
                    f"Rationale: {guidance.get('rationale', '')}",
                    f"Fix: {guidance.get('fix_instructions', '')}",
                    "",
                    "Correct example:",
                    str(guidance.get("correct_example", "")),
                    "",
                    "Anti-pattern:",
                    str(guidance.get("anti_pattern", "")),
                ]
                result = Result.success("\n".join(lines))
        return result
