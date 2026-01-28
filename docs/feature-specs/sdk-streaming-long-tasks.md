<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# SDK Streaming for Long-Running Tasks - Feature Specification Document
Version 0.1 | Status Draft | Owner TBD | Team TeamBot | Target TBD | Lifecycle Discovery

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-28 |
| Problem & Users | 100% | None | 2026-01-28 |
| Scope | 100% | None | 2026-01-28 |
| Requirements | 100% | None | 2026-01-28 |
| Metrics & Risks | 80% | Latency benchmarks TBD | 2026-01-28 |
| Operationalization | 0% | Not started | - |
| Finalization | 0% | Pending review | - |
Unresolved Critical Questions: 0 | TBDs: 1

---

## 1. Executive Summary

### Context
TeamBot currently uses the Copilot SDK's `send_and_wait()` method with a 120-second timeout. Long-running tasks such as "review the entire codebase" or "analyze all dependencies" consistently timeout before completion. The SDK already supports streaming mode (sessions are created with `streaming: True`), but TeamBot doesn't utilize the streaming event model to receive incremental responses.

### Core Opportunity
Replace the blocking `send_and_wait()` pattern with an event-driven streaming approach using the SDK's `session.send()` + event listener model. This allows:
- Tasks to run indefinitely without fixed timeout
- Incremental output display as the agent works
- Better user experience with real-time feedback
- No artificial 120s ceiling on task duration

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Eliminate fixed timeout for agent tasks | Technical | 120s timeout | No timeout | MVP | P0 |
| G-002 | Display streaming output as it arrives | UX | Wait for complete response | Real-time chunks | MVP | P0 |
| G-003 | Support graceful task cancellation | UX | No cancellation | Ctrl+C or /cancel | MVP | P1 |
| G-004 | Maintain backward compatibility | Technical | Current API | Same public interface | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement streaming execution | `execute_streaming()` method with event callbacks | P0 | TBD |
| Integrate with split-pane UI | Streaming chunks appear in OutputPane in real-time | P0 | TBD |
| Add cancellation support | User can cancel running task via /cancel or Ctrl+C | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Fixed 120s timeout**: `CopilotSDKClient.execute()` uses `send_and_wait(timeout=120.0)`
- **All-or-nothing response**: User sees nothing until task completes or times out
- **Wasted work**: Long tasks that timeout lose all partial progress
- **Poor UX**: No indication of progress during execution
- **Streaming unused**: Sessions are created with `streaming: True` but streaming events are ignored

### Problem Statement
The current blocking execution model with fixed timeout makes TeamBot unsuitable for complex, time-consuming tasks. Users cannot execute comprehensive reviews, large-scale refactoring plans, or detailed analysis tasks without encountering timeout failures.

### Root Causes
* `send_and_wait()` is a convenience method that blocks until complete response
* No event listener registered to handle `assistant.message_delta` events
* Timeout is passed to SDK but SDK streaming doesn't respect it the same way
* Original implementation prioritized simplicity over streaming capability

### Impact of Inaction
* Users cannot use TeamBot for meaningful, complex tasks
* Competitive disadvantage vs tools that support long-running operations
* Frustration and workflow interruption when tasks timeout at 119 seconds
* Wasted API calls and compute for timed-out partial work

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer | Run comprehensive code reviews | Tasks timeout before completion | High - blocks primary workflow |
| Architect | Generate detailed system analysis | Cannot analyze large codebases | High - limits tool utility |
| Team Lead | Coordinate multi-agent complex tasks | Pipeline stages timeout | Medium - reduces team adoption |

### Journeys
1. **Long Task Flow**: User submits complex task → sees streaming output appear incrementally → task completes successfully regardless of duration
2. **Cancellation Flow**: User submits task → decides to cancel → presses Ctrl+C or /cancel → task stops, partial output preserved

---

## 4. Scope

