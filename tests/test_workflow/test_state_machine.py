"""Tests for workflow state machine."""

from datetime import datetime

import pytest

from teambot.workflow.stages import WorkflowStage
from teambot.workflow.state_machine import (
    StageHistory,
    WorkflowState,
    WorkflowStateMachine,
)


@pytest.fixture
def teambot_dir(tmp_path):
    """Create a temporary teambot directory."""
    d = tmp_path / ".teambot"
    d.mkdir()
    return d


class TestStageHistory:
    """Tests for StageHistory dataclass."""

    def test_create_history(self):
        """Test creating stage history."""
        now = datetime.now()
        history = StageHistory(
            stage=WorkflowStage.SETUP,
            started_at=now,
        )
        assert history.stage == WorkflowStage.SETUP
        assert history.started_at == now
        assert history.completed_at is None
        assert history.skipped is False

    def test_create_completed_history(self):
        """Test creating completed history."""
        now = datetime.now()
        history = StageHistory(
            stage=WorkflowStage.SETUP,
            started_at=now,
            completed_at=now,
            artifacts=["test.md"],
            notes="Done",
        )
        assert history.completed_at == now
        assert history.artifacts == ["test.md"]


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_create_state(self):
        """Test creating workflow state."""
        now = datetime.now()
        state = WorkflowState(
            current_stage=WorkflowStage.SETUP,
            started_at=now,
            objective="Test objective",
        )
        assert state.current_stage == WorkflowStage.SETUP
        assert state.started_at == now
        assert state.objective == "Test objective"

    def test_state_to_dict(self):
        """Test serializing state to dict."""
        now = datetime.now()
        state = WorkflowState(
            current_stage=WorkflowStage.SETUP,
            started_at=now,
            objective="Test",
        )
        data = state.to_dict()

        assert data["current_stage"] == "SETUP"
        assert data["objective"] == "Test"
        assert "started_at" in data

    def test_state_from_dict(self):
        """Test deserializing state from dict."""
        data = {
            "current_stage": "SPEC",
            "started_at": datetime.now().isoformat(),
            "objective": "Build feature",
            "history": [],
            "metadata": {},
        }
        state = WorkflowState.from_dict(data)

        assert state.current_stage == WorkflowStage.SPEC
        assert state.objective == "Build feature"

    def test_state_roundtrip(self):
        """Test state serialization roundtrip."""
        now = datetime.now()
        original = WorkflowState(
            current_stage=WorkflowStage.IMPLEMENTATION,
            started_at=now,
            objective="Test",
            history=[StageHistory(stage=WorkflowStage.SETUP, started_at=now)],
        )
        data = original.to_dict()
        restored = WorkflowState.from_dict(data)

        assert restored.current_stage == original.current_stage
        assert restored.objective == original.objective
        assert len(restored.history) == 1


