<!-- markdownlint-disable-file -->
# Research Document: File-Based Orchestration

**Date**: 2026-01-29
**Feature**: File-Based Orchestration
**Specification**: `docs/feature-specs/file-based-orchestration.md`
**Status**: ✅ Complete

---

## 1. Research Scope

### Objectives
1. Understand existing orchestration infrastructure and identify integration points
2. Design the execution loop that drives workflow through 13 stages
3. Define objective file parsing approach
4. Design review iteration system with failure handling
5. Define parallel agent execution strategy
6. Identify progress display integration approach
7. Research cancellation and state persistence patterns

### Key Questions Answered
- ✅ How does the existing Orchestrator work?
- ✅ How does AgentRunner execute tasks?
- ✅ How does WorkflowStateMachine persist state?
- ✅ What async patterns exist for parallel execution?
- ✅ How to parse objective files?
- ✅ How to integrate with existing UI components?

---

## 2. Existing Infrastructure Analysis

### 2.1 Orchestrator (`src/teambot/orchestrator.py`)

**Key Methods:**
| Method | Purpose | Lines |
|--------|---------|-------|
| `spawn_agent(agent_config)` | Creates agent process with dedicated queue | 46-62 |
| `assign_task(agent_id, task, context)` | Validates persona, sends TASK_ASSIGN message | 120-158 |
| `advance_workflow(target_stage, artifacts)` | Transitions workflow state | 160-172 |
| `get_agents_for_current_stage()` | Returns agents allowed for current stage | 193-203 |

**Integration Points:**
- Use `assign_task()` to delegate work to agents
- Use `advance_workflow()` to progress through stages
- Use `get_agents_for_current_stage()` to select workers

**Gap Identified:** `_agent_entry_point()` is a placeholder (line 76-84). Need to wire up `AgentRunner`.

### 2.2 AgentRunner (`src/teambot/agent_runner.py`)

**Task Execution Flow:**
```
run() → _handle_message() → [TASK_ASSIGN] → _handle_task() → _execute_task()
```

**`_execute_task(payload)` Implementation (Lines 108-151):**
1. Extract task & context from payload
2. Build prompt using `prompt_template.build_prompt(task, context)`
3. Check `copilot_client.is_available()`
4. Execute: `result = copilot_client.execute(prompt)`
5. Create history entry via `_create_task_history()`
6. Return result dict with status, output, message

**Result Structure:**
```python
{
    "status": "completed" | "failed" | "skipped",
    "output": str,
    "message": str,
    "task": str
}
```

### 2.3 WorkflowStateMachine (`src/teambot/workflow/state_machine.py`)

**State File:** `{teambot_dir}/workflow_state.json`

**State Structure:**
```json
{
  "current_stage": "STAGE_NAME",
  "started_at": "ISO-8601",
  "objective": "string",
  "metadata": {},
  "history": [
    {
      "stage": "STAGE_NAME",
      "started_at": "ISO-8601",
      "completed_at": "ISO-8601 or null",
      "skipped": boolean,
      "artifacts": ["path1"],
      "notes": "string"
    }
  ]
}
```

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `transition_to(target_stage, artifacts, notes)` | Validates and executes stage transition |
| `skip_stage(stage)` | Skips optional stage |
| `can_transition_to(target_stage)` | Checks if transition is valid |
| `is_persona_allowed(persona)` | Checks if persona can work on current stage |
| `save_state()` | Persists to JSON file |

### 2.4 Workflow Stages (`src/teambot/workflow/stages.py`)

**13 Stages with Personas:**
| Stage | Allowed Personas | Required Artifacts |
|-------|-----------------|-------------------|
| SETUP | pm | none |
| BUSINESS_PROBLEM | ba, pm | problem_statement.md (optional stage) |
| SPEC | ba, writer | feature_spec.md |
| SPEC_REVIEW | reviewer, pm | spec_review.md |
| RESEARCH | builder, writer | research.md |
| TEST_STRATEGY | builder, reviewer | test_strategy.md |
| PLAN | pm, builder | implementation_plan.md |
| PLAN_REVIEW | reviewer, pm | plan_review.md |
| IMPLEMENTATION | builder | (dynamic) |
| IMPLEMENTATION_REVIEW | reviewer | impl_review.md |
| TEST | builder, reviewer | test_results.md |
| POST_REVIEW | pm, reviewer | post_review.md |
| COMPLETE | (none) | none |

