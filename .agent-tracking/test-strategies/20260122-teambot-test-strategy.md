<!-- markdownlint-disable-file -->
# Test Strategy: TeamBot

**Strategy Date**: 2026-01-22
**Feature Specification**: docs/feature-specs/teambot.md
**Research Reference**: .agent-tracking/research/20260122-teambot-research.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: HYBRID

### Rationale

TeamBot is a complex, multi-component system with varying levels of risk and clarity across components. The **Hybrid approach** is optimal because:

1. **Core orchestration logic** (multiprocessing, messaging, lifecycle management) is high-risk, well-defined, and critical for system reliability - **TDD** ensures correctness from the start and provides a safety net for complex concurrent code.

2. **External integrations** (window management, Copilot CLI invocation) involve OS-specific behavior and external dependencies that are difficult to mock accurately - **Code-First** allows rapid iteration and validation against real systems before formalizing tests.

3. **Utility components** (history file parsing, visualization) have clear inputs/outputs but moderate complexity - **TDD for core parsing logic**, **Code-First for UI/display** provides the right balance.

This hybrid strategy ensures critical paths are protected by tests written first, while allowing flexibility for exploration in areas with external dependencies.

**Key Factors:**
* Complexity: HIGH (multiprocessing, cross-platform, concurrent agents)
* Risk: CRITICAL (core infrastructure for autonomous development)
* Requirements Clarity: CLEAR (well-defined specification with 23 functional requirements)
* Time Pressure: LOW (quality prioritized over speed per user preference)

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Assessment | TDD Points | Code-First Points |
|--------|------------|------------|-------------------|
| **Requirements Clarity** | Well-defined spec with 23 FRs, clear acceptance criteria | 3 | 0 |
| **Complexity** | High - multiprocessing, cross-platform, concurrent agents | 3 | 0 |
| **Risk Level** | Critical - core infrastructure for autonomous operation | 3 | 0 |
| **Exploratory Nature** | No - clear architecture defined in research | 0 | 0 |
| **Simplicity** | No - complex system with multiple interacting components | 0 | 0 |
| **Time Pressure** | Low - quality prioritized over speed | 0 | 0 |
| **Requirements Stability** | Stable - detailed spec approved | 0 | 0 |

**TDD Score: 9** | **Code-First Score: 0**

### Decision Analysis

Raw scores suggest pure TDD, but practical considerations favor Hybrid:
- Window management requires real OS interaction (hard to TDD effectively)
- Copilot CLI integration needs integration testing more than unit testing
- Visualization is UI-focused where Code-First is more natural

**Final Decision: HYBRID** (TDD for core logic, Code-First for OS integration and UI)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: HIGH - multiprocessing coordination, message routing, workflow state machines
* **Integration Depth**: HIGH - OS subprocess, Copilot CLI, file system, multiple processes
* **State Management**: HIGH - agent lifecycles, workflow stages, history file tracking
* **Error Scenarios**: HIGH - process failures, queue timeouts, file conflicts, cross-platform issues

### Risk Profile
* **Business Criticality**: CRITICAL - core product enabling autonomous development
* **User Impact**: HIGH - failure means complete workflow breakdown
* **Data Sensitivity**: MEDIUM - history files contain code and development context
* **Failure Cost**: HIGH - agent failures could corrupt shared state, lose work progress

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 23 FRs, 15 NFRs, detailed acceptance criteria
* **Acceptance Criteria Quality**: PRECISE - measurable targets (<5s startup, <100ms latency)
* **Edge Cases Identified**: 12+ documented (queue timeouts, file locking, context limits)
* **Dependencies Status**: STABLE - Python stdlib, well-documented libraries

## Test Strategy by Component

### 1. Orchestrator (`src/teambot/orchestrator.py`) - TDD

**Approach**: TDD
**Rationale**: Mission-critical coordination logic with complex state management and concurrent processes. Well-defined message protocol makes test-first natural. Failures here cascade to entire system.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit (isolated), Integration (with mock processes)
* Critical Scenarios:
  * Agent spawning and lifecycle management
  * Message routing between agents
  * Graceful shutdown with sentinel values
  * Queue timeout handling
  * Error propagation from child to parent
* Edge Cases:
  * Agent process crash during operation
  * Queue full condition
  * Duplicate agent IDs
  * Shutdown during active message processing

