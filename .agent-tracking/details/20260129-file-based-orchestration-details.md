<!-- markdownlint-disable-file -->
# Implementation Details: File-Based Orchestration

**Plan Reference**: `.agent-tracking/plans/20260129-file-based-orchestration-plan.instructions.md`
**Research Reference**: `.agent-tracking/research/20260129-file-based-orchestration-research.md`
**Test Strategy Reference**: `.agent-tracking/test-strategies/20260129-file-based-orchestration-test-strategy.md`

---

## Phase 1: Foundation (TDD)

### Task 1.1: Create Orchestration Module Structure

**Files to Create:**
```
src/teambot/orchestration/
├── __init__.py
├── objective_parser.py
├── time_manager.py
├── review_iterator.py
├── execution_loop.py
├── parallel_executor.py
└── progress.py

tests/test_orchestration/
├── __init__.py
├── conftest.py
├── test_objective_parser.py
├── test_time_manager.py
├── test_review_iterator.py
├── test_execution_loop.py
├── test_parallel_executor.py
└── test_integration.py
```

**`src/teambot/orchestration/__init__.py`:**
```python
"""File-based orchestration for autonomous workflow execution."""

from teambot.orchestration.objective_parser import (
    ParsedObjective,
    SuccessCriterion,
    parse_objective_file,
)
from teambot.orchestration.time_manager import TimeManager
from teambot.orchestration.review_iterator import ReviewIterator, ReviewResult
from teambot.orchestration.execution_loop import ExecutionLoop, ExecutionResult
from teambot.orchestration.parallel_executor import ParallelExecutor

__all__ = [
    "ParsedObjective",
    "SuccessCriterion",
    "parse_objective_file",
    "TimeManager",
    "ReviewIterator",
    "ReviewResult",
    "ExecutionLoop",
    "ExecutionResult",
    "ParallelExecutor",
]
```

---

### Task 1.2: ObjectiveParser Tests (TDD)

**Test File**: `tests/test_orchestration/test_objective_parser.py`

**Test Cases to Write:**

1. `test_parse_extracts_title_from_h1` - Title from `# Objective: X` or `# X`
2. `test_parse_extracts_goals_list` - Goals from `## Goals` section
3. `test_parse_extracts_criteria_with_unchecked` - `- [ ] text` → completed=False
4. `test_parse_extracts_criteria_with_checked` - `- [x] text` → completed=True
5. `test_parse_extracts_constraints` - Constraints from `## Constraints`
6. `test_parse_extracts_context` - Context from `## Context` (optional)
7. `test_parse_handles_missing_optional_sections` - No error if Context missing
8. `test_parse_missing_file_raises` - FileNotFoundError
9. `test_parse_empty_file_returns_defaults` - Empty content handled

**Sample Fixture** (from Research Lines 160-175):
```python
@pytest.fixture
def sample_objective_content():
    return """# Objective: Implement User Authentication

## Goals
1. Add login/logout functionality
2. Implement JWT session management

## Success Criteria
- [ ] Login validates credentials
- [x] JWT tokens expire after 24h

## Constraints
- Use existing PostgreSQL database

## Context
Existing codebase uses Express.js
"""
```

---

### Task 1.3: ObjectiveParser Implementation

**File**: `src/teambot/orchestration/objective_parser.py`

**Implementation** (from Research Lines 155-185):

