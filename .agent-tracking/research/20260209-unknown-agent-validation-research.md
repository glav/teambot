<!-- markdownlint-disable-file -->
# 🔍 Research: Unknown Agent ID Validation

**Date**: 2026-02-09
**Feature Spec**: `.teambot/unknown-agent-validation/artifacts/feature_spec.md`
**Status**: ✅ Complete

---

## 1. Scope & Objectives

### Research Questions

1. Where exactly are the validation gaps for unknown agent IDs?
2. What is the minimal set of code changes to close all gaps?
3. What is the single source of truth for valid agents and how should it be imported?
4. What entry points exist for user commands, and which ones lack validation?
5. What test infrastructure exists and what patterns should new tests follow?

### Assumptions

- The 6-agent set is static: `pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`
- 3 aliases exist: `project_manager` → `pm`, `business_analyst` → `ba`, `technical_writer` → `writer`
- `VALID_AGENTS` in `router.py` is the single source of truth
- This is a targeted bug fix, not an architectural refactor

---

## 2. Entry Point Analysis

### User Input Entry Points

| # | Entry Point | Code Path | Validates Agent? | Implementation Required? |
|---|-------------|-----------|:----------------:|:------------------------:|
| 1 | `@agent task` (simple, sync) | `loop.py:322-335` → `router.route()` → `_route_agent()` | ✅ YES | ❌ NO (already works) |
| 2 | `@agent task &` (background) | `loop.py:324-331` → `_handle_advanced_command()` → `executor.execute()` → `_execute_simple()` | ❌ NO | ✅ YES |
| 3 | `@a,b task` (multi-agent) | `loop.py:324-331` → `_handle_advanced_command()` → `executor.execute()` → `_execute_multiagent()` | ❌ NO | ✅ YES |
| 4 | `@a -> @b task` (pipeline) | `loop.py:324-331` → `_handle_advanced_command()` → `executor.execute()` → `_execute_pipeline()` | ❌ NO | ✅ YES |
| 5 | `@agent $ref task` (with refs) | `loop.py:324-331` → `_handle_advanced_command()` → `executor.execute()` → `_execute_simple()` | ❌ NO (refs validated, agent not) | ✅ YES |
| 6 | Split-pane: `@agent task` (simple streaming) | `app.py:175-211` → direct `sdk_client.execute_streaming()` | ❌ NO | ✅ YES |
| 7 | Split-pane: `@a,b task` (multi-agent streaming) | `app.py:152-158` → `_handle_multiagent_streaming()` | ❌ NO | ✅ YES |
| 8 | Split-pane: complex commands | `app.py:213-228` → `executor.execute()` | ❌ NO | ✅ YES (covered by executor fix) |

### Code Path Traces

#### Entry Point 1: Simple Router Path ✅ (Already Works)

1. User enters: `@unknown-agent do something`
2. `loop.py:316` → `parse_command()` → `Command(type=AGENT, agent_ids=["unknown-agent"])`
3. `loop.py:324` → condition: not pipeline, 1 agent, not background, no refs → **simple path**
4. `loop.py:335` → `self._router.route(command)`
5. `router.py:160-169` → `_route_agent()` → `is_valid_agent("unknown-agent")` → **False** → raises `RouterError`
6. `loop.py:345` → catches `RouterError` → prints error ✅

#### Entry Point 2: Background Command ❌ (Bypasses Validation)

1. User enters: `@unknown-agent do something &`
2. `loop.py:316` → `parse_command()` → `Command(type=AGENT, agent_ids=["unknown-agent"], background=True)`
3. `loop.py:324` → condition: `background=True` → **advanced path**
4. `loop.py:331` → `_handle_advanced_command(command)`
5. `loop.py:136` → `executor.execute(command)`
6. `executor.py:182-183` → `_execute_simple()` → uses `command.agent_ids[0]` directly → **no validation** ❌
7. Task created with unknown agent ID, `AgentStatusManager` auto-creates ghost entry

#### Entry Point 3: Multi-Agent Command ❌ (No Validation)

1. User enters: `@builder-1,fake-agent implement feature`
2. Parsed → `Command(agent_ids=["builder-1", "fake-agent"])`
3. Advanced path → `_execute_multiagent()`
4. `executor.py:308` → iterates `command.agent_ids` → creates tasks for both → **no validation** ❌

#### Entry Point 4: Pipeline Command ❌ (No Validation)

1. User enters: `@fake -> @pm create a plan`
2. Parsed → pipeline with stages
3. Advanced path → `_execute_pipeline()`
4. `executor.py:418` → iterates stages → creates tasks for all agents → **no validation** ❌

#### Entry Point 6: Split-Pane Simple ❌ (No Validation)