### In Scope
* Streaming execution via SDK event model (`session.send()` + event listeners)
* Real-time display of `assistant.message_delta` events in OutputPane
* Detection of `session.idle` event to mark task completion
* Task cancellation support (destroy session or send cancel signal)
* Backward-compatible `execute()` method (streaming internally, returns full response)
* Integration with existing TaskExecutor and split-pane UI

### Out of Scope (justified)
* Copilot CLI changes - explicitly excluded per requirements
* Timeout configuration UI - streaming removes need for timeout
* Partial response persistence/resume - complexity exceeds benefit
* Multi-model streaming differences - assume consistent SDK behavior

### Assumptions
* SDK `assistant.message_delta` events contain `delta_content` field
* SDK `session.idle` event signals completion
* SDK `session.send()` is non-blocking and returns immediately
* Cancellation via `session.destroy()` stops in-progress requests

### Constraints
* Must not break existing TaskExecutor public API
* Must work with current split-pane UI architecture
* Must handle SDK errors gracefully (network, auth, etc.)
* Performance: streaming chunks must display within 50ms of receipt

---

## 5. Product Overview

### Value Proposition
TeamBot with SDK streaming enables unlimited-duration agent tasks with real-time output feedback, transforming it from a quick-query tool into a comprehensive AI development assistant capable of complex, time-consuming operations.

### Differentiators
* No artificial timeout ceiling
* Real-time streaming output (not just completion notification)
* Graceful cancellation preserves partial work
* Invisible to user - same commands, better behavior

### UX / UI
**Streaming Output in Split-Pane:**
```
┌─────────────────────────┬───────────────────────────────────────┐
│  INPUT PANE             │  OUTPUT PANE                          │
│                         │                                       │
│  teambot: @pm review    │  [10:30:15] > @pm review codebase     │
│  teambot: _             │  [10:30:16] @pm: Analyzing src/...    │
│                         │  [10:30:18] @pm: Found 3 issues in... │
│                         │  [10:30:20] @pm: Checking tests/...   │
│                         │  [10:30:25] @pm: ██████░░░░ 60%       │
│                         │  ... (streaming continues) ...        │
│                         │  [10:32:45] ✓ @pm: Review complete    │
└─────────────────────────┴───────────────────────────────────────┘
```

**Key UX Elements:**
- Streaming chunks appear as separate lines or appended to current line
- Timestamp updates as new content arrives
- Final completion marked with ✓ indicator
- User can type new commands while streaming continues

| UX Status: Mockup Complete |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-STR-001 | Streaming Execution | SDK client shall use `session.send()` + event listeners instead of `send_and_wait()` | G-001, G-002 | All | P0 | Tasks complete without timeout | Core change |
| FR-STR-002 | Delta Event Handling | Client shall listen for `assistant.message_delta` events and emit content | G-002 | All | P0 | Each delta displayed within 50ms | Real-time feedback |
| FR-STR-003 | Completion Detection | Client shall detect `session.idle` event to mark task complete | G-001 | All | P0 | Task marked complete on idle | End condition |
| FR-STR-004 | Streaming Callback | `execute_streaming()` shall accept callback for incremental output | G-002 | All | P0 | Callback invoked per delta | API contract |
| FR-STR-005 | Backward Compatible Execute | `execute()` shall internally use streaming but return complete response | G-004 | All | P0 | Existing code unchanged | Compatibility |
| FR-STR-006 | OutputPane Streaming | OutputPane shall display streaming chunks as they arrive | G-002 | All | P0 | Chunks visible in real-time | UI integration |
| FR-STR-007 | Task Cancellation | User shall be able to cancel running task via /cancel command | G-003 | All | P1 | Task stops, partial output kept | User control |
| FR-STR-008 | Error Event Handling | Client shall handle `session.error` events gracefully | G-001 | All | P0 | Errors displayed, no crash | Robustness |
| FR-STR-009 | Session Cleanup | Client shall clean up event listeners when task completes/cancels | G-001 | All | P1 | No memory leaks | Resource management |
| FR-STR-010 | Streaming Status Indicator | UI shall indicate when agent is actively streaming | G-002 | All | P2 | Visual indicator shown | UX polish |

