<!-- markdownlint-disable-file -->
# Task Details: File-Based Orchestration Critical Failure Handling

## Research Reference

**Source Research**: .agent-tracking/research/20260129-file-based-orchestration-research.md
**Test Strategy**: .agent-tracking/test-strategies/20260129-file-based-orchestration-test-strategy.md

---

## Phase 1: Core Exception and Validation Infrastructure (TDD)

### Task 1.1: Write tests for MissingArtifactError exception

Create test file with TDD tests for the custom exception class.

* **Files**:
  * `tests/test_orchestration/test_artifact_validator.py` - New test file for artifact validation
* **Success**:
  * Test file created with test cases for MissingArtifactError
  * Tests are failing (TDD red phase)
* **Research References**:
  * .agent-tracking/test-strategies/20260129-file-based-orchestration-test-strategy.md (Lines 65-94) - TDD approach for critical components
* **Dependencies**:
  * None

**Test Cases to Write**:
```python
class TestMissingArtifactError:
    """Tests for MissingArtifactError exception."""

    def test_error_has_artifact_path(self):
        """Exception stores the missing artifact path."""
        
    def test_error_has_stage_name(self):
        """Exception stores which stage required the artifact."""
        
    def test_error_has_recovery_steps(self):
        """Exception includes actionable recovery steps."""
        
    def test_error_message_is_actionable(self):
        """String representation includes all context for user action."""
        
    def test_error_inherits_from_exception(self):
        """MissingArtifactError is a proper Exception subclass."""
```

---

### Task 1.2: Implement MissingArtifactError exception class

Create the exception class to pass tests from Task 1.1.

* **Files**:
  * `src/teambot/orchestration/exceptions.py` - New file for orchestration exceptions
  * `src/teambot/orchestration/__init__.py` - Export the exception
* **Success**:
  * Tests from Task 1.1 pass
  * Exception has `artifact_path`, `stage`, `recovery_steps` attributes
* **Research References**:
  * .agent-tracking/research/20260129-file-based-orchestration-research.md (Lines 349-365) - handle_review_failure pattern
* **Dependencies**:
  * Task 1.1 tests exist

**Implementation Pattern**:
```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MissingArtifactError(Exception):
    """Raised when a required artifact is missing for a stage."""
    
    artifact_path: Path
    stage: str
    recovery_steps: list[str]
    
    def __str__(self) -> str:
        steps = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(self.recovery_steps))
        return (
            f"Critical Failure: Missing required artifact for {self.stage} stage\n\n"
            f"Expected artifact: {self.artifact_path}\n\n"
            f"To resolve:\n{steps}"
        )
```

---

### Task 1.3: Write tests for ArtifactValidator class

Create tests for the validator that checks artifact existence.

* **Files**:
  * `tests/test_orchestration/test_artifact_validator.py` - Add ArtifactValidator tests
* **Success**:
  * Tests exist for validation scenarios
  * Tests are failing (TDD red phase)
* **Research References**:
  * .agent-tracking/research/20260129-file-based-orchestration-research.md (Lines 109-127) - Stage metadata with required artifacts
* **Dependencies**:
  * Task 1.2 complete (MissingArtifactError exists)

**Test Cases to Write**:
```python
class TestArtifactValidator:
    """Tests for ArtifactValidator class."""

    def test_validate_passes_when_artifact_exists(self, tmp_path):
        """Validation passes if artifact file exists."""
        
    def test_validate_raises_when_artifact_missing(self, tmp_path):
        """Validation raises MissingArtifactError if artifact missing."""
        
    def test_validate_checks_multiple_locations(self, tmp_path):
        """Validator checks fallback locations for artifacts."""
        
    def test_validate_returns_actual_path_found(self, tmp_path):
        """Validator returns the path where artifact was found."""
        
    def test_get_required_artifacts_for_stage(self):
        """Returns list of artifacts required for a stage from config."""
        
    def test_validate_all_for_stage_checks_each_artifact(self, tmp_path):
        """validate_all_for_stage checks all required artifacts."""
```

---

### Task 1.4: Implement ArtifactValidator class

Implement the validator class to pass tests.

* **Files**:
  * `src/teambot/orchestration/artifact_validator.py` - New validator module
  * `src/teambot/orchestration/__init__.py` - Export the validator
* **Success**:
  * Tests from Task 1.3 pass
  * Validator can check single or multiple artifacts
* **Research References**:
  * .agent-tracking/research/20260129-file-based-orchestration-research.md (Lines 526-534) - File structure for orchestration
  * src/teambot/orchestration/stage_config.py (Lines 17-35) - StageConfig with artifacts field