```python
"""Objective file parser for extracting goals and criteria."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SuccessCriterion:
    """A success criterion with completion status."""
    description: str
    completed: bool = False


@dataclass
class ParsedObjective:
    """Structured representation of an objective file."""
    title: str
    goals: list[str] = field(default_factory=list)
    success_criteria: list[SuccessCriterion] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    context: str | None = None
    raw_content: str = ""


def parse_objective_file(path: Path) -> ParsedObjective:
    """Parse a markdown objective file.
    
    Args:
        path: Path to the objective markdown file
        
    Returns:
        ParsedObjective with extracted structure
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Objective file not found: {path}")
    
    content = path.read_text()
    sections = _extract_sections(content)
    
    return ParsedObjective(
        title=_extract_title(content),
        goals=_parse_list_section(sections.get("Goals", "")),
        success_criteria=_parse_criteria_section(sections.get("Success Criteria", "")),
        constraints=_parse_list_section(sections.get("Constraints", "")),
        context=sections.get("Context"),
        raw_content=content,
    )


def _extract_title(content: str) -> str:
    """Extract title from H1 heading."""
    match = re.search(r'^#\s+(?:Objective:\s*)?(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def _extract_sections(content: str) -> dict[str, str]:
    """Extract sections by ## headers."""
    sections = {}
    pattern = r'^##\s+(.+?)$'
    matches = list(re.finditer(pattern, content, re.MULTILINE))
    
    for i, match in enumerate(matches):
        header = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[header] = content[start:end].strip()
    
    return sections


def _parse_list_section(content: str) -> list[str]:
    """Parse numbered or bulleted list."""
    items = []
    for line in content.split('\n'):
        # Match "1. text" or "- text" or "* text"
        match = re.match(r'^\s*(?:\d+\.|[-*])\s+(.+)$', line)
        if match:
            items.append(match.group(1).strip())
    return items


def _parse_criteria_section(content: str) -> list[SuccessCriterion]:
    """Parse success criteria with checkbox status."""
    criteria = []
    for line in content.split('\n'):
        # Match "- [ ] text" or "- [x] text"
        match = re.match(r'^\s*-\s+\[([ xX])\]\s+(.+)$', line)
        if match:
            completed = match.group(1).lower() == 'x'
            description = match.group(2).strip()
            criteria.append(SuccessCriterion(description=description, completed=completed))
    return criteria
```

---

### Task 1.4: TimeManager Tests (TDD)

**Test File**: `tests/test_orchestration/test_time_manager.py`

**Test Cases:**

1. `test_start_sets_start_time` - start() initializes time
2. `test_elapsed_seconds_increases` - elapsed tracking works
3. `test_is_expired_false_before_limit` - Not expired at start
4. `test_is_expired_true_at_limit` - Expired at exactly max_seconds
5. `test_is_expired_true_past_limit` - Expired past max_seconds
6. `test_resume_adds_prior_elapsed` - resume(prior) adds to elapsed
7. `test_remaining_seconds` - remaining = max - elapsed
8. `test_format_elapsed` - HH:MM:SS format

---

### Task 1.5: TimeManager Implementation

**File**: `src/teambot/orchestration/time_manager.py`

```python
"""Time management for execution limits."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TimeManager:
    """Tracks elapsed time and enforces execution limits."""
    
    max_seconds: int = 8 * 60 * 60  # 8 hours default
    _start_time: float | None = None
    _prior_elapsed: float = 0.0
    
    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.monotonic()
    
    def resume(self, prior_elapsed: float) -> None:
        """Resume with prior elapsed time."""
        self._prior_elapsed = prior_elapsed
        self.start()
    
    @property
    def elapsed_seconds(self) -> float:
        """Get total elapsed seconds."""
        if self._start_time is None:
            return self._prior_elapsed
        return self._prior_elapsed + (time.monotonic() - self._start_time)
    
    @property
    def remaining_seconds(self) -> float:
        """Get remaining seconds before limit."""
        return max(0, self.max_seconds - self.elapsed_seconds)
    
    def is_expired(self) -> bool:
        """Check if time limit exceeded."""
        return self.elapsed_seconds >= self.max_seconds
    
    def format_elapsed(self) -> str:
        """Format elapsed time as HH:MM:SS."""
        total = int(self.elapsed_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def format_remaining(self) -> str:
        """Format remaining time as HH:MM:SS."""
        total = int(self.remaining_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
```

---

## Phase 2: Review Iteration System (TDD)

### Task 2.1: ReviewIterator Tests (TDD)

**Test File**: `tests/test_orchestration/test_review_iterator.py`

**Test Cases:**

1. `test_approval_on_first_iteration` - Returns APPROVED after first review approves
2. `test_approval_on_second_iteration` - Feedback → retry → approved
3. `test_approval_on_fourth_iteration` - Boundary case
4. `test_failure_after_max_iterations` - 4 rejections → FAILED
5. `test_failure_summary_contains_all_feedback` - Summary has all iteration feedback
6. `test_failure_suggestions_extracted` - Suggestions from reviewer extracted
7. `test_feedback_incorporated_in_next_iteration` - Context includes prior feedback
8. `test_cancellation_during_work_phase` - CancelledError handled
9. `test_cancellation_during_review_phase` - CancelledError handled

**Mock Strategy:**
```python
@pytest.fixture
def mock_sdk_client():
    """Mock SDK client for review tests."""
    client = AsyncMock()
    # First call: work output
    # Second call: review with approval/rejection
    return client
```

