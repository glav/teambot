<!-- markdownlint-disable-file -->
# 🔍 Research: Fix Runtime Validator Error-Scenario Detection & Complete Agent Validation

**Date**: 2026-02-10
**Feature Spec**: `.teambot/runtime-validator-agent/artifacts/feature_spec.md`
**Status**: ✅ Complete

---

## 1. Scope & Objectives

### Research Questions

1. What is the actual root cause of AT-001, AT-002, AT-007 runtime failures?
2. Is `_is_expected_error_scenario()` keyword matching affected by backtick formatting?
3. Are core validation guards (TaskExecutor, App, AgentStatusManager) complete?
4. What remaining issues prevent 7/7 runtime acceptance test scenarios from passing?
5. What is the correct fix with minimal code changes?

### Assumptions

- The 6-agent set is static: `pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`
- 3 aliases exist: `project_manager` → `pm`, `business_analyst` → `ba`, `technical_writer` → `writer`
- `VALID_AGENTS` in `router.py` (line 20) is the single source of truth
- This is a targeted bug fix, not an architectural refactor
- AT-004 (pipeline content) and AT-006 (output matching) are out-of-scope per the feature spec

### Success Criteria

- ✅ Root cause for AT-001/AT-002/AT-007 failures identified and confirmed
- ✅ Core validation guards verified as complete
- ✅ Remaining runtime issues identified with fix recommendations
- ✅ Testing strategy documented
- ✅ Single recommended approach selected

---

## 2. Entry Point Analysis

### User Input Entry Points

| # | Entry Point | Code Path | Validates Agent? | Implementation Status |
|---|-------------|-----------|:----------------:|:---------------------:|
| 1 | `@agent task` (simple, sync) | `loop.py` → `router.route()` → `_route_agent()` | ✅ YES | ✅ Already works |
| 2 | `@agent task &` (background) | `loop.py` → `executor.execute()` | ✅ YES | ✅ Implemented (executor.py:178-196) |
| 3 | `@a,b task` (multi-agent) | `loop.py` → `executor.execute()` | ✅ YES | ✅ Implemented (executor.py:178-196) |
| 4 | `@a -> @b task` (pipeline) | `loop.py` → `executor.execute()` | ✅ YES | ✅ Implemented (executor.py:178-196) |
| 5 | `@agent $ref task` (refs) | `loop.py` → `executor.execute()` | ✅ YES | ✅ Implemented (executor.py:178-196) |
| 6 | Split-pane: `@agent task` | `app.py` → `_handle_agent_command()` | ✅ YES | ✅ Implemented (app.py:149-160) |
| 7 | Split-pane: `@a,b task` | `app.py` → `_handle_agent_command()` | ✅ YES | ✅ Implemented (app.py:149-160) |
| 8 | Split-pane: complex | `app.py` → `executor.execute()` | ✅ YES | ✅ Covered by executor fix |

### Code Path Traces

#### Entry Point 1: Simple Router Path ✅ (Already Works — No Changes Needed)

1. User enters: `@unknown-agent do something`
2. `loop.py` → `parse_command()` → `Command(type=AGENT, agent_ids=["unknown-agent"])`
3. Simple path condition → `self._router.route(command)`
4. `router.py:160-169` → `_route_agent()` → `is_valid_agent("unknown-agent")` → **False** → raises `RouterError`
5. `loop.py` catches `RouterError` → prints error ✅

#### Entry Point 2: Background Command ✅ (Fixed in Current Branch)

1. User enters: `@unknown-agent do something &`
2. `parse_command()` → `Command(agent_ids=["unknown-agent"], background=True)`
3. Advanced path → `executor.execute(command)`
4. `executor.py:178-196` → validates agent IDs → `"unknown-agent"` not in `VALID_AGENTS` → returns `ExecutionResult(success=False)` ✅

#### Entry Point 3: Multi-Agent Command ✅ (Fixed)

1. User enters: `@builder-1,fake-agent implement feature`
2. Parsed → `Command(agent_ids=["builder-1", "fake-agent"])`
3. Advanced path → `executor.execute()`
4. `executor.py:188-196` → iterates all IDs → `"fake-agent"` not in `VALID_AGENTS` → rejects entire command ✅

#### Entry Point 4: Pipeline Command ✅ (Fixed)

1. User enters: `@fake -> @pm create a plan`
2. Advanced path → `executor.execute()`
3. `executor.py:182-184` → collects IDs from pipeline stages → `"fake"` not in `VALID_AGENTS` → rejects ✅

