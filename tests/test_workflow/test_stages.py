"""Tests for workflow stages."""

from teambot.workflow.stages import (
    STAGE_METADATA,
    StageMetadata,
    WorkflowStage,
    can_skip_stage,
    get_allowed_personas,
    get_next_stages,
    get_stage_metadata,
)


class TestWorkflowStage:
    """Tests for WorkflowStage enum."""

    def test_all_stages_exist(self):
        """Test all expected stages are defined."""
        expected = [
            "SETUP",
            "BUSINESS_PROBLEM",
            "SPEC",
            "SPEC_REVIEW",
            "RESEARCH",
            "TEST_STRATEGY",
            "PLAN",
            "PLAN_REVIEW",
            "IMPLEMENTATION",
            "IMPLEMENTATION_REVIEW",
            "TEST",
            "ACCEPTANCE_TEST",
            "POST_REVIEW",
            "COMPLETE",
        ]
        actual = [s.name for s in WorkflowStage]
        assert actual == expected

    def test_stage_count(self):
        """Test correct number of stages."""
        assert len(WorkflowStage) == 14


class TestStageMetadata:
    """Tests for StageMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating stage metadata."""
        meta = StageMetadata(
            name="Test",
            description="Test description",
            allowed_personas=["builder"],
            required_artifacts=["test.md"],
            optional=True,
            next_stages=[WorkflowStage.SPEC],
        )
        assert meta.name == "Test"
        assert meta.description == "Test description"
        assert meta.allowed_personas == ["builder"]
        assert meta.required_artifacts == ["test.md"]
        assert meta.optional is True
        assert meta.next_stages == [WorkflowStage.SPEC]

    def test_default_values(self):
        """Test default values."""
        meta = StageMetadata(
            name="Test",
            description="Test",
            allowed_personas=["pm"],
        )
        assert meta.required_artifacts == []
        assert meta.optional is False
        assert meta.next_stages == []


class TestStageMetadataRegistry:
    """Tests for STAGE_METADATA registry."""

    def test_all_stages_have_metadata(self):
        """Test every stage has metadata defined."""
        for stage in WorkflowStage:
            assert stage in STAGE_METADATA

    def test_setup_metadata(self):
        """Test SETUP stage metadata."""
        meta = STAGE_METADATA[WorkflowStage.SETUP]
        assert meta.name == "Setup"
        assert "pm" in meta.allowed_personas or "project_manager" in meta.allowed_personas
        assert WorkflowStage.BUSINESS_PROBLEM in meta.next_stages

    def test_implementation_metadata(self):
        """Test IMPLEMENTATION stage metadata."""
        meta = STAGE_METADATA[WorkflowStage.IMPLEMENTATION]
        assert "builder" in meta.allowed_personas
        assert WorkflowStage.IMPLEMENTATION_REVIEW in meta.next_stages

    def test_complete_has_no_next(self):
        """Test COMPLETE stage has no next stages."""
        meta = STAGE_METADATA[WorkflowStage.COMPLETE]
        assert meta.next_stages == []


class TestGetStageMetadata:
    """Tests for get_stage_metadata function."""

    def test_get_setup_metadata(self):
        """Test getting SETUP metadata."""
        meta = get_stage_metadata(WorkflowStage.SETUP)
        assert meta.name == "Setup"

    def test_get_complete_metadata(self):
        """Test getting COMPLETE metadata."""
        meta = get_stage_metadata(WorkflowStage.COMPLETE)
        assert meta.name == "Complete"


class TestGetAllowedPersonas:
    """Tests for get_allowed_personas function."""

    def test_setup_allowed_personas(self):
        """Test SETUP allowed personas."""
        personas = get_allowed_personas(WorkflowStage.SETUP)
        assert "pm" in personas or "project_manager" in personas

    def test_implementation_allowed_personas(self):
        """Test IMPLEMENTATION allowed personas."""
        personas = get_allowed_personas(WorkflowStage.IMPLEMENTATION)
        assert "builder" in personas

    def test_complete_no_personas(self):
        """Test COMPLETE has no allowed personas."""
        personas = get_allowed_personas(WorkflowStage.COMPLETE)
        assert personas == []


class TestCanSkipStage:
    """Tests for can_skip_stage function."""

    def test_setup_not_skippable(self):
        """Test SETUP cannot be skipped."""
        assert can_skip_stage(WorkflowStage.SETUP) is False

    def test_business_problem_skippable(self):
        """Test BUSINESS_PROBLEM can be skipped."""
        assert can_skip_stage(WorkflowStage.BUSINESS_PROBLEM) is True

    def test_spec_not_skippable(self):
        """Test SPEC cannot be skipped."""
        assert can_skip_stage(WorkflowStage.SPEC) is False


class TestGetNextStages:
    """Tests for get_next_stages function."""

    def test_setup_next_stages(self):
        """Test SETUP next stages."""
        next_stages = get_next_stages(WorkflowStage.SETUP)
        assert WorkflowStage.BUSINESS_PROBLEM in next_stages
        assert WorkflowStage.SPEC in next_stages

    def test_spec_next_stage(self):
        """Test SPEC next stage."""
        next_stages = get_next_stages(WorkflowStage.SPEC)
        assert WorkflowStage.SPEC_REVIEW in next_stages

    def test_complete_no_next(self):
        """Test COMPLETE has no next stages."""
        next_stages = get_next_stages(WorkflowStage.COMPLETE)
        assert next_stages == []

    def test_workflow_path_exists(self):
        """Test a complete workflow path exists."""
        # Verify we can get from SETUP to COMPLETE
        visited = set()
        current = WorkflowStage.SETUP

        # Walk the workflow (taking first option at each branch)
        max_iterations = 20
        iterations = 0
        while current != WorkflowStage.COMPLETE and iterations < max_iterations:
            visited.add(current)
            next_stages = get_next_stages(current)
            if not next_stages:
                break
            current = next_stages[0]
            iterations += 1

        assert current == WorkflowStage.COMPLETE


class TestParallelStageTransitions:
    """Tests for parallel stage group transitions."""

    def test_spec_review_next_stages_includes_both_parallel_stages(self):
        """SPEC_REVIEW.next_stages includes both RESEARCH and TEST_STRATEGY."""
        next_stages = get_next_stages(WorkflowStage.SPEC_REVIEW)
        assert WorkflowStage.RESEARCH in next_stages
        assert WorkflowStage.TEST_STRATEGY in next_stages
        assert len(next_stages) == 2

    def test_research_converges_at_plan(self):
        """RESEARCH converges at PLAN."""
        next_stages = get_next_stages(WorkflowStage.RESEARCH)
        assert WorkflowStage.PLAN in next_stages

    def test_test_strategy_converges_at_plan(self):
        """TEST_STRATEGY converges at PLAN."""
        next_stages = get_next_stages(WorkflowStage.TEST_STRATEGY)
        assert WorkflowStage.PLAN in next_stages