* **Dependencies**:
  * Task 1.3 tests exist

**Implementation Pattern**:
```python
from pathlib import Path
from teambot.orchestration.exceptions import MissingArtifactError
from teambot.orchestration.stage_config import StagesConfiguration
from teambot.workflow.stages import WorkflowStage

class ArtifactValidator:
    """Validates required artifacts exist before stage execution."""
    
    def __init__(self, teambot_dir: Path, stages_config: StagesConfiguration):
        self.teambot_dir = teambot_dir
        self.stages_config = stages_config
    
    def get_required_artifacts(self, stage: WorkflowStage) -> list[str]:
        """Get list of required artifact filenames for a stage."""
        stage_config = self.stages_config.stages.get(stage)
        if not stage_config:
            return []
        return stage_config.artifacts
    
    def find_artifact(self, artifact_name: str) -> Path | None:
        """Find artifact in possible locations, return path or None."""
        # Check primary location: .teambot/{feature}/artifacts/{name}
        # Check fallback: docs/feature-specs/{name} for specs
        # Check fallback: .agent-tracking/ for research/plans
        ...
    
    def validate_artifact(self, artifact_name: str, stage: WorkflowStage) -> Path:
        """Validate artifact exists, raise MissingArtifactError if not."""
        ...
    
    def validate_all_for_stage(self, stage: WorkflowStage) -> dict[str, Path]:
        """Validate all required artifacts for a stage."""
        ...
```

---

## Phase 2: Artifact Path Resolution Fix

### Task 2.1: Write tests for artifact path resolution scenarios

Create tests covering the path mismatch scenarios.

* **Files**:
  * `tests/test_orchestration/test_artifact_validator.py` - Add path resolution tests
* **Success**:
  * Tests cover all artifact location scenarios
  * Tests document expected search order
* **Research References**:
  * src/teambot/orchestration/execution_loop.py (Lines 771-779) - Current artifact search pattern
  * stages.yaml (Lines 63-78) - Artifact storage documentation
* **Dependencies**:
  * Phase 1 complete

**Test Scenarios**:
```python
class TestArtifactPathResolution:
    """Tests for artifact path resolution across locations."""

    def test_finds_artifact_in_feature_artifacts_dir(self, tmp_path):
        """Finds artifact in .teambot/{feature}/artifacts/."""
        
    def test_finds_spec_in_docs_feature_specs(self, tmp_path):
        """Falls back to docs/feature-specs/ for spec artifacts."""
        
    def test_finds_research_in_agent_tracking(self, tmp_path):
        """Falls back to .agent-tracking/research/ for research docs."""
        
    def test_prioritizes_feature_dir_over_fallback(self, tmp_path):
        """Feature-specific location takes precedence over fallbacks."""
        
    def test_handles_implementation_plan_locations(self, tmp_path):
        """Checks .agent-tracking/plans/ for implementation_plan.md."""
```

---

### Task 2.2: Implement multi-location artifact resolver

Enhance ArtifactValidator to check multiple locations.

* **Files**:
  * `src/teambot/orchestration/artifact_validator.py` - Enhance find_artifact method
* **Success**:
  * Tests from Task 2.1 pass
  * Clear search order documented in code
* **Research References**:
  * stages.yaml (Lines 63-78) - Artifact storage convention
  * src/teambot/orchestration/execution_loop.py (Lines 771-792) - Existing feature spec search
* **Dependencies**:
  * Task 2.1 tests exist

**Search Order Implementation**:
```python
def find_artifact(self, artifact_name: str, feature_name: str | None = None) -> Path | None:
    """Find artifact in possible locations.
    
    Search order:
    1. .teambot/{feature}/artifacts/{artifact_name}
    2. docs/feature-specs/{artifact_name} (for *_spec.md)
    3. .agent-tracking/research/ (for research.md)
    4. .agent-tracking/plans/ (for implementation_plan.md)
    5. .agent-tracking/test-strategies/ (for test_strategy.md)
    """
    search_locations = []
    
    # Primary location
    if feature_name:
        search_locations.append(
            self.teambot_dir / feature_name / "artifacts" / artifact_name
        )
    
    # Fallback locations based on artifact type
    if "spec" in artifact_name.lower():
        search_locations.append(Path("docs/feature-specs") / artifact_name)
    if "research" in artifact_name.lower():
        search_locations.append(Path(".agent-tracking/research") / artifact_name)
    if "plan" in artifact_name.lower():
        search_locations.append(Path(".agent-tracking/plans") / artifact_name)
    if "test_strategy" in artifact_name.lower():
        search_locations.append(Path(".agent-tracking/test-strategies") / artifact_name)
    
    for location in search_locations:
        if location.exists():
            return location
    
    return None
```