#### Entry Point 6: Split-Pane App ✅ (Fixed)

1. User enters: `@unknown-agent task` in split-pane UI
2. `app.py:143` → `_handle_agent_command()`
3. `app.py:149-160` → validates against `VALID_AGENTS` → `output.write_task_error()` → returns ✅

### Coverage Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] All coverage gaps have been closed by existing implementation

---

## 3. Root Cause Analysis

### 🔑 Critical Finding: Original Root Cause Was NOT Backtick Interference

The hypothesis in the objective and feature spec states that backtick formatting in `expected_result` text interferes with keyword matching in `_is_expected_error_scenario()`. **This is incorrect.**

#### Evidence — Backtick Matching Works Correctly

Tested the actual parsing chain against the real feature spec:

```python
# Extracted from real spec via _extract_field():
expected_at001 = "Error message: `Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`"
expected_at001.lower()  # → "error message: `unknown agent: ..." 
"error message" in expected_at001.lower()  # → True ✅
```

All 7 scenarios were tested — `_is_expected_error_scenario()` correctly returns `True` for AT-001, AT-002, AT-003, AT-004, AT-007 and `False` for AT-005, AT-006.

#### Actual Root Cause: Missing `_is_expected_error_scenario()` Integration

The **real** root cause was that the runtime validation execution loop (`_execute_runtime_validation()`) did not consult `_is_expected_error_scenario()` **at all** when commands failed. The original code on the `main` branch:

```python
# BEFORE fix (on main branch):
if result.success:
    outputs[cmd.agent_ids[0]] = result.output
else:
    # ALL failures treated as test failures — no expected-error check!
    all_commands_succeeded = False
    runtime_scenario.failure_reason = f"Command '{cmd_str}' failed: {result.error}"
    break
```

**The `_is_expected_error_scenario()` method itself did not exist on `main`** — it was added along with the loop integration in commit `d12c766`.

#### Current State (After Commit `d12c766`)

The fix adds:
1. `_is_expected_error_scenario()` static method at line 517-542
2. Error-check branching in the execution loop at lines 383-410
3. `expected_error_produced` flag tracking

```python
# AFTER fix (current branch):
else:
    error_msg = result.error or "Execution failed"
    if self._is_expected_error_scenario(scenario.expected_result):
        expected_error_produced = True  # Error IS the expected result
        outputs[cmd.agent_ids[0]] = error_msg
    else:
        all_commands_succeeded = False
        runtime_scenario.failure_reason = ...
```

**Result**: AT-001 ✅, AT-002 ✅, AT-004 ✅, AT-007 ✅ now pass runtime validation.

### Recommended Defense-in-Depth: Strip Backticks

While backticks don't currently interfere, adding backtick stripping in `_is_expected_error_scenario()` is a good defense-in-depth measure for future spec authors who might format expected results differently:

```python
@staticmethod
def _is_expected_error_scenario(expected_result: str) -> bool:
    if not expected_result:
        return False
    # Strip backticks for robust matching regardless of markdown formatting
    lower = expected_result.replace("`", "").lower().strip()
    error_indicators = [...]
    return any(indicator in lower for indicator in error_indicators)
```

**Impact**: 1 line change. No risk — backtick removal is safe for all indicator keywords.

---

## 4. Remaining Runtime Validation Issues

### Issue 1: `extract_commands_from_steps()` Regex — AT-003 and AT-005 ❌

**File**: `src/teambot/orchestration/acceptance_test_executor.py` (line 153)

**Current regex**:
```python
command_pattern = r"`(@[a-zA-Z][a-zA-Z0-9-]*\s+[^`]+)`"
```

**Problem**: The character class `[a-zA-Z0-9-]` does not include:
- `,` (commas) — needed for multi-agent syntax: `@builder-1,fake-agent`
- `_` (underscores) — needed for aliases: `@project_manager`

**Evidence**:
```
AT-003 step: "User enters: `@builder-1,fake-agent implement the feature`"
→ regex matches: [] (empty — comma breaks match)

