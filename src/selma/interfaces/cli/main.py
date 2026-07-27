"""CLI interface — command-line entry point.

Minimal composition root. All logic in use cases.
Selma lints its own source code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from selma.application.dto.lint_request import LintRequest
from selma.composition import Container
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.severity import Severity
from selma.infrastructure.config import ConfigLoader
from selma.infrastructure.config.models import SelmaConfig


def _collect_file_paths(a_path_strings: list[str]) -> list[FilePath]:
    """Collect Python file paths from argument strings."""
    file_paths: list[FilePath] = []
    for path_str in a_path_strings:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            file_paths.append(FilePath(str(path)))
        elif path.is_dir():
            file_paths.extend(
                FilePath(str(py_file)) for py_file in sorted(path.rglob("*.py"))
            )
    return file_paths


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="selma",
        description="Selma — Schema-driven AST linter enforcing Safe Coding Doctrine",
    )
    parser.add_argument("--version", action="version", version="Selma v0.1.0")
    parser.add_argument("paths", nargs="*", help="Files or directories to lint")

    # Output
    parser.add_argument(
        "-f",
        "--format",
        choices=["default", "json", "gcc", "guidance"],
        help="Output format",
    )
    parser.add_argument(
        "--guide", action="store_true", help="Include guidance in output"
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    # Execution
    parser.add_argument("--skip-tools", action="store_true", help="Skip external tools")
    parser.add_argument("--skip-ast", action="store_true", help="Skip AST rules")
    parser.add_argument("--only", help="Run only one check")
    parser.add_argument("--max-workers", type=int, help="Maximum parallel workers")
    parser.add_argument("--file-timeout", type=int, help="Per-file timeout in seconds")

    # Rules filter
    parser.add_argument("--codes", nargs="*", help="Only run rules with these codes")
    parser.add_argument(
        "--exclude-codes", nargs="*", help="Exclude rules with these codes"
    )
    parser.add_argument("--disable", nargs="*", help="Disable rules with these codes")

    # Directive paths
    parser.add_argument("--directive-root", help="Root directive directory")
    parser.add_argument("--directive-policy-dir", help="Policy definitions directory")
    parser.add_argument("--directive-rule-dir", help="Rule definitions directory")

    # Schema paths
    parser.add_argument("--schema-root", help="Root schema directory")
    parser.add_argument("--schema-rule-schema", help="Rule schema JSON file")
    parser.add_argument("--schema-policy-doctrine", help="Policy doctrine YAML file")

    # Config
    parser.add_argument(
        "--config",
        help="Path to pyproject.toml (auto-detected if not specified)",
    )

    # Verbosity
    parser.add_argument("-v", "--verbose", action="store_true")

    return parser


def _find_pyproject() -> Path | None:
    """Find pyproject.toml by walking up from cwd."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def main() -> Result[int]:
    """CLI entry point.

    Parses arguments, loads config, wires dependencies via Container,
    runs lint, formats and outputs results.
    """
    b_continue = True
    exit_code = 0
    parser = _build_parser()
    args = parser.parse_args()

    if b_continue and not args.paths:
        b_continue = False
        parser.print_help()
        exit_code = 0

    config: SelmaConfig | None = None
    if b_continue:
        # Build CLI args dict for config loader
        cli_args: dict[str, object] = {}
        if args.format:
            cli_args["format"] = args.format
        if args.guide:
            cli_args["guide"] = True
        if args.output:
            cli_args["output"] = args.output
        if args.no_color:
            cli_args["no_color"] = True
        if args.skip_tools:
            cli_args["skip_tools"] = True
        if args.skip_ast:
            cli_args["skip_ast"] = True
        if args.only:
            cli_args["only"] = args.only
        if args.max_workers:
            cli_args["max_workers"] = args.max_workers
        if args.file_timeout:
            cli_args["file_timeout"] = args.file_timeout
        if args.codes:
            cli_args["codes"] = args.codes
        if args.exclude_codes:
            cli_args["exclude_codes"] = args.exclude_codes
        if args.disable:
            cli_args["disable"] = args.disable
        if args.directive_root:
            cli_args["directive_root"] = args.directive_root
        if args.directive_policy_dir:
            cli_args["directive_policy_dir"] = args.directive_policy_dir
        if args.directive_rule_dir:
            cli_args["directive_rule_dir"] = args.directive_rule_dir
        if args.schema_root:
            cli_args["schema_root"] = args.schema_root
        if args.schema_rule_schema:
            cli_args["schema_rule_schema"] = args.schema_rule_schema
        if args.schema_policy_doctrine:
            cli_args["schema_policy_doctrine"] = args.schema_policy_doctrine

        # Resolve config path
        config_path: Path | None = None
        if args.config:
            config_path = Path(args.config)
        else:
            config_path = _find_pyproject()

        # Load configuration
        loader = ConfigLoader()
        config_result = loader.load(
            a_config_path=config_path,
            a_cli_args=cli_args or None,
        )

        if config_result.is_failure():
            sys.stderr.write(f"Configuration error: {config_result.message}\n")
            b_continue = False
            exit_code = 1

        if b_continue:
            config = config_result.unwrap()

    if b_continue and config is not None:
        container = Container()
        use_case = container.get_lint_use_case_with_defaults(
            a_rules_dir=config.directive.rule_dir,
            a_schema_path=config.schema_paths.rule_schema,
            a_policy_dir=config.directive.policy_dir,
        )

        exclude_codes: frozenset[str] = (
            frozenset(args.exclude_codes)
            if args.exclude_codes
            else frozenset(config.rules_filter.exclude_codes)
        )
        codes: frozenset[str] = (
            frozenset(args.codes)
            if args.codes
            else frozenset(config.rules_filter.codes)
        )

        file_paths = _collect_file_paths(args.paths)

        request = LintRequest(
            paths=tuple(file_paths),
            exclude_codes=exclude_codes,
            codes=codes,
            format=config.output.format,
            guide=config.output.guide,
            skip_tools=config.execution.skip_tools,
            skip_ast=config.execution.skip_ast,
            only=config.execution.only,
        )

        lint_result = use_case.execute(request)
        if lint_result.is_success():
            response = lint_result.unwrap()
            if args.verbose:
                report_findings = response.findings
            else:
                report_findings = tuple(
                    f for f in response.findings if f.severity != Severity.INFORMATIONAL
                )
            reporter = container.get_reporter(
                config.output.format,
            )
            report_result = reporter.report(
                report_findings,
            )
            if report_result.is_success():
                sys.stdout.write(report_result.unwrap() + "\n")
            if response.finding_count > 0:
                exit_code = 1
        else:
            sys.stderr.write(f"Error: {lint_result.message}\n")
            exit_code = 1

    return Result.success(exit_code)


def cli_entry() -> None:
    """Console script entry point — unwraps Result for sys.exit."""
    result = main()
    sys.exit(result.unwrap() if result.is_success() else 1)


if __name__ == "__main__":
    result = main()
    sys.exit(result.unwrap() if result.is_success() else 1)
