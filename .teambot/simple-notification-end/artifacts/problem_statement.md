# Problem Statement: `@notify` as First-Class Pipeline Agent

## Business Problem

### Current State

TeamBot users currently have **two disconnected mechanisms** for sending notifications:

1. **`/notify <message>`** — A system command that sends a one-off message to configured notification channels. However, it operates outside the agent pipeline, meaning:
   - It cannot reference output from previous agents using `$ref` syntax
   - It cannot be chained with other agents in a pipeline
   - It halts pipeline flow rather than continuing execution
   - It doesn't integrate with the task management system

2. **Event-driven notifications** — The EventBus emits events at predefined workflow milestones (stage completion, errors), but users cannot trigger custom notifications at arbitrary points in their pipelines.

This creates a **usability gap**: users who want to notify stakeholders mid-pipeline (e.g., "Review complete, changes approved by $reviewer") must either:
- Break their pipeline into separate commands
- Use external tooling outside TeamBot
- Manually copy/paste agent outputs into `/notify` commands

### Pain Points

| Issue | Impact |
|-------|--------|
| **No pipeline integration** | Users cannot compose notifications with agent results in a single command |
| **Two interfaces for same action** | Cognitive overhead: when to use `/notify` vs. other methods |
| **No `$ref` support** | Cannot dynamically include agent outputs in notification messages |
| **Pipeline breaks on notify** | `/notify` doesn't return a result that downstream agents can reference |
| **No status visibility** | Users don't see notification status in the agent display |

---

## Goals

### Primary Goal

Enable users to include notifications as **first-class participants** in agent pipelines, allowing seamless composition with other agents using existing pipeline syntax (`$ref`, `&`, `,`).

### Measurable Objectives

| Objective | Metric |
|-----------|--------|
| **Pipeline integration** | `@notify` can appear at any position (start, middle, end) in a pipeline |
| **Reference support** | `$ref` syntax resolves and interpolates agent outputs into messages |
| **Non-blocking execution** | Notification failures log warnings but do not halt the pipeline |
| **Result continuity** | `@notify` returns a confirmation stored in `TaskManager._agent_results` |
| **Interface consolidation** | Single `@notify` interface replaces legacy `/notify` command |
| **Status visibility** | `@notify` appears in agent status display with model "(n/a)" |

---

## Scope

### In Scope

1. **New pseudo-agent `@notify`**
   - Recognized in `VALID_AGENTS` but handled specially (no Copilot SDK call)
   - Accepts a message string as its prompt
   - Dispatches to all configured notification channels via EventBus

2. **`$ref` interpolation**
   - Messages containing `$agent` references are resolved before sending
   - Large outputs truncated to ~500 characters with "..." suffix

3. **Pipeline-safe execution**
   - Returns confirmation output (e.g., `"Notification sent ✅"`)
   - Stores result in `_agent_results["notify"]` for downstream `$notify` references
   - Failures emit warning log but do not raise exceptions

4. **Legacy removal**
   - Remove `/notify` system command from `SystemCommands`

5. **UI integration**
   - Show `@notify` in interactive agent status display
   - Display model as "(n/a)" to indicate pseudo-agent status

### Out of Scope

- New notification channels (Telegram is sufficient for MVP)
- Message templating beyond `$ref` interpolation
- Notification delivery confirmation/receipts
- Two-way notification interactions (replies)
- Scheduled or delayed notifications

---

## Success Criteria

### Functional Requirements

- [ ] `@notify` is recognized as a valid agent ID in `VALID_AGENTS`
- [ ] `@notify` can appear anywhere in a pipeline (beginning, middle, end)
- [ ] `@notify` accepts a message string: `@notify "Build complete!"`
- [ ] `@notify` supports `$ref` syntax: `@notify "Review: $reviewer"`
- [ ] Referenced outputs are interpolated into messages before sending
- [ ] Large referenced outputs truncated (500 chars + "..." suffix)
- [ ] `@notify` dispatches to all configured notification channels
- [ ] `@notify` returns confirmation output: `"Notification sent ✅"`
- [ ] Confirmation stored in `TaskManager._agent_results` for downstream references
- [ ] Notification failures log warnings but don't break pipelines
- [ ] Pseudo-agent bypasses Copilot SDK execution entirely
- [ ] Legacy `/notify` system command removed from `SystemCommands`
- [ ] Interactive agent status display shows `@notify` with model "(n/a)"

### Non-Functional Requirements

- [ ] All new functionality has test coverage (pytest with pytest-mock)
- [ ] No regressions in existing agent pipeline functionality
- [ ] Clean integration with existing EventBus/channel infrastructure

---

## Stakeholders

| Role | Interest |
|------|----------|
| **TeamBot Users** | Seamless notification integration in agent workflows |
| **Pipeline Authors** | Composable notification syntax consistent with agent patterns |
| **System Operators** | Reliable, non-blocking notification delivery |

---

## Assumptions

1. The existing notification infrastructure (EventBus, TelegramChannel) is stable and sufficient
2. Users understand the `@agent` and `$ref` syntax from existing documentation
3. Truncation at 500 characters provides sufficient context for most use cases
4. A single `@notify` pseudo-agent (not per-channel agents) meets user needs

---

## Dependencies

| Dependency | Component | Impact |
|------------|-----------|--------|
| **EventBus** | `src/teambot/notifications/event_bus.py` | Must emit custom messages |
| **Router** | `src/teambot/repl/router.py` | Must recognize `@notify` as valid |
| **Parser** | `src/teambot/repl/parser.py` | `$ref` extraction must work in notify messages |
| **TaskManager** | `src/teambot/tasks/manager.py` | Must store notify results |
| **Executor** | `src/teambot/tasks/executor.py` | Must handle pseudo-agent specially |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing pipelines | Low | High | Comprehensive regression tests |
| Notification failures blocking pipelines | Medium | High | Try/except wrapper with warning logs |
| Large `$ref` outputs causing issues | Medium | Low | Truncation with clear suffix |
| User confusion during transition | Low | Medium | Clear migration note in changelog |

---

## Open Questions

1. **Truncation limit**: Is 500 characters the right threshold, or should it be configurable?
2. **Multiple notifications**: Should `@notify` support multiple messages in one call?
3. **Channel selection**: Should users be able to target specific channels (e.g., `@notify:telegram`)?

---

*Document Version: 1.0*  
*Stage: Business Problem Definition*  
*Status: Ready for Review*