### Feature Hierarchy
```
SDK Streaming
├── Core Streaming
│   ├── Event Listener Registration
│   ├── Delta Content Accumulation
│   ├── Completion Detection (session.idle)
│   └── Error Handling (session.error)
├── API Layer
│   ├── execute_streaming(callback) - New
│   ├── execute() - Backward compatible
│   └── cancel_task() - New
├── UI Integration
│   ├── Streaming to OutputPane
│   ├── Status Indicator
│   └── Cancellation UI (/cancel)
└── Resource Management
    ├── Event Listener Cleanup
    ├── Session State Tracking
    └── Graceful Shutdown
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-STR-001 | Performance | Streaming chunk display latency | < 50ms from SDK event to UI | P0 | Benchmark test | Critical for UX |
| NFR-STR-002 | Reliability | No timeout failures for valid tasks | 0 timeout errors | P0 | Long-running test | Core goal |
| NFR-STR-003 | Reliability | Graceful error recovery | Errors don't crash app | P0 | Error injection test | Stability |
| NFR-STR-004 | Compatibility | Existing tests pass | 100% existing tests | P0 | CI pipeline | No regression |
| NFR-STR-005 | Resource | Memory stability during streaming | < 10MB growth per task | P1 | Memory profiling | No leaks |
| NFR-STR-006 | Usability | Cancellation responsiveness | < 1s to stop streaming | P1 | Manual test | User control |

---

## 8. Data & Analytics

### Inputs
- SDK session events (`assistant.message_delta`, `session.idle`, `session.error`)
- User commands (task submission, cancellation)
- Session state (active, idle, error)

### Outputs / Events
- Streaming content chunks to OutputPane
- Task completion/failure notifications
- Cancellation confirmations

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| streaming_started | Task begins streaming | agent_id, task_id | Track streaming usage | TBD |
| streaming_chunk | Delta received | agent_id, chunk_size, latency_ms | Performance monitoring | TBD |
| streaming_completed | Task finishes | agent_id, total_duration, total_chunks | Success metrics | TBD |
| streaming_cancelled | User cancels | agent_id, partial_duration | Cancellation patterns | TBD |
| streaming_error | Error occurs | agent_id, error_type | Error tracking | TBD |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Timeout errors | Reliability | >0 for long tasks | 0 | Per session | Error logs |
| Chunk latency | Performance | N/A | < 50ms p95 | Per task | Instrumentation |
| Task completion rate | Reliability | ~70% (timeouts) | > 99% | Weekly | Analytics |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Copilot SDK streaming API | External | High | GitHub | API changes | Pin SDK version |
| Split-pane UI | Internal | High | TeamBot | Integration complexity | Phased rollout |
| asyncio event loop | Platform | High | Python | Compatibility | Test on supported versions |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | SDK streaming API differs from documentation | High | Low | Test with actual SDK, fallback to send_and_wait | TBD | Open |
| R-002 | Event ordering issues cause garbled output | Medium | Low | Buffer and sequence chunks if needed | TBD | Open |
| R-003 | Memory growth from long streaming sessions | Medium | Medium | Implement output buffer limits | TBD | Open |
| R-004 | Cancellation doesn't stop SDK processing | Medium | Low | Test cancel behavior, document limitations | TBD | Open |
| R-005 | UI update frequency causes performance issues | Low | Low | Batch updates, throttle if needed | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
- Streaming content: Same as current (user prompts, agent responses)
- No new data collected beyond existing

### PII Handling
N/A - No change to PII handling

### Threat Considerations
- Event injection: Trust SDK events only, validate event types
- Resource exhaustion: Limit concurrent streaming sessions

### Regulatory / Compliance
N/A - No regulatory requirements for this feature

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Feature flag to disable streaming | Falls back to send_and_wait |
| Monitoring | Log streaming errors | Debug logging |
| Support | Document streaming behavior | For troubleshooting |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Description | Gate Criteria | Owner |
|-------|-------------|---------------|-------|
| Phase 1 | Core streaming implementation | Events received and accumulated | TBD |
| Phase 2 | UI integration | Streaming visible in OutputPane | TBD |
| Phase 3 | Cancellation support | /cancel stops streaming tasks | TBD |
| Phase 4 | Polish & edge cases | Error handling, cleanup | TBD |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| `TEAMBOT_STREAMING` | Enable streaming execution | true | Remove after stable |
| `TEAMBOT_STREAMING_DEBUG` | Verbose streaming logs | false | Keep for debugging |

### Communication Plan
- Update README with streaming behavior notes
- Document /cancel command
- Note removal of effective timeout

---

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Does SDK support explicit cancellation or only session destroy? | TBD | Research | Open |

---

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 0.1 | 2026-01-28 | AI Assistant | Initial specification draft | New |

---

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Code | src/teambot/copilot/sdk_client.py | Current SDK client with send_and_wait | Replace with streaming |
| REF-002 | Code | src/teambot/ui/app.py | Split-pane UI for output display | Integrate streaming output |
| REF-003 | External | Copilot SDK docs | Streaming API reference | Follow SDK patterns |
| REF-004 | Spec | docs/feature-specs/split-pane-interface.md | UI architecture | Build upon existing UI |

---

## 17. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Streaming | Receiving response in incremental chunks as generated |
| Delta | A single chunk of content from streaming response |
| send_and_wait | Blocking SDK method that waits for complete response |
| session.idle | SDK event indicating response is complete |

### Technical Approach

**Current Implementation (Blocking):**
```python
async def execute(self, agent_id: str, prompt: str, timeout: float = 120.0) -> str:
    session = await self.get_or_create_session(agent_id)
    response = await session.send_and_wait({"prompt": prompt, "timeout": timeout})
    return response.data.content
