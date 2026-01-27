"""Shared pytest fixtures for TeamBot tests."""

from unittest.mock import AsyncMock, MagicMock

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


# ============================================================================
# Async SDK Mocking Fixtures
# ============================================================================


class MockSDKResponse:
    """Mock response from Copilot SDK."""

    def __init__(self, content: str):
        self.data = MagicMock()
        self.data.content = content


@pytest.fixture
def mock_sdk_response():
    """Create a mock SDK response."""

    def _create(content: str = "OK"):
        return MockSDKResponse(content)

    return _create


@pytest.fixture
def mock_sdk_session(mock_sdk_response):
    """Mock a Copilot SDK session."""
    session = MagicMock()
    session.send_and_wait = AsyncMock(return_value=mock_sdk_response("Task completed"))
    session.destroy = MagicMock()
    session.on = MagicMock()
    session.session_id = "test-session"
    return session


@pytest.fixture
def mock_sdk_client(mock_sdk_session):
    """Mock the Copilot SDK client."""
    client = MagicMock()
    client.start = AsyncMock()
    client.stop = AsyncMock()
    client.create_session = AsyncMock(return_value=mock_sdk_session)
    client.resume_session = AsyncMock(return_value=mock_sdk_session)
    client.list_sessions = MagicMock(return_value=[])
    client.delete_session = MagicMock()
    return client
