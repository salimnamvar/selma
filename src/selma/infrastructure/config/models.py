"""Configuration models — all frozen for immutability using Pydantic v2.

Every value in the system comes from configuration, never hardcoded.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PathsConfig(BaseModel):
    """Directories and files to lint."""

    model_config = ConfigDict(frozen=True)

    include: tuple[str, ...] = ("src", "tests")
    exclude: tuple[str, ...] = (
        "__pycache__",
        "*.pyc",
        ".git",
        ".venv",
        "build",
        "dist",
        "*.egg-info",
    )
    extensions: tuple[str, ...] = (".py",)


class OutputConfig(BaseModel):
    """Output formatting options."""

    model_config = ConfigDict(frozen=True)

    format: str = "default"
    guide: bool = False
    file: str | None = None
    color: bool = True


class ExecutionConfig(BaseModel):
    """Execution behavior options."""

    model_config = ConfigDict(frozen=True)

    skip_tools: bool = False
    skip_ast: bool = False
    only: str | None = None
    max_workers: int = 4
    file_timeout: int = 30


class LoggingConfig(BaseModel):
    """Logging configuration."""

    model_config = ConfigDict(frozen=True)

    level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None


class ToolConfig(BaseModel):
    """Configuration for an external tool (ruff, pylint, pyright)."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    binary: str = ""
    args: tuple[str, ...] = ()
    rcfile: str | None = None
    fail_under: int = 8


class RulesFilterConfig(BaseModel):
    """Top-level rule filtering."""

    model_config = ConfigDict(frozen=True)

    disabled: tuple[str, ...] = ("SC-031", "SC-033", "SC-065", "SC-092", "SC-114")
    codes: tuple[str, ...] = ()
    exclude_codes: tuple[str, ...] = ()


class SC001Config(BaseModel):
    """SC-001: Single Exit Point."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_generators: bool = True
    exempt_names: tuple[str, ...] = ()


class SC002Config(BaseModel):
    """SC-002: Zero Raise."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_adapters: bool = True
    adapter_keywords: tuple[str, ...] = ("exception", "error", "http")


class SC003Config(BaseModel):
    """SC-003: Result Return."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_properties: bool = True
    exempt_abstract: bool = True


class SC004Config(BaseModel):
    """SC-004: INVALID_RESULT Sentinel."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    sentinel_name: str = "INVALID_RESULT"
    exempt_pure: bool = True


class SC005Config(BaseModel):
    """SC-005: No Tuple Returns."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True


class SC007Config(BaseModel):
    """SC-007: No Assert for Validation."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_tests: bool = True
    test_patterns: tuple[str, ...] = ("test_*.py", "*_test.py")


class SC010Config(BaseModel):
    """SC-010: Function Length."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "medium"
    max_lines: int = 60
    count_nested: bool = True
    exclude_non_executable: bool = True


class SC011Config(BaseModel):
    """SC-011: b_continue Pattern."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    require_all: bool = False
    require_result_functions: bool = True
    warn_multi_false: bool = True
    flag_alias: bool = True
    flag_delete: bool = True
    flag_parameter: bool = True
    flag_global: bool = True
    flag_attribute: bool = True


class SC013Config(BaseModel):
    """SC-013: Function Contracts."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    exempt_properties: bool = True
    required_sections: tuple[str, ...] = (
        "preconditions",
        "postconditions",
        "side effect",
        "resource",
        "failure",
    )


class SC022Config(BaseModel):
    """SC-022: No Input Mutation."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    read_only_methods: tuple[str, ...] = (
        "get",
        "copy",
        "items",
        "keys",
        "values",
        "iter",
        "len",
        "str",
        "repr",
    )
    mutation_methods: tuple[str, ...] = (
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "sort",
        "reverse",
        "update",
        "setdefault",
        "popitem",
        "add",
        "discard",
    )


class SC024Config(BaseModel):
    """SC-024: Explicit Return Types."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    exempt_abstract: bool = True


class SC025Config(BaseModel):
    """SC-025: No Star Imports."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "medium"
    allowed_modules: tuple[str, ...] = ()


class SC031Config(BaseModel):
    """SC-031: Type Validation."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "warning"
    exempt_dunders: bool = True
    skip_params: tuple[str, ...] = ("self", "cls")
    framework_types: tuple[str, ...] = ("BaseModel", "BaseSettings", "dataclass")


class SC033Config(BaseModel):
    """SC-033: Nullability Validation."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "warning"
    exempt_dunders: bool = True
    inherently_nullable: tuple[str, ...] = ("None",)
    skip_with_default: bool = True


