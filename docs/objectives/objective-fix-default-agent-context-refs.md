## Objective

- Fix context reference (`$agent`) handling when using the default agent without explicit `@agent` prefix.

**Goal**:

- When a user types `Incorporate the feedback from $reviewer` without specifying an `@agent` prefix, and a default agent (e.g., `pm`) is configured, the `$reviewer` context reference should be correctly extracted and the referenced agent's output should be injected into the prompt.
- Currently, this works correctly when explicitly specifying the agent (e.g., `@pm Incorporate the feedback from $reviewer`), but fails when relying on the default agent routing.

**Problem Statement**:

- In both `src/teambot/repl/loop.py` (lines 309-314) and `src/teambot/ui/app.py` (lines 141-146), when raw input is routed to the default agent **without a pipeline operator** (`->`), a `Command` object is manually constructed:
  ```python
  command = Command(
      type=CommandType.AGENT,
      agent_id=default_agent,
      agent_ids=[default_agent],
      content=command.content,
  )
  ```
- This manually-created command does **not** extract `$agent` references from the content.
- References are only extracted when parsing goes through `_parse_agent_command()` in `parser.py` (lines 219-225), which calls `REFERENCE_PATTERN.findall(content)`.
- When the input contains a pipeline (`->`), the code correctly calls `prepend_default_agent()` and re-parses via `parse_command()`, which extracts references. But non-pipeline input bypasses this.
- The result is that `command.references` remains empty, so `_inject_references()` in the TaskExecutor never injects the referenced agent's output, and the receiving agent sees "[No output available]" or no context at all.

**Success Criteria**:
- [ ] Typing `Incorporate the feedback from $reviewer` (without `@pm` prefix) with a default agent configured correctly extracts `$reviewer` as a reference.
- [ ] The referenced agent's output is injected into the prompt, matching the behavior of `@pm Incorporate the feedback from $reviewer`.
- [ ] Multiple references (e.g., `$reviewer and $ba`) are all extracted correctly.
- [ ] Escaped references (`\$reviewer`) are not extracted, consistent with existing behavior.
- [ ] Pipeline inputs (e.g., `tell joke -> @notify`) continue to work correctly.
- [ ] Both `repl/loop.py` and `ui/app.py` are fixed to maintain consistency.
- [ ] All existing tests pass; new tests cover the default agent + reference extraction scenario.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `src/teambot/repl/loop.py`, `src/teambot/ui/app.py`, and `src/teambot/repl/parser.py`

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (pytest with pytest-mock)

**Key Constraints**:
- The fix should reuse the existing `REFERENCE_PATTERN` from `parser.py` to extract references, avoiding duplication.
- Consider creating a helper function in `parser.py` to extract references from content, which can be called from both code paths.
- Minimal changes — this is a targeted bug fix, not a refactor.
- Must not break existing explicit `@agent` command parsing or pipeline handling.

---

## Additional Context

- The `REFERENCE_PATTERN` regex in `parser.py:93` is: `r"(?<!\\)\$([a-zA-Z][a-zA-Z0-9_-]*)"`
- The reference extraction logic in `_parse_agent_command()` (lines 219-225) deduplicates while preserving order.

## Recommended Approach

**Always re-parse with `parse_command(prepend_default_agent(...))`**

Instead of conditionally handling pipeline vs non-pipeline input differently, always prepend the default agent and re-parse through `parse_command()`. This:

1. **Reduces complexity**: Fewer lines changed, no new helper function needed
2. **Improves reliability**: Uses the exact same parsing path as explicit `@agent` commands
3. **Future-proofs**: Automatically inherits any parser improvements (new flags, features)
4. **Unifies behavior**: Pipeline and non-pipeline default agent routing use identical logic

**Implementation**: In both `repl/loop.py` and `ui/app.py`, remove the conditional that distinguishes pipeline vs non-pipeline. Simply prepend the default agent and call `parse_command()` for all raw input when a default agent is configured.

---
