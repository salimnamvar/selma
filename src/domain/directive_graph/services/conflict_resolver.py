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

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import PRIORITY_RANK, ConflictStrategy
from domain.directive_graph.services.specificity_calculator import SpecificityCalculator
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
        directive_a: Directive,
        directive_b: Directive,
        graph: DirectiveGraph,
    ) -> ConflictResolutionResult:
        """Resolve a conflict between two directives.

        Args:
            directive_a: First directive in the conflict.
            directive_b: Second directive in the conflict.
            graph: Full graph (for defer_to resolution).

        Returns:
            Outcome with winner, loser, and method.
        """
        cr_a = directive_a.conflict_resolution
        cr_b = directive_b.conflict_resolution

        # Step 1: single-sided explicit override
        if cr_a is not None and cr_b is None:
            res = self._apply_strategy(cr_a, directive_a, directive_b, graph)
            if res is not None:
                return res
        elif cr_b is not None and cr_a is None:
            res = self._apply_strategy(cr_b, directive_b, directive_a, graph)
            if res is not None:
                return res

        # Step 1b: dual explicit overrides
        if cr_a is not None and cr_b is not None:
            if self._compatible_overrides(cr_a, cr_b):
                res = self._apply_compatible_overrides(directive_a, directive_b, graph)
                if res is not None:
                    return res
                # null from dual defer_to → fall through to computed resolution
            else:
                return self._unresolvable(
                    directive_a,
                    directive_b,
                    "Incompatible dual conflict_resolution overrides require human review.",
                )

        # Step 2: computed resolution
        return self._computed_resolution(directive_a, directive_b)

    # ------------------------------------------------------------------
    # Explicit override helpers
    # ------------------------------------------------------------------

    def _apply_strategy(
        self,
        strategy: ConflictResolution,
        rule: Directive,
        other: Directive,
        graph: DirectiveGraph,
    ) -> ConflictResolutionResult | None:
        """Apply a single-sided strategy. Returns None to fall through."""
        if strategy.strategy == ConflictStrategy.ALWAYS_WINS:
            return ConflictResolutionResult(winner=rule, loser=other, method="explicit_always_wins")
        if strategy.strategy == ConflictStrategy.NEVER_WINS:
            return ConflictResolutionResult(winner=other, loser=rule, method="explicit_never_wins")
        if strategy.strategy == ConflictStrategy.DEFER_TO:
            if self._pair_has_defer_cycle(rule, other):
                return None  # ignore defer_to overrides → fall through
            target = self._resolve_defer_to_target(strategy, rule, graph)
            if target is None:
                return None
            # Winner is the deferred-to rule when it is the other party, or
            # more generally the resolved target when it matches the conflict pair.
            if target.id == other.id:
                return ConflictResolutionResult(winner=other, loser=rule, method="defer_to")
            if target.id == rule.id:
                return None  # self-ref ignored
            # Target resolved to a third rule — still a deterministic override
            # favoring the deferred target over the deferring rule is not
            # pairwise; fall through unless the target is the other rule.
            return None
        return None

    @staticmethod
    def _compatible_overrides(a: ConflictResolution, b: ConflictResolution) -> bool:
        """Return True for complementary dual overrides (SPEC compatible_overrides)."""
        sa, sb = a.strategy, b.strategy
        if (sa == ConflictStrategy.ALWAYS_WINS and sb == ConflictStrategy.NEVER_WINS) or (
            sa == ConflictStrategy.NEVER_WINS and sb == ConflictStrategy.ALWAYS_WINS
        ):
            return True
        if sa == ConflictStrategy.DEFER_TO and sb == ConflictStrategy.DEFER_TO:
            return a.defer_to == b.defer_to
        return False

    def _apply_compatible_overrides(
        self,
        rule_a: Directive,
        rule_b: Directive,
        graph: DirectiveGraph,
    ) -> ConflictResolutionResult | None:
        """Apply a compatible dual-override pair."""
        sa = rule_a.conflict_resolution
        sb = rule_b.conflict_resolution
        assert sa is not None and sb is not None

        if sa.strategy == ConflictStrategy.ALWAYS_WINS and sb.strategy == ConflictStrategy.NEVER_WINS:
            return ConflictResolutionResult(
                winner=rule_a, loser=rule_b, method="compatible_always_never"
            )
        if sa.strategy == ConflictStrategy.NEVER_WINS and sb.strategy == ConflictStrategy.ALWAYS_WINS:
            return ConflictResolutionResult(
                winner=rule_b, loser=rule_a, method="compatible_always_never"
            )
        if sa.strategy == ConflictStrategy.DEFER_TO and sb.strategy == ConflictStrategy.DEFER_TO:
            if self._pair_has_defer_cycle(rule_a, rule_b):
                return None
            target = self._resolve_defer_to_target(sa, rule_a, graph)
            if target is None:
                # Ambiguous or missing — SPEC: dual-defer ambiguity may escalate.
                # Missing/zero-successor → fall through (return None).
                # Multi-active post-fork → Conflict Artifact.
                if self._defer_is_post_fork_ambiguous(sa, graph):
                    return self._unresolvable(
                        rule_a,
                        rule_b,
                        "Dual defer_to target is post-fork ambiguous; human review required.",
                    )
                return None
            if target.id == rule_a.id:
                return ConflictResolutionResult(winner=rule_a, loser=rule_b, method="defer_to")
            if target.id == rule_b.id:
                return ConflictResolutionResult(winner=rule_b, loser=rule_a, method="defer_to")
            return None

        return self._unresolvable(
            rule_a,
            rule_b,
            "Compatible override pair could not be applied; human review required.",
        )

    def _resolve_defer_to_target(
        self,
        strategy: ConflictResolution,
        rule: Directive,
        graph: DirectiveGraph,
    ) -> Directive | None:
        """Resolve defer_to per SPEC defer_to_reference_resolution.

        Returns:
            Resolved active/draft directive, or None to fall through.
            Raises no Conflict Artifact here for single-sided path.
        """
        target_id = strategy.defer_to
        if not target_id:
            return None
        if target_id == rule.id:
            return None  # self-reference ignored

        target = graph.get_by_id(target_id)
        if target is not None and target.is_active_for_resolution:
            return target

        if target is not None:
            # deprecated/superseded — look for unique active successor in lineage
            lineage_id = target.lineage_id
            active = [d for d in graph.get_by_lineage_id(lineage_id) if d.is_active_for_resolution]
            if len(active) == 1:
                return active[0]
            # 0 or many → fall through (many handled as ambiguous at dual path)
            return None

        return None  # not found

    def _defer_is_post_fork_ambiguous(
        self,
        strategy: ConflictResolution,
        graph: DirectiveGraph,
    ) -> bool:
        """Return True if defer_to points at a lineage with multiple actives."""
        target_id = strategy.defer_to
        if not target_id:
            return False
        target = graph.get_by_id(target_id)
        if target is None:
            return False
        if target.is_active_for_resolution:
            return False
        active = [d for d in graph.get_by_lineage_id(target.lineage_id) if d.is_active_for_resolution]
        return len(active) > 1

    @staticmethod
    def _pair_has_defer_cycle(rule_a: Directive, rule_b: Directive) -> bool:
        """Detect a simple two-node defer_to cycle between the pair."""
        cr_a = rule_a.conflict_resolution
        cr_b = rule_b.conflict_resolution
        return bool(
            cr_a
            and cr_a.strategy == ConflictStrategy.DEFER_TO
            and cr_a.defer_to == rule_b.id
            and cr_b
            and cr_b.strategy == ConflictStrategy.DEFER_TO
            and cr_b.defer_to == rule_a.id
        )

    # ------------------------------------------------------------------
    # Computed resolution
    # ------------------------------------------------------------------

    def _computed_resolution(
        self,
        directive_a: Directive,
        directive_b: Directive,
    ) -> ConflictResolutionResult:
        rank_a = PRIORITY_RANK[directive_a.priority]
        rank_b = PRIORITY_RANK[directive_b.priority]
        if rank_a != rank_b:
            winner, loser = (directive_a, directive_b) if rank_a < rank_b else (directive_b, directive_a)
            return ConflictResolutionResult(winner=winner, loser=loser, method="priority")

        score_a = self._specificity.compute(directive_a)
        score_b = self._specificity.compute(directive_b)
        if score_a != score_b:
            winner, loser = (directive_a, directive_b) if score_a > score_b else (directive_b, directive_a)
            return ConflictResolutionResult(winner=winner, loser=loser, method="specificity")

        if directive_a.created_at != directive_b.created_at:
            winner, loser = (
                (directive_a, directive_b)
                if directive_a.created_at > directive_b.created_at
                else (directive_b, directive_a)
            )
            return ConflictResolutionResult(winner=winner, loser=loser, method="recency")

        return self._unresolvable(
            directive_a,
            directive_b,
            (
                "All resolution factors are equal; human review required. "
                f"a={directive_a.id!r} b={directive_b.id!r}"
            ),
        )

    @staticmethod
    def _unresolvable(
        directive_a: Directive,
        directive_b: Directive,
        reason: str,
    ) -> ConflictResolutionResult:
        return ConflictResolutionResult(
            winner=None,
            loser=None,
            method="unresolvable",
            artifact=ConflictArtifact(
                directive_a_id=directive_a.id,
                directive_b_id=directive_b.id,
                reason=reason,
            ),
        )