**Testing Sequence (TDD)**:
1. Write test for `spawn_agent` creating child process
2. Implement minimal spawning code
3. Write test for `send_to_agent` message delivery
4. Implement queue routing
5. Write test for graceful `shutdown` with sentinels
6. Implement shutdown logic
7. Refactor for clean architecture

### 2. Messaging Protocol (`src/teambot/messaging/`) - TDD

**Approach**: TDD
**Rationale**: Core data structures and serialization must be correct. Clear input/output contract makes TDD ideal. Message corruption would break entire system.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * AgentMessage serialization/deserialization
  * MessageType enum handling
  * Timestamp generation
  * Correlation ID tracking
* Edge Cases:
  * Empty payload handling
  * Large payload serialization
  * Invalid message type
  * Missing required fields

**Testing Sequence (TDD)**:
1. Write test for `AgentMessage` dataclass creation
2. Implement dataclass with required fields
3. Write test for message serialization
4. Implement serialization logic
5. Write test for message type validation
6. Implement validation

### 3. History File Manager (`src/teambot/history/`) - TDD

**Approach**: TDD
**Rationale**: Clear contract - input markdown with frontmatter, output structured data. Critical for context management. Well-suited for test-first development.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration (with temp files)
* Critical Scenarios:
  * Creating history file with frontmatter
  * Parsing existing frontmatter
  * Scanning directory for history files
  * Loading relevant files based on criteria
  * Date/time stamped filename generation
* Edge Cases:
  * Malformed frontmatter YAML
  * Missing required metadata fields
  * Empty content section
  * Unicode in filenames/content
  * Very large history files

**Testing Sequence (TDD)**:
1. Write test for `create_history_file` output format
2. Implement file creation with frontmatter
3. Write test for `scan_frontmatter` returning metadata
4. Implement efficient frontmatter scanning
5. Write test for relevance filtering
6. Implement filter logic

### 4. Context Compactor (`src/teambot/history/compactor.py`) - TDD

**Approach**: TDD
**Rationale**: Critical for preventing context overflow. Clear algorithm with defined compaction levels. Token estimation must be accurate.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit
* Critical Scenarios:
  * Token estimation accuracy
  * Warning threshold detection (80%)
  * Compaction level selection
  * Content truncation at each level
* Edge Cases:
  * Empty content
  * Content exactly at threshold
  * Mixed content (code + prose)
  * Very short content (below minimum)

### 5. Window Manager (`src/teambot/window_manager.py`) - Code-First

**Approach**: Code-First
**Rationale**: OS-specific subprocess spawning is difficult to test without real OS interaction. Better to implement, manually verify on each platform, then add integration tests that validate behavior.

**Test Requirements:**
* Coverage Target: 70%
* Test Types: Integration (real subprocess), Unit (mocked platform detection)
* Critical Scenarios:
  * Windows window spawning with CREATE_NEW_CONSOLE
  * Linux terminal emulator detection
  * macOS AppleScript execution
  * Process handle tracking
* Edge Cases:
  * No terminal emulator available (Linux)
  * AppleScript permission denied (macOS)
  * Working directory doesn't exist
  * Script path with spaces

**Testing Sequence (Code-First)**:
1. Implement cross-platform window spawning
2. Manually test on each OS (or CI matrix)
3. Add unit tests for platform detection logic
4. Add integration test that spawns real process (short-lived)
5. Mock subprocess for remaining unit tests

### 6. Console Visualization (`src/teambot/visualization/`) - Code-First

**Approach**: Code-First
**Rationale**: UI/display code is best validated visually first. Rich library handles complexity. Tests focus on data flow, not visual output.

**Test Requirements:**
* Coverage Target: 60%
* Test Types: Unit (mocked Console)
* Critical Scenarios:
  * Agent addition to display
  * Status updates
  * Progress tracking
  * Color mapping by persona
* Edge Cases:
  * Unknown agent ID update
  * Progress > 100%
  * Concurrent updates (thread safety)

**Testing Sequence (Code-First)**:
1. Implement basic console output with Rich
2. Visually validate appearance
3. Add tests for data management (agent_tasks dict)
4. Mock Rich Console for unit tests
5. Test thread safety with concurrent updates

### 7. Configuration Loader (`src/teambot/config/`) - TDD

