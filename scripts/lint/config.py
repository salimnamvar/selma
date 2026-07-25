"""Read lint configuration from pyproject.toml [tool.selma.lint]."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path



@dataclass(frozen=True, slots=True)
class RunnerConfig:
    ruff: str = "ruff"
    pylint: str = "pylint"
    pyright: str = "pyright"


@dataclass(frozen=True, slots=True)
class ExcludeConfig:
    paths: tuple[str, ...] = ()
    codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComplexityConfig:
    max_lines: int = 60


@dataclass(frozen=True, slots=True)
class ResourcesConfig:
    calls: tuple[str, ...] = (
        "open", "Popen", "Lock", "RLock", "connect",
        "NamedTemporaryFile", "TemporaryFile", "TemporaryDirectory",
        "socket", "urlopen",
    )


@dataclass(frozen=True, slots=True)
class DeterminismConfig:
    forbidden: tuple[str, ...] = (
        "datetime.now", "datetime.utcnow",
        "time.time", "time.monotonic", "time.localtime", "time.gmtime",
        "random.random", "random.randint", "random.choice", "random.sample",
        "random.shuffle", "random.gauss",
        "uuid.uuid4",
    )


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    secret_patterns: tuple[str, ...] = (
        "password", "secret", "api_key", "apikey", "token",
        "private_key", "access_key", "auth_token",
    )


@dataclass(frozen=True, slots=True)
class RulesConfig:
    disabled: tuple[str, ...] = ()
    complexity: ComplexityConfig = field(default_factory=ComplexityConfig)
    resources: ResourcesConfig = field(default_factory=ResourcesConfig)
    determinism: DeterminismConfig = field(default_factory=DeterminismConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)


@dataclass(frozen=True, slots=True)
class LintConfig:
    paths: tuple[str, ...] = ("src", "tests")
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)
    rules: RulesConfig = field(default_factory=RulesConfig)


def _parse_determinism(forbidden: list[str]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for entry in forbidden:
        if "." in entry:
            mod, method = entry.split(".", 1)
            result.setdefault(mod, set()).add(method)
    return result


def load_config(a_project_root: str | Path | None = None) -> LintConfig:
    """Load lint configuration from pyproject.toml."""
    if a_project_root is None:
        a_project_root = Path(__file__).resolve().parent.parent.parent
    else:
        a_project_root = Path(a_project_root)

    pyproject = a_project_root / "pyproject.toml"
    config = LintConfig()
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)

        selma = data.get("tool", {}).get("selma", {}).get("lint", {})
        if selma:
            paths = tuple(selma.get("paths", ["src", "tests"]))

            runner_raw = selma.get("runner", {})
            runner = RunnerConfig(
                ruff=runner_raw.get("ruff", "ruff"),
                pylint=runner_raw.get("pylint", "pylint"),
                pyright=runner_raw.get("pyright", "pyright"),
            )

            exclude_raw = selma.get("exclude", {})
            exclude = ExcludeConfig(
                paths=tuple(exclude_raw.get("paths", [])),
                codes=tuple(exclude_raw.get("codes", [])),
            )

            rules_raw = selma.get("rules", {})
            complexity_raw = rules_raw.get("complexity", {})
            resources_raw = rules_raw.get("resources", {})
            determinism_raw = rules_raw.get("determinism", {})
            security_raw = rules_raw.get("security", {})

            rules = RulesConfig(
                disabled=tuple(rules_raw.get("disabled", [])),
                complexity=ComplexityConfig(
                    max_lines=complexity_raw.get("max-lines", 60),
                ),
                resources=ResourcesConfig(
                    calls=tuple(resources_raw.get("calls", [])) or ResourcesConfig.calls,
                ),
                determinism=DeterminismConfig(
                    forbidden=tuple(determinism_raw.get("forbidden", [])) or DeterminismConfig.forbidden,
                ),
                security=SecurityConfig(
                    secret_patterns=tuple(security_raw.get("secret-patterns", [])) or SecurityConfig.secret_patterns,
                ),
            )

            config = LintConfig(paths=paths, runner=runner, exclude=exclude, rules=rules)

    return config
