# Implementation Plan: SDK Streaming for Long-Running Tasks

**Date**: 2026-01-28
**Feature Spec**: docs/feature-specs/sdk-streaming-long-tasks.md
**Test Strategy**: .agent-tracking/test-strategies/20260128-sdk-streaming-long-tasks-strategy.md
**Research**: .agent-tracking/research/20260128-sdk-streaming-long-tasks-research.md

---

## Overview

Replace the blocking `send_and_wait()` pattern with event-driven streaming to eliminate the 120-second timeout limit for long-running agent tasks.

**Approach**: TDD - Write tests first, then implement to pass tests.

---

## Implementation Phases

### Phase 1: TDD Tests for SDK Client (Write First)
**Goal**: Create failing tests that define streaming behavior

| Task | File | Description |
|------|------|-------------|
| 1.1 | `tests/conftest.py` | Add `mock_streaming_session` fixture |
| 1.2 | `tests/conftest.py` | Add `fire_event()` helper function |
| 1.3 | `tests/test_copilot/test_sdk_streaming.py` | Create test file with 11 TDD tests |

**Tests to Write**:
- `test_execute_streaming_receives_delta_events`
- `test_execute_streaming_completes_on_session_idle`
- `test_execute_streaming_handles_session_error`
- `test_execute_streaming_accumulates_content`
- `test_execute_streaming_unsubscribes_on_complete`
- `test_execute_streaming_unsubscribes_on_error`
- `test_execute_streaming_filters_empty_deltas`
- `test_backward_compatible_execute`
- `test_cancel_current_request_calls_abort`
- `test_cancel_returns_true_on_success`
- `test_cancel_returns_false_no_session`

**Validation**: Run tests → all 11 should FAIL (no implementation yet)

---

### Phase 2: Implement SDK Client Streaming
**Goal**: Make all TDD tests pass

| Task | File | Description |
|------|------|-------------|
| 2.1 | `src/teambot/copilot/sdk_client.py` | Add `execute_streaming()` method |
| 2.2 | `src/teambot/copilot/sdk_client.py` | Add `cancel_current_request()` method |
| 2.3 | `src/teambot/copilot/sdk_client.py` | Update `execute()` to use streaming internally |

**Implementation Details**:

```python
# execute_streaming signature
async def execute_streaming(
    self,
    agent_id: str,
    prompt: str,
    on_chunk: Callable[[str], None],
) -> str:
    """Execute with streaming output callbacks."""

# cancel_current_request signature  
async def cancel_current_request(self, agent_id: str) -> bool:
    """Cancel active request for agent using session.abort()."""
```

**Validation**: Run tests → all 11 should PASS

---

### Phase 3: UI Integration - OutputPane Streaming
**Goal**: Display streaming chunks in real-time

| Task | File | Description |
|------|------|-------------|
| 3.1 | `src/teambot/ui/widgets/output_pane.py` | Add `write_streaming_chunk()` method |
| 3.2 | `src/teambot/ui/widgets/output_pane.py` | Add `finish_streaming()` method |
| 3.3 | `src/teambot/ui/widgets/output_pane.py` | Add `_streaming_buffers` dict for state |
| 3.4 | `tests/test_ui/test_output_pane.py` | Add streaming display tests |

**Implementation Details**:

```python
def write_streaming_chunk(self, agent_id: str, chunk: str) -> None:
    """Append streaming chunk to current agent output."""
    
def finish_streaming(self, agent_id: str) -> None:
    """Mark streaming complete, finalize display."""
```

**Validation**: Run UI tests → streaming tests pass

---

### Phase 4: TaskExecutor Integration
**Goal**: Wire streaming through executor to UI

| Task | File | Description |
|------|------|-------------|
| 4.1 | `src/teambot/tasks/executor.py` | Add `on_streaming_chunk` callback parameter |
| 4.2 | `src/teambot/tasks/executor.py` | Update `_execute_agent_task()` to use streaming |
| 4.3 | `tests/test_tasks/test_executor.py` | Add streaming callback tests |

**Validation**: Executor passes streaming callbacks correctly

---

### Phase 5: App Integration
**Goal**: Connect streaming from SDK → Executor → OutputPane

| Task | File | Description |
|------|------|-------------|
| 5.1 | `src/teambot/ui/app.py` | Update `_handle_agent_command()` to use streaming |
| 5.2 | `src/teambot/ui/app.py` | Add `/cancel` command support |
| 5.3 | `src/teambot/repl/commands.py` | Register `/cancel` command |

**Implementation Details**:

```python
# In TeamBotApp._handle_agent_command
async def _handle_agent_command(self, command):
    output = self.query_one("#output", OutputPane)
    
    def on_chunk(chunk: str):
        # Thread-safe callback from SDK
        self.call_from_thread(output.write_streaming_chunk, agent_id, chunk)
    
    result = await self._executor.execute_streaming(command, on_chunk)
    output.finish_streaming(agent_id)
```

