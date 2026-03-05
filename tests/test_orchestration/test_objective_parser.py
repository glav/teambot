"""Tests for ObjectiveParser (TDD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from teambot.orchestration.objective_parser import (
    FrontmatterData,
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

    def test_parse_extracts_criteria_with_unchecked(self, objective_file: Path) -> None:
        """Unchecked criteria have completed=False."""
        result = parse_objective_file(objective_file)
        unchecked = [c for c in result.success_criteria if not c.completed]
        assert len(unchecked) == 2
        assert unchecked[0].description == "Login validates credentials against database"

    def test_parse_extracts_criteria_with_checked(self, objective_file: Path) -> None:
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

    def test_parse_handles_missing_optional_sections(self, minimal_objective_file: Path) -> None:
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
        empty_file.write_text("", encoding="utf-8")
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


class TestFeatureName:
    """Tests for feature_name property."""

    def test_feature_name_from_simple_title(self) -> None:
        """Simple title becomes feature name."""
        obj = ParsedObjective(title="User Authentication")
        assert obj.feature_name == "user-authentication"

    def test_feature_name_strips_common_words(self) -> None:
        """Common words like 'Add', 'Create' are stripped."""
        obj = ParsedObjective(title="Add User Authentication with OAuth2 Support")
        assert obj.feature_name == "user-authentication-oauth2"

    def test_feature_name_limits_to_three_words(self) -> None:
        """Feature name limited to 3 meaningful words."""
        obj = ParsedObjective(title="Implement Complex User Authentication System Module")
        assert obj.feature_name == "complex-user-authentication"

    def test_feature_name_handles_untitled(self) -> None:
        """Untitled objective gets 'feature' name."""
        obj = ParsedObjective(title="Untitled")
        assert obj.feature_name == "feature"

    def test_feature_name_handles_empty_title(self) -> None:
        """Empty title gets 'feature' name."""
        obj = ParsedObjective(title="")
        assert obj.feature_name == "feature"

    def test_feature_name_handles_objective_prefix(self) -> None:
        """Objective: prefix is stripped."""
        obj = ParsedObjective(title="Objective: Build API Endpoints")
        assert obj.feature_name == "api-endpoints"

    def test_feature_name_lowercase(self) -> None:
        """Feature name is lowercase."""
        obj = ParsedObjective(title="HTTP REST API")
        assert obj.feature_name == "http-rest-api"

    def test_feature_name_alphanumeric_only(self) -> None:
        """Feature name contains only alphanumeric and dashes."""
        obj = ParsedObjective(title="OAuth2.0 & JWT Auth!")
        assert obj.feature_name == "oauth2-jwt-auth"

    def test_feature_name_single_word(self) -> None:
        """Single meaningful word works."""
        obj = ParsedObjective(title="Refactoring")
        assert obj.feature_name == "refactoring"

    def test_feature_name_from_parsed_file(self, objective_file: Path) -> None:
        """Feature name derived from parsed objective file."""
        from teambot.orchestration.objective_parser import parse_objective_file

        result = parse_objective_file(objective_file)
        # Title is "Implement User Authentication"
        assert result.feature_name == "user-authentication"


class TestFrontmatterData:
    """Tests for FrontmatterData dataclass."""

    def test_default_values_are_none_or_empty(self) -> None:
        """All FrontmatterData fields default to None or empty list."""
        fmd = FrontmatterData()
        assert fmd.feature_name is None
        assert fmd.language is None
        assert fmd.framework is None
        assert fmd.test_preference is None
        assert fmd.scope is None
        assert fmd.acceptance_scenarios == []

    def test_can_set_all_fields(self) -> None:
        """All fields can be set."""
        fmd = FrontmatterData(
            feature_name="my-feature",
            language="python",
            framework="fastapi",
            test_preference="tdd",
            scope="medium",
            acceptance_scenarios=[{"name": "test", "steps": [], "expected": "pass"}],
        )
        assert fmd.feature_name == "my-feature"
        assert fmd.language == "python"
        assert fmd.framework == "fastapi"
        assert fmd.test_preference == "tdd"
        assert fmd.scope == "medium"
        assert len(fmd.acceptance_scenarios) == 1


class TestParsedObjectiveWithFrontmatter:
    """Tests for ParsedObjective with frontmatter defaults."""

    def test_frontmatter_defaults_to_empty(self) -> None:
        """ParsedObjective.frontmatter defaults to a FrontmatterData()."""
        obj = ParsedObjective(title="Test")
        assert isinstance(obj.frontmatter, FrontmatterData)
        assert obj.frontmatter.feature_name is None

    def test_frontmatter_instances_not_shared(self) -> None:
        """Each ParsedObjective gets its own FrontmatterData instance."""
        obj1 = ParsedObjective(title="A")
        obj2 = ParsedObjective(title="B")
        obj1.frontmatter.feature_name = "a-feature"
        assert obj2.frontmatter.feature_name is None


class TestFrontmatterParsing:
    """Tests for frontmatter parsing in parse_objective_file."""

    def test_frontmatter_feature_name_is_parsed(
        self, objective_file_with_frontmatter: Path
    ) -> None:
        """feature_name from frontmatter is parsed into FrontmatterData."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.frontmatter.feature_name == "user-auth"

    def test_frontmatter_language_is_parsed(self, objective_file_with_frontmatter: Path) -> None:
        """language from frontmatter is parsed correctly."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.frontmatter.language == "python"

    def test_frontmatter_framework_is_parsed(self, objective_file_with_frontmatter: Path) -> None:
        """framework from frontmatter is parsed correctly."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.frontmatter.framework == "fastapi"

    def test_frontmatter_test_preference_is_parsed(
        self, objective_file_with_frontmatter: Path
    ) -> None:
        """test_preference from frontmatter is parsed correctly."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.frontmatter.test_preference == "tdd"

    def test_frontmatter_scope_is_parsed(self, objective_file_with_frontmatter: Path) -> None:
        """scope from frontmatter is parsed correctly."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.frontmatter.scope == "medium"

    def test_frontmatter_acceptance_scenarios_are_parsed(
        self, objective_file_with_frontmatter: Path
    ) -> None:
        """acceptance_scenarios from frontmatter are parsed correctly."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert len(result.frontmatter.acceptance_scenarios) == 1
        scenario = result.frontmatter.acceptance_scenarios[0]
        assert scenario["name"] == "User can log in"
        assert scenario["steps"] == ["POST /login with valid credentials"]
        assert scenario["expected"] == "JWT token returned with 200 status"

    def test_frontmatter_feature_name_overrides_title(
        self, objective_file_with_frontmatter: Path
    ) -> None:
        """Frontmatter feature_name takes priority over title-derived name."""
        result = parse_objective_file(objective_file_with_frontmatter)
        # Title would give "user-authentication", but frontmatter has "user-auth"
        assert result.feature_name == "user-auth"

    def test_body_sections_still_parsed_with_frontmatter(
        self, objective_file_with_frontmatter: Path
    ) -> None:
        """Markdown body sections are correctly parsed when frontmatter is present."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.title == "Implement User Authentication"
        assert result.goals == ["Add login/logout functionality"]
        assert any(
            c.description == "Login validates credentials against database"
            for c in result.success_criteria
        )

    def test_file_without_frontmatter_still_works(self, objective_file: Path) -> None:
        """Files without frontmatter parse correctly (backward compatibility)."""
        result = parse_objective_file(objective_file)
        assert result.frontmatter.feature_name is None
        assert result.frontmatter.language is None
        assert result.frontmatter.acceptance_scenarios == []
        # Normal parsing still works
        assert result.title == "Implement User Authentication"
        assert len(result.goals) == 3

    def test_partial_frontmatter_works(self, tmp_path: Path) -> None:
        """Partial frontmatter (some fields missing) parses without error."""
        content = """---
language: python
scope: small
---
# My Task

## Goals
1. Do the thing

## Success Criteria
- [ ] Thing is done
"""
        path = tmp_path / "partial_frontmatter.md"
        path.write_text(content, encoding="utf-8")
        result = parse_objective_file(path)
        assert result.frontmatter.language == "python"
        assert result.frontmatter.scope == "small"
        assert result.frontmatter.feature_name is None
        assert result.frontmatter.framework is None
        assert result.frontmatter.test_preference is None
        assert result.frontmatter.acceptance_scenarios == []
        assert result.title == "My Task"

    def test_raw_content_includes_frontmatter(self, objective_file_with_frontmatter: Path) -> None:
        """raw_content stores the full file including frontmatter delimiters."""
        result = parse_objective_file(objective_file_with_frontmatter)
        assert result.raw_content.startswith("---")
        assert "feature_name: user-auth" in result.raw_content
        assert "# Objective:" in result.raw_content
