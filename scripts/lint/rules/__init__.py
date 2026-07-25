"""Auto-discover and register all lint rules."""

from __future__ import annotations

from scripts.lint.config import LintConfig
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.rules.assertions import AssertValidationRule
from scripts.lint.rules.b_continue import BContinueRule
from scripts.lint.rules.complexity import FunctionLengthRule
from scripts.lint.rules.control_flow import SingleExitRule
from scripts.lint.rules.control_flow import ZeroRaiseRule
from scripts.lint.rules.error_handling import NoReraiseRule
from scripts.lint.rules.error_handling import NoSilentFailureRule
from scripts.lint.rules.error_handling import SpecificExceptionRule
from scripts.lint.rules.imports import ImportInFunctionRule
from scripts.lint.rules.resources import ResourceContextManagerRule
from scripts.lint.rules.returns import ExplicitReturnTypeRule
from scripts.lint.rules.returns import NoStarImportRule
from scripts.lint.rules.returns import ResultReturnRule
from scripts.lint.rules.security import NoEvalExecRule
from scripts.lint.rules.security import NoSecretsRule
from scripts.lint.rules.security import ParameterizedQueryRule
from scripts.lint.rules.state import DeterminismRule
from scripts.lint.rules.state import NoModuleLevelMutableRule
from scripts.lint.rules.style import APrefixRule
from scripts.lint.rules.style import FunctionContractRule
from scripts.lint.rules.style import NoMutableDefaultRule


def all_rules(a_config: LintConfig | None = None) -> Result[list[Rule]]:
    """Return all registered lint rules, filtered by config.

    Precondition: None.
    Postcondition: Returns Ok with list of enabled Rule instances.
    Side effect: None.
    Resource: None.
    Failure: Never fails (always returns success).
    """
    b_continue = True
    rules: list[Rule] = []
    result: Result[list[Rule]] = Result.success(rules)
    if b_continue:
        cfg = a_config or LintConfig()
        disabled = frozenset(cfg.rules.disabled)

        rules = [
            # Control flow
            SingleExitRule(),
            ZeroRaiseRule(),
            # Returns
            ResultReturnRule(),
            ExplicitReturnTypeRule(),
            NoStarImportRule(),
            # Assertions
            AssertValidationRule(),
            # Complexity (configurable)
            FunctionLengthRule(cfg.rules.complexity),
            # Error handling
            SpecificExceptionRule(),
            NoSilentFailureRule(),
            NoReraiseRule(),
            # Resources (configurable)
            ResourceContextManagerRule(cfg.rules.resources),
            # State & determinism (configurable)
            DeterminismRule(cfg.rules.determinism),
            NoModuleLevelMutableRule(),
            # Security (configurable)
            NoEvalExecRule(),
            ParameterizedQueryRule(),
            NoSecretsRule(cfg.rules.security),
            # Style
            APrefixRule(),
            FunctionContractRule(),
            NoMutableDefaultRule(),
            # Imports
            ImportInFunctionRule(),
            # b_continue
            BContinueRule(),
        ]

        if disabled:
            rules = [r for r in rules if r.code not in disabled]

        result = Result.success(rules)
    return result
