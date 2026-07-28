"""Selma Textual TUI — interactive inspect + queryable directive catalog.

Agents and humans share one session: inspect code, then ask for policy
guidance to correct findings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import ClassVar
from typing import cast

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.binding import BindingType
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import RichLog
from textual.widgets import Static

from selma.application.dto.inspect_request import InspectRequest
from selma.application.dto.query_request import QueryKind
from selma.application.dto.query_request import QueryRequest
from selma.application.use_cases.inspect_source import InspectSourceUseCase
from selma.application.use_cases.query_directive import QueryDirectiveUseCase
from selma.composition import Container
from selma.domain.value_objects.file_path import FilePath
from selma.infrastructure.config.models import SelmaConfig


class SelmaApp(App[None]):
    """Interactive governance session.

    Commands (type in the input box):

    - ``help`` — show this help
    - ``list`` — list directives
    - ``search <text>`` — search directives
    - ``policy <ID>`` — show policy / reasoning for Machine ID
    - ``rule <ID>`` — show executable rule
    - ``guidance <ID>`` — show remediation guidance
    - ``inspect <path> [path...]`` — inspect Python sources
    - ``quit`` / ``exit`` — leave the session
    """

    CSS = """
    Screen {
        layout: vertical;
    }
    #banner {
        height: 3;
        padding: 0 1;
        background: $boost;
        color: $text;
    }
    #output {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    #cmdline {
        dock: bottom;
        height: 3;
        margin: 0 1 1 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(
        self,
        a_inspect: InspectSourceUseCase,
        a_query: QueryDirectiveUseCase,
    ) -> None:
        super().__init__()
        self._inspect = a_inspect
        self._query = a_query
        self.title = "Selma"
        self.sub_title = "Governance session"

    def compose(self) -> ComposeResult:
        """Build the session layout."""
        yield Header()
        yield Static(
            "Selma governance session — type help for commands",
            id="banner",
        )
        with Vertical():
            yield RichLog(id="output", highlight=True, markup=True, wrap=True)
            with Horizontal(id="cmdline"):
                yield Input(
                    placeholder="command (list | policy SC-001 | inspect src)…",
                    id="cmd",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Focus command input and print welcome."""
        log = self.query_one("#output", RichLog)
        log.write(
            "[bold green]Selma[/] ready. Directives are queryable and inspectable."
        )
        log.write(
            "Examples: [cyan]list[/] · [cyan]policy SC-001[/] · [cyan]inspect src[/]"
        )
        self.query_one("#cmd", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle a command line."""
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        log = self.query_one("#output", RichLog)
        log.write(f"[bold]$[/] {text}")
        await self._dispatch(text, log)

    async def _dispatch(self, a_line: str, a_log: RichLog) -> None:
        """Route a command to inspect or query use cases."""
        parts = a_line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in {"quit", "exit", "q"}:
            self.exit()
            return
        if cmd in {"help", "?"}:
            a_log.write(self.__doc__ or "help")
            return
        if cmd == "list":
            await self._query_cmd(QueryKind.LIST, "", "", a_log)
            return
        if cmd == "search":
            await self._query_cmd(QueryKind.SEARCH, "", " ".join(args), a_log)
            return
        if cmd in {"policy", "rule", "directive", "guidance"}:
            if not args:
                a_log.write(f"[red]usage:[/] {cmd} <LINEAGE_ID>")
                return
            await self._query_cmd(QueryKind(cmd), args[0].upper(), "", a_log)
            return
        if cmd in {"inspect", "lint"}:
            if not args:
                a_log.write("[red]usage:[/] inspect <path> [path...]")
                return
            await self._inspect_cmd(args, a_log)
            return

        a_log.write(f"[yellow]Unknown command:[/] {cmd}. Type [cyan]help[/].")

    async def _query_cmd(
        self,
        a_kind: QueryKind,
        a_lineage_id: str,
        a_text: str,
        a_log: RichLog,
    ) -> None:
        """Run QueryDirectiveUseCase and render."""
        request = QueryRequest(
            kind=a_kind,
            lineage_id=a_lineage_id,
            text=a_text,
            limit=40,
        )
        result = await self._query.execute(request)
        if result.is_failure():
            a_log.write(f"[red]{result.message}[/]")
            return
        response = result.unwrap()
        a_log.write(f"[bold]{response.summary}[/]")
        for item in response.items:
            lineage = item.get("lineage_id", "")
            title = item.get("title", item.get("message", ""))
            status = item.get("status", "")
            a_log.write(f"  [cyan]{lineage}[/] {title} ([dim]{status}[/])")
        if response.payload and a_kind != QueryKind.LIST:
            guidance_obj = response.payload.get("guidance")
            if isinstance(guidance_obj, dict) and guidance_obj:
                guidance = cast("dict[str, Any]", guidance_obj)
                a_log.write(f"[green]Title:[/] {guidance.get('title', '')}")
                a_log.write(f"[green]Rationale:[/] {guidance.get('rationale', '')}")
                a_log.write(f"[green]Fix:[/] {guidance.get('fix_instructions', '')}")
                correct = str(guidance.get("correct_example") or "")
                anti = str(guidance.get("anti_pattern") or "")
                if correct:
                    a_log.write("[green]Correct example:[/]")
                    a_log.write(correct[:2000])
                if anti:
                    a_log.write("[red]Anti-pattern:[/]")
                    a_log.write(anti[:2000])
            elif a_kind == QueryKind.POLICY:
                policy_obj = response.payload.get("policy")
                if policy_obj is None:
                    a_log.write("[yellow]No policy document paired.[/]")
                elif isinstance(policy_obj, dict):
                    policy = cast("dict[str, Any]", policy_obj)
                    preamble: dict[str, Any] = {}
                    preamble_raw = policy.get("preamble")
                    if isinstance(preamble_raw, dict):
                        preamble = cast("dict[str, Any]", preamble_raw)
                    a_log.write(f"[green]Purpose:[/] {preamble.get('purpose', '')}")
                    a_log.write(f"[green]Scope:[/] {preamble.get('scope', '')}")
                    guide: dict[str, Any] = {}
                    guide_raw = policy.get("guidance")
                    if isinstance(guide_raw, dict):
                        guide = cast("dict[str, Any]", guide_raw)
                    a_log.write(f"[green]Reasoning:[/] {guide.get('reasoning', '')}")

    async def _inspect_cmd(self, a_paths: list[str], a_log: RichLog) -> None:
        """Run InspectSourceUseCase and render findings."""
        file_paths: list[FilePath] = []
        for path_str in a_paths:
            path = Path(path_str)
            if path.is_file() and path.suffix == ".py":
                file_paths.append(FilePath(str(path)))
            elif path.is_dir():
                file_paths.extend(
                    FilePath(str(py)) for py in sorted(path.rglob("*.py"))
                )
            else:
                a_log.write(f"[yellow]Skip missing path:[/] {path_str}")
        if not file_paths:
            a_log.write("[yellow]No Python files found.[/]")
            return
        request = InspectRequest(paths=tuple(file_paths), guide=True)
        result = await self._inspect.execute(request)
        if result.is_failure():
            a_log.write(f"[red]{result.message}[/]")
            return
        response = result.unwrap()
        a_log.write(f"[bold]{response.summary}[/]")
        for finding in response.findings:
            a_log.write(str(finding))
            if finding.guidance is not None:
                fix = finding.guidance.fix_instructions[:200]
                a_log.write(f"  [dim]→[/] {fix}")
                a_log.write(f"  [dim]hint:[/] ask  guidance {finding.rule_id}")


async def run_tui(a_config: SelmaConfig) -> None:
    """Build container and run the Textual app."""
    container = Container()
    repository = container.get_directive_repository(
        a_rules_dir=a_config.directive.rule_dir,
        a_schema_path=a_config.schema_paths.rule_schema,
        a_policy_dir=a_config.directive.policy_dir,
    )
    inspect_uc = container.get_inspect_use_case(
        a_directive_repository=repository,
        a_reporter=container.get_reporter("default"),
    )
    query_uc = container.get_query_use_case(a_directive_repository=repository)
    app = SelmaApp(a_inspect=inspect_uc, a_query=query_uc)
    await app.run_async()
