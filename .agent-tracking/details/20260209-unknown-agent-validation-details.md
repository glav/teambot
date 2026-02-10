<!-- markdownlint-disable-file -->
# Implementation Details: Unknown Agent ID Validation

**Research Reference**: [.agent-tracking/research/20260209-unknown-agent-validation-research.md](../research/20260209-unknown-agent-validation-research.md)
**Plan Reference**: [.agent-tracking/plans/20260209-unknown-agent-validation-plan.instructions.md](../plans/20260209-unknown-agent-validation-plan.instructions.md)

---

## Task 1.1: Add Agent ID Validation to `TaskExecutor.execute()`

**File**: `src/teambot/tasks/executor.py`
**Location**: Insert after line 176 (the `CommandType.AGENT` check), before line 178 (`command.is_pipeline`)
**Research Reference**: Research doc, Section 3 — Change 1 (Lines 122-171)

### What to Change

Insert a validation block that collects all agent IDs from the command (including pipeline stages), resolves aliases, and checks each against `VALID_AGENTS`. Return an error `ExecutionResult` on the first invalid ID.

### Exact Code to Insert (after line 176, before line 178)

```python
        # Validate all agent IDs before dispatch
        from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS

        all_agent_ids = []
        if command.is_pipeline and command.pipeline:
            for stage in command.pipeline:
                all_agent_ids.extend(stage.agent_ids)
        else:
            all_agent_ids = list(command.agent_ids)

        for agent_id in all_agent_ids:
            canonical = AGENT_ALIASES.get(agent_id, agent_id)
            if canonical not in VALID_AGENTS:
                valid_list = ", ".join(sorted(VALID_AGENTS))
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Unknown agent: '{agent_id}'. Valid agents: {valid_list}",
                )
```

### Pattern Followed

Local import pattern — matches existing usage at line 199:
```python
from teambot.repl.router import VALID_AGENTS
```
Extended to also import `AGENT_ALIASES` for alias resolution.

Error return pattern — matches existing usage at lines 204-208:
```python
return ExecutionResult(success=False, output="", error=f"Unknown agent ref: ...")
```

### Key Decisions

- **Alias resolution**: `AGENT_ALIASES.get(agent_id, agent_id)` — same pattern as `router.resolve_agent_id()` (Research Lines 266-268)
- **Pipeline handling**: Iterates `command.pipeline` stages to collect all agent IDs across all stages
- **Early return**: Returns on first invalid ID — consistent with existing ref validation behavior
- **Error message format**: `Unknown agent: '{original_id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer` — uses original (not canonical) ID in error for user clarity

---

## Task 1.2: Add Agent ID Validation to `TeamBotApp._handle_agent_command()`

**File**: `src/teambot/ui/app.py`
**Location**: Insert after line 147 (the executor-None check), before line 149 (`content = command.content or ""`)
**Research Reference**: Research doc, Section 3 — Change 2 (Lines 172-207)

### What to Change

Insert a validation block at the top of `_handle_agent_command()` that checks all agent IDs before any status updates or streaming begins.

### Exact Code to Insert (after line 147, before line 149)

```python
        # Validate all agent IDs before dispatch
        from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS

        for agent_id in command.agent_ids:
            canonical = AGENT_ALIASES.get(agent_id, agent_id)
            if canonical not in VALID_AGENTS:
                valid_list = ", ".join(sorted(VALID_AGENTS))
                output.write_task_error(
                    agent_id,
                    f"Unknown agent: '{agent_id}'. Valid agents: {valid_list}",
                )
                return
```

### Why This Location

- **Before line 149** (`content = command.content or ""`): ensures no content processing happens
- **Before line 152-158** (multi-agent streaming check): ensures multi-agent commands are validated
- **Before line 164** (`self._agent_status.set_running(...)`): prevents ghost status entries
- **Before line 198** (`sdk_client.execute_streaming(...)`): prevents invalid SDK calls

### Key Decisions

- **Error display**: Uses `output.write_task_error()` — consistent with error display in the same method (line 212, 228, 232)
- **No pipeline handling needed**: Split-pane app routes pipelines through executor (line 213-215), which will have its own validation from Task 1.1
- **Covers multi-agent streaming**: Validation runs before the `_handle_multiagent_streaming()` call at line 158

---

## Task 2.1: Guard `AgentStatusManager` Auto-Creation

**File**: `src/teambot/ui/agent_state.py`
**Locations**: Three methods need guards
**Research Reference**: Research doc, Section 3 — Change 3 (Lines 209-253)

### Change A: Guard `_update()` method (line 184)

**Current code** (lines 184-185):
```python
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
```

**New code**:
```python
        if agent_id not in self._statuses:
            if agent_id not in DEFAULT_AGENTS:
                return
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
```

### Change B: Guard `set_idle()` method (line 159)

**Current code** (lines 159-161):
```python
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
            return
```

**New code**:
```python
        if agent_id not in self._statuses:
            if agent_id not in DEFAULT_AGENTS:
                return
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
            return
```

### Change C: Guard `set_model()` method (line 202)

**Current code** (lines 202-205):
```python
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id, model=model)
            self._notify()
            return
```

**New code**:
```python
        if agent_id not in self._statuses:
            if agent_id not in DEFAULT_AGENTS:
                return
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id, model=model)
            self._notify()
            return
```

