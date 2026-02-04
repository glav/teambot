<!-- markdownlint-disable-file -->
# Shared Context Reference Syntax - Technical Research Document

**Date**: 2026-02-03  
**Feature**: Agent Output Reference Syntax (`$agent` notation)  
**Status**: Research Complete ✅  
**Researcher**: Builder-1  

---

## Executive Summary

This research document provides comprehensive technical analysis for implementing a **shared context reference syntax** (`$agent`) that allows TeamBot users to reference another agent's most recent output within prompts. This feature enables intuitive, dependency-based workflows where one agent can wait for and consume another agent's results.

**Key Findings**:
- ✅ Existing pipeline (`->`) syntax provides sequential dependencies but requires explicit chaining
- ✅ New `$agent` syntax will allow **implicit** dependency on any agent's last output
- ✅ TaskManager and OutputInjector already support dependency handling - can be extended
- ✅ Parser requires minimal changes to detect `$agent` references in prompt content
- ✅ Agent status tracking exists in OverlayRenderer - needs "waiting" state addition

---

## Table of Contents

1. [Scope & Objectives](#1-scope--objectives)
2. [Entry Point Analysis](#2-entry-point-analysis)
3. [Existing Architecture Analysis](#3-existing-architecture-analysis)
4. [Technical Approach](#4-technical-approach)
5. [Implementation Guidance](#5-implementation-guidance)
6. [Testing Strategy Research](#6-testing-strategy-research)
7. [Task Implementation Requests](#7-task-implementation-requests)
8. [Potential Next Research](#8-potential-next-research)

---

## 1. Scope & Objectives

### 1.1 Feature Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| **Syntax** | `$pm`, `$ba`, `$builder-1` etc. to reference agent output | P0 |
| **Waiting Behavior** | Agent waits for referenced agent to complete | P0 |
| **Status Display** | Show waiting/executing/idle status accurately | P0 |
| **Documentation** | README comparison of `$ref` vs `->` syntax | P0 |
| **Multiple References** | Support multiple `$agent` references in single prompt | P1 |

### 1.2 Success Criteria

- [ ] Easy-to-use `$pm` syntax to reference PM agent's results
- [ ] Referencing agent waits for referenced agent to complete
- [ ] README.md documents both syntaxes with comparison
- [ ] Agent status accurately reflects waiting/executing/idle

### 1.3 Assumptions

- Users are familiar with basic TeamBot `@agent` syntax
- Referenced agents have produced output in current session
- Feature operates in interactive REPL mode

---

## 2. Entry Point Analysis

### 2.1 User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `@pm task $ba` (simple) | loop.py → router.py → sdk | ⚠️ NO (simple path) | ✅ YES |
| `@pm task $ba &` (background) | loop.py → executor.py → manager.py | ✅ YES (via executor) | ✅ YES |
| `@pm,@ba task $writer` (multi-agent) | loop.py → executor.py → manager.py | ✅ YES | ✅ YES |
| `@pm -> @ba task` (pipeline) | loop.py → executor.py → manager.py | ✅ YES | ✅ NO (existing) |

### 2.2 Code Path Trace

#### Entry Point 1: Simple Command `@pm task with $ba reference`
1. User enters: `@pm Summarize $ba`
2. Handled by: `repl/loop.py:REPLLoop.run()` (lines 256-300)
3. Parsed by: `repl/parser.py:parse_command()` (lines 83-110)
4. Routes via: `repl/loop.py` checks if advanced command (lines 280-290)
5. **Problem**: Simple commands go to `router.py:_route_agent()` which calls SDK directly
6. Does NOT reach: `tasks/executor.py` where dependency handling exists ❌

#### Entry Point 2: Background Command `@pm task $ba &`
1. User enters: `@pm Summarize $ba &`
2. Handled by: `repl/loop.py:REPLLoop.run()` (lines 256-300)
3. Parsed by: `repl/parser.py:parse_command()` (lines 83-110)
4. **Background flag detected**: Routes to `_handle_advanced_command()` (line 286)
5. Reaches: `tasks/executor.py:execute()` (line 104)
6. Reaches: `tasks/manager.py:execute_task()` (line 126) ✅

#### Entry Point 3: Multi-Agent `@pm,@ba task with $writer`
1. User enters: `@pm,ba Analyze using $writer`
2. **Multiple agents detected**: Routes to `_handle_advanced_command()`
3. Reaches: `tasks/executor.py:_execute_multiagent()` (line 171)
4. Each task created via: `tasks/manager.py:create_task()` (line 62) ✅

### 2.3 Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| Simple `@agent` commands bypass executor | `$ref` won't work for basic commands | Route ALL commands through TaskExecutor |
| No `$ref` pattern detection in parser | Can't identify references | Add regex pattern in parser.py |
| No result storage per agent | Can't lookup last result | Store results by agent_id in TaskManager |
| No "waiting" status | Status display incomplete | Add WAITING to TaskStatus enum |

### 2.4 Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 3. Existing Architecture Analysis

### 3.1 Parser Module (`src/teambot/repl/parser.py`)

**Current Capabilities** (Lines 1-224):
- Parses `@agent` commands with regex pattern (line 74)
- Supports multi-agent via comma separation (line 132)
- Supports background via `&` suffix (line 136-140)
- Supports pipeline via `->` operator (line 162)

**Key Patterns Found**:
```python
# Line 74 - Agent pattern
AGENT_PATTERN = re.compile(r"^@([a-zA-Z][a-zA-Z0-9,-]*)\s*(.*)", re.DOTALL)

# Line 80 - Pipeline pattern
PIPELINE_PATTERN = re.compile(r"\s*->\s*@")
```

**Extension Point**: Add new pattern for `$agent` references within content:
```python
# Proposed addition
REFERENCE_PATTERN = re.compile(r"\$([a-zA-Z][a-zA-Z0-9-]*)")
```

### 3.2 Command Dataclass (`src/teambot/repl/parser.py`, Lines 47-71)

**Current Structure**:
```python
@dataclass
class Command:
    type: CommandType
    agent_id: Optional[str] = None
    agent_ids: list[str] = field(default_factory=list)
    content: Optional[str] = None
    background: bool = False
    is_pipeline: bool = False
    pipeline: Optional[list[PipelineStage]] = None
```

**Extension Point**: Add field for referenced agents:
```python
    references: list[str] = field(default_factory=list)  # Agent IDs from $ref syntax
```

### 3.3 Task Models (`src/teambot/tasks/models.py`)

**TaskStatus Enum** (Lines 9-30):
```python
class TaskStatus(Enum):
    PENDING = auto()    # Waiting to run (may have unmet dependencies)
    RUNNING = auto()    # Currently executing
    COMPLETED = auto()  # Finished successfully
    FAILED = auto()     # Finished with error
    SKIPPED = auto()    # Skipped due to parent failure
    CANCELLED = auto()  # Cancelled by user
```

**Extension Point**: Add WAITING status for explicit "waiting for dependency":
```python
    WAITING = auto()    # Waiting for referenced agent to complete
```

### 3.4 TaskManager (`src/teambot/tasks/manager.py`)

**Key Methods**:
- `create_task()` (Lines 62-97): Creates task with dependencies
- `execute_task()` (Lines 126-163): Executes single task with prompt injection
- `_build_prompt()` (Lines 165-189): Injects parent outputs

**Dependency Handling** (Lines 165-189):
```python
def _build_prompt(self, task: Task) -> str:
    """Build prompt with injected parent outputs."""
    if not task.dependencies:
        return task.prompt

    # Build agent map for nicer headers
    agent_map = {
        tid: self._tasks[tid].agent_id
        for tid in task.dependencies
        if tid in self._tasks
    }

    return self._injector.inject(
        task.prompt,
        self._results,
        task.dependencies,
        agent_map=agent_map,
    )
```

**Extension Point**: Need to store/lookup results by agent_id, not just task_id:
```python
    self._agent_results: dict[str, TaskResult] = {}  # agent_id -> latest result
```

### 3.5 OutputInjector (`src/teambot/tasks/output_injector.py`)

**Injection Logic** (Lines 15-71):
- Prepends parent outputs with headers
- Appends child's original prompt
- Handles missing/failed parent results

**Output Format**:
```
=== Output from @pm (task task-pm-abc123) ===
{pm's output content}

=== Your Task ===
{original prompt}
```

**Extension Point**: Support agent-id-based lookup (not just task-id):
```python
def inject_by_agent(
    self,
    prompt: str,
    agent_results: dict[str, TaskResult],  # agent_id -> result
    referenced_agents: list[str],
) -> str:
```

### 3.6 REPL Loop (`src/teambot/repl/loop.py`)

**Command Routing Logic** (Lines 278-301):
```python
# Check if this is an advanced agent command
if command.type == CommandType.AGENT and (
    command.is_pipeline or
    len(command.agent_ids) > 1 or
    command.background
):
    # Use task executor for parallel/pipeline/background
    result = await self._handle_advanced_command(command)
else:
    # Use existing router for simple commands
    result = await self._router.route(command)
```

**Critical Gap**: Simple `@agent` commands bypass TaskExecutor entirely!

**Required Change**: Route commands with `$ref` through TaskExecutor:
```python
if command.type == CommandType.AGENT and (
    command.is_pipeline or
    len(command.agent_ids) > 1 or
    command.background or
    command.references  # NEW: Has $ref dependencies
):
```

### 3.7 Overlay Status Display (`src/teambot/visualization/overlay.py`)

**State Tracking** (Lines 45-76):
```python
@dataclass
class OverlayState:
    enabled: bool = True
    active_agents: list[str] = field(default_factory=list)
    running_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
```

**Extension Point**: Add waiting_count and waiting_for tracking:
```python
    waiting_count: int = 0
    waiting_agents: dict[str, list[str]] = field(default_factory=dict)  # agent -> [waiting_for]
```

---

## 4. Technical Approach

### 4.1 Selected Implementation Approach

**Strategy**: Extend existing pipeline/dependency infrastructure with agent-result lookup

**Rationale**:
- Reuses proven TaskManager dependency handling
- OutputInjector already formats injected content
- Minimal parser changes required
- Consistent with existing patterns

### 4.2 Key Components to Modify

| Component | Change Type | Complexity |
|-----------|-------------|------------|
| `repl/parser.py` | Add reference detection | Low |
| `repl/parser.py:Command` | Add `references` field | Low |
| `repl/loop.py` | Route referenced commands to executor | Low |
| `tasks/manager.py` | Store results by agent_id | Medium |
| `tasks/manager.py` | Wait for agent completion | Medium |
| `tasks/executor.py` | Handle reference-based dependencies | Medium |
| `tasks/output_injector.py` | Support agent-id injection | Low |
| `tasks/models.py` | Add WAITING status | Low |
| `visualization/overlay.py` | Display waiting state | Low |
| `README.md` | Document syntax comparison | Low |

### 4.3 Syntax Comparison: `$ref` vs `->`

| Aspect | `$ref` Syntax | `->` Pipeline Syntax |
|--------|---------------|---------------------|
| **Example** | `@pm Summarize $ba output` | `@ba Analyze -> @pm Summarize` |
| **Direction** | Consumer references producer | Producer chains to consumer |
| **Explicit Task** | Producer runs independently | Producer task specified in pipeline |
| **Use Case** | Reference previous session output | Sequential task chain |
| **Waiting** | Waits for current/recent task | Waits for pipeline stage |
| **Multiple Refs** | `@pm Use $ba and $writer` | `@ba,writer -> @pm` (parallel then) |
| **Result Source** | Latest completed result | Immediate predecessor output |

### 4.4 Data Flow Diagram

```
User Input: "@pm Summarize $ba's findings"
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ Parser (parse_command)                                          │
│  1. Match @pm as target agent                                   │
│  2. Detect $ba in content → references = ["ba"]                 │
│  3. Return Command(agent_ids=["pm"], references=["ba"], ...)    │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPL Loop (route decision)                                      │
│  - command.references is not empty → use TaskExecutor           │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ TaskExecutor (execute)                                          │
│  1. Check if "ba" has running task → wait for completion        │
│  2. Lookup agent_results["ba"] for latest output                │
│  3. Create task with implicit dependency                        │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ TaskManager (create_task + execute_task)                        │
│  1. Task created with status=WAITING if dependency pending      │
│  2. On dependency complete: status=PENDING → RUNNING            │
│  3. OutputInjector prepends referenced output to prompt         │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ SDK Client (execute)                                            │
│  Prompt: "=== Output from @ba ===\n{ba_output}\n\n              │
│           === Your Task ===\nSummarize $ba's findings"          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Guidance

### 5.1 Parser Changes (`src/teambot/repl/parser.py`)

**Add Reference Pattern** (after line 80):
```python
# Pattern for agent references in content: $pm, $ba, $builder-1
REFERENCE_PATTERN = re.compile(r"\$([a-zA-Z][a-zA-Z0-9-]*)")
```

**Modify Command Dataclass** (line 47-71):
```python
@dataclass
class Command:
    # ... existing fields ...
    references: list[str] = field(default_factory=list)  # Agent IDs from $ref
```

**Add Reference Detection** (in `_parse_agent_command`, after line 145):
```python
# Detect $agent references in content
references = REFERENCE_PATTERN.findall(content) if content else []
# Deduplicate while preserving order
seen = set()
references = [r for r in references if not (r in seen or seen.add(r))]
```

### 5.2 TaskManager Changes (`src/teambot/tasks/manager.py`)

**Add Agent Result Storage** (in `__init__`, after line 47):
```python
self._agent_results: dict[str, TaskResult] = {}  # agent_id -> latest result
```

**Update on Task Completion** (in `execute_task`, after line 151):
```python
# Store result by agent_id for $ref lookup
self._agent_results[task.agent_id] = task.result
```

**Add Lookup Method**:
```python
def get_agent_result(self, agent_id: str) -> Optional[TaskResult]:
    """Get latest result for an agent.
    
    Args:
        agent_id: Agent identifier.
        
    Returns:
        Latest TaskResult for agent, or None.
    """
    return self._agent_results.get(agent_id)

def get_running_task_for_agent(self, agent_id: str) -> Optional[Task]:
    """Get currently running task for an agent.
    
    Args:
        agent_id: Agent identifier.
        
    Returns:
        Running Task if found, else None.
    """
    for task in self._tasks.values():
        if task.agent_id == agent_id and task.status == TaskStatus.RUNNING:
            return task
    return None
```

### 5.3 TaskExecutor Changes (`src/teambot/tasks/executor.py`)

**Handle References in Simple Execution** (modify `_execute_simple`):
```python
async def _execute_simple(self, command: Command) -> ExecutionResult:
    """Execute simple single-agent command, handling $ref dependencies."""
    agent_id = command.agent_ids[0]
    
    # Check for $ref dependencies
    if command.references:
        # Wait for any referenced agents that are currently running
        await self._wait_for_references(command.references)
        
        # Build prompt with injected outputs
        prompt = self._inject_references(command.content, command.references)
    else:
        prompt = command.content
    
    task = self._manager.create_task(
        agent_id=agent_id,
        prompt=prompt,
        background=command.background,
    )
    # ... rest of method
```

**Add Reference Helpers**:
```python
async def _wait_for_references(self, references: list[str]) -> None:
    """Wait for referenced agents to complete any running tasks.
    
    Args:
        references: List of agent IDs to wait for.
    """
    for agent_id in references:
        running_task = self._manager.get_running_task_for_agent(agent_id)
        if running_task:
            # Wait for the task to complete
            while running_task.status == TaskStatus.RUNNING:
                await asyncio.sleep(0.1)

def _inject_references(self, prompt: str, references: list[str]) -> str:
    """Inject referenced agent outputs into prompt.
    
    Args:
        prompt: Original prompt with $ref tokens.
        references: List of agent IDs referenced.
        
    Returns:
        Prompt with outputs prepended.
    """
    sections = []
    for agent_id in references:
        result = self._manager.get_agent_result(agent_id)
        if result and result.success:
            sections.append(
                f"=== Output from @{agent_id} ===\n{result.output}\n"
            )
        else:
            sections.append(
                f"=== Output from @{agent_id} ===\n[No output available]\n"
            )
    
    sections.append(f"=== Your Task ===\n{prompt}")
    return "\n".join(sections)
```

### 5.4 REPL Loop Changes (`src/teambot/repl/loop.py`)

**Update Routing Condition** (lines 280-286):
```python
# Check if this is an advanced agent command
if command.type == CommandType.AGENT and (
    command.is_pipeline or
    len(command.agent_ids) > 1 or
    command.background or
    command.references  # NEW: Has $ref dependencies
):
    # Use task executor for parallel/pipeline/background/references
    result = await self._handle_advanced_command(command)
```

### 5.5 Status Enum Changes (`src/teambot/tasks/models.py`)

**Add WAITING Status** (line 17):
```python
class TaskStatus(Enum):
    PENDING = auto()    # Waiting to run (may have unmet dependencies)
    WAITING = auto()    # Waiting for referenced agent to complete  # NEW
    RUNNING = auto()    # Currently executing
    # ... rest
```

### 5.6 Overlay Changes (`src/teambot/visualization/overlay.py`)

**Update State** (lines 45-68):
```python
@dataclass
class OverlayState:
    # ... existing fields ...
    waiting_count: int = 0
    waiting_for: dict[str, str] = field(default_factory=dict)  # agent -> waiting_for_agent
```

**Update Display** (in `_build_content`, lines 297-323):
```python
def _build_content(self) -> list[str]:
    lines = []
    
    if self._state.is_idle():
        lines.append("✓ Idle")
    else:
        # Show waiting agents
        if self._state.waiting_count > 0:
            waiting = ", ".join(f"@{a}→@{w}" for a, w in self._state.waiting_for.items())
            lines.append(f"⏳ Waiting: {waiting}"[:OVERLAY_WIDTH - 4])
        
        # Show active agents with spinner
        spinner = SPINNER_FRAMES[self._state.spinner_frame % len(SPINNER_FRAMES)]
        agents = ", ".join(f"@{a}" for a in self._state.active_agents[:3])
        lines.append(f"{spinner} {agents}"[:OVERLAY_WIDTH - 4])
    
    # Task counts with waiting
    running = self._state.running_count
    waiting = self._state.waiting_count
    pending = self._state.pending_count
    completed = self._state.completed_count
    counts = f"{running}🔄 {waiting}⏳ {pending}⏸ {completed}✓"
    lines.append(f"Tasks: {counts}"[:OVERLAY_WIDTH - 4])
    
    return lines
```

### 5.7 README Documentation

**Add Section** (after line 243 "Syntax Quick Reference" table):

```markdown
### Shared Context References (`$agent`)

Reference another agent's most recent output using `$agent` syntax:

```bash
# Reference PM's last output
teambot: @builder-1 Implement based on $pm

# Reference multiple agents
teambot: @reviewer Check $builder-1 against $pm requirements

# Wait for running task
teambot: @pm Summarize $ba  # Waits if @ba is still running
```

**How It Works**:
1. Parser detects `$agent` references in your prompt
2. If referenced agent has a running task, waits for completion
3. Referenced agent's latest output is prepended to your prompt
4. Your agent receives full context automatically

**Example Output Injection**:
```
=== Output from @ba ===
The requirements are:
1. User authentication
2. Profile management

=== Your Task ===
Implement based on $ba
```

### Comparing `$ref` vs `->` Syntax

| Feature | `$ref` Syntax | `->` Pipeline |
|---------|---------------|---------------|
| **Use Case** | Reference existing output | Chain new tasks |
| **Example** | `@pm Summarize $ba` | `@ba Analyze -> @pm Summarize` |
| **Producer Task** | Uses last completed output | Runs new task |
| **Direction** | Consumer pulls | Producer pushes |
| **Multiple Sources** | `@pm Use $ba and $writer` | `@ba,writer Analyze -> @pm` |
| **Best For** | Building on previous work | Designing new workflows |

**When to Use Which**:
- **`$ref`**: When you want to reference work an agent already completed
- **`->`**: When you want to define a complete workflow from scratch
```

---

## 6. Testing Strategy Research

### 6.1 Existing Test Infrastructure

| Aspect | Details |
|--------|---------|
| **Framework** | pytest 7.x |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage** | 83% overall (750 tests) |
| **Fixtures** | Per-module conftest.py files |

### 6.2 Test Patterns Found

**File**: `tests/test_repl/test_parser.py` (Lines 1-264)
- Clear arrange-act-assert structure
- Pytest class grouping by concern
- Error case testing with `pytest.raises`

**Example Pattern**:
```python
class TestParseAgentCommands:
    def test_parse_agent_command_basic(self):
        """Test parsing basic @agent command."""
        result = parse_command("@pm Create a project plan")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a project plan"
```

**File**: `tests/test_tasks/test_executor.py` (Lines 1-441)
- Async tests with `@pytest.mark.asyncio`
- Mock SDK client with `AsyncMock`
- Callback testing patterns

**Example Pattern**:
```python
@pytest.mark.asyncio
async def test_pipeline_passes_output(self):
    """Test that pipeline passes output to next stage."""
    captured_prompts = []

    async def capture_execute(agent_id, prompt):
        captured_prompts.append((agent_id, prompt))
        return f"{agent_id} completed"

    mock_sdk = AsyncMock()
    mock_sdk.execute = capture_execute

    executor = TaskExecutor(sdk_client=mock_sdk)
    cmd = parse_command("@pm Create plan -> @builder-1 Implement")

    await executor.execute(cmd)

    # Second stage should include first stage's output
    assert len(captured_prompts) == 2
    builder_prompt = captured_prompts[1][1]
    assert "pm completed" in builder_prompt
```

### 6.3 Required Test Cases

#### Parser Tests (`tests/test_repl/test_parser.py`)

```python
class TestParseReferences:
    """Tests for $agent reference parsing."""

    def test_parse_single_reference(self):
        """Test parsing single $agent reference."""
        result = parse_command("@pm Summarize $ba output")
        
        assert result.references == ["ba"]
        assert "$ba" in result.content

    def test_parse_multiple_references(self):
        """Test parsing multiple references."""
        result = parse_command("@reviewer Check $builder-1 against $pm")
        
        assert result.references == ["builder-1", "pm"]

    def test_parse_reference_with_hyphen(self):
        """Test parsing reference with hyphenated agent ID."""
        result = parse_command("@pm Use $builder-1 work")
        
        assert result.references == ["builder-1"]

    def test_parse_no_reference(self):
        """Test command without references."""
        result = parse_command("@pm Create a plan")
        
        assert result.references == []

    def test_parse_duplicate_references_deduplicated(self):
        """Test duplicate references are deduplicated."""
        result = parse_command("@pm Check $ba then verify $ba again")
        
        assert result.references == ["ba"]  # Only one

    def test_reference_in_pipeline(self):
        """Test reference detection in pipeline stage."""
        result = parse_command("@pm Plan -> @builder-1 Implement $pm")
        
        # Last stage should have reference
        assert result.pipeline[-1].content == "Implement $pm"
```

#### Executor Tests (`tests/test_tasks/test_executor.py`)

```python
class TestExecutorReferences:
    """Tests for $ref execution."""

    @pytest.mark.asyncio
    async def test_reference_injects_output(self):
        """Test that referenced output is injected."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # First, run a task for ba
        cmd1 = parse_command("@ba Analyze requirements")
        await executor.execute(cmd1)
        
        # Now reference ba's output
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)
        
        # Check that PM received BA's output
        call_args = mock_sdk.execute.call_args_list[-1]
        prompt = call_args[0][1]
        assert "=== Output from @ba ===" in prompt
        assert "Done" in prompt

    @pytest.mark.asyncio
    async def test_reference_waits_for_running_task(self):
        """Test that reference waits for running task."""
        import asyncio
        
        call_order = []
        
        async def slow_execute(agent_id, prompt):
            call_order.append(f"{agent_id}_start")
            if agent_id == "ba":
                await asyncio.sleep(0.5)
            call_order.append(f"{agent_id}_end")
            return f"{agent_id} output"
        
        mock_sdk = AsyncMock()
        mock_sdk.execute = slow_execute
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # Start BA in background
        cmd1 = parse_command("@ba Analyze &")
        await executor.execute(cmd1)
        
        # PM references BA (should wait)
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)
        
        # BA should complete before PM starts using its output
        assert call_order.index("ba_end") < call_order.index("pm_end")

    @pytest.mark.asyncio
    async def test_reference_no_output_available(self):
        """Test graceful handling when no output available."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # Reference agent that hasn't run
        cmd = parse_command("@pm Summarize $ba")
        result = await executor.execute(cmd)
        
        # Should still execute with placeholder
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]
        assert "[No output available]" in prompt
```

#### Integration Tests

```python
class TestSharedContextIntegration:
    """Integration tests for shared context feature."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_references(self):
        """Test complete workflow: BA → PM references BA → Builder references PM."""
        mock_sdk = AsyncMock()
        
        outputs = {
            "ba": "Requirements: login, dashboard",
            "pm": "Plan: 1. Build login 2. Build dashboard",
            "builder-1": "Implementation complete",
        }
        
        async def mock_execute(agent_id, prompt):
            return outputs.get(agent_id, "default")
        
        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # BA analyzes
        await executor.execute(parse_command("@ba Analyze requirements"))
        
        # PM references BA
        await executor.execute(parse_command("@pm Create plan based on $ba"))
        
        # Builder references PM
        result = await executor.execute(
            parse_command("@builder-1 Implement $pm")
        )
        
        # Verify chain worked
        assert result.success
```

### 6.4 Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| Parser (`references` detection) | TDD | Clear requirements, easy to test |
| TaskManager (agent result storage) | TDD | Critical data path |
| TaskExecutor (wait/inject) | Code-First | Complex async, easier to iterate |
| Overlay (waiting display) | Code-First | UI, subjective |
| Integration | Code-First | End-to-end validation |

---

## 7. Task Implementation Requests

### 7.1 Parser Enhancement

**File**: `src/teambot/repl/parser.py`

**Tasks**:
1. Add `REFERENCE_PATTERN` regex constant
2. Add `references: list[str]` field to `Command` dataclass
3. Modify `_parse_agent_command()` to detect references
4. Modify `_parse_pipeline()` to detect references in stages
5. Add unit tests for reference parsing

**Estimated Complexity**: Low

### 7.2 TaskManager Enhancement

**File**: `src/teambot/tasks/manager.py`

**Tasks**:
1. Add `_agent_results` dict to store latest results by agent
2. Update `execute_task()` to populate `_agent_results`
3. Add `get_agent_result()` method
4. Add `get_running_task_for_agent()` method
5. Add unit tests for agent result storage/lookup

**Estimated Complexity**: Medium

### 7.3 TaskExecutor Enhancement

**File**: `src/teambot/tasks/executor.py`

**Tasks**:
1. Add `_wait_for_references()` async method
2. Add `_inject_references()` method
3. Modify `_execute_simple()` to handle references
4. Add unit tests for reference waiting and injection

**Estimated Complexity**: Medium

### 7.4 REPL Loop Enhancement

**File**: `src/teambot/repl/loop.py`

**Tasks**:
1. Update routing condition to include `command.references`
2. No new tests needed (existing routing tests cover pattern)

**Estimated Complexity**: Low

### 7.5 Status Model Enhancement

**File**: `src/teambot/tasks/models.py`

**Tasks**:
1. Add `WAITING` to `TaskStatus` enum
2. Update `is_terminal()` to handle WAITING
3. Add unit test for new status

**Estimated Complexity**: Low

### 7.6 Overlay Enhancement

**File**: `src/teambot/visualization/overlay.py`

**Tasks**:
1. Add `waiting_count` and `waiting_for` to `OverlayState`
2. Update `_build_content()` to display waiting state
3. Add `on_task_waiting()` callback
4. Add unit tests for waiting display

**Estimated Complexity**: Low

### 7.7 Documentation Update

**File**: `README.md`

**Tasks**:
1. Add "Shared Context References" section
2. Add syntax comparison table
3. Add usage examples

**Estimated Complexity**: Low

---

## 8. Potential Next Research

### 8.1 Completed Research ✅

- [x] Parser extension for `$ref` pattern
- [x] TaskManager agent result storage
- [x] TaskExecutor dependency waiting
- [x] REPL routing changes
- [x] Status display updates
- [x] Entry point analysis

### 8.2 No Further Research Required

All technical questions have been addressed. Implementation can proceed.

---

## Appendix A: File Reference Summary

| File | Lines | Purpose |
|------|-------|---------|
| `src/teambot/repl/parser.py` | 1-224 | Command parsing with patterns |
| `src/teambot/repl/loop.py` | 1-398 | REPL main loop and routing |
| `src/teambot/repl/router.py` | 1-183 | Agent routing and validation |
| `src/teambot/tasks/executor.py` | 1-382 | Command to task bridging |
| `src/teambot/tasks/manager.py` | 1-270 | Task lifecycle management |
| `src/teambot/tasks/models.py` | 1-166 | Task and result models |
| `src/teambot/tasks/output_injector.py` | 1-95 | Output injection formatting |
| `src/teambot/visualization/overlay.py` | 1-513 | Status overlay display |
| `tests/test_repl/test_parser.py` | 1-264 | Parser test patterns |
| `tests/test_tasks/test_executor.py` | 1-441 | Executor test patterns |

---

## Appendix B: Syntax Quick Reference

```
# Existing Syntax
@pm task                    # Simple command
@pm,ba task                 # Multi-agent parallel
@pm task &                  # Background
@pm task -> @ba task        # Pipeline

# New Syntax
@pm task $ba               # Reference BA's output
@pm task $ba $writer       # Multiple references
@pm task $ba &             # Background with reference
@pm task $ba -> @reviewer  # Pipeline with reference
```
