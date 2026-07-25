"""Read lint configuration from pyproject.toml [tool.selma.lint]."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import logging
from pathlib import Path
import tomllib

from scripts.lint.core.result import Result

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    """Binary paths for external lint tools."""

    ruff: str = "ruff"
    pylint: str = "pylint"
    pyright: str = "pyright"


@dataclass(frozen=True, slots=True)
class ExcludeConfig:
    """Path and code exclusion lists."""

    paths: tuple[str, ...] = ()
    codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComplexityConfig:
    """Function complexity thresholds."""

    max_lines: int = 60


@dataclass(frozen=True, slots=True)
class ResourcesConfig:
    """Resource calls that require context managers."""

    calls: tuple[str, ...] = (
        "open",
        "Popen",
        "Lock",
        "RLock",
        "connect",
        "NamedTemporaryFile",
        "TemporaryFile",
        "TemporaryDirectory",
        "socket",
        "urlopen",
    )


@dataclass(frozen=True, slots=True)
class DeterminismConfig:
    """Non-deterministic function calls to forbid."""

    forbidden: tuple[str, ...] = (
        "datetime.now",
        "datetime.utcnow",
        "time.time",
        "time.monotonic",
        "time.localtime",
        "time.gmtime",
        "random.random",
        "random.randint",
        "random.choice",
        "random.sample",
        "random.shuffle",
        "random.gauss",
        "uuid.uuid4",
    )


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Secret pattern names to detect in assignments."""

    secret_patterns: tuple[str, ...] = (
        "password",
        "secret",
        "api_key",
        "apikey",
        "token",
        "private_key",
        "access_key",
        "auth_token",
    )


@dataclass(frozen=True, slots=True)
class RulesConfig:
    """Rule configuration with sub-sections."""

    disabled: tuple[str, ...] = ()
    complexity: ComplexityConfig = field(default_factory=ComplexityConfig)
    resources: ResourcesConfig = field(default_factory=ResourcesConfig)
    determinism: DeterminismConfig = field(default_factory=DeterminismConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)


@dataclass(frozen=True, slots=True)
class LintConfig:
    """Top-level lint configuration loaded from pyproject.toml."""

    paths: tuple[str, ...] = ("src", "tests")
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    exclude: ExcludeConfig = field(default_factory=ExcludeConfig)
    rules: RulesConfig = field(default_factory=RulesConfig)


def load_config(a_project_root: str | Path | None = None) -> Result[LintConfig]:
    """Load lint configuration from pyproject.toml.

    Precondition: a_project_root is None or a valid directory path.
    Postcondition: returns parsed LintConfig or defaults on error.
    Side effect: reads pyproject.toml if present.
    Resource: file handle for pyproject.toml.
    Failure: returns Result.failure on read or parse error.
    """
    b_continue = True
    result: Result[LintConfig] = Result.success(LintConfig())

    if a_project_root is None:
        a_project_root = Path(__file__).resolve().parent.parent.parent
    else:
        a_project_root = Path(a_project_root)

    pyproject = a_project_root / "pyproject.toml"
    config = LintConfig()
    if pyproject.exists():
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
        except OSError as exc:
            b_continue = False
            logger.warning("Failed to read pyproject.toml: %s", exc)
            result = Result.failure(str(exc))
        except tomllib.TOMLDecodeError as exc:
            b_continue = False
            logger.warning("Invalid TOML in pyproject.toml: %s", exc)
            result = Result.failure(str(exc))

        if b_continue:
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
                        calls=tuple(resources_raw.get("calls", []))
                        or ResourcesConfig.calls,
                    ),
                    determinism=DeterminismConfig(
                        forbidden=tuple(determinism_raw.get("forbidden", []))
                        or DeterminismConfig.forbidden,
                    ),
                    security=SecurityConfig(
                        secret_patterns=tuple(security_raw.get("secret-patterns", []))
                        or SecurityConfig.secret_patterns,
                    ),
                )

                config = LintConfig(
                    paths=paths, runner=runner, exclude=exclude, rules=rules
                )

            result = Result.success(config)

    return result
