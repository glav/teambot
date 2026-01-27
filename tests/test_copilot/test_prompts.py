"""Tests for prompt templates."""

import pytest

from teambot.prompts.templates import (
    BUILDER,
    BUSINESS_ANALYST,
    PERSONA_TEMPLATES,
    PROJECT_MANAGER,
    REVIEWER,
    TECHNICAL_WRITER,
    PromptTemplate,
    get_persona_template,
)


class TestPromptTemplate:
    """Tests for PromptTemplate class."""

    def test_build_system_context(self):
        """Test building system context."""
        template = PromptTemplate(
            persona="test",
            role_description="Test Role",
            capabilities=["Cap 1", "Cap 2"],
            constraints=["Constraint 1"],
        )
        context = template.build_system_context()

        assert "Test Role" in context
        assert "Cap 1" in context
        assert "Cap 2" in context
        assert "Constraint 1" in context

    def test_build_system_context_with_output_format(self):
        """Test system context includes output format."""
        template = PromptTemplate(
            persona="test",
            role_description="Test",
            capabilities=["Cap"],
            constraints=["Con"],
            output_format="JSON",
        )
        context = template.build_system_context()

        assert "Output format: JSON" in context

    def test_build_prompt_basic(self):
        """Test building a basic prompt."""
        template = PromptTemplate(
            persona="test",
            role_description="Test",
            capabilities=["Cap"],
            constraints=["Con"],
        )
        prompt = template.build_prompt("Do something")

        assert "Task: Do something" in prompt
        assert "Test" in prompt

    def test_build_prompt_with_context(self):
        """Test building prompt with context."""
        template = PromptTemplate(
            persona="test",
            role_description="Test",
            capabilities=["Cap"],
            constraints=["Con"],
        )
        prompt = template.build_prompt("Do something", context="Prior work done")

        assert "Task: Do something" in prompt
        assert "Context:" in prompt
        assert "Prior work done" in prompt


class TestMVPPersonas:
    """Tests for MVP persona templates."""

    def test_project_manager_exists(self):
        """Test Project Manager template exists."""
        assert PROJECT_MANAGER is not None
        assert PROJECT_MANAGER.persona == "project_manager"
        assert "Coordinator" in PROJECT_MANAGER.role_description

    def test_business_analyst_exists(self):
        """Test Business Analyst template exists."""
        assert BUSINESS_ANALYST is not None
        assert BUSINESS_ANALYST.persona == "business_analyst"
        assert "requirements" in BUSINESS_ANALYST.role_description.lower()

    def test_technical_writer_exists(self):
        """Test Technical Writer template exists."""
        assert TECHNICAL_WRITER is not None
        assert TECHNICAL_WRITER.persona == "technical_writer"
        assert "documentation" in TECHNICAL_WRITER.role_description.lower()

    def test_builder_exists(self):
        """Test Builder template exists."""
        assert BUILDER is not None
        assert BUILDER.persona == "builder"
        assert "implement" in BUILDER.role_description.lower()

    def test_reviewer_exists(self):
        """Test Reviewer template exists."""
        assert REVIEWER is not None
        assert REVIEWER.persona == "reviewer"
        assert "review" in REVIEWER.role_description.lower()


class TestGetPersonaTemplate:
    """Tests for get_persona_template function."""

    def test_get_pm_template(self):
        """Test getting PM template."""
        template = get_persona_template("project_manager")
        assert template == PROJECT_MANAGER

    def test_get_pm_alias(self):
        """Test getting PM template via alias."""
        template = get_persona_template("pm")
        assert template == PROJECT_MANAGER

    def test_get_ba_template(self):
        """Test getting BA template."""
        template = get_persona_template("business_analyst")
        assert template == BUSINESS_ANALYST

    def test_get_ba_alias(self):
        """Test getting BA template via alias."""
        template = get_persona_template("ba")
        assert template == BUSINESS_ANALYST

    def test_get_writer_template(self):
        """Test getting writer template."""
        template = get_persona_template("technical_writer")
        assert template == TECHNICAL_WRITER

    def test_get_writer_alias(self):
        """Test getting writer template via alias."""
        template = get_persona_template("writer")
        assert template == TECHNICAL_WRITER

    def test_get_builder_template(self):
        """Test getting builder template."""
        template = get_persona_template("builder")
        assert template == BUILDER

    def test_get_builder_alias(self):
        """Test getting builder via developer alias."""
        template = get_persona_template("developer")
        assert template == BUILDER

    def test_get_reviewer_template(self):
        """Test getting reviewer template."""
        template = get_persona_template("reviewer")
        assert template == REVIEWER

    def test_case_insensitive(self):
        """Test lookup is case insensitive."""
        assert get_persona_template("PM") == PROJECT_MANAGER
        assert get_persona_template("Builder") == BUILDER

    def test_unknown_persona_raises(self):
        """Test unknown persona raises ValueError."""
        with pytest.raises(ValueError, match="Unknown persona"):
            get_persona_template("unknown_persona")

    def test_error_message_includes_available(self):
        """Test error message includes available personas."""
        with pytest.raises(ValueError, match="Available:"):
            get_persona_template("invalid")


class TestPersonaTemplatesRegistry:
    """Tests for PERSONA_TEMPLATES registry."""

    def test_all_personas_registered(self):
        """Test all MVP personas are registered."""
        required = ["pm", "ba", "writer", "builder", "reviewer"]
        for persona in required:
            assert persona in PERSONA_TEMPLATES

    def test_aliases_map_correctly(self):
        """Test aliases map to correct templates."""
        assert PERSONA_TEMPLATES["pm"] == PERSONA_TEMPLATES["project_manager"]
        assert PERSONA_TEMPLATES["ba"] == PERSONA_TEMPLATES["business_analyst"]
        assert PERSONA_TEMPLATES["writer"] == PERSONA_TEMPLATES["technical_writer"]
        assert PERSONA_TEMPLATES["developer"] == PERSONA_TEMPLATES["builder"]
