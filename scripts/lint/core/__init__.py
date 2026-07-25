from scripts.lint.core.engine import LintEngine
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import LintVisitor

INVALID_RESULT = None

__all__ = ["LintEngine", "LintVisitor", "Rule", "Violation"]
