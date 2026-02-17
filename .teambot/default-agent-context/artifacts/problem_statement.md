# Problem Statement: Context References Not Extracted for Default Agent Routing

## Business Problem

When users type a command that references another agent's output using the `$agent` syntax (e.g., `Incorporate the feedback from $reviewer`), the referenced agent's output should be injected into the prompt. This works correctly when the user explicitly specifies the target agent (e.g., `@pm Incorporate the feedback from $reviewer`), but **fails silently when relying on default agent routing**.

This inconsistency forces users to always type the `@agent` prefix, negating the productivity benefit of configuring a default agent. Users expect the behavior to be identical whether they explicitly specify the agent or rely on the configured default.

## Root Cause

When a command is routed to the default agent, the system creates a `Command` object manually rather than using the standard `parse_command()` function. This manual instantiation **bypasses the reference extraction logic** that uses `REFERENCE_PATTERN` to detect `$agent` references in the content.

| Input Path | Reference Extraction | Result |
|------------|---------------------|--------|
| Explicit `@pm task $reviewer` | ✓ Via `parse_command()` | Works correctly |
| Default routing `task $reviewer` | ✗ Manual `Command()` instantiation | **References field empty** |

## Affected Components

- `src/teambot/repl/loop.py` — REPL input handling (lines ~298-314)
- `src/teambot/ui/app.py` — UI input handling (lines ~131-146)
- Both paths contain identical logic with the same gap

## Business Impact

| Impact Area | Description |
|-------------|-------------|
| **User Experience** | Inconsistent behavior erodes user trust and causes confusion |
| **Productivity** | Users must remember to always prefix commands, reducing efficiency |
| **Adoption** | Default agent feature appears broken, discouraging its use |

## Goals

1. **Consistency**: `Incorporate the feedback from $reviewer` (without prefix) should behave identically to `@pm Incorporate the feedback from $reviewer` when a default agent is configured.

2. **Reference Extraction**: All `$agent` references must be extracted from user input, regardless of whether an explicit agent prefix is used.

3. **Backward Compatibility**: Existing explicit `@agent` commands, escaped references (`\$reviewer`), and pipeline inputs (`tell joke -> @notify`) must continue to work correctly.

## Success Criteria

| Criterion | Verification Method |
|-----------|---------------------|
| `Incorporate the feedback from $reviewer` (no prefix) correctly extracts `$reviewer` | Unit test |
| Referenced agent's output is injected into prompt | Integration test |
| Multiple references (`$reviewer and $ba`) all extracted correctly | Unit test |
| Escaped references (`\$reviewer`) are not extracted | Unit test (existing) |
| Pipeline inputs (`tell joke -> @notify`) continue working | Unit test (existing) |
| Both `repl/loop.py` and `ui/app.py` fixed consistently | Code review |
| All existing tests pass | CI pipeline |
| New tests cover default agent + reference extraction | Test coverage report |

## Constraints

- **Minimal Changes**: This is a targeted bug fix, not a refactor
- **Reuse Existing Logic**: Use `REFERENCE_PATTERN` from `parser.py` to avoid duplication
- **Helper Function**: Consider creating a shared helper in `parser.py` for reference extraction
- **No Breaking Changes**: Must not affect explicit `@agent` parsing or pipeline handling

## Stakeholders

| Role | Interest |
|------|----------|
| End Users | Consistent, predictable behavior when using context references |
| Developers | Clean implementation that follows existing patterns |
| QA | Testable fix with clear acceptance criteria |

## Out of Scope

- Changes to how references are resolved or injected (working correctly)
- Changes to REFERENCE_PATTERN syntax
- UI/UX changes beyond fixing the bug
- Performance optimizations

---

*Document Created: Business Problem Stage*  
*Next Stage: SPEC — Detailed feature specification*
