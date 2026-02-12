<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# @notify Pseudo-Agent - Feature Specification Document
Version 1.0 | Status **Draft** | Owner TBD | Team TeamBot | Target 0.3.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-12 |
| Problem & Users | 100% | None | 2026-02-12 |
| Scope | 100% | None | 2026-02-12 |
| Requirements | 100% | None | 2026-02-12 |
| Metrics & Risks | 100% | None | 2026-02-12 |
| Test Strategy | 100% | None | 2026-02-12 |
| Finalization | 0% | Pending implementation | 2026-02-12 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot's notification system (implemented in v0.2.0) provides real-time alerts via external channels (Telegram) when workflow events occur. However, users cannot currently send custom notifications as part of agent pipelines. The existing `/notify` system command operates outside the pipeline, cannot reference agent outputs, and breaks pipeline flow.

### Core Opportunity
Implement `@notify` as a **pseudo-agent** that integrates seamlessly with TeamBot's agent pipeline syntax. This enables users to:
1. Compose notifications with agent outputs using `$ref` syntax
2. Place notifications anywhere in a pipeline (start, middle, end)
3. Continue pipeline execution after notification (non-blocking)
4. Use a single, consistent interface for all notifications

This transforms notifications from a terminal-bound utility into a **first-class pipeline participant**.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-NP-001 | Users can send notifications from within agent pipelines | Core | System command only | `@notify` pseudo-agent | MVP | P0 |
| G-NP-002 | Notifications can include output from any prior agent | UX | No `$ref` support | Full `$ref` interpolation | MVP | P0 |
| G-NP-003 | Notification failures never block pipeline execution | Reliability | N/A | Warning logged, pipeline continues | MVP | P0 |
| G-NP-004 | Single consistent notification interface | UX | Two interfaces (`/notify` + events) | `@notify` only | MVP | P0 |
| G-NP-005 | `@notify` appears in agent status display | Visibility | Not shown | Shown with model "(n/a)" | MVP | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Add `notify` to VALID_AGENTS | Router recognizes `@notify` as valid agent ID | P0 | TBD |
| Implement pseudo-agent executor | Execute notification without Copilot SDK call | P0 | TBD |
| Implement `$ref` interpolation | Agent outputs resolved and injected into message | P0 | TBD |
| Implement output truncation | Large outputs truncated to 500 chars + "..." | P0 | TBD |
| Store result in TaskManager | Confirmation stored for downstream `$notify` references | P0 | TBD |
| Remove `/notify` command | Legacy system command deleted | P0 | TBD |
| Update agent status display | Show `@notify` with model "(n/a)" | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **`/notify` system command exists**: Sends message to all configured notification channels
- **No pipeline integration**: `/notify` is a terminal command, not an agent
- **No `$ref` support**: Cannot dynamically include agent outputs in messages
- **Pipeline breaks**: `/notify` returns void; no result for downstream agents
- **Two interfaces**: Users must choose between `/notify` and event-driven notifications

### Problem Statement
Users who want to notify stakeholders mid-pipeline (e.g., "Review complete, changes approved by $reviewer") cannot do so without breaking their pipeline into separate commands. The current `/notify` command:
1. Cannot reference outputs from prior agents using `$ref` syntax
2. Cannot be chained with other agents in a pipeline
3. Does not return a result that downstream agents can reference
4. Does not appear in the agent status display

### Root Causes
* `/notify` designed as system command (synchronous, terminal-bound)
* No pseudo-agent pattern existed in codebase
* `$ref` interpolation not applied to system commands
* Task result storage not integrated with system commands

### Impact of Inaction
* Users must manually copy/paste agent outputs into notifications
* Pipeline workflows cannot include notification checkpoints
* Two interfaces creates cognitive overhead
* Notification status not visible in agent display
* TeamBot perceived as having incomplete pipeline integration

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Pipeline Author | Compose end-to-end workflows with notification checkpoints | Cannot include notifications in pipelines | High - primary user |
| Solo Developer | Get notified when specific agents complete | Must monitor terminal or use separate commands | High - common use case |
| Team Lead | Share agent results with team via notification | Cannot include agent output in notification | Medium - collaboration |
| CI Integrator | Send pipeline status to team channels | Must use external tooling | Medium - automation |