**Approach**: TDD
**Rationale**: Clear JSON schema defined. Validation logic must be correct. Config errors should fail fast with clear messages.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit
* Critical Scenarios:
  * Valid config loading
  * Schema validation
  * Default value application
  * Error messages for invalid config
* Edge Cases:
  * Missing required fields
  * Invalid agent persona type
  * Malformed JSON
  * Empty config file

### 8. Agent Runner (`src/teambot/agent_runner.py`) - Code-First

**Approach**: Code-First
**Rationale**: Heavy integration with Copilot CLI. Better to implement working integration first, then add tests for message handling and state management.

**Test Requirements:**
* Coverage Target: 70%
* Test Types: Unit (mocked Copilot), Integration
* Critical Scenarios:
  * Queue message reception
  * Copilot CLI invocation
  * History file creation on actions
  * Shutdown signal handling
* Edge Cases:
  * Copilot CLI not available
  * Copilot CLI timeout
  * Invalid task assignment

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest (to be added - currently no tests)
* **Version**: 7.4.0+ (recommended)
* **Configuration**: `pyproject.toml` (to be configured)
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (stdlib) + `pytest-mock` for convenience
* **Assertions**: pytest built-in assertions
* **Coverage**: `pytest-cov` - Target: 80% overall
* **Test Data**: Fixtures in `conftest.py`, temp directories for file tests