**Review Stages:** SPEC_REVIEW, PLAN_REVIEW, IMPLEMENTATION_REVIEW, POST_REVIEW

### 2.5 Messaging System (`src/teambot/messaging/`)

**MessageRouter:** Routes messages to agent queues by agent_id or broadcasts to "all"

**Message Types:**
```python
TASK_ASSIGN       # Orchestrator → Agent
TASK_COMPLETE     # Agent → Orchestrator
TASK_FAILED       # Agent → Orchestrator
STATUS_UPDATE     # Agent → Orchestrator
CONTEXT_SHARE     # Agent → Agent
SHUTDOWN          # Orchestrator → All
```

### 2.6 Copilot SDK Client (`src/teambot/copilot/sdk_client.py`)

**Streaming Execution (Lines 200-270):**
```python
async def execute_streaming(agent_id: str, prompt: str, on_chunk: Callable) -> str:
    # 1. Get/create session
    # 2. Setup event handler for streaming chunks
    # 3. Subscribe to events
    # 4. Send prompt (non-blocking)
    # 5. Wait for completion with 30-min timeout
    # 6. Return accumulated response
```

**Cancellation:** `session.abort()` cancels in-progress request

---

## 3. Technical Approach

### 3.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ExecutionLoop (NEW)                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ObjectiveParser  →  StageExecutor  →  ReviewIterator      ││
│  │         ↓                  ↓                  ↓             ││
│  │  ParsedObjective    AgentTask(s)      ReviewResult         ││
│  └─────────────────────────────────────────────────────────────┘│
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  TimeManager  │  ProgressDisplay  │  CancellationHandler   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 EXISTING INFRASTRUCTURE                         │
│  Orchestrator ← AgentRunner ← CopilotSDKClient                 │
│       ↓              ↓              ↓                           │
│  WorkflowStateMachine  HistoryManager  MessageRouter           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 New Components

#### ObjectiveParser (`src/teambot/orchestration/objective_parser.py`)

**Purpose:** Parse markdown objective files into structured data

**Approach:** Use `python-frontmatter` library (already in project) + regex for section extraction

**Implementation Pattern:**
```python
@dataclass
class ParsedObjective:
    title: str
    goals: list[str]
    success_criteria: list[SuccessCriterion]
    constraints: list[str]
    context: str | None
    raw_content: str

@dataclass
class SuccessCriterion:
    description: str
    completed: bool = False

def parse_objective_file(path: Path) -> ParsedObjective:
    content = path.read_text()
    
    # Extract title from H1
    title_match = re.search(r'^#\s+(?:Objective:\s*)?(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"
    
    # Extract sections by ## headers
    sections = extract_sections(content)
    
    return ParsedObjective(
        title=title,
        goals=parse_list_section(sections.get("Goals", "")),
        success_criteria=parse_criteria_section(sections.get("Success Criteria", "")),
        constraints=parse_list_section(sections.get("Constraints", "")),
        context=sections.get("Context"),
        raw_content=content,
    )
```

#### ExecutionLoop (`src/teambot/orchestration/execution_loop.py`)

**Purpose:** Main driver that coordinates workflow execution

**Key Responsibilities:**
1. Load objective file and initialize/resume workflow state
2. Drive through stages by generating tasks
3. Route tasks to appropriate agents
4. Handle review iterations
5. Enforce time limits
6. Support cancellation

