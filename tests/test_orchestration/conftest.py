"""Shared fixtures for orchestration tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_load_stages_config():
    """Auto-use fixture to prevent loading stages.yaml artifact requirements during tests.

    The repo root contains a stages.yaml with artifact requirements that
    would cause test failures. This fixture patches load_stages_config
    to clear artifact requirements while preserving other config like
    parallel groups that tests may need.

    Tests that explicitly provide a stages_config path get the real
    implementation so they can test custom configurations.
    """
    from teambot.orchestration.stage_config import (
        load_stages_config as real_load_config,
    )

    def mock_load_config(config_path=None):
        # Use the real implementation
        config = real_load_config(config_path)

        # Only clear artifact requirements when using the default (repo root)
        # stages.yaml. Tests that explicitly provide a config_path get the
        # real artifacts so they can test custom configurations.
        if config_path is None:
            for stage_config in config.stages.values():
                stage_config.artifacts = []

        return config

    # Patch both locations where load_stages_config might be imported
    with (
        patch(
            "teambot.orchestration.execution_loop.load_stages_config",
            side_effect=mock_load_config,
        ),
        patch(
            "teambot.orchestration.stage_config.load_stages_config",
            side_effect=mock_load_config,
        ),
    ):
        yield


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
def sample_feature_spec_content() -> str:
    """Sample feature spec without acceptance test scenarios.

    This spec intentionally does NOT include an 'Acceptance Test Scenarios'
    section so that orchestration tests can pass without needing to execute
    actual acceptance tests. Tests that specifically need acceptance tests
    should create their own spec content.
    """
    return """# Feature Specification: User Authentication

## Overview
This feature implements user authentication functionality.

## Requirements
- REQ-001: Users can log in with email and password
- REQ-002: JWT tokens are issued on successful login

## Technical Design
Uses Express middleware with bcrypt for password hashing.
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
    path.write_text(sample_objective_content, encoding="utf-8")
    return path


@pytest.fixture
def minimal_objective_file(tmp_path: Path, minimal_objective_content: str) -> Path:
    """Create a minimal objective file."""
    path = tmp_path / "minimal.md"
    path.write_text(minimal_objective_content, encoding="utf-8")
    return path


@pytest.fixture
def mock_sdk_client() -> AsyncMock:
    """Mock SDK client for agent execution tests."""
    client = AsyncMock()
    client.execute_streaming = AsyncMock(return_value="Mock output")
    return client


@pytest.fixture
def test_stages_config():
    """Create a stages config without artifact requirements for testing.

    This ensures tests don't pick up the stages.yaml from the repo root
    which has artifact requirements that would cause test failures.
    """
    from teambot.orchestration.stage_config import _get_default_configuration

    # Load defaults directly without looking for stages.yaml
    config = _get_default_configuration()

    # Clear any artifact requirements - tests don't have all artifacts
    for stage_config in config.stages.values():
        stage_config.artifacts = []

    return config


@pytest.fixture
def teambot_dir(tmp_path: Path) -> Path:
    """Create a temporary teambot directory.

    Note: The ExecutionLoop will create a feature-specific subdirectory
    under this directory based on the objective's feature_name. Tests
    that need a feature spec should use the teambot_dir_with_spec fixture.
    """
    dir_path = tmp_path / ".teambot"
    dir_path.mkdir()
    return dir_path


@pytest.fixture
def teambot_dir_with_spec(tmp_path: Path, sample_feature_spec_content: str) -> Path:
    """Create a teambot directory with feature spec.

    Creates the spec in the expected location based on the sample objective's
    feature name (user-authentication).
    """
    dir_path = tmp_path / ".teambot"
    dir_path.mkdir()

    # Create feature-specific directory matching sample_objective_content
    feature_dir = dir_path / "user-authentication"
    feature_dir.mkdir()
    artifacts_dir = feature_dir / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "feature_spec.md").write_text(sample_feature_spec_content, encoding="utf-8")

    return dir_path