class SC041Config(BaseModel):
    """SC-041: Specific Exception Handling."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    allow_broad_last: bool = True
    allow_bare_except: bool = False
    allow_base_exception: bool = False


class SC042Config(BaseModel):
    """SC-042: No Silent Failures."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    flag_empty: bool = True
    flag_pass_only: bool = True


class SC052Config(BaseModel):
    """SC-052: No Re-Raising."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    allow_in_finally: bool = False


class SC060Config(BaseModel):
    """SC-060: Log at First Detection Layer."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "warning"
    flag_duplicate: bool = True


class SC061Config(BaseModel):
    """SC-061: Structured Logging."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "warning"
    exempt_methods: tuple[str, ...] = ("debug",)
    flag_printf: bool = True
    flag_fstring: bool = True
    flag_percent: bool = True


class SC062Config(BaseModel):
    """SC-062: No Sensitive Data in Logs."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    sensitive_patterns: tuple[str, ...] = (
        "password",
        "secret",
        "api_key",
        "apikey",
        "token",
        "private_key",
        "access_key",
        "auth_token",
        "credential",
    )


class SC065Config(BaseModel):
    """SC-065: Mandatory Failure Logging."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    exempt_safe_decorator: bool = True
    log_levels: dict[str, str] = Field(
        default_factory=lambda: {
            "validation": "warning",
            "computation": "error",
            "system": "critical",
        }
    )


class SC070Config(BaseModel):
    """SC-070: No Module-Level Mutable State."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    exempt_constants: bool = True
    exempt_dunders: tuple[str, ...] = ("__all__", "__version__")
    exempt_context_var: bool = True
    exempt_frozen_dataclass: bool = True
    framework_globals: tuple[str, ...] = (
        "logger",
        "log",
        "app",
        "router",
        "db",
        "engine",
        "session",
        "config",
        "settings",
        "base",
        "Base",
        "metadata",
    )


class SC071Config(BaseModel):
    """SC-071: Deterministic Execution."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    forbidden_calls: tuple[str, ...] = (
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
    exempt_injection: bool = True
    injection_params: tuple[str, ...] = (
        "timestamp",
        "a_timestamp",
        "a_time",
        "seed",
        "a_seed",
        "a_clock",
    )
    exempt_crypto: bool = True
    exempt_infrastructure: tuple[str, ...] = (
        "logging",
        "structlog",
        "prometheus",
        "statsd",
    )


class SC080Config(BaseModel):
    """SC-080: Context Managers."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    resource_calls: tuple[str, ...] = (
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
        "sqlite3.connect",
    )


class SC090Config(BaseModel):
    """SC-090: Shared State Protection."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    detect_global: bool = True
    detect_nonlocal: bool = True
    strict_async: bool = True


class SC092Config(BaseModel):
    """SC-092: No Shared Mutable State Without Sync."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    sync_primitives: tuple[str, ...] = (
        "Lock",
        "RLock",
        "asyncio.Lock",
        "Semaphore",
        "asyncio.Semaphore",
    )


class SC100Config(BaseModel):
    """SC-100: No Secrets."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    secret_patterns: tuple[str, ...] = (
        "password",
        "secret",
        "api_key",
        "apikey",
        "token",
        "private_key",
        "access_key",
        "auth_token",
        "credential",
    )
    min_length: int = 8


class SC101Config(BaseModel):
    """SC-101: Parameterized Queries."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    execute_methods: tuple[str, ...] = (
        "execute",
        "executemany",
        "executescript",
    )
    sql_keywords: tuple[str, ...] = (
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "FROM",
        "WHERE",
        "JOIN",
        "INTO",
        "VALUES",
    )


class SC104Config(BaseModel):
    """SC-104: No eval/exec."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    forbidden_functions: tuple[str, ...] = ("eval", "exec", "compile")


class SC114Config(BaseModel):
    """SC-114: Recursion Limits."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "critical"
    max_depth: int = 10
    depth_param: str = "a_depth"
    exempt_names: tuple[str, ...] = ()


class SC115Config(BaseModel):
    """SC-115: Configurable Timeouts."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "high"
    io_calls: tuple[str, ...] = (
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.patch",
        "requests.head",
        "requests.options",
        "httpx.get",
        "httpx.post",
        "httpx.put",
        "httpx.delete",
        "aiohttp.ClientSession.get",
        "aiohttp.ClientSession.post",
        "urlopen",
        "socket.connect",
        "subprocess.run",
        "subprocess.Popen",
    )
    timeout_param: str = "timeout"
    default_timeout: int = 30


class NoPrintConfig(BaseModel):
    """No print() in src/."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "warning"
    exempt_tests: bool = True
    test_patterns: tuple[str, ...] = ("test_*.py", "*_test.py")