**Core Algorithm:**
```python
class ExecutionLoop:
    def __init__(self, objective_path: Path, config: dict, teambot_dir: Path):
        self.objective = parse_objective_file(objective_path)
        self.orchestrator = Orchestrator(config, objective=self.objective.raw_content)
        self.time_manager = TimeManager(max_seconds=8*60*60)
        self.cancelled = False
        
    async def run(self, on_progress: Callable) -> ExecutionResult:
        """Main execution loop."""
        self.time_manager.start()
        
        while not self.orchestrator.workflow_complete:
            if self.cancelled:
                return ExecutionResult.CANCELLED
            if self.time_manager.is_expired():
                return ExecutionResult.TIMEOUT
            
            stage = self.orchestrator.current_stage
            
            if self._is_review_stage(stage):
                result = await self._execute_review_stage(stage, on_progress)
                if result == ReviewResult.FAILED:
                    return ExecutionResult.REVIEW_FAILED
            else:
                await self._execute_work_stage(stage, on_progress)
            
            # Advance to next stage
            next_stage = self._get_next_stage(stage)
            self.orchestrator.advance_workflow(next_stage)
        
        return ExecutionResult.COMPLETE
```

#### ReviewIterator (`src/teambot/orchestration/review_iterator.py`)

**Purpose:** Manages review→feedback→action cycles (max 4 iterations)

**Implementation:**
```python
@dataclass
class IterationResult:
    iteration: int
    work_output: str
    review_output: str
    approved: bool
    feedback: str | None

class ReviewIterator:
    MAX_ITERATIONS = 4
    
    async def execute(self, stage: WorkflowStage, context: str, 
                      on_progress: Callable) -> ReviewResult:
        iteration_history = []
        
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            on_progress(f"Review iteration {iteration}/{self.MAX_ITERATIONS}")
            
            # Execute work
            work_result = await self._execute_work(stage, context, iteration_history)
            
            # Execute review
            review_result = await self._execute_review(stage, work_result)
            
            iteration_history.append(IterationResult(
                iteration=iteration,
                work_output=work_result,
                review_output=review_result.output,
                approved=review_result.approved,
                feedback=review_result.feedback,
            ))
            
            if review_result.approved:
                return ReviewResult.APPROVED
            
            # Prepare feedback for next iteration
            context = self._incorporate_feedback(context, review_result.feedback)
        
        # Max iterations reached - generate failure report
        return self._generate_failure_result(stage, iteration_history)
    
    def _generate_failure_result(self, stage, history) -> ReviewResult:
        """Generate detailed failure report with suggestions."""
        summary = self._summarize_failures(history)
        suggestions = self._extract_suggestions(history)
        
        # Save failure report
        report_path = self._save_failure_report(stage, summary, suggestions)
        
        return ReviewResult(
            status=ReviewStatus.FAILED,
            summary=summary,
            suggestions=suggestions,
            report_path=report_path,
        )
```

#### ParallelExecutor (`src/teambot/orchestration/parallel_executor.py`)

**Purpose:** Execute builder-1 and builder-2 concurrently during IMPLEMENTATION

**Approach:** Use `asyncio.gather()` with semaphore for concurrency control

**Task Partitioning Strategy:**
1. Extract task list from implementation plan
2. Assign odd-indexed tasks to builder-1, even to builder-2
3. Or: partition by file/module boundaries
4. Each builder works on separate files to avoid conflicts

**Implementation:**
```python
class ParallelExecutor:
    def __init__(self, sdk_client: CopilotSDKClient, max_concurrent: int = 2):
        self.sdk_client = sdk_client
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_parallel(self, tasks: list[AgentTask],
                               on_progress: Callable) -> dict[str, TaskResult]:
        """Execute multiple agent tasks in parallel."""
        async def execute_one(task: AgentTask) -> tuple[str, TaskResult]:
            async with self.semaphore:
                on_progress(task.agent_id, "running", task.description)
                try:
                    output = await self.sdk_client.execute_streaming(
                        task.agent_id, task.prompt,
                        lambda chunk: on_progress(task.agent_id, "chunk", chunk)
                    )
                    on_progress(task.agent_id, "complete")
                    return (task.agent_id, TaskResult(success=True, output=output))
                except Exception as e:
                    on_progress(task.agent_id, "failed", str(e))
                    return (task.agent_id, TaskResult(success=False, error=str(e)))
        
        results = await asyncio.gather(
            *[execute_one(t) for t in tasks],
            return_exceptions=True
        )
        return dict(results)
```

### 3.3 Progress Display Integration

**Approach:** Extend existing `StatusPanel` or create `OrchestrationDisplay`