**Validation**: End-to-end streaming works in UI

---

### Phase 6: Feature Flag & Fallback
**Goal**: Add ability to disable streaming if needed

| Task | File | Description |
|------|------|-------------|
| 6.1 | `src/teambot/copilot/sdk_client.py` | Check `TEAMBOT_STREAMING` env var |
| 6.2 | `src/teambot/copilot/sdk_client.py` | Fallback to `send_and_wait()` if disabled |

**Environment Variables**:
- `TEAMBOT_STREAMING=false` → Use blocking `send_and_wait()`
- `TEAMBOT_STREAMING=true` (default) → Use streaming

---

### Phase 7: Final Validation
**Goal**: Ensure all tests pass, no regressions

| Task | Description |
|------|-------------|
| 7.1 | Run full test suite: `uv run pytest` |
| 7.2 | Run coverage: `uv run pytest --cov=src/teambot` |
| 7.3 | Manual testing with long-running task |
| 7.4 | Verify `/cancel` command works |

**Success Criteria**:
- [ ] All existing tests pass (no regression)
- [ ] All new streaming tests pass
- [ ] Coverage ≥ 88% (maintain current level)
- [ ] Long task runs > 120s without timeout
- [ ] Streaming chunks appear in real-time
- [ ] `/cancel` stops active streaming

---

## Task Checklist

```markdown
## Phase 1: TDD Tests (Write First)
- [ ] 1.1 Add mock_streaming_session fixture to conftest.py
- [ ] 1.2 Add fire_event() helper function
- [ ] 1.3 Create test_sdk_streaming.py with 11 tests
- [ ] Verify: All 11 tests FAIL

## Phase 2: SDK Client Implementation
- [ ] 2.1 Implement execute_streaming() method
- [ ] 2.2 Implement cancel_current_request() method
- [ ] 2.3 Update execute() to use streaming internally
- [ ] Verify: All 11 tests PASS

## Phase 3: OutputPane Streaming
- [ ] 3.1 Add write_streaming_chunk() method
- [ ] 3.2 Add finish_streaming() method
- [ ] 3.3 Add _streaming_buffers state dict
- [ ] 3.4 Add streaming display tests
- [ ] Verify: UI tests pass

## Phase 4: TaskExecutor Integration
- [ ] 4.1 Add on_streaming_chunk callback parameter
- [ ] 4.2 Update _execute_agent_task() to use streaming
- [ ] 4.3 Add streaming callback tests
- [ ] Verify: Executor tests pass

## Phase 5: App Integration
- [ ] 5.1 Update _handle_agent_command() for streaming
- [ ] 5.2 Add /cancel command handler
- [ ] 5.3 Register /cancel command
- [ ] Verify: End-to-end streaming works

## Phase 6: Feature Flag
- [ ] 6.1 Check TEAMBOT_STREAMING env var
- [ ] 6.2 Implement fallback to send_and_wait()

## Phase 7: Final Validation
- [ ] 7.1 Full test suite passes
- [ ] 7.2 Coverage ≥ 88%
- [ ] 7.3 Manual test: long task > 120s
- [ ] 7.4 Manual test: /cancel works
```

---

## Files Changed Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `tests/conftest.py` | Modify | Add streaming fixtures |
| `tests/test_copilot/test_sdk_streaming.py` | Create | TDD tests for streaming |
| `tests/test_tasks/test_executor.py` | Modify | Add streaming tests |
| `tests/test_ui/test_output_pane.py` | Modify | Add streaming display tests |
| `src/teambot/copilot/sdk_client.py` | Modify | Add streaming methods |
| `src/teambot/tasks/executor.py` | Modify | Streaming callback support |
| `src/teambot/ui/widgets/output_pane.py` | Modify | Streaming display methods |
| `src/teambot/ui/app.py` | Modify | Wire streaming, add /cancel |
| `src/teambot/repl/commands.py` | Modify | Register /cancel command |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SDK API differs from research | Feature flag allows fallback |
| Event ordering issues | Buffer chunks by message_id if needed |
| Thread safety in callbacks | Use `call_from_thread()` for UI updates |
| Memory growth | Limit streaming buffer size |

---

## Estimated Effort

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Phase 1 | 3 | Low (test setup) |
| Phase 2 | 3 | Medium (core logic) |
| Phase 3 | 4 | Low (UI methods) |
| Phase 4 | 3 | Medium (integration) |
| Phase 5 | 3 | Medium (wiring) |
| Phase 6 | 2 | Low (config) |
| Phase 7 | 4 | Low (validation) |

**Total**: 22 tasks across 7 phases

---

Generated 2026-01-28T05:40:00Z by sdd.5-task-planner-for-feature
