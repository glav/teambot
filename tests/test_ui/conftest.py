"""Textual test fixtures for UI tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_executor():
    """Create a mock TaskExecutor."""
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=MagicMock(success=True, output="Task completed", task_id="task-1")
    )
    return executor


@pytest.fixture
def mock_router():
    """Create a mock router."""
    router = MagicMock()
    router.route_system = AsyncMock(return_value="Status output")
    return router