class TodoFormatConfig(BaseModel):
    """TODO Format."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "info"
    require_bug_ref: bool = True
    valid_format: str = "TODO(bugref): description"


class APrefixConfig(BaseModel):
    """a-prefix on function arguments."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "error"
    exempt_params: tuple[str, ...] = ("self", "cls", "args", "kwargs")
    exempt_prefixes: tuple[str, ...] = ("_", "__")
    inherited_methods: tuple[str, ...] = (
        "filter",
        "emit",
        "format",
        "formatTime",
        "formatException",
        "write",
        "read",
        "close",
        "flush",
        "seek",
        "tell",
        "readline",
        "readlines",
        "writelines",
    )
    exempt_decorated: bool = True


class MutableDefaultConfig(BaseModel):
    """Mutable default arguments."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    severity: str = "error"
    mutable_types: tuple[str, ...] = ("list", "dict", "set")


class RulesConfig(BaseModel):
    """Per-rule configuration container."""

    model_config = ConfigDict(frozen=True)

    sc001: SC001Config = Field(default_factory=SC001Config)
    sc002: SC002Config = Field(default_factory=SC002Config)
    sc003: SC003Config = Field(default_factory=SC003Config)
    sc004: SC004Config = Field(default_factory=SC004Config)
    sc005: SC005Config = Field(default_factory=SC005Config)
    sc007: SC007Config = Field(default_factory=SC007Config)
    sc010: SC010Config = Field(default_factory=SC010Config)
    sc011: SC011Config = Field(default_factory=SC011Config)
    sc013: SC013Config = Field(default_factory=SC013Config)
    sc022: SC022Config = Field(default_factory=SC022Config)
    sc024: SC024Config = Field(default_factory=SC024Config)
    sc025: SC025Config = Field(default_factory=SC025Config)
    sc031: SC031Config = Field(default_factory=SC031Config)
    sc033: SC033Config = Field(default_factory=SC033Config)
    sc041: SC041Config = Field(default_factory=SC041Config)
    sc042: SC042Config = Field(default_factory=SC042Config)
    sc052: SC052Config = Field(default_factory=SC052Config)
    sc060: SC060Config = Field(default_factory=SC060Config)
    sc061: SC061Config = Field(default_factory=SC061Config)
    sc062: SC062Config = Field(default_factory=SC062Config)
    sc065: SC065Config = Field(default_factory=SC065Config)
    sc070: SC070Config = Field(default_factory=SC070Config)
    sc071: SC071Config = Field(default_factory=SC071Config)
    sc080: SC080Config = Field(default_factory=SC080Config)
    sc090: SC090Config = Field(default_factory=SC090Config)
    sc092: SC092Config = Field(default_factory=SC092Config)
    sc100: SC100Config = Field(default_factory=SC100Config)
    sc101: SC101Config = Field(default_factory=SC101Config)
    sc104: SC104Config = Field(default_factory=SC104Config)
    sc114: SC114Config = Field(default_factory=SC114Config)
    sc115: SC115Config = Field(default_factory=SC115Config)
    no_print: NoPrintConfig = Field(default_factory=NoPrintConfig)
    todo_format: TodoFormatConfig = Field(default_factory=TodoFormatConfig)
    a_prefix: APrefixConfig = Field(default_factory=APrefixConfig)
    mutable_default: MutableDefaultConfig = Field(default_factory=MutableDefaultConfig)


def _default_ruff() -> ToolConfig:
    return ToolConfig(binary="ruff")


def _default_pylint() -> ToolConfig:
    return ToolConfig(
        binary="pylint",
        rcfile="pylintrc",
        fail_under=8,
        args=("--recursive=y",),
    )


def _default_pyright() -> ToolConfig:
    return ToolConfig(binary="pyright", args=("--strict",))


class ToolsConfig(BaseModel):
    """External tools configuration."""

    model_config = ConfigDict(frozen=True)

    ruff: ToolConfig = Field(default_factory=_default_ruff)
    pylint: ToolConfig = Field(default_factory=_default_pylint)
    pyright: ToolConfig = Field(default_factory=_default_pyright)


class SelmaConfig(BaseModel):
    """Top-level immutable configuration.

    All values come from configuration sources, never hardcoded.
    """

    model_config = ConfigDict(frozen=True)

    version: str = "0.1.0"
    name: str = "selma"

    paths: PathsConfig = Field(default_factory=PathsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    rules_filter: RulesFilterConfig = Field(default_factory=RulesFilterConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