AT-005 step: "User enters: `@project_manager create a project plan`"
→ regex matches: [] (empty — underscore breaks match)
```

**Fix**: Broaden the agent-name character class to match any non-whitespace character before the first space:

```python
command_pattern = r"`(@[a-zA-Z][^\s`]*\s+[^`]+)`"
```

**Verified**: This regex correctly matches ALL 7 scenario commands:
| Scenario | Step Command | Matches? |
|----------|-------------|:--------:|
| AT-001 | `@unknown-agent do something` | ✅ |
| AT-002 | `@unknown-agent do something &` | ✅ |
| AT-003 | `@builder-1,fake-agent implement the feature` | ✅ (was ❌) |
| AT-004 | `@fake -> @pm create a plan` | ✅ |
| AT-005 | `@project_manager create a project plan` | ✅ (was ❌) |
| AT-006 | `@pm plan this` (6 commands) | ✅ |
| AT-007 | `@buidler-1 implement login` | ✅ |

**Impact**: AT-003 will now extract the command and execute it via `TaskExecutor`, which will correctly reject `fake-agent` as unknown. AT-005 will extract the alias command and execute it successfully.

### Issue 2: AT-006 Output Matching Limitation

**Scenario**: AT-006 expects "All 6 commands are accepted and dispatched to the correct agent" but mock SDK returns generic text.

**Root cause**: `_verify_expected_output()` (line 478-515) extracts key terms from the expected result and checks if ≥30% appear in the actual output. With a mock SDK returning generic text, the key terms (`commands`, `accepted`, `dispatched`, `correct`) aren't present.

**Recommendation**: This is **out of scope** per the feature spec (Section 4: Out of Scope). The AT-006 scenario tests "all 6 agents work" which requires real SDK execution. Options:
1. **Skip AT-006 runtime validation** with documented rationale (recommended — simplest, matches scope)
2. Mock SDK responses to include expected keywords (fragile)
3. Accept AT-006 failure as known limitation

### Issue 3: AT-004 May Still Fail After Regex Fix

**Scenario**: AT-004 `@fake -> @pm create a plan` — the command extracts correctly but the parser may not handle the pipeline syntax properly when used in the acceptance test executor's context. Current test shows it passes (the executor catches the exception and treats it as an expected error).

**Current status**: ✅ AT-004 passes runtime validation.

---

## 5. Core Validation Guards — Verification

### TaskExecutor.execute() ✅ VERIFIED COMPLETE

**File**: `src/teambot/tasks/executor.py` (lines 178-196)

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
            success=False, output="",
            error=f"Unknown agent: '{agent_id}'. Valid agents: {valid_list}",
        )
```

**Coverage**:
- ✅ Simple commands (`@unknown task`)
- ✅ Background commands (`@unknown task &`)
- ✅ Multi-agent (`@a,unknown task`)
- ✅ Pipeline (`@unknown -> @pm task`)
- ✅ Alias resolution (`@project_manager` → `pm` → accepted)

**Tests**: 47 tests in `tests/test_tasks/test_executor.py` pass, including specific unknown agent rejection tests.

### TeamBotApp._handle_agent_command() ✅ VERIFIED COMPLETE

**File**: `src/teambot/ui/app.py` (lines 149-160)