---

## Phase 3: ExecutionLoop Integration

### Task 3.1: Write integration tests for pre-stage validation

Create integration tests for validation in execution loop.

* **Files**:
  * `tests/test_orchestration/test_execution_loop.py` - Add artifact validation tests
* **Success**:
  * Tests for pre-stage validation exist
  * Tests verify workflow halts on missing artifact
* **Research References**:
  * tests/test_orchestration/test_execution_loop.py (Lines 53-98) - Existing test patterns
  * .agent-tracking/test-strategies/20260129-file-based-orchestration-test-strategy.md (Lines 153-179) - ExecutionLoop test approach
* **Dependencies**:
  * Phase 2 complete

**Test Cases**:
```python
class TestExecutionLoopArtifactValidation:
    """Tests for artifact validation in ExecutionLoop."""

    @pytest.mark.asyncio
    async def test_halts_on_missing_required_artifact(self, loop, mock_sdk_client):
        """Workflow halts when required artifact is missing for stage."""
        
    @pytest.mark.asyncio
    async def test_emits_critical_failure_event(self, loop, mock_sdk_client):
        """Emits critical_failure event on missing artifact."""
        
    @pytest.mark.asyncio
    async def test_saves_state_on_critical_failure(self, loop, mock_sdk_client):
        """Saves state with CRITICAL_FAILURE result."""
        
    @pytest.mark.asyncio
    async def test_error_message_includes_recovery_steps(self, loop, mock_sdk_client):
        """Error includes actionable recovery steps."""
```

---

### Task 3.2: Add artifact validation to ExecutionLoop._execute_work_stage

Integrate validation before work stage execution.

* **Files**:
  * `src/teambot/orchestration/execution_loop.py` - Add validation call
* **Success**:
  * Integration tests pass
  * Validation occurs before agent task execution
* **Research References**:
  * src/teambot/orchestration/execution_loop.py (Lines 232-233) - _execute_work_stage call site
* **Dependencies**:
  * Task 3.1 tests exist

**Integration Point** (around line 232-233):
```python
async def _execute_work_stage(
    self,
    stage: WorkflowStage,
    on_progress: Callable[[str, Any], None] | None,
) -> None:
    """Execute a work stage with pre-validation."""
    # NEW: Validate required artifacts before execution
    try:
        self._validate_required_artifacts(stage)
    except MissingArtifactError as e:
        self._handle_critical_failure(e, on_progress)
        raise
    
    # Existing work stage logic...
```

---

### Task 3.3: Add artifact validation to ExecutionLoop._execute_review_stage

Integrate validation before review stage execution.

* **Files**:
  * `src/teambot/orchestration/execution_loop.py` - Add validation to review stages
* **Success**:
  * Review stages also validate prerequisites
  * Validation happens before ReviewIterator
* **Research References**:
  * src/teambot/orchestration/execution_loop.py (Lines 227-231) - Review stage call site
* **Dependencies**:
  * Task 3.2 complete

**Integration Point**:
```python
async def _execute_review_stage(
    self,
    stage: WorkflowStage,
    on_progress: Callable[[str, Any], None] | None,
) -> ReviewStatus:
    """Execute review stage with pre-validation."""
    # NEW: Validate prerequisite artifacts
    try:
        self._validate_prerequisite_artifacts(stage)
    except MissingArtifactError as e:
        self._handle_critical_failure(e, on_progress)
        raise
    
    # Existing review logic...
```

---

## Phase 4: Notification System Integration

### Task 4.1: Write tests for critical failure notification events

Create tests for notification event emission.

* **Files**:
  * `tests/test_notifications/test_events.py` - Add critical_failure event tests
* **Success**:
  * Tests for critical_failure event type
  * Tests verify event data structure
* **Research References**:
  * src/teambot/notifications/events.py (Lines 1-28) - NotificationEvent structure
* **Dependencies**:
  * Phase 3 complete

---

### Task 4.2: Add critical_failure event type to notification system

Add new event type for critical failures.

* **Files**:
  * `src/teambot/notifications/events.py` - Add event type constant
  * `src/teambot/notifications/templates.py` - Add message template
* **Success**:
  * `critical_failure` event type defined
  * Template produces actionable message
* **Research References**:
  * src/teambot/notifications/events.py (Lines 1-28) - Event structure
* **Dependencies**:
  * Task 4.1 tests exist