### User Journeys

#### Journey 1: Pipeline with Notification Checkpoint
1. User defines pipeline: `@pm plan, @builder-1 implement, @notify "Build complete: $builder-1", @reviewer review`
2. Each agent executes in sequence
3. After `@builder-1` completes, `@notify` sends notification with builder's output
4. `@reviewer` continues with code review
5. User receives notification on phone, knows build is ready for review

#### Journey 2: End-of-Pipeline Summary
1. User runs: `@reviewer review the changes, @notify "Review complete: $reviewer"`
2. `@reviewer` analyzes changes and produces output
3. `@notify` interpolates reviewer's output (truncated if large) into message
4. User receives notification with review summary
5. Pipeline completes successfully

#### Journey 3: Error Notification (Non-Blocking)
1. User runs: `@notify "Starting build", @builder-1 build, @notify "Build done: $builder-1"`
2. First notification sends successfully
3. `@builder-1` completes
4. Second notification fails (network error)
5. Warning logged but pipeline continues
6. User sees warning in terminal, but workflow is not interrupted

---

## 4. Scope

### In Scope
* **New pseudo-agent `@notify`**: Recognized in `VALID_AGENTS` with special handling
* **`$ref` interpolation**: Messages containing `$agent` references resolved before sending
* **Output truncation**: Large outputs truncated to 500 characters with "..." suffix
* **Pipeline-safe execution**: Returns confirmation, stores result, handles failures gracefully
* **Legacy removal**: Remove `/notify` system command from `SystemCommands`
* **UI integration**: Show `@notify` in agent status display with model "(n/a)"

### Out of Scope
* New notification channels (Telegram is sufficient)
* Message templating beyond `$ref` interpolation
* Notification delivery confirmation/receipts
* Two-way notification interactions (replies)
* Scheduled or delayed notifications
* Per-channel targeting (e.g., `@notify:telegram`)
* Configurable truncation threshold

### Assumptions
* Existing notification infrastructure (EventBus, TelegramChannel) is stable and sufficient
* Users understand `@agent` and `$ref` syntax from existing documentation
* Truncation at 500 characters provides sufficient context for most use cases
* A single `@notify` pseudo-agent (not per-channel agents) meets user needs

### Constraints
* Must not break existing agent pipeline functionality
* Must integrate cleanly with existing EventBus/channel infrastructure
* Must work with all existing pipeline features: `$ref` dependencies, `&` background execution, multi-agent `,` syntax
* Must not make any Copilot SDK API calls (pure pseudo-agent)

---

## 5. Product Overview

### Value Proposition
`@notify` enables users to compose notifications directly within agent pipelines, using the same syntax they already know (`@agent`, `$ref`). This eliminates the need for separate notification commands and enables powerful workflows where notifications serve as checkpoints or summaries within larger pipelines.

### Key Behaviors

#### 5.1 Agent Recognition
`@notify` is recognized as a valid agent ID by the router, but handled as a pseudo-agent (no Copilot SDK call).

**Syntax Examples:**
```
@notify "Build complete!"
@notify "Review done: $reviewer"
@notify "Stage 1 done, stage 2 starting"
```

#### 5.2 Pipeline Positioning
`@notify` can appear anywhere in a pipeline:
```
# Beginning
@notify "Starting workflow", @pm plan

# Middle
@pm plan, @notify "Plan ready: $pm", @builder-1 implement

# End
@builder-1 implement, @reviewer review, @notify "All done: $reviewer"
```

#### 5.3 `$ref` Interpolation
Agent outputs are resolved and injected into the message:
```
@reviewer analyze the code, @notify "Review: $reviewer"
```
Results in notification: `Review: [reviewer's analysis output]`

