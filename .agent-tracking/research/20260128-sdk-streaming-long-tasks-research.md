<!-- markdownlint-disable-file -->
# Research: SDK Streaming for Long-Running Tasks

**Research Date**: 2026-01-28
**Feature Spec**: docs/feature-specs/sdk-streaming-long-tasks.md
**Researcher**: Research Agent

---

## Executive Summary

Research confirms the Copilot SDK fully supports streaming execution. The SDK provides:
- `session.send()` - non-blocking message send
- `session.on(handler)` - event subscription with unsubscribe
- `session.abort()` - explicit cancellation of in-progress requests
- Event types: `ASSISTANT_MESSAGE_DELTA`, `SESSION_IDLE`, `SESSION_ERROR`
- Data field: `event.data.delta_content` for streaming chunks

**Recommendation**: Proceed with implementation. All spec assumptions validated.

---

## SDK API Findings

### 1. CopilotClient

```python
from copilot import CopilotClient

client = CopilotClient()
await client.start()
session = await client.create_session({"streaming": True})
await client.stop()
```

**Key Methods:**
- `create_session(config)` - Creates session, config can include `streaming: True`
- `start()` / `stop()` - Lifecycle management
- `force_stop()` - Forceful cleanup if stop() hangs

### 2. CopilotSession

```python
# Event subscription
unsubscribe = session.on(event_handler)

# Non-blocking send (returns message_id)
message_id = await session.send({"prompt": "..."})

# Blocking send (current implementation)
response = await session.send_and_wait({"prompt": "..."}, timeout=120)

# Cancellation
await session.abort()  # Aborts current request, session remains valid

# Cleanup
await session.destroy()  # Destroys session entirely
```

**Critical Finding**: `session.abort()` is the correct cancellation method - it stops the current request but keeps the session valid for future use. This is better than `session.destroy()` which would require recreating the session.

### 3. Session Event Types

From `copilot.generated.session_events.SessionEventType`:

| Event Type | Purpose | When Fired |
|------------|---------|------------|
| `ASSISTANT_MESSAGE_DELTA` | Streaming content chunk | Each token/chunk generated |
| `ASSISTANT_MESSAGE` | Complete message | After all deltas, final content |
| `SESSION_IDLE` | Response complete | When assistant finishes |
| `SESSION_ERROR` | Error occurred | On any error |
| `ASSISTANT_TURN_START` | Turn begins | When assistant starts responding |
| `ASSISTANT_TURN_END` | Turn ends | When assistant stops |
| `ABORT` | Request aborted | After session.abort() called |

### 4. Event Data Structure

```python
from copilot.generated.session_events import SessionEvent, Data

# Event structure
event.type      # SessionEventType enum
event.data      # Data object
event.id        # UUID
event.timestamp # datetime

# Data fields for ASSISTANT_MESSAGE_DELTA
event.data.delta_content  # str - The streaming chunk
event.data.message_id     # str - Correlate chunks to message
event.data.turn_id        # str - Correlate to turn

# Data fields for SESSION_ERROR  
event.data.error_type     # str
event.data.message        # str - Error message
event.data.stack          # str - Stack trace

# Data fields for ASSISTANT_MESSAGE (final)
event.data.content        # str - Complete message content
```

---

## Validated Assumptions

| Assumption | Spec Reference | Validation | Status |
|------------|----------------|------------|--------|
| `delta_content` field exists | Line 106 | `event.data.delta_content` confirmed | ✅ VALID |
| `session.idle` signals completion | Line 107 | `SESSION_IDLE` event type exists | ✅ VALID |
| `session.send()` is non-blocking | Line 108 | Returns message_id immediately | ✅ VALID |
| Cancellation via destroy | Line 109 | Better: `session.abort()` available | ✅ IMPROVED |

---

## Recommended Implementation

### 1. Streaming Execute Method

