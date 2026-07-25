"""Configuration dataclasses — all frozen for immutability.

Every value in the system comes from configuration, never hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class PathsConfig:
    """Directories and files to lint."""

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


@dataclass(frozen=True)
class OutputConfig:
    """Output formatting options."""

    format: str = "default"
    guide: bool = False
    file: str | None = None
    color: bool = True


@dataclass(frozen=True)
class ExecutionConfig:
    """Execution behavior options."""

    skip_tools: bool = False
    skip_ast: bool = False
    only: str | None = None
    max_workers: int = 4
    file_timeout: int = 30


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None


@dataclass(frozen=True)
class ToolConfig:
    """Configuration for an external tool (ruff, pylint, pyright)."""

    enabled: bool = True
    binary: str = ""
    args: tuple[str, ...] = ()
    rcfile: str | None = None
    fail_under: int = 8


@dataclass(frozen=True)
class RulesFilterConfig:
    """Top-level rule filtering."""

    disabled: tuple[str, ...] = ("SC-031", "SC-033", "SC-114")
    codes: tuple[str, ...] = ()
    exclude_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SC001Config:
    """SC-001: Single Exit Point."""

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_generators: bool = True
    exempt_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class SC002Config:
    """SC-002: Zero Raise."""

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_adapters: bool = True
    adapter_keywords: tuple[str, ...] = ("exception", "error", "http")


@dataclass(frozen=True)
class SC003Config:
    """SC-003: Result Return."""

    enabled: bool = True
    severity: str = "critical"
    exempt_dunders: bool = True
    exempt_properties: bool = True
    exempt_abstract: bool = True


@dataclass(frozen=True)
class SC004Config:
    """SC-004: INVALID_RESULT Sentinel."""

    enabled: bool = True
    severity: str = "critical"
    sentinel_name: str = "INVALID_RESULT"
    exempt_pure: bool = True


@dataclass(frozen=True)
class SC005Config:
    """SC-005: No Tuple Returns."""

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True


@dataclass(frozen=True)
class SC007Config:
    """SC-007: No Assert for Validation."""

    enabled: bool = True
    severity: str = "critical"
    exempt_tests: bool = True
    test_patterns: tuple[str, ...] = ("test_*.py", "*_test.py")


@dataclass(frozen=True)
class SC010Config:
    """SC-010: Function Length."""

    enabled: bool = True
    severity: str = "medium"
    max_lines: int = 60
    count_nested: bool = True
    exclude_non_executable: bool = True


@dataclass(frozen=True)
class SC011Config:
    """SC-011: b_continue Pattern."""

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


@dataclass(frozen=True)
class SC013Config:
    """SC-013: Function Contracts."""

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


@dataclass(frozen=True)
class SC022Config:
    """SC-022: No Input Mutation."""

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
        "remove",
    )


@dataclass(frozen=True)
class SC024Config:
    """SC-024: Explicit Return Types."""

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    exempt_abstract: bool = True


@dataclass(frozen=True)
class SC025Config:
    """SC-025: No Star Imports."""

    enabled: bool = True
    severity: str = "medium"
    allowed_modules: tuple[str, ...] = ()


@dataclass(frozen=True)
class SC031Config:
    """SC-031: Type Validation."""

    enabled: bool = True
    severity: str = "warning"
    exempt_dunders: bool = True
    skip_params: tuple[str, ...] = ("self", "cls")
    framework_types: tuple[str, ...] = ("BaseModel", "BaseSettings", "dataclass")


@dataclass(frozen=True)
class SC033Config:
    """SC-033: Nullability Validation."""

    enabled: bool = True
    severity: str = "warning"
    exempt_dunders: bool = True
    inherently_nullable: tuple[str, ...] = ("None",)
    skip_with_default: bool = True


@dataclass(frozen=True)
class SC041Config:
    """SC-041: Specific Exception Handling."""

    enabled: bool = True
    severity: str = "critical"
    allow_broad_last: bool = True
    allow_bare_except: bool = False
    allow_base_exception: bool = False


@dataclass(frozen=True)
class SC042Config:
    """SC-042: No Silent Failures."""

    enabled: bool = True
    severity: str = "critical"
    flag_empty: bool = True
    flag_pass_only: bool = True


@dataclass(frozen=True)
class SC052Config:
    """SC-052: No Re-Raising."""

    enabled: bool = True
    severity: str = "critical"
    allow_in_finally: bool = False


@dataclass(frozen=True)
class SC060Config:
    """SC-060: Log at First Detection Layer."""

    enabled: bool = True
    severity: str = "warning"
    flag_duplicate: bool = True


@dataclass(frozen=True)
class SC061Config:
    """SC-061: Structured Logging."""

    enabled: bool = True
    severity: str = "warning"
    exempt_methods: tuple[str, ...] = ("debug",)
    flag_printf: bool = True
    flag_fstring: bool = True
    flag_percent: bool = True


@dataclass(frozen=True)
class SC062Config:
    """SC-062: No Sensitive Data in Logs."""

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


@dataclass(frozen=True)
class SC065Config:
    """SC-065: Mandatory Failure Logging."""

    enabled: bool = True
    severity: str = "high"
    exempt_dunders: bool = True
    exempt_safe_decorator: bool = True
    log_levels: dict[str, str] = field(
        default_factory=lambda: {
            "validation": "warning",
            "computation": "error",
            "system": "critical",
        }
    )


@dataclass(frozen=True)
class SC070Config:
    """SC-070: No Module-Level Mutable State."""

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


@dataclass(frozen=True)
class SC071Config:
    """SC-071: Deterministic Execution."""

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


@dataclass(frozen=True)
class SC080Config:
    """SC-080: Context Managers."""

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


@dataclass(frozen=True)
class SC090Config:
    """SC-090: Shared State Protection."""

    enabled: bool = True
    severity: str = "critical"
    detect_global: bool = True
    detect_nonlocal: bool = True
    strict_async: bool = True


@dataclass(frozen=True)
class SC092Config:
    """SC-092: No Shared Mutable State Without Sync."""

    enabled: bool = True
    severity: str = "critical"
    sync_primitives: tuple[str, ...] = (
        "Lock",
        "RLock",
        "asyncio.Lock",
        "Semaphore",
        "asyncio.Semaphore",
    )


@dataclass(frozen=True)
class SC100Config:
    """SC-100: No Secrets."""

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


@dataclass(frozen=True)
class SC101Config:
    """SC-101: Parameterized Queries."""

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


@dataclass(frozen=True)
class SC104Config:
    """SC-104: No eval/exec."""

    enabled: bool = True
    severity: str = "critical"
    forbidden_functions: tuple[str, ...] = ("eval", "exec", "compile")


@dataclass(frozen=True)
class SC114Config:
    """SC-114: Recursion Limits."""

    enabled: bool = True
    severity: str = "critical"
    max_depth: int = 10
    depth_param: str = "a_depth"
    exempt_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class SC115Config:
    """SC-115: Configurable Timeouts."""

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


@dataclass(frozen=True)
class NoPrintConfig:
    """No print() in src/."""

    enabled: bool = True
    severity: str = "warning"
    exempt_tests: bool = True
    test_patterns: tuple[str, ...] = ("test_*.py", "*_test.py")


@dataclass(frozen=True)
class TodoFormatConfig:
    """TODO Format."""

    enabled: bool = True
    severity: str = "info"
    require_bug_ref: bool = True
    valid_format: str = "TODO(bugref): description"


@dataclass(frozen=True)
class APrefixConfig:
    """a-prefix on function arguments."""

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


@dataclass(frozen=True)
class MutableDefaultConfig:
    """Mutable default arguments."""

    enabled: bool = True
    severity: str = "error"
    mutable_types: tuple[str, ...] = ("list", "dict", "set")


@dataclass(frozen=True)
class RulesConfig:
    """Per-rule configuration container."""

    sc001: SC001Config = field(default_factory=SC001Config)
    sc002: SC002Config = field(default_factory=SC002Config)
    sc003: SC003Config = field(default_factory=SC003Config)
    sc004: SC004Config = field(default_factory=SC004Config)
    sc005: SC005Config = field(default_factory=SC005Config)
    sc007: SC007Config = field(default_factory=SC007Config)
    sc010: SC010Config = field(default_factory=SC010Config)
    sc011: SC011Config = field(default_factory=SC011Config)
    sc013: SC013Config = field(default_factory=SC013Config)
    sc022: SC022Config = field(default_factory=SC022Config)
    sc024: SC024Config = field(default_factory=SC024Config)
    sc025: SC025Config = field(default_factory=SC025Config)
    sc031: SC031Config = field(default_factory=SC031Config)
    sc033: SC033Config = field(default_factory=SC033Config)
    sc041: SC041Config = field(default_factory=SC041Config)
    sc042: SC042Config = field(default_factory=SC042Config)
    sc052: SC052Config = field(default_factory=SC052Config)
    sc060: SC060Config = field(default_factory=SC060Config)
    sc061: SC061Config = field(default_factory=SC061Config)
    sc062: SC062Config = field(default_factory=SC062Config)
    sc065: SC065Config = field(default_factory=SC065Config)
    sc070: SC070Config = field(default_factory=SC070Config)
    sc071: SC071Config = field(default_factory=SC071Config)
    sc080: SC080Config = field(default_factory=SC080Config)
    sc090: SC090Config = field(default_factory=SC090Config)
    sc092: SC092Config = field(default_factory=SC092Config)
    sc100: SC100Config = field(default_factory=SC100Config)
    sc101: SC101Config = field(default_factory=SC101Config)
    sc104: SC104Config = field(default_factory=SC104Config)
    sc114: SC114Config = field(default_factory=SC114Config)
    sc115: SC115Config = field(default_factory=SC115Config)
    no_print: NoPrintConfig = field(default_factory=NoPrintConfig)
    todo_format: TodoFormatConfig = field(default_factory=TodoFormatConfig)
    a_prefix: APrefixConfig = field(default_factory=APrefixConfig)
    mutable_default: MutableDefaultConfig = field(
        default_factory=MutableDefaultConfig
    )


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


@dataclass(frozen=True)
class ToolsConfig:
    """External tools configuration."""

    ruff: ToolConfig = field(default_factory=_default_ruff)
    pylint: ToolConfig = field(default_factory=_default_pylint)
    pyright: ToolConfig = field(default_factory=_default_pyright)


@dataclass(frozen=True)
class SelmaConfig:
    """Top-level immutable configuration.

    All values come from configuration sources, never hardcoded.
    """

    version: str = "0.1.0"
    name: str = "selma"

    paths: PathsConfig = field(default_factory=PathsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    rules_filter: RulesFilterConfig = field(
        default_factory=RulesFilterConfig
    )
    rules: RulesConfig = field(default_factory=RulesConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