class TestWorkflowStateMachine:
    """Tests for WorkflowStateMachine class."""

    def test_create_machine(self, teambot_dir):
        """Test creating state machine."""
        machine = WorkflowStateMachine(teambot_dir)
        assert machine.current_stage == WorkflowStage.SETUP
        assert not machine.is_complete

    def test_create_with_objective(self, teambot_dir):
        """Test creating machine with objective."""
        machine = WorkflowStateMachine(teambot_dir, objective="Build a chatbot")
        assert machine.state.objective == "Build a chatbot"

    def test_save_and_load_state(self, teambot_dir):
        """Test saving and loading state."""
        machine = WorkflowStateMachine(teambot_dir, objective="Test")
        machine.save_state()

        # Create new machine, should load state
        machine2 = WorkflowStateMachine(teambot_dir)
        assert machine2.state.objective == "Test"

    def test_can_transition_valid(self, teambot_dir):
        """Test valid transition check."""
        machine = WorkflowStateMachine(teambot_dir)
        # From SETUP, can go to BUSINESS_PROBLEM or SPEC
        assert machine.can_transition_to(WorkflowStage.BUSINESS_PROBLEM)
        assert machine.can_transition_to(WorkflowStage.SPEC)

    def test_can_transition_invalid(self, teambot_dir):
        """Test invalid transition check."""
        machine = WorkflowStateMachine(teambot_dir)
        # From SETUP, cannot jump to IMPLEMENTATION
        assert not machine.can_transition_to(WorkflowStage.IMPLEMENTATION)

    def test_transition_to_valid(self, teambot_dir):
        """Test valid transition."""
        machine = WorkflowStateMachine(teambot_dir)
        machine.transition_to(WorkflowStage.SPEC, artifacts=["spec.md"])

        assert machine.current_stage == WorkflowStage.SPEC
        # History contains only the new stage (SPEC) since SETUP wasn't completed
        assert len(machine.state.history) == 1
        assert machine.state.history[0].stage == WorkflowStage.SPEC

    def test_transition_to_invalid_raises(self, teambot_dir):
        """Test invalid transition raises error."""
        machine = WorkflowStateMachine(teambot_dir)
        with pytest.raises(ValueError, match="Cannot transition"):
            machine.transition_to(WorkflowStage.COMPLETE)

    def test_skip_optional_stage(self, teambot_dir):
        """Test skipping optional stage."""
        machine = WorkflowStateMachine(teambot_dir)
        # First transition to BUSINESS_PROBLEM
        machine.transition_to(WorkflowStage.BUSINESS_PROBLEM)

        # BUSINESS_PROBLEM is optional, skip it
        machine.skip_stage(WorkflowStage.BUSINESS_PROBLEM)
        assert machine.current_stage == WorkflowStage.SPEC

    def test_skip_required_stage_raises(self, teambot_dir):
        """Test skipping required stage raises error."""
        machine = WorkflowStateMachine(teambot_dir)
        with pytest.raises(ValueError, match="not optional"):
            machine.skip_stage(WorkflowStage.SETUP)

    def test_get_stage_info(self, teambot_dir):
        """Test getting stage info."""
        machine = WorkflowStateMachine(teambot_dir)
        info = machine.get_stage_info()

        assert info["stage"] == "SETUP"
        assert info["name"] == "Setup"
        assert "allowed_personas" in info

    def test_get_progress(self, teambot_dir):
        """Test getting progress."""
        machine = WorkflowStateMachine(teambot_dir)
        progress = machine.get_progress()

        assert progress["current_stage"] == "SETUP"
        assert progress["completed_stages"] == 0
        assert progress["is_complete"] is False

    def test_is_persona_allowed(self, teambot_dir):
        """Test checking if persona is allowed."""
        machine = WorkflowStateMachine(teambot_dir)
        # PM/project_manager allowed in SETUP
        assert machine.is_persona_allowed("pm")
        assert machine.is_persona_allowed("project_manager")
        # Builder not allowed in SETUP
        assert not machine.is_persona_allowed("builder")

    def test_full_workflow_path(self, teambot_dir):
        """Test walking through a complete workflow.

        Note: With parallel stage groups, RESEARCH and TEST_STRATEGY both
        branch from SPEC_REVIEW and converge at PLAN. This test takes the
        RESEARCH path; test_full_workflow_path_via_test_strategy takes the
        alternate path.
        """
        machine = WorkflowStateMachine(teambot_dir, objective="Test project")

        # Walk through workflow (RESEARCH path through parallel group)
        machine.transition_to(WorkflowStage.SPEC)
        machine.transition_to(WorkflowStage.SPEC_REVIEW)
        machine.transition_to(WorkflowStage.RESEARCH)  # One path through parallel group
        machine.transition_to(WorkflowStage.PLAN)  # RESEARCH → PLAN (convergence)
        machine.transition_to(WorkflowStage.PLAN_REVIEW)
        machine.transition_to(WorkflowStage.IMPLEMENTATION)
        machine.transition_to(WorkflowStage.IMPLEMENTATION_REVIEW)
        machine.transition_to(WorkflowStage.TEST)
        machine.transition_to(WorkflowStage.ACCEPTANCE_TEST)
        machine.transition_to(WorkflowStage.POST_REVIEW)
        machine.transition_to(WorkflowStage.COMPLETE)

        assert machine.is_complete
        progress = machine.get_progress()
        assert progress["is_complete"] is True

    def test_full_workflow_path_via_test_strategy(self, teambot_dir):
        """Test walking through workflow via TEST_STRATEGY path.

        With parallel stage groups, RESEARCH and TEST_STRATEGY both branch
        from SPEC_REVIEW. This test takes the TEST_STRATEGY path.
        """
        machine = WorkflowStateMachine(teambot_dir, objective="Test project")

        # Walk through workflow (TEST_STRATEGY path through parallel group)
        machine.transition_to(WorkflowStage.SPEC)
        machine.transition_to(WorkflowStage.SPEC_REVIEW)
        machine.transition_to(WorkflowStage.TEST_STRATEGY)  # Alternate path
        machine.transition_to(WorkflowStage.PLAN)  # TEST_STRATEGY → PLAN (convergence)
        machine.transition_to(WorkflowStage.PLAN_REVIEW)
        machine.transition_to(WorkflowStage.IMPLEMENTATION)
        machine.transition_to(WorkflowStage.IMPLEMENTATION_REVIEW)
        machine.transition_to(WorkflowStage.TEST)
        machine.transition_to(WorkflowStage.ACCEPTANCE_TEST)
        machine.transition_to(WorkflowStage.POST_REVIEW)
        machine.transition_to(WorkflowStage.COMPLETE)

        assert machine.is_complete

    def test_persistence_across_instances(self, teambot_dir):
        """Test state persists across machine instances."""
        machine1 = WorkflowStateMachine(teambot_dir, objective="Test")
        machine1.transition_to(WorkflowStage.SPEC)
        machine1.save_state()

        machine2 = WorkflowStateMachine(teambot_dir)
        assert machine2.current_stage == WorkflowStage.SPEC
        assert machine2.state.objective == "Test"