1. User enters: `@unknown-agent task` in split-pane UI
2. `app.py:114` → `parse_command()`
3. `app.py:116-118` → all AGENT commands go to `_handle_agent_command()`
4. `app.py:161` → `agent_id = command.agent_id` → used directly
5. `app.py:164` → `self._agent_status.set_running(agent_id, ...)` → **auto-creates ghost** ❌
6. `app.py:198` → `sdk_client.execute_streaming(agent_id, ...)` → **no validation** ❌

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `TaskExecutor.execute()` has no agent validation | Unknown agents silently executed on all advanced paths | Add validation at top of `execute()` |
| `app.py._handle_agent_command()` has no agent validation | Unknown agents executed in split-pane UI | Add validation at top of method |
| `app.py._handle_multiagent_streaming()` has no agent validation | Unknown agents in multi-agent streaming | Covered by validation in `_handle_agent_command()` |
| `AgentStatusManager._update()` auto-creates entries | Ghost agents appear in status window | Add guard in `_update()`, `set_idle()`, `set_model()` |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 3. Technical Approach — Selected

### Approach: Validate at `TaskExecutor.execute()` + `TeamBotApp._handle_agent_command()` + `AgentStatusManager` Guard

**Rationale**: Placing validation at the executor's `execute()` entry point covers all advanced-path commands (background, multi-agent, pipeline, `$ref`) in a single check. The split-pane app (`app.py`) has an independent code path that bypasses the executor for simple streaming, so it also needs a validation check. The `AgentStatusManager` guard is defence-in-depth.

#### Why Not Other Approaches

| Alternative | Why Not Selected |
|-------------|-----------------|
| Validate in parser | Parser handles syntax, not semantics; mixing concerns |
| Validate in `loop.py` before routing | Would duplicate logic already present in router; doesn't cover split-pane app |
| Validate in each `_execute_*` method | Redundant — one check in `execute()` covers all three |
| Validate in `TaskManager.create_task()` | Too deep — error would be hard to surface cleanly to user |

### Implementation Plan

#### Change 1: `TaskExecutor.execute()` — Add Agent ID Validation (executor.py)

**File**: `src/teambot/tasks/executor.py`
**Location**: Lines 162-183 (top of `execute()` method)
**What**: After the `CommandType.AGENT` check and before routing to sub-methods, validate all agent IDs.

```python
async def execute(self, command: Command) -> ExecutionResult:
    if command.type != CommandType.AGENT:
        return ExecutionResult(
            success=False, output="", error="Not an agent command",
        )

    # --- NEW: Validate all agent IDs before dispatch ---
    from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS

    all_agent_ids = []
    if command.is_pipeline and command.pipeline:
        for stage in command.pipeline:
            all_agent_ids.extend(stage.agent_ids)
    else:
        all_agent_ids = command.agent_ids

    for agent_id in all_agent_ids:
        canonical = AGENT_ALIASES.get(agent_id, agent_id)
        if canonical not in VALID_AGENTS:
            valid_list = ", ".join(sorted(VALID_AGENTS))
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unknown agent: '{agent_id}'. Valid agents: {valid_list}",
            )
    # --- END NEW ---

    if command.is_pipeline:
        return await self._execute_pipeline(command)
    elif len(command.agent_ids) > 1:
        return await self._execute_multiagent(command)
    else:
        return await self._execute_simple(command)
```

**Key Details**:
- Uses existing local-import pattern (already used at line 199 for `$ref` validation)
- Resolves aliases before checking — `@project_manager` works
- Collects agent IDs from pipeline stages when applicable
- Returns `ExecutionResult(success=False)` — consistent with existing error pattern
- Error message format: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
- No circular import risk: `executor.py` already imports from `router.py` locally

#### Change 2: `TeamBotApp._handle_agent_command()` — Add Validation (app.py)

**File**: `src/teambot/ui/app.py`
**Location**: Lines 143-237 (`_handle_agent_command()` method)
**What**: Add agent ID validation at the top of the method, before any status updates or streaming.

```python
async def _handle_agent_command(self, command, output):
    """Route agent command to executor and display streaming result."""
    if not self._executor:
        output.write_info("No executor available")
        return

    # --- NEW: Validate all agent IDs ---
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
    # --- END NEW ---

    content = command.content or ""
    # ... rest of method unchanged
```

**Key Details**:
- Catches unknown agents before `_handle_multiagent_streaming()` is called
- Catches unknown agents before direct SDK streaming path
- Uses `output.write_task_error()` for consistent error display in split-pane UI
- Same alias resolution and error format as executor

#### Change 3: `AgentStatusManager` — Guard Against Ghost Entries (agent_state.py)

**File**: `src/teambot/ui/agent_state.py`
**Location**: Lines 153-210 (`set_idle()`, `_update()`, `set_model()`)
**What**: Guard auto-creation to only allow known agent IDs.