---

### Task 2.2: ReviewIterator Implementation

**File**: `src/teambot/orchestration/review_iterator.py`

**Key Implementation** (from Research Lines 195-240):

```python
"""Review iteration system with max 4 iterations."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from teambot.workflow.stages import WorkflowStage


class ReviewStatus(Enum):
    """Status of review iteration."""
    APPROVED = "approved"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class IterationResult:
    """Result of a single review iteration."""
    iteration: int
    work_output: str
    review_output: str
    approved: bool
    feedback: str | None = None


@dataclass
class ReviewResult:
    """Final result of review iteration process."""
    status: ReviewStatus
    iterations_used: int
    summary: str | None = None
    suggestions: list[str] = field(default_factory=list)
    report_path: Path | None = None


class ReviewIterator:
    """Manages review→feedback→action cycles."""
    
    MAX_ITERATIONS = 4
    
    def __init__(self, sdk_client, teambot_dir: Path):
        self.sdk_client = sdk_client
        self.teambot_dir = teambot_dir
    
    async def execute(
        self,
        stage: WorkflowStage,
        work_agent: str,
        review_agent: str,
        context: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> ReviewResult:
        """Execute review iteration loop.
        
        Args:
            stage: Current workflow stage
            work_agent: Agent ID for work tasks
            review_agent: Agent ID for review tasks
            context: Initial context/prompt
            on_progress: Optional progress callback
            
        Returns:
            ReviewResult with status and details
        """
        iteration_history: list[IterationResult] = []
        current_context = context
        
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            if on_progress:
                on_progress(f"Review iteration {iteration}/{self.MAX_ITERATIONS}")
            
            try:
                # Execute work
                work_output = await self._execute_work(
                    work_agent, current_context, iteration_history
                )
                
                # Execute review
                review_output, approved, feedback = await self._execute_review(
                    review_agent, work_output
                )
                
                iteration_history.append(IterationResult(
                    iteration=iteration,
                    work_output=work_output,
                    review_output=review_output,
                    approved=approved,
                    feedback=feedback,
                ))
                
                if approved:
                    return ReviewResult(
                        status=ReviewStatus.APPROVED,
                        iterations_used=iteration,
                    )
                
                # Incorporate feedback for next iteration
                current_context = self._incorporate_feedback(
                    current_context, feedback, work_output
                )
                
            except asyncio.CancelledError:
                return ReviewResult(
                    status=ReviewStatus.CANCELLED,
                    iterations_used=iteration,
                )
        
        # Max iterations reached - generate failure report
        return self._generate_failure_result(stage, iteration_history)
```

---

### Task 2.3: Failure Report Generation

**Add to review_iterator.py:**

```python
def _generate_failure_result(
    self, stage: WorkflowStage, history: list[IterationResult]
) -> ReviewResult:
    """Generate detailed failure report."""
    summary = self._summarize_failures(history)
    suggestions = self._extract_suggestions(history)
    report_path = self._save_failure_report(stage, summary, suggestions, history)
    
    return ReviewResult(
        status=ReviewStatus.FAILED,
        iterations_used=len(history),
        summary=summary,
        suggestions=suggestions,
        report_path=report_path,
    )

def _summarize_failures(self, history: list[IterationResult]) -> str:
    """Create summary of all iteration failures."""
    lines = [f"Review failed after {len(history)} iterations:", ""]
    for result in history:
        lines.append(f"### Iteration {result.iteration}")
        lines.append(f"**Feedback**: {result.feedback or 'No specific feedback'}")
        lines.append("")
    return "\n".join(lines)

def _extract_suggestions(self, history: list[IterationResult]) -> list[str]:
    """Extract actionable suggestions from review feedback."""
    suggestions = []
    for result in history:
        if result.feedback:
            # Extract bullet points or numbered items from feedback
            for line in result.feedback.split('\n'):
                if line.strip().startswith(('-', '*', '•')) or \
                   (line.strip() and line.strip()[0].isdigit()):
                    suggestions.append(line.strip().lstrip('-*•0123456789. '))
    return suggestions

def _save_failure_report(
    self, stage: WorkflowStage, summary: str, 
    suggestions: list[str], history: list[IterationResult]
) -> Path:
    """Save failure report to .teambot/failures/."""
    from datetime import datetime
    
    failures_dir = self.teambot_dir / "failures"
    failures_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{stage.name.lower()}-review-failure.md"
    report_path = failures_dir / filename
    
    content = f"""# Review Failure Report: {stage.name}

**Timestamp**: {datetime.now().isoformat()}
**Stage**: {stage.name}
**Iterations**: {len(history)}

## Summary

{summary}

## Suggestions for Resolution

{chr(10).join(f"- {s}" for s in suggestions) if suggestions else "No specific suggestions extracted."}

## Full Iteration History

{"".join(f'''
### Iteration {r.iteration}

**Work Output** (truncated):
```
{r.work_output[:500]}{'...' if len(r.work_output) > 500 else ''}
```

**Review Feedback**:
{r.feedback or 'No feedback'}

**Approved**: {r.approved}
''' for r in history)}
"""
    report_path.write_text(content)
    return report_path
```