```python
from copilot.generated.session_events import SessionEventType
from typing import Callable, Optional
import asyncio

async def execute_streaming(
    self,
    agent_id: str,
    prompt: str,
    on_chunk: Callable[[str], None],
    on_complete: Optional[Callable[[str], None]] = None,
) -> str:
    """Execute with streaming output.
    
    Args:
        agent_id: Agent identifier
        prompt: The prompt to send
        on_chunk: Callback for each streaming chunk
        on_complete: Optional callback with final complete content
        
    Returns:
        Complete accumulated response
    """
    session = await self.get_or_create_session(agent_id)
    
    accumulated: list[str] = []
    done = asyncio.Event()
    error_holder: list[Optional[Exception]] = [None]
    final_content: list[Optional[str]] = [None]
    
    def on_event(event):
        if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
            chunk = event.data.delta_content
            if chunk:
                accumulated.append(chunk)
                on_chunk(chunk)
        elif event.type == SessionEventType.ASSISTANT_MESSAGE:
            # Final complete message
            final_content[0] = event.data.content
        elif event.type == SessionEventType.SESSION_IDLE:
            done.set()
        elif event.type == SessionEventType.SESSION_ERROR:
            error_holder[0] = SDKClientError(
                f"{event.data.error_type}: {event.data.message}"
            )
            done.set()
        elif event.type == SessionEventType.ABORT:
            error_holder[0] = SDKClientError("Request aborted")
            done.set()
    
    unsubscribe = session.on(on_event)
    
    try:
        await session.send({"prompt": prompt})
        await done.wait()
        
        if error_holder[0]:
            raise error_holder[0]
        
        # Prefer final content if available, else accumulated
        result = final_content[0] or "".join(accumulated)
        
        if on_complete:
            on_complete(result)
            
        return result
    finally:
        unsubscribe()
```

### 2. Backward Compatible Execute

```python
async def execute(self, agent_id: str, prompt: str, timeout: float = 120.0) -> str:
    """Execute with backward compatibility.
    
    Note: timeout parameter kept for API compatibility but not enforced
    when streaming. The request runs until completion or cancellation.
    """
    return await self.execute_streaming(
        agent_id, 
        prompt, 
        on_chunk=lambda _: None
    )
```

### 3. Cancellation Support

```python
async def cancel_current_request(self, agent_id: str) -> bool:
    """Cancel the current request for an agent.
    
    Returns:
        True if request was cancelled, False if no active request.
    """
    session_id = f"{self.SESSION_PREFIX}{agent_id}"
    session = self._sessions.get(session_id)
    
    if session:
        try:
            await session.abort()
            return True
        except Exception:
            return False
    return False
```

### 4. OutputPane Streaming Method

```python
# In OutputPane widget
def write_streaming_chunk(self, agent_id: str, chunk: str) -> None:
    """Write a streaming chunk, appending to current line."""
    # Get or create the streaming line for this agent
    if not hasattr(self, '_streaming_lines'):
        self._streaming_lines = {}
    
    if agent_id not in self._streaming_lines:
        # Start new streaming output
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._streaming_lines[agent_id] = f"[dim]{timestamp}[/dim] @{agent_id}: "
    
    self._streaming_lines[agent_id] += chunk
    
    # Update the display (Textual handles this efficiently)
    self._update_streaming_display(agent_id)

def finish_streaming(self, agent_id: str) -> None:
    """Mark streaming complete for an agent."""
    if hasattr(self, '_streaming_lines') and agent_id in self._streaming_lines:
        # Finalize the line
        del self._streaming_lines[agent_id]
```

---

## Integration with Existing Code

### Files to Modify

| File | Changes |
|------|---------|
| `src/teambot/copilot/sdk_client.py` | Add `execute_streaming()`, `cancel_current_request()` |
| `src/teambot/tasks/executor.py` | Add streaming callback support |
| `src/teambot/ui/app.py` | Pass streaming callback to executor |
| `src/teambot/ui/widgets/output_pane.py` | Add `write_streaming_chunk()`, `finish_streaming()` |