#### 5.4 Output Truncation
Large referenced outputs are truncated:
- First 500 characters preserved
- "..." suffix appended
- Example: `Review: [first 500 chars of output]...`

#### 5.5 Result Continuity
`@notify` returns a confirmation that downstream agents can reference:
- Output: `"Notification sent ✅"`
- Stored in `TaskManager._agent_results["notify"]`
- Downstream can use `$notify` (though rarely useful)

#### 5.6 Failure Handling
Notification failures do not break the pipeline:
- Exception caught and logged as warning
- Output: `"Notification failed ⚠️ (warning logged)"`
- Pipeline continues with next agent

### UX / UI
| Element | Behavior |
|---------|----------|
| Agent status display | Shows `@notify` with model "(n/a)" and status (Idle/Active) |
| REPL output | Shows confirmation message after notification |
| Error display | Shows warning if notification fails, but does not halt |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-001 | Agent recognition | `@notify` recognized as valid agent ID in `VALID_AGENTS` set | G-NP-001 | All | P0 | `@notify` does not raise "unknown agent" error | Add "notify" to VALID_AGENTS in router.py |
| FR-002 | Message acceptance | `@notify` accepts a message string as its prompt | G-NP-001 | All | P0 | `@notify "Hello"` parses successfully | Standard agent prompt syntax |
| FR-003 | `$ref` support | `@notify` supports `$ref` syntax in messages | G-NP-002 | All | P0 | `@notify "Result: $pm"` resolves $pm output | Use existing parser $ref extraction |
| FR-004 | Reference interpolation | Referenced agent outputs interpolated into message before sending | G-NP-002 | All | P0 | `$agent` replaced with actual output text | Similar to _inject_references() |
| FR-005 | Output truncation | Large referenced outputs truncated to 500 chars + "..." | G-NP-002 | All | P0 | 1000-char output becomes 500 chars + "..." | Prevents excessively long notifications |
| FR-006 | Channel dispatch | `@notify` dispatches to all configured notification channels | G-NP-001 | All | P0 | All enabled channels receive message | Use existing EventBus.emit() |
| FR-007 | Confirmation output | `@notify` returns confirmation: `"Notification sent ✅"` | G-NP-001 | All | P0 | Output displayed in REPL | Standard success message |
| FR-008 | Result storage | Confirmation stored in `TaskManager._agent_results` | G-NP-001 | All | P0 | `get_agent_result("notify")` returns TaskResult | Enables `$notify` references |
| FR-009 | Failure handling | Notification failures log warning but don't break pipeline | G-NP-003 | All | P0 | Pipeline continues after network error | Try/except with logging.warning |
| FR-010 | SDK bypass | `@notify` bypasses Copilot SDK execution entirely | G-NP-001 | All | P0 | No SDK API call made | Pseudo-agent pattern |
| FR-011 | Legacy removal | `/notify` system command removed from SystemCommands | G-NP-004 | All | P0 | `/notify` returns "unknown command" | Delete from commands.py |
| FR-012 | Status display | `@notify` appears in agent status display | G-NP-005 | All | P1 | Status panel shows `@notify` with model "(n/a)" | Update AgentStatusManager |
| FR-013 | Pipeline positioning | `@notify` can appear at beginning, middle, or end of pipeline | G-NP-001 | All | P0 | All positions work correctly | No position restrictions |
| FR-014 | Background execution | `@notify` supports `&` background execution syntax | G-NP-001 | All | P0 | `@notify "Hello" &` works | Standard background pattern |
| FR-015 | Multi-agent syntax | `@notify` works with `,` multi-agent syntax | G-NP-001 | All | P0 | `@pm plan, @notify "Done"` works | Standard multi-agent pattern |

