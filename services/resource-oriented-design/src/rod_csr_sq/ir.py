"""IR for RoD-CSR-SQ combined analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CSRAnalysis:
    """CSR layer interaction analysis."""
    has_actor: bool = False
    actor_name: str = ""
    entry_chain: list[str] = field(default_factory=list)
    has_controller: bool = False
    has_service: bool = False
    has_repository: bool = False
    has_database: bool = False
    controller_to_repo_calls: list[str] = field(default_factory=list)
    repo_to_service_calls: list[str] = field(default_factory=list)
    business_logic_in_controller: list[str] = field(default_factory=list)
    dto_transformations: list[str] = field(default_factory=list)
    validation_phases: list[str] = field(default_factory=list)
    is_infra_access: bool = False  # True when Service is absent and flow is Controller→Repository/Infra


@dataclass
class RoDAnalysis:
    """Resource-Oriented Design analysis."""
    resource_name: str = ""
    method_type: str = ""  # Get, List, Create, Update, Delete, Custom
    http_verb: str = ""
    uri_pattern: str = ""
    has_pagination: bool = False
    has_update_mask: bool = False
    has_state_transition: bool = False
    state_from: str = ""
    state_to: str = ""
    custom_method_name: str = ""
    resource_names_in_messages: list[str] = field(default_factory=list)
    method_names_in_service_calls: list[str] = field(default_factory=list)
    verb_as_path: list[str] = field(default_factory=list)


@dataclass
class SQStructureAnalysis:
    """SQ diagram structure analysis."""
    has_intro_note: bool = False
    has_summary_note: bool = False
    intro_fields: list[str] = field(default_factory=list)
    summary_fields: list[str] = field(default_factory=list)
    has_activation_bars: bool = False
    failure_paths: list[str] = field(default_factory=list)
    http_codes_on_returns: list[str] = field(default_factory=list)
    ref_targets: list[str] = field(default_factory=list)


@dataclass
class RodCsrSqDiagram:
    """Combined analysis of a single SQ diagram."""
    filename: str
    source: str = ""
    title: str = ""
    csr: CSRAnalysis = field(default_factory=CSRAnalysis)
    rod: RoDAnalysis = field(default_factory=RoDAnalysis)
    sq: SQStructureAnalysis = field(default_factory=SQStructureAnalysis)
    raw_participants: list[str] = field(default_factory=list)
    raw_messages: list[str] = field(default_factory=list)