```python
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

**Coverage**:
- ✅ All agent commands in split-pane UI
- ✅ Catches unknown agents before `_handle_multiagent_streaming()`
- ✅ Catches unknown agents before direct SDK streaming path

### AgentStatusManager Guards ✅ VERIFIED COMPLETE

**File**: `src/teambot/ui/agent_state.py`

| Method | Lines | Guard |
|--------|-------|-------|
| `set_idle()` | 159-161 | `if agent_id not in DEFAULT_AGENTS: return` |
| `_update()` | 187-188 | `if agent_id not in DEFAULT_AGENTS: return` |
| `set_model()` | 207-208 | `if agent_id not in DEFAULT_AGENTS: return` |

Uses `DEFAULT_AGENTS` (line 73) instead of `VALID_AGENTS` to avoid coupling `agent_state.py` → `router.py`. Both lists contain the same 6 agents.

**Tests**: 30 tests in `tests/test_ui/test_agent_state.py` pass, including unknown agent guard tests.

---

## 6. Code Patterns & References

### Error Indicator Keywords (acceptance_test_executor.py:534-541)

```python
error_indicators = [
    "error message",
    "error identifying",
    "error listing",
    "rejected",
    "rejects",
    "unknown agent",
]
```

| Scenario | Expected Result Text | Matching Indicator |
|----------|---------------------|-------------------|
| AT-001 | "Error message: `Unknown agent: ...`" | `"error message"` ✅ |
| AT-002 | "Error message listing valid agents..." | `"error message"` ✅ |
| AT-003 | "Error message identifying 'fake-agent'..." | `"error message"` ✅ |
| AT-004 | "Error message identifying 'fake'..." | `"error message"` ✅ |
| AT-005 | "Command is accepted and routed..." | None → `False` ✅ |
| AT-006 | "All 6 commands are accepted..." | None → `False` ✅ |
| AT-007 | "Error message: `Unknown agent: ...`" | `"error message"` ✅ |

### Local Import Pattern (executor.py:179)

```python
# Inside execute() method — avoids circular import
from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS
```

Same pattern used for reference validation at executor.py line 217.

### Consistent Error Message Format

All validation paths use the same format:
```
Unknown agent: '{agent_id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer
```

Verified in: `executor.py:195`, `app.py:158`, `router.py:170` (via `RouterError`).

---

## 7. Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Detail |
|--------|--------|
| **Framework** | pytest with `pytest-asyncio`, `pytest-mock`, `pytest-cov` |
| **Location** | `tests/` directory |
| **Naming** | `test_*.py` files, `Test*` classes, `test_*` methods |
| **Runner** | `uv run pytest` |
| **Coverage** | 80% (1074 tests as of current branch) |
| **Async** | `asyncio_mode = "auto"` in `pyproject.toml` |
| **Config** | `pyproject.toml:42-48` |

### Existing Test Coverage for This Feature

| Test File | Tests | Scope |
|-----------|:-----:|-------|
| `tests/test_orchestration/test_acceptance_test_executor.py` | 25 | `_is_expected_error_scenario()`, parsing, runtime validation |
| `tests/test_acceptance_unknown_agent.py` | 24 | Full acceptance scenarios AT-001 through AT-007 |
| `tests/test_acceptance_validation.py` | 47 | Acceptance validation for startup animation + unknown agent |
| `tests/test_tasks/test_executor.py` | 47 | TaskExecutor including unknown agent rejection |
| `tests/test_ui/test_agent_state.py` | 30 | AgentStatusManager including unknown agent guards |

### Tests Already Covering `_is_expected_error_scenario()`

**File**: `tests/test_orchestration/test_acceptance_test_executor.py` (lines 458-480)

```python
def test_is_expected_error_scenario_detects_error_messages(self):
    executor = AcceptanceTestExecutor(spec_content="")
    assert executor._is_expected_error_scenario(
        "Error message: `Unknown agent: 'unknown-agent'`"
    )
    assert executor._is_expected_error_scenario(
        "Error message listing valid agents; no background task spawned"
    )
    assert executor._is_expected_error_scenario(
        "Error message identifying 'fake' as unknown; no pipeline stages execute"
    )

def test_is_expected_error_scenario_rejects_normal(self):
    executor = AcceptanceTestExecutor(spec_content="")
    assert not executor._is_expected_error_scenario("PM agent responds with output")
    assert not executor._is_expected_error_scenario(
        "All 6 commands are accepted and dispatched to the correct agent"
    )
    assert not executor._is_expected_error_scenario("")