---

## Phase 3: Execution Loop (Code-First)

### Task 3.1: ExecutionLoop Implementation

**File**: `src/teambot/orchestration/execution_loop.py`

**Key Implementation** (from Research Lines 185-220):

```python
"""Main execution loop for file-based orchestration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from teambot.orchestration.objective_parser import ParsedObjective, parse_objective_file
from teambot.orchestration.time_manager import TimeManager
from teambot.orchestration.review_iterator import ReviewIterator, ReviewStatus
from teambot.orchestrator import Orchestrator
from teambot.workflow.stages import WorkflowStage, STAGE_METADATA


class ExecutionResult(Enum):
    """Result of execution loop."""
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    REVIEW_FAILED = "review_failed"
    ERROR = "error"


REVIEW_STAGES = {
    WorkflowStage.SPEC_REVIEW,
    WorkflowStage.PLAN_REVIEW,
    WorkflowStage.IMPLEMENTATION_REVIEW,
    WorkflowStage.POST_REVIEW,
}


class ExecutionLoop:
    """Main driver for file-based orchestration."""
    
    def __init__(
        self,
        objective_path: Path,
        config: dict[str, Any],
        teambot_dir: Path,
        max_hours: float = 8.0,
    ):
        self.objective = parse_objective_file(objective_path)
        self.objective_path = objective_path
        self.config = config
        self.teambot_dir = teambot_dir
        self.time_manager = TimeManager(max_seconds=int(max_hours * 3600))
        self.cancelled = False
        
        # Initialize orchestrator with objective
        self.orchestrator = Orchestrator(config, objective=self.objective.raw_content)
        
        # Will be set during run()
        self.sdk_client = None
        self.review_iterator = None
    
    async def run(
        self,
        sdk_client,
        on_progress: Callable[[str, Any], None] | None = None,
    ) -> ExecutionResult:
        """Execute the workflow loop.
        
        Args:
            sdk_client: CopilotSDKClient for agent execution
            on_progress: Optional callback for progress updates
            
        Returns:
            ExecutionResult indicating outcome
        """
        self.sdk_client = sdk_client
        self.review_iterator = ReviewIterator(sdk_client, self.teambot_dir)
        self.time_manager.start()
        
        try:
            while not self.orchestrator.workflow_complete:
                # Check cancellation
                if self.cancelled:
                    self._save_state()
                    return ExecutionResult.CANCELLED
                
                # Check timeout
                if self.time_manager.is_expired():
                    self._save_state()
                    return ExecutionResult.TIMEOUT
                
                stage = self.orchestrator.current_stage
                
                if on_progress:
                    on_progress("stage_changed", {"stage": stage.name})
                
                # Execute stage
                if stage in REVIEW_STAGES:
                    result = await self._execute_review_stage(stage, on_progress)
                    if result == ReviewStatus.FAILED:
                        self._save_state()
                        return ExecutionResult.REVIEW_FAILED
                else:
                    await self._execute_work_stage(stage, on_progress)
                
                # Advance to next stage
                next_stage = self._get_next_stage(stage)
                if next_stage:
                    self.orchestrator.advance_workflow(next_stage)
            
            self._save_state()
            return ExecutionResult.COMPLETE
            
        except Exception as e:
            self._save_state()
            raise
    
    def cancel(self) -> None:
        """Request cancellation of execution."""
        self.cancelled = True
    
    # ... additional methods in details file
```

---

### Task 3.3: State Persistence

**Extend workflow state with orchestration fields:**

