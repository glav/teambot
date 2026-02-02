"""Shared fixtures for orchestration tests."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import AsyncMock


@pytest.fixture
def sample_objective_content() -> str:
    """Sample objective markdown content."""
    return """# Objective: Implement User Authentication

## Goals
1. Add login/logout functionality
2. Implement JWT session management
3. Add password reset flow

## Success Criteria
- [ ] Login validates credentials against database
- [x] JWT tokens expire after 24 hours
- [ ] Password reset sends email

## Constraints
- Use existing PostgreSQL database
- Follow OAuth 2.0 standards

## Context
Existing codebase uses Express.js with TypeScript.
The authentication should integrate with the existing middleware.
"""


@pytest.fixture
def minimal_objective_content() -> str:
    """Minimal valid objective content."""
    return """# My Task

## Goals
1. Do the thing

## Success Criteria
- [ ] Thing is done
"""


@pytest.fixture
def objective_file(tmp_path: Path, sample_objective_content: str) -> Path:
    """Create a sample objective file."""
    path = tmp_path / "objective.md"
    path.write_text(sample_objective_content)
    return path


@pytest.fixture
def minimal_objective_file(tmp_path: Path, minimal_objective_content: str) -> Path:
    """Create a minimal objective file."""
    path = tmp_path / "minimal.md"
    path.write_text(minimal_objective_content)
    return path


@pytest.fixture
def mock_sdk_client() -> AsyncMock:
    """Mock SDK client for agent execution tests."""
    client = AsyncMock()
    client.execute_streaming = AsyncMock(return_value="Mock output")
    return client


@pytest.fixture
def teambot_dir(tmp_path: Path) -> Path:
    """Create a temporary teambot directory."""
    dir_path = tmp_path / ".teambot"
    dir_path.mkdir()
    return dir_path
