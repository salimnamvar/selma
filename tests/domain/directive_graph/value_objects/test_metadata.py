"""Tests for DirectiveMetadata and DatasetMetadata executable hint prohibition."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.directive_graph.value_objects.metadata import DatasetMetadata, DirectiveMetadata


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveMetadataHintProhibition:
    def test_valid_extension_key_accepted(self) -> None:
        dm = DirectiveMetadata(extensions={"x-custom-tag": "value"})
        assert dm.extensions["x-custom-tag"] == "value"

    def test_x_exec_prefix_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DirectiveMetadata(extensions={"x-exec-script": "rm -rf /"})

    def test_x_eval_prefix_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DirectiveMetadata(extensions={"x-eval-mode": "strict"})

    def test_x_hint_prefix_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DirectiveMetadata(extensions={"x-hint-message": "do this"})

    def test_evaluator_underscore_prefix_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DirectiveMetadata(extensions={"evaluator_type": "regex"})

    def test_evaluator_dot_prefix_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DirectiveMetadata(extensions={"evaluator.config": "value"})

    def test_empty_extensions_accepted(self) -> None:
        dm = DirectiveMetadata()
        assert dm.extensions == {}

    def test_frozen(self) -> None:
        dm = DirectiveMetadata()
        with pytest.raises(Exception):
            dm.extensions = {"new": "val"}  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.domain
class TestDatasetMetadataHintProhibition:
    def test_prohibited_key_raises(self) -> None:
        with pytest.raises(ValidationError, match="prohibited executable-hint"):
            DatasetMetadata(extensions={"x-exec-cmd": "payload"})

    def test_normal_keys_accepted(self) -> None:
        dm = DatasetMetadata(domain="finance", jurisdiction="EU")
        assert dm.domain == "finance"
