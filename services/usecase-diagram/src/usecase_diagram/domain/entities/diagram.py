"""UCDiagram — intermediate representation of a parsed PlantUML use case diagram."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UCDiagram:
    """Intermediate representation of a single use case diagram."""

    filename: str
    title: str
    source: str
    group: str
    header: dict[str, str] = field(default_factory=dict)
    usecases: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    associations: list[dict] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    actor_aliases: dict[str, str] = field(default_factory=dict)
    extref_aliases: dict[str, str] = field(default_factory=dict)
    has_subject_boundary: bool = False
    technology_in_body: bool = False
