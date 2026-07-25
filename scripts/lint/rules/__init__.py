"""Auto-discover and register all lint rules.

Loads both Python rule classes AND JSON rule files.
JSON rules are loaded from schema/rules/ directory.
"""

from __future__ import annotations

from pathlib import Path

from scripts.lint.config import LintConfig
from scripts.lint.core.json_rule import load_json_rules
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

_RULES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "schema" / "rules"


def all_rules(a_config: LintConfig | None = None) -> Result[list[Rule]]:
    """Return all registered lint rules, filtered by config.

    Loads Python rule classes AND JSON rule files from schema/rules/.
    JSON rules are added alongside Python rules. Duplicate codes are
    resolved by preferring Python rules (they can override JSON rules).

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

        # Python rule classes (existing)
        python_rules: list[Rule] = [
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

        # JSON rule files (new)
        json_rules = load_json_rules(_RULES_DIR)

        # Merge: Python rules take precedence over JSON rules with same code
        python_codes = {r.code for r in python_rules}
        json_only = [r for r in json_rules if r.code not in python_codes]

        rules = python_rules + json_only

        if disabled:
            rules = [r for r in rules if r.code not in disabled]

        result = Result.success(rules)
    return result