**Option 1: Extend StatusPanel** (Recommended)
- Add orchestration mode that shows stage progress, time, activity log
- Reuse existing `AgentStatusManager` for agent states
- Add methods: `set_objective()`, `set_stage()`, `set_elapsed_time()`

**Option 2: New OrchestrationDisplay widget**
- Full-screen Textual app for orchestration mode
- More flexibility but more code

**Progress Callback Pattern:**
```python
def create_progress_callback(status_manager: AgentStatusManager, 
                             display: OrchestrationDisplay):
    def on_progress(event_type: str, **kwargs):
        if event_type == "agent_started":
            status_manager.set_running(kwargs["agent_id"], kwargs["task"])
        elif event_type == "agent_streaming":
            status_manager.set_streaming(kwargs["agent_id"])
        elif event_type == "agent_complete":
            status_manager.set_completed(kwargs["agent_id"])
        elif event_type == "stage_changed":
            display.set_stage(kwargs["stage"])
        elif event_type == "time_update":
            display.set_elapsed(kwargs["elapsed"])
    return on_progress
```

### 3.4 Cancellation & State Persistence

**Cancellation Flow:**
1. User presses Ctrl+C
2. Signal handler sets `loop.cancelled = True`
3. Current agent operations cancelled via `sdk_client.cancel_current_request()`
4. State saved to `workflow_state.json`
5. Exit cleanly with message

**State Persistence Enhancement:**
Extend `WorkflowState` with orchestration-specific fields:
```python
{
  # Existing fields...
  "orchestration": {
    "objective_file": "objectives/auth.md",
    "started_at": "ISO-8601",
    "elapsed_seconds": 9255,
    "max_seconds": 28800,
    "review_iterations": {
      "SPEC_REVIEW": 2,
      "PLAN_REVIEW": 1
    },
    "success_criteria_status": {
      "Login form validates": false,
      "JWT tokens expire": true
    },
    "status": "running" | "paused" | "complete" | "failed"
  }
}
```

**Resume Capability:**
```python
def resume_execution(teambot_dir: Path) -> ExecutionLoop:
    state = load_workflow_state(teambot_dir)
    if state.orchestration.status != "paused":
        raise ValueError("No paused orchestration to resume")
    
    loop = ExecutionLoop.from_state(state)
    loop.time_manager.resume(state.orchestration.elapsed_seconds)
    return loop
```

---

## 4. Testing Strategy Research

### 4.1 Existing Test Infrastructure

**Framework:** pytest 7.x with pytest-cov, pytest-mock, pytest-asyncio

**Location:** `tests/` directory mirrors `src/teambot/` structure

**Runner:** `uv run pytest` (configured in pyproject.toml)

**Coverage:** 84% overall (per previous runs)

### 4.2 Relevant Test Patterns Found

**test_orchestrator.py (Lines 1-50):**
- Uses `sample_agent_config` fixture
- Mocks `_create_agent_process` to avoid actual process spawning
- Tests queue creation, router setup, task assignment

**test_agent_runner.py:**
- Mocks `CopilotClient` for task execution
- Tests message handling flow
- Tests history file creation

**test_workflow/ (state_machine tests):**
- Tests stage transitions
- Tests state persistence/loading
- Tests persona validation

### 4.3 Test Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| ObjectiveParser | TDD | Well-defined input/output, critical for correctness |
| ExecutionLoop | Code-First | Complex async, easier to iterate then test |
| ReviewIterator | TDD | Clear algorithm, critical review logic |
| ParallelExecutor | Code-First | Async complexity, leverage existing patterns |
| Progress integration | Code-First | UI integration, manual testing more valuable |

### 4.4 Mock Strategy

```python
# Mock CopilotSDKClient for unit tests
@pytest.fixture
def mock_sdk_client():
    client = AsyncMock(spec=CopilotSDKClient)
    client.execute_streaming = AsyncMock(return_value="Task completed successfully")
    client.cancel_current_request = AsyncMock()
    return client

# Mock Orchestrator for execution loop tests
@pytest.fixture
def mock_orchestrator():
    orch = MagicMock(spec=Orchestrator)
    orch.current_stage = WorkflowStage.SETUP
    orch.workflow_complete = False
    return orch
```

