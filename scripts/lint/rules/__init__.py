"""Auto-discover and register all lint rules."""
from __future__ import annotations

from scripts.lint.config import LintConfig
from scripts.lint.core.rule import Rule
from scripts.lint.rules.control_flow import SingleExitRule, ZeroRaiseRule
from scripts.lint.rules.returns import (
    ResultReturnRule, ExplicitReturnTypeRule, NoStarImportRule, InvalidResultSentinelRule,
)
from scripts.lint.rules.assertions import AssertValidationRule
from scripts.lint.rules.complexity import FunctionLengthRule
from scripts.lint.rules.error_handling import SpecificExceptionRule, NoSilentFailureRule, NoReraiseRule
from scripts.lint.rules.resources import ResourceContextManagerRule
from scripts.lint.rules.state import DeterminismRule, NoModuleLevelMutableRule
from scripts.lint.rules.security import NoEvalExecRule, ParameterizedQueryRule, NoSecretsRule
from scripts.lint.rules.style import APrefixRule, FunctionContractRule, NoMutableDefaultRule
from scripts.lint.rules.imports import ImportInFunctionRule
from scripts.lint.rules.b_continue import BContinueRule

INVALID_RESULT = None


def all_rules(a_config: LintConfig | None = None) -> list[Rule]:
    """Return all registered lint rules, filtered by config."""
    cfg = a_config or LintConfig()
    disabled = frozenset(cfg.rules.disabled)

    rules: list[Rule] = [
        # Control flow
        SingleExitRule(),
        ZeroRaiseRule(),
        # Returns
        ResultReturnRule(),
        ExplicitReturnTypeRule(),
        NoStarImportRule(),
        InvalidResultSentinelRule(),
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

    return rules
