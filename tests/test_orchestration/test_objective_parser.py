"""Tests for ObjectiveParser (TDD)."""

from __future__ import annotations

import pytest
from pathlib import Path

from teambot.orchestration.objective_parser import (
    ParsedObjective,
    SuccessCriterion,
    parse_objective_file,
)


class TestParseObjectiveFile:
    """Tests for parse_objective_file function."""

    def test_parse_extracts_title_from_h1(self, objective_file: Path) -> None:
        """Title is extracted from H1 heading."""
        result = parse_objective_file(objective_file)
        assert result.title == "Implement User Authentication"

    def test_parse_extracts_title_without_objective_prefix(
        self, minimal_objective_file: Path
    ) -> None:
        """Title works without 'Objective:' prefix."""
        result = parse_objective_file(minimal_objective_file)
        assert result.title == "My Task"

    def test_parse_extracts_goals_list(self, objective_file: Path) -> None:
        """Goals are extracted from Goals section."""
        result = parse_objective_file(objective_file)
        assert len(result.goals) == 3
        assert result.goals[0] == "Add login/logout functionality"
        assert result.goals[1] == "Implement JWT session management"
        assert result.goals[2] == "Add password reset flow"

    def test_parse_extracts_criteria_with_unchecked(
        self, objective_file: Path
    ) -> None:
        """Unchecked criteria have completed=False."""
        result = parse_objective_file(objective_file)
        unchecked = [c for c in result.success_criteria if not c.completed]
        assert len(unchecked) == 2
        assert unchecked[0].description == "Login validates credentials against database"

    def test_parse_extracts_criteria_with_checked(
        self, objective_file: Path
    ) -> None:
        """Checked criteria have completed=True."""
        result = parse_objective_file(objective_file)
        checked = [c for c in result.success_criteria if c.completed]
        assert len(checked) == 1
        assert checked[0].description == "JWT tokens expire after 24 hours"

    def test_parse_extracts_constraints(self, objective_file: Path) -> None:
        """Constraints are extracted from Constraints section."""
        result = parse_objective_file(objective_file)
        assert len(result.constraints) == 2
        assert "Use existing PostgreSQL database" in result.constraints
        assert "Follow OAuth 2.0 standards" in result.constraints

    def test_parse_extracts_context(self, objective_file: Path) -> None:
        """Context is extracted from Context section."""
        result = parse_objective_file(objective_file)
        assert result.context is not None
        assert "Express.js" in result.context
        assert "middleware" in result.context

    def test_parse_handles_missing_optional_sections(
        self, minimal_objective_file: Path
    ) -> None:
        """Missing optional sections don't cause errors."""
        result = parse_objective_file(minimal_objective_file)
        assert result.context is None
        assert result.constraints == []

    def test_parse_missing_file_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError raised for missing file."""
        nonexistent = tmp_path / "nonexistent.md"
        with pytest.raises(FileNotFoundError):
            parse_objective_file(nonexistent)

    def test_parse_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        """Empty file returns defaults without error."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")
        result = parse_objective_file(empty_file)
        assert result.title == "Untitled"
        assert result.goals == []
        assert result.success_criteria == []

    def test_parse_stores_raw_content(self, objective_file: Path) -> None:
        """Raw content is stored for reference."""
        result = parse_objective_file(objective_file)
        assert "# Objective:" in result.raw_content
        assert "## Goals" in result.raw_content


class TestSuccessCriterion:
    """Tests for SuccessCriterion dataclass."""

    def test_default_completed_is_false(self) -> None:
        """Default completed status is False."""
        criterion = SuccessCriterion(description="Test")
        assert criterion.completed is False

    def test_can_create_completed_criterion(self) -> None:
        """Can create criterion with completed=True."""
        criterion = SuccessCriterion(description="Done", completed=True)
        assert criterion.completed is True


class TestParsedObjective:
    """Tests for ParsedObjective dataclass."""

    def test_default_factory_for_lists(self) -> None:
        """Lists default to empty, not None."""
        obj = ParsedObjective(title="Test")
        assert obj.goals == []
        assert obj.success_criteria == []
        assert obj.constraints == []
        assert obj.context is None

    def test_raw_content_defaults_to_empty(self) -> None:
        """Raw content defaults to empty string."""
        obj = ParsedObjective(title="Test")
        assert obj.raw_content == ""