### Feature Hierarchy
```
@notify Pseudo-Agent
├── Agent Recognition (FR-001, FR-002)
│   ├── Add "notify" to VALID_AGENTS
│   └── Parse @notify with message prompt
├── $ref Interpolation (FR-003, FR-004, FR-005)
│   ├── Extract $ref tokens from message
│   ├── Resolve agent outputs from TaskManager
│   └── Truncate large outputs (500 chars)
├── Notification Dispatch (FR-006, FR-009)
│   ├── Create EventBus from config
│   ├── Emit custom_message event
│   └── Catch failures, log warning
├── Result Management (FR-007, FR-008)
│   ├── Return confirmation output
│   └── Store in _agent_results["notify"]
├── Execution Bypass (FR-010)
│   └── Skip Copilot SDK call for pseudo-agents
├── Legacy Removal (FR-011)
│   └── Delete /notify from SystemCommands
├── UI Integration (FR-012)
│   └── Add @notify to status panel
└── Pipeline Compatibility (FR-013, FR-014, FR-015)
    ├── All positions (begin, middle, end)
    ├── Background execution (&)
    └── Multi-agent syntax (,)
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Notification dispatch completes within 5 seconds | < 5s latency | P0 | Integration test with mock channel | Timeout after 5s, log warning |
| NFR-002 | Reliability | Notification failures do not block pipeline | 0 pipeline failures from notify errors | P0 | Test with failing channel | Try/except wrapper |
| NFR-003 | Compatibility | Works with all existing pipeline features | Pass all existing pipeline tests | P0 | Regression test suite | $ref, &, multi-agent |
| NFR-004 | Maintainability | Code follows existing patterns | Consistent with executor.py patterns | P1 | Code review | Use existing abstractions |
| NFR-005 | Testability | All new code has test coverage | > 80% coverage | P0 | pytest --cov | Follow pytest-mock patterns |
| NFR-006 | Security | No secrets logged or exposed | 0 secrets in logs | P0 | Security review | Use existing channel sanitization |

---

## 8. Data & Analytics

### Inputs
| Input | Source | Format |
|-------|--------|--------|
| Message string | User prompt | String (may contain $ref tokens) |
| Agent outputs | TaskManager._agent_results | TaskResult objects |
| Notification config | teambot.json | JSON (channels, enabled) |

### Outputs / Events
| Output | Destination | Format |
|--------|-------------|--------|
| Notification message | All enabled channels | Channel-specific (HTML for Telegram) |
| Confirmation output | REPL display | String ("Notification sent ✅") |
| TaskResult | TaskManager._agent_results | TaskResult object |

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| notify_sent | After successful dispatch | {message_length, channels_count} | Track usage | TBD |
| notify_failed | After dispatch failure | {error_type, channel} | Debug failures | TBD |
| notify_truncated | When output truncated | {original_length, agent_id} | Track truncation frequency | TBD |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Notifications sent | Counter | 0 | > 0 | Daily | Event logs |
| Pipeline failures from notify | Counter | 0 | 0 | Daily | Error logs |
| Truncation events | Counter | 0 | Track | Daily | Event logs |
| User adoption | Percentage | 0% | > 50% of notify users | 30 days | Usage analytics |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| EventBus | Internal | High | TeamBot | Low - stable | Use existing emit() |
| TaskManager | Internal | High | TeamBot | Low - stable | Use existing _agent_results |
| Parser | Internal | High | TeamBot | Low - stable | Use existing $ref extraction |
| Router | Internal | High | TeamBot | Low - stable | Add to VALID_AGENTS |
| Executor | Internal | High | TeamBot | Medium - complex | Add pseudo-agent detection |
| AgentStatusManager | Internal | Medium | TeamBot | Low - stable | Add notify agent |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Breaking existing pipelines | High | Low | Comprehensive regression tests | TBD | Open |
| R-002 | Notification failures blocking pipelines | High | Medium | Try/except wrapper with warning logs | TBD | Open |
| R-003 | Large $ref outputs causing issues | Low | Medium | Truncation with clear "..." suffix | TBD | Open |
| R-004 | User confusion during transition | Medium | Low | Clear migration note in changelog | TBD | Open |
| R-005 | Executor complexity increase | Medium | Medium | Minimal pseudo-agent detection logic | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
* **Notification messages**: May contain user-defined content and agent outputs
* **Agent outputs**: May contain code, analysis, or other project-specific data

### PII Handling
* No PII expected in typical usage
* Users responsible for content they include in notifications
* Existing channel sanitization applies (HTML escaping)

### Threat Considerations
* **Credential exposure**: Channels handle their own credential management via environment variables
* **Message injection**: HTML escaping prevents XSS in Telegram messages (existing mitigation)

### Regulatory / Compliance
N/A - No regulatory requirements for this feature.

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard package update | No infrastructure changes |
| Rollback | Revert to previous version | `/notify` would need restoration |
| Monitoring | Existing notification monitoring | notify_sent/notify_failed events |
| Alerting | No new alerts required | Uses existing channel alerting |
| Support | Document migration from `/notify` | Changelog entry |
| Capacity Planning | No impact | Same notification volume |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|---------------|-------|
| Implementation | All FRs implemented, tests passing | TBD |
| Code Review | PR approved by reviewer | TBD |
| Integration Test | End-to-end pipeline with @notify works | TBD |
| Documentation | CHANGELOG and guides updated | TBD |
| Release | Version bump to 0.3.0 | TBD |

### Migration Notes
```markdown
## Breaking Change: `/notify` Replaced by `@notify`