### Test Organization
* **Test Location**: `tests/` directory (mirrors `src/teambot/` structure)
* **Naming Convention**: `test_*.py` files, `test_*` functions, `Test*` classes
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`
* **Setup/Teardown**: pytest fixtures with `yield` for cleanup

### Required pyproject.toml Updates

```toml
[dependency-groups]
dev = [
    "ruff>=0.8.0",
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/teambot --cov-report=term-missing --cov-fail-under=80"
```

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 80% (minimum)
* **Integration Coverage**: 70%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 85%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Approach | Notes |
|-----------|--------|---------------|----------|----------|-------|
| orchestrator.py | 90% | 80% | CRITICAL | TDD | Core coordination logic |
| messaging/protocol.py | 95% | N/A | CRITICAL | TDD | Message data structures |
| messaging/router.py | 85% | 75% | HIGH | TDD | Queue routing |
| history/manager.py | 90% | 80% | CRITICAL | TDD | File operations |
| history/frontmatter.py | 95% | N/A | HIGH | TDD | Parsing logic |
| history/compactor.py | 85% | N/A | HIGH | TDD | Token management |
| window_manager.py | 70% | 60% | HIGH | Code-First | OS-specific |
| visualization/console.py | 60% | N/A | MEDIUM | Code-First | UI output |
| config/loader.py | 85% | 70% | HIGH | TDD | Config validation |
| agent_runner.py | 70% | 60% | HIGH | Code-First | Copilot integration |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Agent Lifecycle Management** (Priority: CRITICAL)
   * **Description**: Spawn, manage, and shutdown agent processes correctly
   * **Test Type**: Unit + Integration
   * **Success Criteria**: All agents spawn, receive messages, and shutdown gracefully
   * **Test Approach**: TDD

2. **Message Routing** (Priority: CRITICAL)
   * **Description**: Messages delivered to correct agent via queues
   * **Test Type**: Unit
   * **Success Criteria**: 100% message delivery to target agent
   * **Test Approach**: TDD

3. **History File Creation** (Priority: CRITICAL)
   * **Description**: Every modifying action creates properly formatted history file
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Valid frontmatter, correct filename format, content preserved
   * **Test Approach**: TDD

4. **Cross-Platform Window Spawning** (Priority: HIGH)
   * **Description**: Agent windows spawn on Windows, Linux, macOS
   * **Test Type**: Integration
   * **Success Criteria**: Process created and tracked on each supported OS
   * **Test Approach**: Code-First

5. **Graceful Shutdown** (Priority: CRITICAL)
   * **Description**: System shuts down cleanly without orphan processes
   * **Test Type**: Integration
   * **Success Criteria**: All agents receive shutdown signal, all processes terminated
   * **Test Approach**: TDD

6. **Context Overflow Prevention** (Priority: HIGH)
   * **Description**: Warning issued when approaching context limits
   * **Test Type**: Unit
   * **Success Criteria**: Warning at 80% threshold, compaction options offered
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Queue Timeout**: Agent doesn't respond within timeout period
* **Process Crash**: Child process terminates unexpectedly
* **File Lock Conflict**: Two agents try to write same file
* **Malformed Frontmatter**: History file has invalid YAML
* **Terminal Not Found**: Linux has no supported terminal emulator
* **Config Validation Failure**: Invalid JSON or missing required fields
* **Large History Directory**: 1000+ files to scan
* **Unicode Content**: Non-ASCII in filenames and content
* **Empty Objective**: User provides blank objective file

### Error Scenarios

* **OrchestratorError**: Agent fails to spawn → Log error, continue with other agents
* **MessageDeliveryError**: Queue full or timeout → Retry with backoff, then fail task
* **HistoryWriteError**: Cannot create file → Log error, continue operation
* **WindowSpawnError**: OS rejects subprocess → Provide clear error message with instructions
* **ConfigurationError**: Invalid config → Fail fast with specific validation error

## Test Data Strategy

### Test Data Requirements
* **Agent configurations**: JSON fixtures for various persona configurations
* **Objective files**: Sample markdown objectives with various structures
* **History files**: Sample history files with valid/invalid frontmatter
* **Large datasets**: Generated files for performance testing (1000+ history files)

### Test Data Management
* **Storage**: `tests/fixtures/` directory
* **Generation**: Pytest fixtures create temp directories and files
* **Isolation**: Each test gets fresh temp directory via `tmp_path` fixture
* **Cleanup**: Automatic via pytest temp directory management

## Example Test Patterns

### Recommended Test Structure

```python
# tests/conftest.py
import pytest
from pathlib import Path
import tempfile
import json

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
        "workflow_stages": ["implementation", "testing"]
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
```

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from multiprocessing import Queue
import time

class TestOrchestrator:
    """Tests for parent orchestrator process."""
    
    def test_spawn_agent_creates_process(self, sample_agent_config):
        """Test that spawning an agent creates a child process."""
        # Arrange
        from teambot.orchestrator import Orchestrator
        orchestrator = Orchestrator({"agents": [sample_agent_config]})
        
        # Act
        process = orchestrator.spawn_agent(sample_agent_config)
        
        # Assert
        assert process is not None
        assert process.is_alive()
        
        # Cleanup
        process.terminate()
        process.join(timeout=2)
    
    def test_send_to_agent_delivers_message(self, sample_agent_config):
        """Test that messages are delivered to the correct agent queue."""
        # Arrange
        from teambot.orchestrator import Orchestrator
        from teambot.messaging.protocol import AgentMessage, MessageType
        
        orchestrator = Orchestrator({"agents": [sample_agent_config]})
        agent_id = sample_agent_config["id"]
        
        # Create a mock queue we can inspect
        mock_queue = Queue()
        orchestrator.agent_queues[agent_id] = mock_queue
        
        message = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent=agent_id,
            payload={"task": "implement feature"}
        )
        
        # Act
        orchestrator.send_to_agent(agent_id, message)
        
        # Assert
        received = mock_queue.get(timeout=1)
        assert received.type == MessageType.TASK_ASSIGN
        assert received.payload["task"] == "implement feature"
    
    def test_shutdown_sends_sentinel_to_all_agents(self):
        """Test that shutdown broadcasts sentinel message to all agents."""
        # Arrange
        from teambot.orchestrator import Orchestrator
        from teambot.messaging.protocol import MessageType
        
        orchestrator = Orchestrator({"agents": []})
        
        # Add mock queues for multiple agents
        queues = {}
        for agent_id in ["pm", "builder-1", "reviewer"]:
            q = Queue()
            orchestrator.agent_queues[agent_id] = q
            queues[agent_id] = q
        
        # Act
        orchestrator.shutdown()
        
        # Assert - each queue should have shutdown message
        for agent_id, q in queues.items():
            msg = q.get(timeout=1)
            assert msg.type == MessageType.SHUTDOWN


class TestHistoryFileManager:
    """Tests for history file management."""
    
    def test_create_history_file_with_frontmatter(self, temp_teambot_dir):
        """Test that history files are created with correct frontmatter."""
        # Arrange
        from teambot.history.manager import HistoryFileManager, HistoryMetadata
        from datetime import datetime
        
        manager = HistoryFileManager(temp_teambot_dir)
        metadata = HistoryMetadata(
            title="Created auth module",
            description="Implemented JWT authentication",
            timestamp=datetime(2026, 1, 22, 10, 30, 0),
            agent_id="builder-1",
            action_type="code_created"
        )
        content = "## Changes Made\n\nImplemented JWT auth in src/auth/jwt.py"
        
        # Act
        filepath = manager.create_history_file(metadata, content)
        
        # Assert
        assert filepath.exists()
        assert "2026-01-22-103000" in filepath.name
        assert "code-created" in filepath.name
        
        # Verify frontmatter
        import frontmatter
        post = frontmatter.load(filepath)
        assert post["title"] == "Created auth module"
        assert post["agent_id"] == "builder-1"
        assert content in post.content
    
    def test_scan_frontmatter_returns_metadata_only(self, temp_teambot_dir):
        """Test that scanning returns metadata without loading full content."""
        # Arrange
        from teambot.history.manager import HistoryFileManager, HistoryMetadata
        from datetime import datetime
        
        manager = HistoryFileManager(temp_teambot_dir)
        
        # Create multiple history files
        for i in range(3):
            metadata = HistoryMetadata(
                title=f"Action {i}",
                description=f"Description {i}",
                timestamp=datetime(2026, 1, 22, 10, i, 0),
                agent_id="builder-1",
                action_type="code_created"
            )
            manager.create_history_file(metadata, f"Content {i}" * 1000)
        
        # Act
        results = manager.scan_frontmatter()
        
        # Assert
        assert len(results) == 3
        for result in results:
            assert "metadata" in result
            assert "path" in result
            assert "title" in result["metadata"]
```

**Key Conventions:**
* Use class-based test organization for related tests
* Fixtures for common setup (temp directories, configs)
* Clear Arrange-Act-Assert structure
* Descriptive test names explaining expected behavior
* Proper cleanup of processes and resources

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 critical scenarios identified)
* [ ] Coverage targets are met per component (80% overall minimum)
* [ ] All edge cases are tested (9 edge cases documented)
* [ ] Error paths are validated (5 error scenarios documented)
* [ ] Tests follow codebase conventions (pytest, fixtures, AAA pattern)
* [ ] Tests are maintainable and clear
* [ ] CI/CD integration is working (pytest in pyproject.toml)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness from multiprocessing)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For TDD Components (Orchestrator, Messaging, History, Config):
1. Start with simplest test case (e.g., create empty orchestrator)
2. Write minimal code to pass
3. Add next test case (e.g., spawn single agent)
4. Refactor when all tests pass
5. Focus on behavior, not implementation
6. Use mocks sparingly - prefer real objects when practical