```

**Proposed Implementation (Streaming):**
```python
async def execute_streaming(
    self, 
    agent_id: str, 
    prompt: str,
    on_chunk: Callable[[str], None],
) -> str:
    session = await self.get_or_create_session(agent_id)
    accumulated = []
    done = asyncio.Event()
    error_holder = [None]
    
    def on_event(event):
        if event.type.value == "assistant.message_delta":
            chunk = event.data.delta_content
            accumulated.append(chunk)
            on_chunk(chunk)
        elif event.type.value == "session.idle":
            done.set()
        elif event.type.value == "session.error":
            error_holder[0] = event.data
            done.set()
    
    session.on(on_event)
    await session.send({"prompt": prompt})
    await done.wait()
    
    if error_holder[0]:
        raise SDKClientError(f"SDK error: {error_holder[0]}")
    
    return "".join(accumulated)

async def execute(self, agent_id: str, prompt: str) -> str:
    """Backward compatible - uses streaming internally."""
    return await self.execute_streaming(agent_id, prompt, on_chunk=lambda _: None)
```

**UI Integration:**
```python
async def _handle_agent_command(self, command, output):
    def on_chunk(chunk):
        # Append chunk to current output line or start new line
        output.write_streaming_chunk(command.agent_id, chunk)
    
    result = await self._executor.execute_streaming(command, on_chunk)
    output.write_task_complete(command.agent_id, "Done")
```

### SDK Event Types Reference
| Event Type | Meaning | Data Fields |
|------------|---------|-------------|
| `assistant.message_delta` | Incremental content chunk | `delta_content` |
| `session.idle` | Response complete | None |
| `session.error` | Error occurred | Error details |

Generated 2026-01-28T02:50:00Z by sdd.1-create-feature-spec (mode: collaborative)
<!-- markdown-table-prettify-ignore-end -->