### Execution Flow

```
User Input (@pm task)
    │
    ▼
TeamBotApp.handle_input()
    │
    ▼
TaskExecutor.execute() ──► execute_streaming(on_chunk=output.write_streaming_chunk)
    │
    ▼
CopilotSDKClient.execute_streaming()
    │
    ├──► session.send() [non-blocking]
    │
    ├──► on_event(ASSISTANT_MESSAGE_DELTA) ──► on_chunk(delta_content) ──► OutputPane
    │
    ├──► on_event(SESSION_IDLE) ──► done.set()
    │
    ▼
Return accumulated content
```

---

## Edge Cases & Handling

### 1. Empty Delta Content
Some delta events may have `None` or empty `delta_content`. Filter these:
```python
if chunk:  # Only process non-empty chunks
    accumulated.append(chunk)
    on_chunk(chunk)
```

### 2. Multiple Concurrent Streams
Each agent has its own session, so concurrent streams are naturally isolated. The `_streaming_lines` dict in OutputPane tracks per-agent state.

### 3. Network Disconnection
If connection drops, `SESSION_ERROR` will be fired. Handle gracefully:
```python
elif event.type == SessionEventType.SESSION_ERROR:
    error_holder[0] = SDKClientError(...)
    done.set()  # Unblock the wait
```

### 4. User Cancellation During Stream
```python
# In TeamBotApp
async def _handle_cancel_command(self, agent_id: str):
    await self._sdk_client.cancel_current_request(agent_id)
    output.write_info(f"Cancelled request for @{agent_id}")
```

### 5. Session Reuse After Abort
The `session.abort()` method keeps the session valid. Next request will work normally. No need to recreate session.

---

## Performance Considerations

### Chunk Display Latency
- SDK events are delivered via asyncio
- `on_chunk` callback runs in event loop
- Textual's `write()` is async-safe
- Expected latency: < 10ms per chunk (well under 50ms target)

### Memory Management
- Accumulated chunks stored in list
- For very long responses (>1MB), consider:
  - Streaming to file instead of memory
  - Limiting `_streaming_lines` buffer size
  - OutputPane already has line limits via RichLog

### Event Listener Cleanup
Always unsubscribe in `finally` block to prevent memory leaks:
```python
unsubscribe = session.on(on_event)
try:
    ...
finally:
    unsubscribe()
```

---

## Test Strategy Implications

### TDD Tests (Write First)
1. `test_streaming_receives_delta_events` - Mock SDK, verify chunks received
2. `test_streaming_completes_on_idle` - Verify SESSION_IDLE ends stream
3. `test_streaming_handles_error` - Verify SESSION_ERROR handled
4. `test_cancel_aborts_request` - Verify abort() called
5. `test_backward_compatible_execute` - Verify old API still works

### Code-First Tests (After Implementation)
1. OutputPane streaming display tests
2. Integration test with real SDK (if available)
3. Concurrent streaming test

---

## Open Questions Resolved

| Question | Answer |
|----------|--------|
| Q-001: Explicit cancellation or only destroy? | **`session.abort()`** - explicit cancel, keeps session valid |
| Delta content field name? | `event.data.delta_content` confirmed |
| Completion event? | `SESSION_IDLE` event type |
| Error handling? | `SESSION_ERROR` with `error_type`, `message`, `stack` |

---

## Recommendations

1. **Proceed with implementation** - All assumptions validated
2. **Use `session.abort()`** for cancellation (better than `destroy()`)
3. **Handle `ABORT` event** after cancel for clean state
4. **Keep timeout parameter** in `execute()` for API compatibility (ignored internally)
5. **Add feature flag** `TEAMBOT_STREAMING=true` (default) for rollback capability

---

## References

- SDK Source: `copilot` package (github-copilot-sdk==0.1.16)
- Event Types: `copilot.generated.session_events.SessionEventType`
- Data Class: `copilot.generated.session_events.Data`
- Session API: `copilot.session.CopilotSession`