---

## 5. Implementation Guidance

### 5.1 File Structure

```
src/teambot/orchestration/
├── __init__.py
├── objective_parser.py      # ParsedObjective, parse_objective_file()
├── execution_loop.py        # ExecutionLoop, ExecutionResult
├── review_iterator.py       # ReviewIterator, ReviewResult
├── parallel_executor.py     # ParallelExecutor
├── time_manager.py          # TimeManager
└── progress.py              # Progress callback utilities

tests/test_orchestration/
├── __init__.py
├── test_objective_parser.py
├── test_execution_loop.py
├── test_review_iterator.py
├── test_parallel_executor.py
└── test_time_manager.py
```

### 5.2 Implementation Order

1. **ObjectiveParser** - Foundation, no dependencies
2. **TimeManager** - Simple, needed by ExecutionLoop
3. **ReviewIterator** - Core review logic
4. **ParallelExecutor** - Parallel agent execution
5. **ExecutionLoop** - Main coordinator (depends on 1-4)
6. **CLI Integration** - Wire up `teambot run`
7. **Progress Display** - UI integration

### 5.3 Key Integration Points

**CLI Integration (`src/teambot/cli.py` Lines 88-131):**
```python
def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    # ... existing code ...
    
    if objective:
        # NEW: Run orchestration instead of warning
        from teambot.orchestration import ExecutionLoop
        
        loop = ExecutionLoop(
            objective_path=Path(args.objective),
            config=config,
            teambot_dir=Path(".teambot"),
        )
        
        try:
            result = asyncio.run(loop.run(on_progress=display.update))
            return 0 if result == ExecutionResult.COMPLETE else 1
        except KeyboardInterrupt:
            loop.cancel()
            return 130  # Standard interrupted exit code
```

### 5.4 Prompt Generation for Stages

Each stage needs a task prompt incorporating:
1. Objective context
2. Stage-specific instructions
3. Previous stage artifacts
4. Review feedback (if iteration)

**Example for SPEC stage:**
```python
def generate_spec_prompt(objective: ParsedObjective, context: str) -> str:
    return f"""
Create a detailed feature specification for the following objective.

## Objective
{objective.title}

## Goals
{chr(10).join(f"- {g}" for g in objective.goals)}

## Success Criteria
{chr(10).join(f"- {c.description}" for c in objective.success_criteria)}

## Constraints
{chr(10).join(f"- {c}" for c in objective.constraints)}

## Additional Context
{objective.context or "None provided"}

## Instructions
Create a comprehensive feature specification that:
1. Defines all functional requirements
2. Specifies acceptance criteria
3. Identifies technical approach
4. Documents risks and mitigations

Output the specification in markdown format.
"""
```

---

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Review loops never approve | Max 4 iterations with clear failure report |
| Parallel agent conflicts | Partition tasks by file/module |
| State corruption on crash | Atomic writes, backup before save |
| Memory leak in long runs | Process isolation, periodic cleanup |
| Copilot CLI rate limits | Backoff strategy, configurable delays |

---

## 7. Next Steps

1. **Create formal test strategy** via `/sdd.4-determine-test-strategy`
2. **Create implementation plan** via `/sdd.5-task-planner-for-feature`
3. **Implement ObjectiveParser** first (TDD)
4. **Implement TimeManager** (simple, needed early)
5. **Build ReviewIterator** with failure handling
6. **Wire up ExecutionLoop** integrating all components
7. **Add CLI integration** for `teambot run`
8. **Add progress display** to UI

---

## Appendix: Code References

| File | Key Lines | Purpose |
|------|-----------|---------|
| `orchestrator.py` | 120-158 | assign_task() with validation |
| `orchestrator.py` | 160-172 | advance_workflow() |
| `agent_runner.py` | 108-151 | _execute_task() flow |
| `state_machine.py` | 138-141 | save_state() persistence |
| `stages.py` | 46-151 | Stage metadata with personas |
| `sdk_client.py` | 200-270 | execute_streaming() |
| `frontmatter.py` | 55-63 | parse_frontmatter() |
| `templates.py` | 39-54 | build_prompt() |
