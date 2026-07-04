"""Tests for the CLI controller."""

from click.testing import CliRunner

from usecase_diagram.controller import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Use case diagram" in result.output


def test_lint_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", "--help"])
    assert result.exit_code == 0
    assert "Validate use case diagrams" in result.output


def test_fix_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["fix", "--help"])
    assert result.exit_code == 0
    assert "Apply deterministic fixes" in result.output