```python
def _save_state(self) -> None:
    """Save orchestration state to workflow state file."""
    state = self.orchestrator.workflow.state
    
    # Add orchestration-specific fields
    state.metadata["orchestration"] = {
        "objective_file": str(self.objective_path),
        "elapsed_seconds": self.time_manager.elapsed_seconds,
        "max_seconds": self.time_manager.max_seconds,
        "status": "paused" if self.cancelled else "complete",
    }
    
    self.orchestrator.workflow.save_state()

@classmethod
def resume(cls, teambot_dir: Path, config: dict, sdk_client) -> "ExecutionLoop":
    """Resume from saved state."""
    from teambot.workflow.state_machine import WorkflowStateMachine
    
    workflow = WorkflowStateMachine(teambot_dir)
    orchestration = workflow.state.metadata.get("orchestration", {})
    
    if not orchestration:
        raise ValueError("No orchestration state to resume")
    
    objective_path = Path(orchestration["objective_file"])
    loop = cls(
        objective_path=objective_path,
        config=config,
        teambot_dir=teambot_dir,
        max_hours=orchestration["max_seconds"] / 3600,
    )
    
    loop.time_manager.resume(orchestration["elapsed_seconds"])
    return loop
```

---

## Phase 4: Parallel Execution (Code-First)

### Task 4.1: ParallelExecutor Implementation

**File**: `src/teambot/orchestration/parallel_executor.py`

```python
"""Parallel execution for builder agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable


@dataclass
class AgentTask:
    """A task to be executed by an agent."""
    agent_id: str
    prompt: str
    description: str = ""


@dataclass
class TaskResult:
    """Result of agent task execution."""
    success: bool
    output: str = ""
    error: str | None = None


class ParallelExecutor:
    """Execute multiple agent tasks in parallel."""
    
    def __init__(self, sdk_client, max_concurrent: int = 2):
        self.sdk_client = sdk_client
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_parallel(
        self,
        tasks: list[AgentTask],
        on_progress: Callable[[str, str, str], None] | None = None,
    ) -> dict[str, TaskResult]:
        """Execute tasks in parallel with concurrency limit.
        
        Args:
            tasks: List of agent tasks to execute
            on_progress: Callback(agent_id, event, data)
            
        Returns:
            Dict mapping agent_id to TaskResult
        """
        if not tasks:
            return {}
        
        async def execute_one(task: AgentTask) -> tuple[str, TaskResult]:
            async with self.semaphore:
                if on_progress:
                    on_progress(task.agent_id, "running", task.description)
                
                try:
                    chunks = []
                    
                    def on_chunk(chunk: str):
                        chunks.append(chunk)
                        if on_progress:
                            on_progress(task.agent_id, "chunk", chunk)
                    
                    output = await self.sdk_client.execute_streaming(
                        task.agent_id, task.prompt, on_chunk
                    )
                    
                    if on_progress:
                        on_progress(task.agent_id, "complete", "")
                    
                    return (task.agent_id, TaskResult(success=True, output=output))
                    
                except asyncio.CancelledError:
                    if on_progress:
                        on_progress(task.agent_id, "cancelled", "")
                    raise
                    
                except Exception as e:
                    if on_progress:
                        on_progress(task.agent_id, "failed", str(e))
                    return (task.agent_id, TaskResult(success=False, error=str(e)))
        
        results = await asyncio.gather(
            *[execute_one(t) for t in tasks],
            return_exceptions=True
        )
        
        # Convert to dict, handling exceptions
        output = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            agent_id, task_result = result
            output[agent_id] = task_result
        
        return output


def partition_tasks(
    tasks: list[str], 
    agents: list[str] = ["builder-1", "builder-2"]
) -> list[AgentTask]:
    """Partition tasks among builder agents.
    
    Strategy: Round-robin assignment.
    
    Args:
        tasks: List of task descriptions
        agents: Agent IDs to distribute to
        
    Returns:
        List of AgentTask with assignments
    """
    result = []
    for i, task in enumerate(tasks):
        agent = agents[i % len(agents)]
        result.append(AgentTask(
            agent_id=agent,
            prompt=task,
            description=task[:50] + "..." if len(task) > 50 else task,
        ))
    return result
```

---

## Phase 5: Integration

### Task 5.1: CLI Integration

**Modify**: `src/teambot/cli.py` (Lines 88-131)

