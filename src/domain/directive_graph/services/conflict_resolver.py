"""Conflict resolver domain service.

Implements the deterministic multi-factor resolution algorithm from
SPECIFICATION.md §2.15.

Resolution order:
1. Explicit ``always_wins`` / ``never_wins`` overrides
2. Compatible symmetric override pairs
3. ``defer_to`` resolution
4. Priority comparison (lower rank = higher authority)
5. Specificity score (higher = more specific = wins)
6. Recency (newer ``created_at`` wins)
7. Unresolvable → ``ConflictArtifact``

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import ConflictStrategy
from domain.directive_graph.enums import PRIORITY_RANK
from domain.directive_graph.services.specificity_calculator import SpecificityCalculator


@dataclass(frozen=True)
class ConflictArtifact:
    """Escalation record when resolution cannot deterministically select a winner.

    Attributes:
        directive_a_id (str): First conflicting directive.
        directive_b_id (str): Second conflicting directive.
        reason (str): Human-readable explanation of why resolution failed.
    """

    directive_a_id: str
    directive_b_id: str
    reason: str


@dataclass(frozen=True)
class ConflictResolutionResult:
    """Result of a conflict resolution attempt between two directives.

    Attributes:
        winner (Directive | None): Winning directive, or None if unresolvable.
        loser (Directive | None): Losing directive, or None if unresolvable.
        method (str): Name of the tie-breaking step that determined the winner.
        artifact (ConflictArtifact | None): Present when resolution is unresolvable.
    """

    winner: Directive | None
    loser: Directive | None
    method: str
    artifact: ConflictArtifact | None = None


class ConflictResolver:
    """Resolves conflicts between two directives using the §2.15 algorithm.

    Attributes:
        _specificity (SpecificityCalculator): Specificity scorer.
    """

    def __init__(self, specificity_calculator: SpecificityCalculator | None = None) -> None:
        self._specificity = specificity_calculator or SpecificityCalculator()

    def resolve(
        self,
        directive_a: Directive,
        directive_b: Directive,
        graph: DirectiveGraph,
    ) -> ConflictResolutionResult:
        """Resolve a conflict between two directives.

        Args:
            directive_a (Directive): First directive in the conflict.
            directive_b (Directive): Second directive in the conflict.
            graph (DirectiveGraph): Full graph (for defer_to resolution).

        Returns:
            ConflictResolutionResult: Outcome with winner, loser, and method.
        """
        # Step 1: Explicit always_wins / never_wins (handles dual-always_wins escalation)
        res = self._check_explicit_overrides(directive_a, directive_b)
        if res is not None:
            return res

        # Step 2: defer_to resolution
        res = self._check_defer_to(directive_a, directive_b, graph)
        if res is not None:
            return res

        # Step 3: priority comparison (lower rank = higher authority)
        rank_a = PRIORITY_RANK[directive_a.priority]
        rank_b = PRIORITY_RANK[directive_b.priority]
        if rank_a != rank_b:
            winner, loser = (directive_a, directive_b) if rank_a < rank_b else (directive_b, directive_a)
            return ConflictResolutionResult(winner=winner, loser=loser, method="priority")

        # Step 4: Specificity
        score_a = self._specificity.compute(directive_a)
        score_b = self._specificity.compute(directive_b)
        if score_a != score_b:
            winner, loser = (directive_a, directive_b) if score_a > score_b else (directive_b, directive_a)
            return ConflictResolutionResult(winner=winner, loser=loser, method="specificity")

        # Step 5: Recency (newer created_at wins; lexicographic ISO 8601 comparison)
        if directive_a.created_at != directive_b.created_at:
            winner, loser = (
                (directive_a, directive_b)
                if directive_a.created_at > directive_b.created_at
                else (directive_b, directive_a)
            )
            return ConflictResolutionResult(winner=winner, loser=loser, method="recency")

        # Step 6: Unresolvable — escalate to Conflict Artifact
        return ConflictResolutionResult(
            winner=None,
            loser=None,
            method="unresolvable",
            artifact=ConflictArtifact(
                directive_a_id=directive_a.id,
                directive_b_id=directive_b.id,
                reason=(
                    "All resolution factors are equal; human review required. "
                    f"a={directive_a.id!r} b={directive_b.id!r}"
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_explicit_overrides(self, a: Directive, b: Directive) -> ConflictResolutionResult | None:
        """Handle always_wins / never_wins for either directive.

        Incompatible dual-always_wins is escalated to a Conflict Artifact
        before any single-sided winner is selected.

        Args:
            a (Directive): First directive.
            b (Directive): Second directive.

        Returns:
            ConflictResolutionResult | None: Result if deterministic; else None.
        """
        cr_a = a.conflict_resolution
        cr_b = b.conflict_resolution

        # Incompatible: both claim always_wins → escalate immediately
        if (
            cr_a is not None
            and cr_a.strategy == ConflictStrategy.ALWAYS_WINS
            and cr_b is not None
            and cr_b.strategy == ConflictStrategy.ALWAYS_WINS
        ):
            return ConflictResolutionResult(
                winner=None,
                loser=None,
                method="unresolvable",
                artifact=ConflictArtifact(
                    directive_a_id=a.id,
                    directive_b_id=b.id,
                    reason=("Both directives declare always_wins; " "incompatible overrides require human review."),
                ),
            )

        if cr_a is not None:
            if cr_a.strategy == ConflictStrategy.ALWAYS_WINS:
                return ConflictResolutionResult(winner=a, loser=b, method="explicit_always_wins")
            if cr_a.strategy == ConflictStrategy.NEVER_WINS:
                return ConflictResolutionResult(winner=b, loser=a, method="explicit_never_wins")

        if cr_b is not None:
            if cr_b.strategy == ConflictStrategy.ALWAYS_WINS:
                return ConflictResolutionResult(winner=b, loser=a, method="explicit_always_wins")
            if cr_b.strategy == ConflictStrategy.NEVER_WINS:
                return ConflictResolutionResult(winner=a, loser=b, method="explicit_never_wins")

        return None

    def _check_defer_to(self, a: Directive, b: Directive, graph: DirectiveGraph) -> ConflictResolutionResult | None:
        """Handle defer_to references.

        Args:
            a (Directive): First directive.
            b (Directive): Second directive.
            graph (DirectiveGraph): Graph for target resolution.

        Returns:
            ConflictResolutionResult | None: Result if deterministic; else None.
        """
        cr_a = a.conflict_resolution
        cr_b = b.conflict_resolution

        if cr_a is not None and cr_a.strategy == ConflictStrategy.DEFER_TO and cr_a.defer_to:
            target = graph.get_by_id(cr_a.defer_to)
            if target is not None and target.id == b.id:
                return ConflictResolutionResult(winner=b, loser=a, method="defer_to")

        if cr_b is not None and cr_b.strategy == ConflictStrategy.DEFER_TO and cr_b.defer_to:
            target = graph.get_by_id(cr_b.defer_to)
            if target is not None and target.id == a.id:
                return ConflictResolutionResult(winner=a, loser=b, method="defer_to")

        return None