The `/notify` system command has been replaced by the `@notify` pseudo-agent.

**Before (0.2.x):**
```
/notify Build complete!
```

**After (0.3.0+):**
```
@notify "Build complete!"
```

**New capabilities:**
- Works anywhere in pipelines: `@pm plan, @notify "Plan ready: $pm"`
- Supports $ref syntax: `@notify "Review: $reviewer"`
- Returns result for downstream agents
- Appears in agent status display
```

### Communication Plan
* CHANGELOG entry describing migration
* Documentation update in interactive-mode.md
* Example pipelines in guides

---

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| (none) | All questions resolved | - | - | - |

**Resolved Questions:**
| Question | Resolution |
|----------|------------|
| Truncation limit (500 chars)? | 500 chars is reasonable for notifications; can be made configurable in future |
| Multiple messages in one call? | Not needed; users can use multiple `@notify` calls |
| Per-channel targeting? | Out of scope; single `@notify` dispatches to all channels |

---

## 15. Acceptance Test Scenarios

### AT-001: Simple Notification
**Description**: User sends a simple notification message
**Preconditions**: REPL running, notifications configured and enabled
**Steps**:
1. User enters: `@notify "Build complete!"`
2. Wait for notification to dispatch
**Expected Result**: Notification sent to all configured channels
**Verification**: 
- REPL shows "Notification sent ✅"
- Telegram receives message "Build complete!"

### AT-002: Notification with $ref
**Description**: User sends notification containing agent output reference
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@pm create a brief project summary`
2. Wait for PM to complete
3. User enters: `@notify "Project summary: $pm"`
**Expected Result**: Notification contains PM's output
**Verification**:
- Telegram message includes PM's summary text
- REPL shows "Notification sent ✅"

### AT-003: Notification with Large Output Truncation
**Description**: Referenced output exceeds 500 characters
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@pm create a detailed 1000-word analysis`
2. Wait for PM to complete (large output)
3. User enters: `@notify "Analysis: $pm"`
**Expected Result**: Notification contains truncated output
**Verification**:
- Telegram message is ~500 chars + "..."
- Full PM output NOT included

### AT-004: Notification in Pipeline Middle
**Description**: Notification appears between two agents in pipeline
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@pm plan the feature, @notify "Plan ready: $pm", @reviewer review the plan from $pm`
**Expected Result**: All three stages execute in order
**Verification**:
- PM completes first
- Notification sent with PM's output
- Reviewer executes after notification
- REPL shows all outputs in order