```

### Additional Tests Recommended

| Test | Description | Priority |
|------|-------------|:--------:|
| `test_is_expected_error_scenario_backtick_only` | Text with ONLY backtick-wrapped content and no plain "error message" prefix | P1 |
| `test_extract_commands_multiagent` | `@builder-1,fake-agent implement feature` extracted correctly | P0 |
| `test_extract_commands_underscore_alias` | `@project_manager create plan` extracted correctly | P0 |
| `test_extract_commands_pipeline` | `@fake -> @pm create plan` extracted correctly | P1 |
| `test_runtime_validation_multiagent_expected_error` | AT-003 passes runtime with fixed regex | P0 |
| `test_runtime_validation_alias_command` | AT-005 passes runtime with fixed regex | P0 |

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `extract_commands_from_steps()` regex fix | Code-First | Clear regex fix, add tests after |
| Backtick stripping defense-in-depth | Code-First | Single line change, low risk |
| New `_is_expected_error_scenario()` edge cases | Code-First | Extend existing test class |

---

## 8. Recommended Implementation — Selected Approach

### Change 1: Fix `extract_commands_from_steps()` Regex (P0)

**File**: `src/teambot/orchestration/acceptance_test_executor.py` (line 153)

**Before**:
```python
command_pattern = r"`(@[a-zA-Z][a-zA-Z0-9-]*\s+[^`]+)`"
```

**After**:
```python
command_pattern = r"`(@[a-zA-Z][^\s`]*\s+[^`]+)`"
```

**Rationale**: The character class `[^\s`]` matches any character that isn't whitespace or a backtick, which naturally supports hyphens, underscores, commas, and any future special syntax. This is simpler and more robust than enumerating allowed characters.

**Impact**: Fixes AT-003 (multi-agent) and AT-005 (alias) command extraction. 1 line change.

### Change 2: Add Backtick Stripping in `_is_expected_error_scenario()` (P1 — Defense-in-Depth)

**File**: `src/teambot/orchestration/acceptance_test_executor.py` (line 533)

**Before**:
```python
lower = expected_result.lower().strip()
```

**After**:
```python
lower = expected_result.replace("`", "").lower().strip()
```

**Rationale**: While backticks don't currently cause failures, future spec authors might write expected results where backticks could separate keywords (e.g., `` `error` `message` `` instead of `error message`). This 1-character-position change makes the method robust.

**Impact**: 1 line change. No behavioral change for current inputs.

### Change 3: Add Tests for Regex Fix and Edge Cases (P1)

**File**: `tests/test_orchestration/test_acceptance_test_executor.py`

Add tests for:
1. `extract_commands_from_steps()` with multi-agent syntax
2. `extract_commands_from_steps()` with underscore aliases
3. `_is_expected_error_scenario()` with backtick-only text

### Why Not Other Approaches

| Alternative | Why Not Selected |
|-------------|-----------------|
| Enumerate specific chars in regex (`,_@`) | Brittle — breaks again if new syntax added |
| Change `_extract_field()` to strip backticks | Upstream change affects all field extraction, not just error detection |
| Add new error indicators | Problem is command extraction, not error detection |
| Skip all runtime validation | Loses end-to-end confidence that the feature works |

---

## 9. Risk Analysis

| Risk | Severity | Likelihood | Mitigation |
|------|:--------:|:----------:|------------|
| Broadened regex matches non-command text in backticks | Low | Low | Regex still requires `@` prefix + space + content; unlikely to match prose |
| Backtick stripping changes keyword matching | Low | Very Low | All current indicators are plain words; removing backticks only helps |
| AT-006 still fails after fix | Low | High | Out of scope per spec; document as known limitation |
| Regex change affects other feature specs | Low | Low | Pattern still starts with `@` and requires space before content |

---

## 10. File Change Summary

| File | Change Type | Lines Affected | Description |
|------|:-----------:|:--------------:|-------------|
| `src/teambot/orchestration/acceptance_test_executor.py` | Modify | Line 153 | Fix command extraction regex |
| `src/teambot/orchestration/acceptance_test_executor.py` | Modify | Line 533 | Add backtick stripping (defense-in-depth) |
| `tests/test_orchestration/test_acceptance_test_executor.py` | Modify | New tests | Tests for regex fix + edge cases |

**Total estimated change**: ~3 lines of production code + ~30 lines of new tests

---

## 11. Task Implementation Requests

### Task 1: Fix Command Extraction Regex (P0)

- **File**: `src/teambot/orchestration/acceptance_test_executor.py` (line 153)
- **What**: Change `[a-zA-Z0-9-]*` to `[^\s\`]*` in `extract_commands_from_steps()` to support multi-agent commas and underscore aliases
- **Impact**: Fixes AT-003 and AT-005 runtime extraction
- **Risk**: Low — regex still requires `@` prefix + whitespace + content

### Task 2: Add Backtick Stripping Defense-in-Depth (P1)

- **File**: `src/teambot/orchestration/acceptance_test_executor.py` (line 533)
- **What**: Add `.replace("\`", "")` before `.lower().strip()` in `_is_expected_error_scenario()`
- **Impact**: Robustness for future spec formatting variations
- **Risk**: None — removing backticks is safe for all indicator keywords

### Task 3: Add Unit Tests for Regex Fix and Edge Cases (P1)

- **File**: `tests/test_orchestration/test_acceptance_test_executor.py`
- **What**: Test `extract_commands_from_steps()` with multi-agent, underscore, and pipeline syntax; test `_is_expected_error_scenario()` with edge cases
- **Tests**: ~5 new test methods

### Task 4: Verify Runtime Validation Results (P0)

- **What**: Run runtime validation after fixes and confirm AT-001 through AT-005 and AT-007 pass (6/7); document AT-006 skip rationale
- **Expected**: 6/7 pass, AT-006 known limitation (mock SDK output matching)

---

## 12. Potential Next Research

*No remaining research tasks. All technical questions have been answered:*

- ✅ Root cause confirmed: missing `_is_expected_error_scenario()` integration (now fixed)
- ✅ Backtick interference disproven — not the actual cause, but defense-in-depth added
- ✅ Core validation guards verified complete across all entry points
- ✅ Remaining issues are command extraction regex (fix identified) and AT-006 mock limitation (out of scope)
- ✅ Single recommended approach selected with evidence