```python
# Add import at module level (no circular import risk — agent_state.py has no repl imports)
# Actually, to avoid coupling agent_state to router, use the existing DEFAULT_AGENTS list
# which is already defined at line 73

def _update(self, agent_id: str, state: AgentState, task: str | None) -> None:
    if agent_id not in self._statuses:
        # Only auto-create for known default agents
        if agent_id not in DEFAULT_AGENTS:
            return  # Silently ignore unknown agents
        self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
    # ... rest unchanged

def set_idle(self, agent_id: str) -> None:
    if agent_id not in self._statuses:
        if agent_id not in DEFAULT_AGENTS:
            return  # Silently ignore unknown agents
        self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
        return
    # ... rest unchanged

def set_model(self, agent_id: str, model: str | None) -> None:
    if agent_id not in self._statuses:
        if agent_id not in DEFAULT_AGENTS:
            return  # Silently ignore unknown agents
        self._statuses[agent_id] = AgentStatus(agent_id=agent_id, model=model)
        self._notify()
        return
    # ... rest unchanged
```

**Design Decision**: Use `DEFAULT_AGENTS` (already defined in `agent_state.py` at line 73) rather than importing `VALID_AGENTS` from `router.py`. Reasons:
1. `DEFAULT_AGENTS` is identical in content to `VALID_AGENTS` — both list the same 6 agents
2. Avoids coupling `agent_state.py` → `router.py` (currently no such import exists)
3. Defence-in-depth — primary validation is in the executor; this just prevents auto-creation
4. If agents are ever dynamic, both constants would need updating anyway

**⚠️ Note**: `DEFAULT_AGENTS` does not include aliases. But aliases should already be resolved to canonical IDs by the time status updates are called (the executor and app handle resolution). This is correct because status entries should always use canonical IDs.

---

## 4. Code Patterns & References

### Existing Validation Pattern — Router (router.py:55-76)

```python
# src/teambot/repl/router.py — lines 55-76
def is_valid_agent(self, agent_id: str) -> bool:
    canonical = self.resolve_agent_id(agent_id)
    return canonical in VALID_AGENTS

def resolve_agent_id(self, agent_id: str) -> str:
    return AGENT_ALIASES.get(agent_id, agent_id)
```
✅ We replicate this inline using the same `AGENT_ALIASES.get(agent_id, agent_id)` pattern.

### Existing Local Import Pattern — Executor (executor.py:198-199)

```python
# src/teambot/tasks/executor.py — lines 198-199
if command.references:
    from teambot.repl.router import VALID_AGENTS
    invalid_refs = [ref for ref in command.references if ref not in VALID_AGENTS]
```
✅ Our new validation uses the same local import pattern, extended to also import `AGENT_ALIASES`.

### Existing Error Return Pattern — Executor (executor.py:204-208)

```python
# src/teambot/tasks/executor.py — lines 204-208
return ExecutionResult(
    success=False,
    output="",
    error=f"Unknown agent ref: ${invalid_refs[0]}. Valid: {valid_list}",
)
```
✅ Our new validation returns an `ExecutionResult` in the same style.

### Existing Auto-Creation Pattern — AgentStatusManager (agent_state.py:184-185)

```python
# src/teambot/ui/agent_state.py — lines 184-185
if agent_id not in self._statuses:
    self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
```
🔧 We add a guard: `if agent_id not in DEFAULT_AGENTS: return` before auto-creation.

### Router Error Handling in Loop (loop.py:345-346)

```python
# src/teambot/repl/loop.py — lines 345-346
except RouterError as e:
    self._console.print(f"[red]Error: {e}[/red]")
```
ℹ️ The simple path already catches `RouterError`. The advanced path returns `ExecutionResult` with `success=False`, which is handled at `loop.py:144-145`.

---

## 5. Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Detail |
|--------|--------|
| **Framework** | pytest 7.x with `pytest-asyncio`, `pytest-mock`, `pytest-cov` |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` files, `Test*` classes, `test_*` methods |
| **Runner** | `uv run pytest` |
| **Coverage** | ~80% (943 tests as of recent runs) |
| **Async** | `@pytest.mark.asyncio` decorator for async tests |
| **Mocking** | `unittest.mock.AsyncMock` for SDK clients |

### Representative Test Patterns

#### Executor Tests (`tests/test_tasks/test_executor.py`)

```python
# Pattern: Create mock SDK, create executor, parse command, execute, assert
@pytest.mark.asyncio
async def test_execute_simple_command(self):
    mock_sdk = AsyncMock()
    mock_sdk.execute = AsyncMock(return_value="Task completed")
    executor = TaskExecutor(sdk_client=mock_sdk)
    cmd = parse_command("@pm Create a plan")
    result = await executor.execute(cmd)
    assert result.success
    assert "Task completed" in result.output