### AT-005: Notification at Pipeline End
**Description**: Notification as final step in pipeline
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@builder-1 implement the feature, @reviewer review, @notify "All done: $reviewer"`
**Expected Result**: Pipeline completes with final notification
**Verification**:
- Builder and reviewer execute in order
- Final notification contains reviewer's output
- Pipeline completes successfully

### AT-006: Notification Failure Non-Blocking
**Description**: Notification fails but pipeline continues
**Preconditions**: REPL running, notifications misconfigured (invalid token)
**Steps**:
1. User enters: `@pm plan, @notify "Plan ready", @reviewer review $pm`
**Expected Result**: Pipeline continues despite notification failure
**Verification**:
- PM completes
- Notification fails (warning logged)
- Reviewer still executes
- Pipeline completes

### AT-007: Agent Status Display
**Description**: @notify appears in agent status panel
**Preconditions**: REPL running with status panel visible
**Steps**:
1. Observe agent status panel
2. Look for @notify entry
**Expected Result**: @notify shown with model "(n/a)"
**Verification**:
- Status panel includes "notify" row
- Model column shows "(n/a)"
- Status shows "Idle" when not executing

### AT-008: Background Notification Execution
**Description**: @notify supports background execution with &
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@notify "Background notification" &`
2. User immediately enters another command
**Expected Result**: Notification sends in background
**Verification**:
- Control returns immediately
- Notification eventually sends
- No blocking of subsequent commands

### AT-009: Downstream $notify Reference
**Description**: Downstream agent can reference $notify output
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters: `@notify "Test message", @pm summarize this: $notify`
**Expected Result**: PM receives notify's confirmation output
**Verification**:
- PM's input includes "Notification sent ✅"
- PM produces output based on that input

### AT-010: Legacy /notify Removed
**Description**: /notify system command no longer exists
**Preconditions**: REPL running
**Steps**:
1. User enters: `/notify Test message`
**Expected Result**: Unknown command error
**Verification**:
- Error message indicates unknown command
- Suggests using `@notify` instead

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-12 | TeamBot BA | Initial specification | New |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Code | src/teambot/repl/router.py | VALID_AGENTS set, routing logic |
| REF-002 | Code | src/teambot/repl/parser.py | $ref extraction regex and parsing |
| REF-003 | Code | src/teambot/tasks/executor.py | Task execution, _inject_references() |
| REF-004 | Code | src/teambot/tasks/manager.py | TaskResult storage in _agent_results |
| REF-005 | Code | src/teambot/repl/commands.py | /notify implementation (to be removed) |
| REF-006 | Code | src/teambot/notifications/event_bus.py | EventBus.emit() for notification dispatch |
| REF-007 | Spec | docs/feature-specs/realtime-notifications.md | Existing notification architecture |
| REF-008 | Problem | .teambot/simple-notification-end/artifacts/problem_statement.md | Problem definition |

---

## 18. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Pseudo-agent | Agent ID recognized by router but not executed via Copilot SDK |
| $ref | Syntax for referencing output from another agent (e.g., `$pm`) |
| Pipeline | Sequence of agents executed in order, using `,` syntax |
| EventBus | Pub/sub system for dispatching notifications to channels |

### Implementation Notes

#### Pseudo-Agent Detection
The executor should detect `@notify` and bypass Copilot SDK execution:
```
if agent_id == "notify":
    return execute_notify_pseudo_agent(prompt, references)
```

#### Message Interpolation
References should be interpolated before sending:
```
# Input: "Review: $reviewer"
# After interpolation: "Review: [reviewer's output here]"
```

#### Truncation Logic
```
MAX_REF_LENGTH = 500
if len(output) > MAX_REF_LENGTH:
    output = output[:MAX_REF_LENGTH] + "..."
```

#### Confirmation Output
```
SUCCESS_OUTPUT = "Notification sent ✅"
FAILURE_OUTPUT = "Notification failed ⚠️ (warning logged)"
```

---

**VALIDATION_STATUS: PASS**
- Placeholders: 0 remaining
- Sections Complete: 18/18
- Technical Stack: DEFINED (Python, pytest, pytest-mock)
- Testing Approach: DEFINED (follow existing patterns)
- Acceptance Tests: 10 scenarios defined

<!-- markdown-table-prettify-ignore-end -->