### For Code-First Components (Window Manager, Visualization, Agent Runner):
1. Implement core functionality
2. Manually test on target platform(s)
3. Add happy path test
4. Identify edge cases from implementation
5. Add edge case tests
6. Verify coverage meets target

### For Hybrid Approach:
1. Start with TDD components (orchestrator, messaging)
2. Establish solid foundation before integrations
3. Proceed to Code-First components (window manager)
4. Ensure integration tests cover boundaries
5. Validate overall feature behavior end-to-end

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD on critical paths ensures reliability of core infrastructure
* Code-First on OS integrations allows practical validation first
* Hybrid approach balances thoroughness with pragmatism
* Clear component boundaries make testing manageable

### Accepted Trade-offs:
* Window manager may have lower coverage due to OS-specific challenges
* Visualization testing focuses on data flow, not visual output
* Some integration tests require real processes (slower)

### Risk Mitigation:
* TDD for orchestrator mitigates R-001 (API changes) by defining behavior
* TDD for history management mitigates R-002 (file conflicts) by testing edge cases
* Context compactor TDD mitigates R-003 (large files) by validating thresholds

## References

* **Feature Spec**: [docs/feature-specs/teambot.md](../../docs/feature-specs/teambot.md)
* **Research Doc**: [.agent-tracking/research/20260122-teambot-research.md](./../research/20260122-teambot-research.md)
* **Spec Review**: [.agent-tracking/spec-reviews/20260122-teambot-review.md](./../spec-reviews/20260122-teambot-review.md)
* **Test Examples**: Provided in this document (no existing tests in codebase)
* **Test Standards**: AGENTS.md recommends pytest

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: APPROVED
**Approved By**: User (2026-01-22T03:59:59Z)
**Ready for Planning**: YES
