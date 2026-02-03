"""Tests for ReviewIterator (TDD)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from teambot.orchestration.review_iterator import (
    IterationResult,
    ReviewIterator,
    ReviewResult,
    ReviewStatus,
)
from teambot.workflow.stages import WorkflowStage


class TestReviewIterator:
    """Tests for ReviewIterator class."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def iterator(self, mock_sdk_client: AsyncMock, teambot_dir: Path) -> ReviewIterator:
        """Create ReviewIterator instance."""
        return ReviewIterator(mock_sdk_client, teambot_dir)

    @pytest.mark.asyncio
    async def test_approval_on_first_iteration(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Returns APPROVED after first review approves."""
        # Work output, then review output with approval
        mock_sdk_client.execute_streaming.side_effect = [
            "Implementation complete",
            "APPROVED: Looks good!",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create specification",
        )

        assert result.status == ReviewStatus.APPROVED
        assert result.iterations_used == 1

    @pytest.mark.asyncio
    async def test_approval_on_second_iteration(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Feedback → retry → approved on second iteration."""
        mock_sdk_client.execute_streaming.side_effect = [
            "First attempt",
            "REJECTED: Need more detail",
            "Improved implementation",
            "APPROVED: Great work!",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create specification",
        )

        assert result.status == ReviewStatus.APPROVED
        assert result.iterations_used == 2

    @pytest.mark.asyncio
    async def test_approval_on_fourth_iteration(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Boundary case: approved on iteration 4."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Attempt 1",
            "REJECTED: Fix A",
            "Attempt 2",
            "REJECTED: Fix B",
            "Attempt 3",
            "REJECTED: Fix C",
            "Attempt 4",
            "APPROVED: Finally!",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create specification",
        )

        assert result.status == ReviewStatus.APPROVED
        assert result.iterations_used == 4

    @pytest.mark.asyncio
    async def test_failure_after_max_iterations(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """4 rejections → FAILED status."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Attempt 1",
            "REJECTED: Issue 1",
            "Attempt 2",
            "REJECTED: Issue 2",
            "Attempt 3",
            "REJECTED: Issue 3",
            "Attempt 4",
            "REJECTED: Issue 4",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create specification",
        )

        assert result.status == ReviewStatus.FAILED
        assert result.iterations_used == 4
        assert result.summary is not None

    @pytest.mark.asyncio
    async def test_failure_summary_contains_all_feedback(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Failure summary contains all iteration feedback."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Attempt 1",
            "REJECTED: First issue",
            "Attempt 2",
            "REJECTED: Second issue",
            "Attempt 3",
            "REJECTED: Third issue",
            "Attempt 4",
            "REJECTED: Fourth issue",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test context",
        )

        assert "First issue" in result.summary
        assert "Second issue" in result.summary
        assert "Fourth issue" in result.summary

    @pytest.mark.asyncio
    async def test_failure_suggestions_extracted(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Suggestions from reviewer are extracted."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Attempt",
            "REJECTED:\n- Add tests\n- Fix imports",
            "Attempt",
            "REJECTED:\n- Update docs",
            "Attempt",
            "REJECTED:\n- Handle errors",
            "Attempt",
            "REJECTED:\n- Final fix",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test",
        )

        assert len(result.suggestions) > 0
        assert "Add tests" in result.suggestions

    @pytest.mark.asyncio
    async def test_feedback_incorporated_in_next_iteration(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Context includes prior feedback for subsequent iterations."""
        mock_sdk_client.execute_streaming.side_effect = [
            "First attempt",
            "REJECTED: Need error handling",
            "Improved with error handling",
            "APPROVED: Good!",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create feature",
        )

        # Verify the review was approved on second iteration
        assert result.status == ReviewStatus.APPROVED
        assert result.iterations_used == 2

        # Check that the second work call included feedback context
        calls = mock_sdk_client.execute_streaming.call_args_list
        assert len(calls) == 4
        # Second work call (index 2) should have feedback in prompt
        second_work_call = calls[2]
        assert "error handling" in second_work_call[0][1].lower()

    @pytest.mark.asyncio
    async def test_cancellation_during_work_phase(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """CancelledError during work phase returns CANCELLED."""
        mock_sdk_client.execute_streaming.side_effect = asyncio.CancelledError()

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test",
        )

        assert result.status == ReviewStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancellation_during_review_phase(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """CancelledError during review phase returns CANCELLED."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Work output",
            asyncio.CancelledError(),
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test",
        )

        assert result.status == ReviewStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_progress_callback_called(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Progress callback is invoked with iteration info."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Work",
            "APPROVED: Good",
        ]
        progress_calls = []

        _ = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test",
            on_progress=lambda msg: progress_calls.append(msg),
        )

        assert len(progress_calls) > 0
        assert "iteration" in progress_calls[0].lower()


class TestReviewIteratorFailureReport:
    """Tests for failure report generation."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        return AsyncMock()

    @pytest.fixture
    def iterator(self, mock_sdk_client: AsyncMock, teambot_dir: Path) -> ReviewIterator:
        """Create ReviewIterator instance."""
        return ReviewIterator(mock_sdk_client, teambot_dir)

    @pytest.mark.asyncio
    async def test_failure_report_saved_to_teambot_dir(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock, teambot_dir: Path
    ) -> None:
        """Failure report is saved to .teambot/failures/."""
        mock_sdk_client.execute_streaming.side_effect = [
            "A1",
            "REJECTED: R1",
            "A2",
            "REJECTED: R2",
            "A3",
            "REJECTED: R3",
            "A4",
            "REJECTED: R4",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Test",
        )

        assert result.report_path is not None
        assert result.report_path.exists()
        assert result.report_path.parent.name == "failures"

    @pytest.mark.asyncio
    async def test_failure_report_contains_stage_info(
        self, iterator: ReviewIterator, mock_sdk_client: AsyncMock
    ) -> None:
        """Failure report contains stage information."""
        mock_sdk_client.execute_streaming.side_effect = [
            "A1",
            "REJECTED: R1",
            "A2",
            "REJECTED: R2",
            "A3",
            "REJECTED: R3",
            "A4",
            "REJECTED: R4",
        ]

        result = await iterator.execute(
            stage=WorkflowStage.IMPLEMENTATION_REVIEW,
            work_agent="builder-1",
            review_agent="reviewer",
            context="Test",
        )

        report_content = result.report_path.read_text()
        assert "IMPLEMENTATION_REVIEW" in report_content


class TestIterationResult:
    """Tests for IterationResult dataclass."""

    def test_default_feedback_is_none(self) -> None:
        """Default feedback is None."""
        result = IterationResult(
            iteration=1,
            work_output="output",
            review_output="review",
            approved=True,
        )
        assert result.feedback is None


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_default_suggestions_is_empty_list(self) -> None:
        """Default suggestions is empty list."""
        result = ReviewResult(
            status=ReviewStatus.APPROVED,
            iterations_used=1,
        )
        assert result.suggestions == []
        assert result.report_path is None