```python
def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Run TeamBot with an objective."""
    # ... existing config loading ...
    
    if objective:
        # Run file-based orchestration
        from teambot.orchestration import ExecutionLoop, ExecutionResult
        from teambot.copilot.sdk_client import CopilotSDKClient
        
        sdk_client = CopilotSDKClient()
        
        loop = ExecutionLoop(
            objective_path=Path(args.objective),
            config=config,
            teambot_dir=Path(".teambot"),
            max_hours=getattr(args, "max_hours", 8.0),
        )
        
        # Setup signal handler
        import signal
        
        def handle_interrupt(sig, frame):
            display.print_warning("Cancellation requested, saving state...")
            loop.cancel()
        
        signal.signal(signal.SIGINT, handle_interrupt)
        
        try:
            result = asyncio.run(loop.run(
                sdk_client=sdk_client,
                on_progress=lambda e, d: display.print_info(f"{e}: {d}"),
            ))
            
            if result == ExecutionResult.COMPLETE:
                display.print_success("Objective completed!")
                return 0
            elif result == ExecutionResult.CANCELLED:
                display.print_warning("Cancelled. Resume with: teambot run --resume")
                return 130
            elif result == ExecutionResult.TIMEOUT:
                display.print_warning("Time limit reached. Resume with: teambot run --resume")
                return 1
            elif result == ExecutionResult.REVIEW_FAILED:
                display.print_error("Review failed after 4 iterations. See .teambot/failures/")
                return 1
        except Exception as e:
            display.print_error(f"Execution error: {e}")
            return 1
```

**Add CLI arguments:**
```python
run_parser.add_argument(
    "--resume", action="store_true", help="Resume interrupted orchestration"
)
run_parser.add_argument(
    "--max-hours", type=float, default=8.0, help="Maximum execution hours (default: 8)"
)
```

---

### Task 5.2: Progress Display Integration

**Create**: `src/teambot/orchestration/progress.py`

```python
"""Progress callback utilities for orchestration."""

from typing import Any, Callable

from teambot.ui.agent_state import AgentState, AgentStatusManager


def create_progress_callback(
    status_manager: AgentStatusManager,
    on_stage: Callable[[str], None] | None = None,
    on_time: Callable[[str, str], None] | None = None,
) -> Callable[[str, Any], None]:
    """Create progress callback for orchestration.
    
    Args:
        status_manager: AgentStatusManager for agent state updates
        on_stage: Callback for stage changes
        on_time: Callback for time updates (elapsed, remaining)
        
    Returns:
        Progress callback function
    """
    def on_progress(event_type: str, data: Any) -> None:
        if event_type == "agent_running":
            status_manager.set_running(data["agent_id"], data.get("task"))
        elif event_type == "agent_streaming":
            status_manager.set_streaming(data["agent_id"])
        elif event_type == "agent_complete":
            status_manager.set_completed(data["agent_id"])
        elif event_type == "agent_failed":
            status_manager.set_failed(data["agent_id"])
        elif event_type == "agent_idle":
            status_manager.set_idle(data["agent_id"])
        elif event_type == "stage_changed":
            if on_stage:
                on_stage(data["stage"])
        elif event_type == "time_update":
            if on_time:
                on_time(data["elapsed"], data["remaining"])
    
    return on_progress
```

---

## Phase 6: Finalization

### Task 6.1: Integration Tests

**File**: `tests/test_orchestration/test_integration.py`

**Key Test Cases:**

1. `test_full_workflow_execution` - All 13 stages complete with mocked agents
2. `test_resume_after_cancellation` - Save state, reload, continue
3. `test_parallel_builder_execution` - builder-1 and builder-2 concurrent
4. `test_review_iteration_with_feedback` - Review rejects, then approves
5. `test_timeout_enforcement` - Time limit triggers timeout result

---

### Task 6.3: Documentation Updates

**Update README.md with:**

```markdown
## File-Based Orchestration

Run autonomous objectives:

```bash
# Run an objective file
teambot run objectives/my-task.md

# Resume interrupted execution
teambot run --resume

# Set custom time limit (default: 8 hours)
teambot run objectives/task.md --max-hours 4
```

### Objective File Format

```markdown
# Objective: Feature Name

## Goals
1. Goal one
2. Goal two

## Success Criteria
- [ ] Criterion one
- [ ] Criterion two

## Constraints
- Constraint one

## Context
Additional context for agents.
```
```
