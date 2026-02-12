## Objective

- Introduce a `@notify` pseudo-agent that integrates notifications directly into agent pipelines, enabling users to send notifications at any point in a chain while leveraging existing `$ref` syntax for message content.

**Goal**:

- Users should be able to use `@notify` as a first-class participant in agent pipelines, not just as a terminal system command.
- `@notify` should accept a message string and send it to all configured notification channels.
- `@notify` should support `$ref` syntax to include output from previous agents in the notification message.
- `@notify` should return a simple confirmation output that downstream agents can reference, allowing the pipeline to continue.
- Large referenced outputs should be truncated to a reasonable length for notifications.
- Notification failures should not break the pipeline — the chain continues with a warning.
- The legacy `/notify` system command should be removed since `@notify` supersedes it entirely.
- The interactive agent status display should show `@notify` as an agent with model displayed as "(n/a)".

**Problem Statement**:

- The current `/notify` system command cannot be used within agent pipelines because the parser and executor only support agent commands (`@agent`) in the `->` chain syntax.
- Users who want to receive a notification when a multi-agent pipeline completes must manually run `/notify` afterward, which defeats the purpose of autonomous chaining.
- There is no way to send progress notifications mid-pipeline (e.g., "Plan complete, starting implementation").
- The existing `$ref` syntax for referencing agent outputs would be perfect for composing notification messages, but system commands don't support it.

**Success Criteria**:

- [ ] `@notify` is recognized as a valid agent ID in `VALID_AGENTS` (router.py) but is handled specially as a pseudo-agent.
- [ ] `@notify` can appear anywhere in a pipeline — beginning, middle, or end.
- [ ] `@notify` accepts a message string as its prompt: `@notify "Build complete!"`.
- [ ] `@notify` supports `$ref` syntax in the message: `@notify "Review done: $reviewer"`.
- [ ] Referenced agent outputs (`$ref`) are interpolated into the message before sending.
- [ ] Large referenced outputs are truncated (e.g., first 500 characters + "..." suffix) to keep notifications readable.
- [ ] `@notify` dispatches to all configured notification channels (same behavior as `/notify`).
- [ ] `@notify` returns a simple confirmation output: `"Notification sent ✅"` (or similar).
- [ ] The confirmation output is stored in `TaskManager._agent_results` so downstream agents can reference `$notify` if needed.
- [ ] If notification delivery fails (network error, invalid config, etc.), the pipeline continues with a warning logged — the failure does not stop the chain.
- [ ] The pseudo-agent bypasses Copilot SDK execution entirely — no API call is made to the Copilot CLI.
- [ ] The legacy `/notify` system command is removed from `SystemCommands` — `@notify` is the sole notification interface.
- [ ] The interactive agent status display (showing Idle/Active agents) includes `@notify` with model shown as "(n/a)".
- [ ] All new functionality has test coverage following existing patterns (`pytest` with `pytest-mock`).

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically the REPL layer (`src/teambot/repl/router.py`, `src/teambot/repl/parser.py`), task execution (`src/teambot/tasks/executor.py`, `src/teambot/tasks/manager.py`), and integration with the existing notifications module (`src/teambot/notifications/`).

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:

- Must not break existing agent pipeline functionality.
- Must integrate cleanly with the existing notification infrastructure (EventBus, channels, templates).
- Must work with all existing pipeline features: `$ref` dependencies, `&` background execution, multi-agent `,` syntax.
- Notification failures must be non-blocking — the pipeline always continues.

---

## Additional Context

### Usage Examples

```bash
# Simple notification at end of pipeline
@builder-1 implement feature -> @notify "Feature implemented!"

# Include previous agent output in notification
@reviewer review code -> @notify "Review complete: $reviewer"

# Mid-pipeline progress notification
@pm create plan -> @notify "Plan ready, starting build" -> @builder-1 implement $pm

# Multiple notifications in a chain
@pm plan -> @notify "Planning done" -> @builder-1 $pm -> @notify "Build done: $builder-1"

# Reference notify output (confirmation) in downstream agent
@pm plan -> @notify "Started" -> @builder-1 $pm $notify
# $notify resolves to "Notification sent ✅"
```

### Architecture

The `@notify` pseudo-agent introduces special handling at two layers:

1. **Router Layer** (`src/teambot/repl/router.py`):
   - Add `"notify"` to `VALID_AGENTS` set
   - Add detection logic to identify `@notify` as a pseudo-agent (not a real Copilot agent)