**Event Data Structure**:
```python
# Event type
CRITICAL_FAILURE = "critical_failure"

# Event data for critical_failure
{
    "error_type": "MissingArtifactError",
    "artifact_path": "/path/to/expected/artifact",
    "stage": "PLAN",
    "recovery_steps": ["Run step X", "Create artifact Y"],
    "feature_name": "user-authentication"
}
```

---

### Task 4.3: Integrate notification emission on MissingArtifactError

Emit notification when critical failure occurs.

* **Files**:
  * `src/teambot/orchestration/execution_loop.py` - Emit event in _handle_critical_failure
* **Success**:
  * Notification sent on critical failure
  * Message is actionable
* **Research References**:
  * src/teambot/notifications/event_bus.py - Event emission pattern
* **Dependencies**:
  * Task 4.2 complete

---

## Phase 5: State Persistence and Recovery

### Task 5.1: Write tests for state persistence on critical failure

Test that state is saved properly for recovery.

* **Files**:
  * `tests/test_orchestration/test_execution_loop.py` - Add state persistence tests
* **Success**:
  * Tests verify state file written on critical failure
  * State includes recovery information
* **Research References**:
  * src/teambot/orchestration/execution_loop.py (Lines 1031-1065) - _save_state implementation
* **Dependencies**:
  * Phase 4 complete

---

### Task 5.2: Add CRITICAL_FAILURE result type and state handling

Add new ExecutionResult and handle in state saving.

* **Files**:
  * `src/teambot/orchestration/execution_loop.py` - Add result type and handling
* **Success**:
  * CRITICAL_FAILURE added to ExecutionResult enum
  * State includes failure details
  * Recovery steps stored in state
* **Research References**:
  * src/teambot/orchestration/execution_loop.py (Lines 26-35) - ExecutionResult enum
* **Dependencies**:
  * Task 5.1 tests exist

**Changes to ExecutionResult**:
```python
class ExecutionResult(Enum):
    """Result of execution loop."""
    
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    REVIEW_FAILED = "review_failed"
    ACCEPTANCE_TEST_FAILED = "acceptance_test_failed"
    ERROR = "error"
    CRITICAL_FAILURE = "critical_failure"  # NEW
```

---

## Phase 6: Final Validation and Documentation

### Task 6.1: Create acceptance test for critical failure scenario

End-to-end test of critical failure handling.

* **Files**:
  * `tests/test_critical_failure_acceptance.py` - New acceptance test
* **Success**:
  * Test simulates missing artifact scenario
  * Verifies halt, notification, state save
* **Research References**:
  * .agent-tracking/test-strategies/20260129-file-based-orchestration-test-strategy.md (Lines 269-295) - Critical test scenarios
* **Dependencies**:
  * Phase 5 complete

**Acceptance Test**:
```python
@pytest.mark.acceptance
class TestCriticalFailureAcceptance:
    """Acceptance tests for critical failure handling."""

    @pytest.mark.asyncio
    async def test_at_001_missing_implementation_plan_halts_workflow(self):
        """
        AT-001: Workflow halts immediately when implementation_plan.md is missing.
        
        Given: PLAN stage requires implementation_plan.md
        When: Workflow reaches PLAN stage without artifact
        Then: Workflow halts with CRITICAL_FAILURE
        And: Error message includes exact path expected
        And: Error message includes recovery steps
        And: State is saved for recovery
        """
```

---

### Task 6.2: Run full test suite and validate coverage

Ensure all tests pass and coverage meets target.

* **Files**:
  * Run: `uv run pytest --cov=src/teambot --cov-report=term-missing -v`
* **Success**:
  * All tests pass
  * Coverage ≥ 85% overall
  * New code has ≥ 95% coverage
* **Dependencies**:
  * Task 6.1 complete

---

### Task 6.3: Lint and format code

Ensure code meets project standards.

* **Files**:
  * Run: `uv run ruff format . && uv run ruff check . --fix`
  * Verify: `uv run ruff format --check .`
* **Success**:
  * No linting errors
  * Code formatted per project standards
* **Research References**:
  * AGENTS.md - Clean commit requirements
* **Dependencies**:
  * Task 6.2 complete

---

## Dependencies

* pytest, pytest-asyncio, pytest-cov (existing dev dependencies)
* Existing notification system infrastructure

## Success Criteria

* Workflow immediately halts when required artifacts are missing
* Error messages include exact path expected and which stage requires it
* Error messages include actionable recovery steps
* Notifications sent to configured channels on critical failure
* State properly saved for potential recovery/resume
* All existing tests continue to pass
* New test coverage ≥ 85% for new code
