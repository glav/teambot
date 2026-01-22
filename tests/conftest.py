"""Shared pytest fixtures for TeamBot tests."""

import pytest


@pytest.fixture
def temp_teambot_dir(tmp_path):
    """Create a temporary .teambot directory structure."""
    teambot_dir = tmp_path / ".teambot"
    teambot_dir.mkdir()
    (teambot_dir / "history").mkdir()
    (teambot_dir / "state").mkdir()
    return teambot_dir


@pytest.fixture
def sample_agent_config():
    """Standard agent configuration for testing."""
    return {
        "id": "builder-1",
        "persona": "builder",
        "display_name": "Builder (Primary)",
        "parallel_capable": True,
        "workflow_stages": ["implementation", "testing"],
    }


@pytest.fixture
def sample_objective():
    """Sample objective markdown content."""
    return """# Objective: Test Feature

## Description
Build a test feature for validation.

## Definition of Done
- [ ] Feature implemented
- [ ] Tests passing

## Success Criteria
- API responds correctly
- No errors in logs

## Implementation Specifics
- Use Python
- Follow project conventions
"""