### Key Decisions

- **Use `DEFAULT_AGENTS`**: Already defined at line 73, identical to `VALID_AGENTS`. Avoids coupling `agent_state.py` to `router.py`.
- **Silent return**: No error raised — this is defence-in-depth. Primary validation happens in executor/app.
- **Only guards auto-creation**: If an agent_id is already in `_statuses` (e.g., added via `__post_init__`), it is NOT affected. The guard only prevents **new** entries for unknown agents.
- **Does not include aliases**: Correct — aliases should be resolved to canonical IDs before reaching the status manager.

---

## Task 3.1: TaskExecutor Agent Validation Tests

**File**: `tests/test_tasks/test_executor.py`
**Location**: Append new test class after existing classes
**Research Reference**: Research doc, Section 5 — New Tests Required (Lines 361-371)

### New Test Class: `TestTaskExecutorAgentValidation`

```python
class TestTaskExecutorAgentValidation:
    """Tests for unknown agent ID validation in TaskExecutor."""

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_agent(self):
        """Unknown agent ID returns error via executor."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@unknown-agent do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_agent_background(self):
        """Background command with unknown agent returns error."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@fake-agent do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_in_multiagent(self):
        """Multi-agent with invalid ID rejects entire command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,fake-agent do something")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_in_pipeline(self):
        """Pipeline with invalid agent rejects entire pipeline."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@fake-agent Do research -> @pm Create plan")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_accepts_valid_alias(self):
        """Valid alias (project_manager) is accepted."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@project_manager Create a plan &")

        result = await executor.execute(cmd)

        # Should succeed (not rejected as unknown)
        assert result.success or result.background

    @pytest.mark.asyncio
    async def test_execute_accepts_all_valid_agents(self):
        """All 6 canonical agent IDs are accepted (regression guard)."""
        from teambot.repl.router import VALID_AGENTS

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        for agent_id in sorted(VALID_AGENTS):
            executor = TaskExecutor(sdk_client=mock_sdk)
            cmd = parse_command(f"@{agent_id} do work &")
            result = await executor.execute(cmd)
            assert result.error is None or "Unknown agent" not in (result.error or ""), \
                f"Valid agent '{agent_id}' was rejected"

    @pytest.mark.asyncio
    async def test_execute_error_message_lists_valid_agents(self):
        """Error message contains sorted list of all valid agents."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@nobody do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "ba, builder-1, builder-2, pm, reviewer, writer" in result.error
```

### Patterns Used

- `AsyncMock()` for SDK client (matches line 17 pattern in existing tests)
- `parse_command()` to construct commands (matches line 30 pattern)
- `result.success`, `result.error` assertions (matches line 34-35 pattern)
- `mock_sdk.execute.assert_not_called()` to verify no dispatch
- `@pytest.mark.asyncio` for all async tests

---

## Task 3.2: AgentStatusManager Guard Tests

**File**: `tests/test_ui/test_agent_state.py`
**Location**: Append new test class after existing classes
**Research Reference**: Research doc, Section 5 — For AgentStatusManager (Lines 373-381)

### New Test Class: `TestAgentStatusManagerGuard`

```python
class TestAgentStatusManagerGuard:
    """Tests for ghost agent prevention in AgentStatusManager."""

    def test_set_running_ignores_unknown_agent(self):
        """set_running for unknown agent does not create status entry."""
        manager = AgentStatusManager()
        manager.set_running("fake-agent", "some task")
        assert manager.get("fake-agent") is None

    def test_set_idle_ignores_unknown_agent(self):
        """set_idle for unknown agent does not create status entry."""
        manager = AgentStatusManager()
        manager.set_idle("fake-agent")
        assert manager.get("fake-agent") is None

    def test_set_model_ignores_unknown_agent(self):
        """set_model for unknown agent does not create status entry."""
        manager = AgentStatusManager()
        manager.set_model("fake-agent", "gpt-4")
        assert manager.get("fake-agent") is None

    def test_default_agents_still_auto_created(self):
        """Known agents still get auto-created status entries."""
        manager = AgentStatusManager()
        manager.set_running("pm", "plan authentication")
        status = manager.get("pm")
        assert status is not None
        assert status.state == AgentState.RUNNING
```

### Patterns Used

- Direct instantiation of `AgentStatusManager()` (matches line 44 pattern)
- `manager.get()` assertions (matches line 47-54 pattern)
- `AgentState` enum comparisons (matches line 49, 59 pattern)

---

## Task 4.1: Full Suite Validation

### Verification Commands

```bash
# 1. Run all tests
uv run pytest

# 2. Check for lint errors
uv run ruff check .

# 3. Check formatting
uv run ruff format .

# 4. Verify single source of truth (no duplication)
grep -n "VALID_AGENTS" src/teambot/repl/router.py  # Should be the definition
grep -rn "VALID_AGENTS" src/teambot/ --include="*.py" | grep -v "import"  # No other definitions

# 5. Verify error message format in tests
grep -n "Unknown agent:" tests/test_tasks/test_executor.py
```

### Expected Results

- All 943+ existing tests pass
- All 11 new tests pass
- Zero lint errors
- Zero formatting changes needed
- `VALID_AGENTS` defined only in `router.py`
- Error messages match format: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
