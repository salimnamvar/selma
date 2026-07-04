"""UCDiagram — intermediate representation of a parsed PlantUML use case diagram."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class UCDiagram:
    """Intermediate representation of a single use case diagram.

    Attributes:
        filename (str): PlantUML source filename.
        title (str): Diagram title from header.
        source (str): Raw PlantUML source text.
        group (str): Filename-based group classification.
        header (Dict[str, str]): Parsed header key-value pairs.
        usecases (List[Dict[str, Any]]): Parsed use case entries.
        notes (List[str]): Diagram note texts.
        relations (List[Dict[str, Any]]): Parsed relationship entries.
        associations (List[Dict[str, Any]]): Parsed association entries.
        actors (List[str]): Actor names found in diagram.
        actor_aliases (Dict[str, str]): Actor name to alias mapping.
        extref_aliases (Dict[str, str]): External reference alias mapping.
        has_subject_boundary (bool): Whether a subject boundary exists.
        technology_in_body (bool): Whether technology terms appear in body.
    """

    filename: str
    title: str
    source: str
    group: str
    header: Dict[str, str] = field(default_factory=dict)
    usecases: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    associations: List[Dict[str, Any]] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    actor_aliases: Dict[str, str] = field(default_factory=dict)
    extref_aliases: Dict[str, str] = field(default_factory=dict)
    has_subject_boundary: bool = False
    technology_in_body: bool = False