2. **Executor Layer** (`src/teambot/tasks/executor.py`):
   - Before calling Copilot SDK, check if agent_id is `"notify"`
   - If so, route to a dedicated `_execute_notify()` handler instead
   - `_execute_notify()`:
     - Interpolates `$ref` values into the message (reuse `_inject_references` logic)
     - Truncates large outputs (500 char limit + "...")
     - Calls notification system (reuse logic from `SystemCommands.handle_notify`)
     - Returns a synthetic `TaskResult` with output `"Notification sent ✅"`
     - On failure, logs warning and returns `TaskResult` with warning message

3. **Manager Layer** (`src/teambot/tasks/manager.py`):
   - Stores `@notify` result in `_agent_results["notify"]` like any other agent
   - Enables `$notify` reference in downstream stages

### Message Interpolation

The message to `@notify` undergoes `$ref` interpolation before sending:

```
Input:  @reviewer review -> @notify "Done: $reviewer"
                                          ↓
Interpolation: _inject_references("Done: $reviewer", ["reviewer"])
                                          ↓
Output: "Done: [reviewer's output, truncated if >500 chars]"
                                          ↓
Send to all notification channels
```

### Truncation Strategy

For notification readability, referenced outputs are truncated:

- Maximum length: 500 characters per reference
- Truncation suffix: `"... [truncated]"`
- Applied per-reference before message composition
- Full output remains available via `$ref` in actual agent stages (no truncation there)

### Failure Handling

When notification delivery fails:

1. Log warning with error details: `"@notify: Failed to send notification: {error}"`
2. Return `TaskResult(success=True, output="Notification failed (continuing): {error}")`
3. Pipeline continues to next stage
4. Downstream `$notify` references get the failure message

This matches the existing notification system's philosophy: notifications are informational and should never block workflow execution.

### Deprecation of `/notify` Command

The `/notify` system command is removed entirely:

- `@notify` supersedes `/notify` with full pipeline support
- No migration needed — `@notify "msg"` works identically for standalone use
- Reduces duplicate code paths and user confusion
- `/help` output updated to remove `/notify` reference

### Agent Status Display

The interactive UI showing agent status (Idle/Active) is updated:

- `@notify` appears in the agent list alongside `@pm`, `@builder-1`, etc.
- Status shown as "Idle" or "Active" like other agents
- Model column displays "(n/a)" since `@notify` doesn't use a language model
- Example display:
  ```
  Agent       Status   Model
  ──────────────────────────────
  pm          Idle     claude-sonnet-4
  builder-1   Active   claude-sonnet-4
  notify      Idle     (n/a)
  ```

---

## Task Breakdown

### Phase 1: Core Pseudo-Agent Infrastructure

- [ ] Add `"notify"` to `VALID_AGENTS` in `router.py`
- [ ] Add pseudo-agent detection logic in router/executor
- [ ] Implement `_execute_notify()` handler in `TaskExecutor`
- [ ] Implement message interpolation with `$ref` support
- [ ] Implement output truncation (500 char limit)
- [ ] Return synthetic `TaskResult` for pipeline continuation
- [ ] Store result in `TaskManager._agent_results`

### Phase 2: Notification Integration

- [ ] Integrate with existing notification system (EventBus/channels)
- [ ] Implement failure handling (warn and continue)
- [ ] Support all configured channels

### Phase 3: Legacy Cleanup

- [ ] Remove `/notify` command from `SystemCommands.dispatch()` in `commands.py`
- [ ] Remove `/notify` from `/help` output
- [ ] Remove any `/notify`-specific tests (replace with `@notify` equivalents)

### Phase 4: UI Integration

- [ ] Add `@notify` to agent status display in interactive UI
- [ ] Display model as "(n/a)" for `@notify` pseudo-agent
- [ ] Ensure status toggles between Idle/Active during execution

### Phase 5: Testing

- [ ] Unit tests for `_execute_notify()` handler
- [ ] Unit tests for message interpolation with `$ref`
- [ ] Unit tests for truncation logic
- [ ] Unit tests for failure handling (continue on error)
- [ ] Integration tests for `@notify` in pipelines
- [ ] Integration tests for `$notify` references in downstream stages
- [ ] Tests for `/notify` removal (command not recognized)

### Phase 6: Documentation

- [ ] Update interactive mode guide with `@notify` examples
- [ ] Update pipeline syntax documentation
- [ ] Add `@notify` to agent reference documentation

---