```

#### Agent State Tests (`tests/test_ui/test_agent_state.py`)

```python
# Pattern: Create manager, call method, assert state
def test_get_returns_none_for_unknown_agent(self):
    manager = AgentStatusManager()
    assert manager.get("unknown-agent") is None

def test_set_running_updates_state(self):
    manager = AgentStatusManager()
    manager.set_running("pm", "plan authentication")
    status = manager.get("pm")
    assert status.state == AgentState.RUNNING
```

### New Tests Required

#### For TaskExecutor (in `tests/test_tasks/test_executor.py`)

| Test | Description |
|------|-------------|
| `test_execute_rejects_unknown_agent` | `@unknown task` returns error via executor |
| `test_execute_rejects_unknown_agent_background` | `@unknown task &` returns error |
| `test_execute_rejects_unknown_in_multiagent` | `@pm,unknown task` rejects entire command |
| `test_execute_rejects_unknown_in_pipeline` | `@unknown -> @pm task` rejects entire pipeline |
| `test_execute_accepts_valid_alias` | `@project_manager task` succeeds |
| `test_execute_accepts_all_valid_agents` | All 6 agents accepted |
| `test_execute_error_message_format` | Error matches expected format |

#### For AgentStatusManager (in `tests/test_ui/test_agent_state.py`)

| Test | Description |
|------|-------------|
| `test_update_ignores_unknown_agent` | `set_running("fake", ...)` does not create entry |
| `test_set_idle_ignores_unknown_agent` | `set_idle("fake")` does not create entry |
| `test_set_model_ignores_unknown_agent` | `set_model("fake", "gpt-4")` does not create entry |
| `test_default_agents_still_auto_created` | `set_running("pm", ...)` still works |

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `TaskExecutor.execute()` validation | Code-First | Clear requirements, simple validation logic, add tests after |
| `AgentStatusManager` guard | Code-First | Straightforward guard pattern, add tests after |
| `app.py` validation | Code-First | Mirrors executor pattern, covered by executor tests conceptually |

---

## 6. Risk Analysis

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **Circular import** when executor imports from router | Medium | Low | Already mitigated: executor.py uses local imports at lines 199/398 |
| **DEFAULT_AGENTS out of sync with VALID_AGENTS** | Low | Very Low | Both are hardcoded sets of the same 6 agents; both live in well-known locations |
| **Split-pane app diverges from loop.py** | Medium | Medium | Explicitly add validation to `app.py._handle_agent_command()` |
| **Aliases not resolved before status update** | Low | Low | Executor resolves aliases during validation; status manager receives canonical IDs |
| **Breaking existing tests** | Medium | Low | Changes are additive guards; existing valid-agent paths unchanged |

---

## 7. File Change Summary

| File | Change Type | Lines Affected | Description |
|------|-------------|----------------|-------------|
| `src/teambot/tasks/executor.py` | **Modify** | ~162-183 | Add agent ID validation in `execute()` |
| `src/teambot/ui/app.py` | **Modify** | ~143-150 | Add agent ID validation in `_handle_agent_command()` |
| `src/teambot/ui/agent_state.py` | **Modify** | ~153-161, ~176-185, ~195-205 | Guard auto-creation in `set_idle()`, `_update()`, `set_model()` |
| `tests/test_tasks/test_executor.py` | **Modify** | New tests added | 7 new tests for agent validation |
| `tests/test_ui/test_agent_state.py` | **Modify** | New tests added | 4 new tests for ghost agent prevention |

**Total estimated change**: ~60 lines of new code + ~50 lines of new tests

---

## 8. Task Implementation Requests

### Task 1: Add Agent ID Validation to TaskExecutor.execute()

- **File**: `src/teambot/tasks/executor.py`
- **What**: Add validation block at top of `execute()` that checks all agent IDs (including pipeline stages) against `VALID_AGENTS` with alias resolution
- **Error format**: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
- **Pattern**: Follow existing local-import pattern at line 199
- **Priority**: P0

### Task 2: Add Agent ID Validation to TeamBotApp._handle_agent_command()

- **File**: `src/teambot/ui/app.py`
- **What**: Add validation at top of `_handle_agent_command()` before any status updates or streaming
- **Error display**: Use `output.write_task_error()` for consistent UI
- **Priority**: P0

### Task 3: Guard AgentStatusManager Auto-Creation

- **File**: `src/teambot/ui/agent_state.py`
- **What**: Add `if agent_id not in DEFAULT_AGENTS: return` guard before auto-creation in `_update()`, `set_idle()`, `set_model()`
- **Priority**: P1

### Task 4: Add Tests for Agent Validation

- **Files**: `tests/test_tasks/test_executor.py`, `tests/test_ui/test_agent_state.py`
- **What**: ~11 new test cases covering all validation paths
- **Priority**: P1

---

## 9. Potential Next Research

*No remaining research tasks. All technical questions are answered and a single approach is selected.*
