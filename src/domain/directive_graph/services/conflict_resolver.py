"""Conflict resolver domain service.

Implements the deterministic multi-factor resolution algorithm from
SPECIFICATION.md §2.15.

Resolution order:
1. Single-sided explicit override (always_wins / never_wins / defer_to)
1b. Dual explicit overrides — compatible pairs or Conflict Artifact
2. Priority comparison (lower rank = higher authority)
3. Specificity score (higher = more specific = wins)
4. Recency (newer ``created_at`` wins)
5. Unresolvable → ``ConflictArtifact``

Reference: SPECIFICATION.md §2.15
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.directive_graph.enums import PRIORITY_RANK
from domain.directive_graph.enums import ConflictStrategy
from domain.directive_graph.services.specificity_calculator import SpecificityCalculator

if TYPE_CHECKING:
    from domain.directive_graph.directive import Directive
    from domain.directive_graph.directive_graph import DirectiveGraph
    from domain.directive_graph.value_objects.conflict_resolution import ConflictResolution


@dataclass(frozen=True)
class ConflictArtifact:
    """Escalation record when resolution cannot deterministically select a winner.

    Attributes:
        directive_a_id: First conflicting directive.
        directive_b_id: Second conflicting directive.
        reason: Human-readable explanation of why resolution failed.
    """

    directive_a_id: str
    directive_b_id: str
    reason: str


@dataclass(frozen=True)
class ConflictResolutionResult:
    """Result of a conflict resolution attempt between two directives.

    Attributes:
        winner: Winning directive, or None if unresolvable.
        loser: Losing directive, or None if unresolvable.
        method: Name of the tie-breaking step that determined the winner.
        artifact: Present when resolution is unresolvable.
    """

    winner: Directive | None
    loser: Directive | None
    method: str
    artifact: ConflictArtifact | None = None


class ConflictResolver:
    """Resolves conflicts between two directives using the §2.15 algorithm."""

    def __init__(self, specificity_calculator: SpecificityCalculator | None = None) -> None:
        """Create a resolver, optionally injecting a specificity calculator.

        Args:
            specificity_calculator: Optional scorer; a default is created if omitted.
        """
        self._specificity = specificity_calculator or SpecificityCalculator()

    def resolve(
        self,
        a_directive_a: Directive,
        a_directive_b: Directive,
        a_graph: DirectiveGraph,
    ) -> ConflictResolutionResult:
        """Resolve a conflict between two directives.

        Args:
            a_directive_a: First directive in the conflict.
            a_directive_b: Second directive in the conflict.
            a_graph: Full graph (for defer_to resolution).

        Returns:
            Outcome with winner, loser, and method.
        """
        cr_a = a_directive_a.conflict_resolution
        cr_b = a_directive_b.conflict_resolution

        result = None

        if cr_a is not None and cr_b is None:
            result = self._apply_strategy(cr_a, a_directive_a, a_directive_b, a_graph)
        elif cr_b is not None and cr_a is None:
            result = self._apply_strategy(cr_b, a_directive_b, a_directive_a, a_graph)

        if result is None and cr_a is not None and cr_b is not None:
            if self._compatible_overrides(cr_a, cr_b):
                result = self._apply_compatible_overrides(a_directive_a, a_directive_b, a_graph)
            else:
                result = self._unresolvable(
                    a_directive_a,
                    a_directive_b,
                    "Incompatible dual conflict_resolution overrides require human review.",
                )

        if result is None:
            result = self._computed_resolution(a_directive_a, a_directive_b)

        return result

    # ------------------------------------------------------------------
    # Explicit override helpers
    # ------------------------------------------------------------------

    def _apply_strategy(
        self,
        a_strategy: ConflictResolution,
        a_rule: Directive,
        a_other: Directive,
        a_graph: DirectiveGraph,
    ) -> ConflictResolutionResult | None:
        """Apply a single-sided strategy. Returns None to fall through."""
        result = None
        if a_strategy.strategy == ConflictStrategy.ALWAYS_WINS:
            result = ConflictResolutionResult(winner=a_rule, loser=a_other, method="explicit_always_wins")
        elif a_strategy.strategy == ConflictStrategy.NEVER_WINS:
            result = ConflictResolutionResult(winner=a_other, loser=a_rule, method="explicit_never_wins")
        elif a_strategy.strategy == ConflictStrategy.DEFER_TO and not self._pair_has_defer_cycle(a_rule, a_other):
            target = self._resolve_defer_to_target(a_strategy, a_rule, a_graph)
            if target is not None and target.id == a_other.id:
                result = ConflictResolutionResult(winner=a_other, loser=a_rule, method="defer_to")
        return result

    @staticmethod
    def _compatible_overrides(a_a: ConflictResolution, a_b: ConflictResolution) -> bool:
        """Return True for complementary dual overrides (SPEC compatible_overrides)."""
        sa, sb = a_a.strategy, a_b.strategy
        result = False
        if (sa == ConflictStrategy.ALWAYS_WINS and sb == ConflictStrategy.NEVER_WINS) or (
            sa == ConflictStrategy.NEVER_WINS and sb == ConflictStrategy.ALWAYS_WINS
        ):
            result = True
        elif sa == ConflictStrategy.DEFER_TO and sb == ConflictStrategy.DEFER_TO:
            result = a_a.defer_to == a_b.defer_to
        return result

    def _apply_compatible_overrides(
        self,
        a_rule_a: Directive,
        a_rule_b: Directive,
        a_graph: DirectiveGraph,
    ) -> ConflictResolutionResult | None:
        """Apply a compatible dual-override pair."""
        sa = a_rule_a.conflict_resolution
        sb = a_rule_b.conflict_resolution

        result = None

        if sa is None or sb is None:
            pass
        elif sa.strategy == ConflictStrategy.ALWAYS_WINS and sb.strategy == ConflictStrategy.NEVER_WINS:
            result = ConflictResolutionResult(winner=a_rule_a, loser=a_rule_b, method="compatible_always_never")
        elif sa.strategy == ConflictStrategy.NEVER_WINS and sb.strategy == ConflictStrategy.ALWAYS_WINS:
            result = ConflictResolutionResult(winner=a_rule_b, loser=a_rule_a, method="compatible_always_never")
        elif sa.strategy == ConflictStrategy.DEFER_TO and sb.strategy == ConflictStrategy.DEFER_TO:
            if not self._pair_has_defer_cycle(a_rule_a, a_rule_b):
                target = self._resolve_defer_to_target(sa, a_rule_a, a_graph)
                if target is None:
                    if self._defer_is_post_fork_ambiguous(sa, a_graph):
                        result = self._unresolvable(
                            a_rule_a,
                            a_rule_b,
                            "Dual defer_to target is post-fork ambiguous; human review required.",
                        )
                elif target.id == a_rule_a.id:
                    result = ConflictResolutionResult(winner=a_rule_a, loser=a_rule_b, method="defer_to")
                elif target.id == a_rule_b.id:
                    result = ConflictResolutionResult(winner=a_rule_b, loser=a_rule_a, method="defer_to")
        else:
            result = self._unresolvable(
                a_rule_a,
                a_rule_b,
                "Compatible override pair could not be applied; human review required.",
            )

        return result

    def _resolve_defer_to_target(
        self,
        a_strategy: ConflictResolution,
        a_rule: Directive,
        a_graph: DirectiveGraph,
    ) -> Directive | None:
        """Resolve defer_to per SPEC defer_to_reference_resolution.

        Returns:
            Resolved active/draft directive, or None to fall through.
            Raises no Conflict Artifact here for single-sided path.
        """
        target_id = a_strategy.defer_to
        result = None
        if target_id and target_id != a_rule.id:
            target = a_graph.get_by_id(target_id)
            if target is not None and target.is_active_for_resolution:
                result = target
            elif target is not None:
                lineage_id = target.lineage_id
                active = [d for d in a_graph.get_by_lineage_id(lineage_id) if d.is_active_for_resolution]
                if len(active) == 1:
                    result = active[0]
        return result

    def _defer_is_post_fork_ambiguous(
        self,
        a_strategy: ConflictResolution,
        a_graph: DirectiveGraph,
    ) -> bool:
        """Return True if defer_to points at a lineage with multiple actives."""
        result = False
        target_id = a_strategy.defer_to
        if target_id:
            target = a_graph.get_by_id(target_id)
            if target is not None and not target.is_active_for_resolution:
                active = [d for d in a_graph.get_by_lineage_id(target.lineage_id) if d.is_active_for_resolution]
                result = len(active) > 1
        return result

    @staticmethod
    def _pair_has_defer_cycle(a_rule_a: Directive, a_rule_b: Directive) -> bool:
        """Detect a simple two-node defer_to cycle between the pair."""
        cr_a = a_rule_a.conflict_resolution
        cr_b = a_rule_b.conflict_resolution
        return bool(
            cr_a
            and cr_a.strategy == ConflictStrategy.DEFER_TO
            and cr_a.defer_to == a_rule_b.id
            and cr_b
            and cr_b.strategy == ConflictStrategy.DEFER_TO
            and cr_b.defer_to == a_rule_a.id
        )

    # ------------------------------------------------------------------
    # Computed resolution
    # ------------------------------------------------------------------

    def _computed_resolution(
        self,
        a_directive_a: Directive,
        a_directive_b: Directive,
    ) -> ConflictResolutionResult:
        rank_a = PRIORITY_RANK[a_directive_a.priority]
        rank_b = PRIORITY_RANK[a_directive_b.priority]

        if rank_a != rank_b:
            winner, loser = (a_directive_a, a_directive_b) if rank_a < rank_b else (a_directive_b, a_directive_a)
            result = ConflictResolutionResult(winner=winner, loser=loser, method="priority")
        else:
            score_a = self._specificity.compute(a_directive_a)
            score_b = self._specificity.compute(a_directive_b)
            if score_a != score_b:
                winner, loser = (a_directive_a, a_directive_b) if score_a > score_b else (a_directive_b, a_directive_a)
                result = ConflictResolutionResult(winner=winner, loser=loser, method="specificity")
            elif a_directive_a.created_at != a_directive_b.created_at:
                winner, loser = (
                    (a_directive_a, a_directive_b)
                    if a_directive_a.created_at > a_directive_b.created_at
                    else (a_directive_b, a_directive_a)
                )
                result = ConflictResolutionResult(winner=winner, loser=loser, method="recency")
            else:
                result = self._unresolvable(
                    a_directive_a,
                    a_directive_b,
                    (
                        f"All resolution factors are equal; human review required. a={a_directive_a.id!r} b={a_directive_b.id!r}"
                    ),
                )

        return result

    @staticmethod
    def _unresolvable(
        a_directive_a: Directive,
        a_directive_b: Directive,
        a_reason: str,
    ) -> ConflictResolutionResult:
        return ConflictResolutionResult(
            winner=None,
            loser=None,
            method="unresolvable",
            artifact=ConflictArtifact(
                directive_a_id=a_directive_a.id,
                directive_b_id=a_directive_b.id,
                reason=a_reason,
            ),
        )
