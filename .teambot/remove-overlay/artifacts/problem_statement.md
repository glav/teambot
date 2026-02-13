# Problem Statement: Remove Overlay Feature

## Business Problem

The persistent status overlay feature in TeamBot displays real-time agent and task status in a fixed terminal position. **This feature is no longer needed or used** and should be removed from the codebase.

## Why This Is a Problem

| Issue | Impact |
|-------|--------|
| **Unused functionality** | Feature provides no current value to users |
| **Maintenance burden** | ~600+ lines of code requiring ongoing maintenance |
| **Codebase complexity** | Adds complexity to REPL, config loader, and task executor |
| **Technical debt** | Keeping unused code increases cognitive load for developers |

## Business Goals

1. **Reduce maintenance overhead** - Eliminate code that provides no business value
2. **Simplify the product** - Remove feature clutter from the REPL interface
3. **Improve developer experience** - Less code to understand and maintain

## Success Criteria

| Criterion | Measurable Target |
|-----------|-------------------|
| **Complete removal** | All overlay-related files, code, and tests are deleted |
| **No regressions** | All existing tests pass (`uv run pytest`) |
| **Clean codebase** | Linting passes (`uv run ruff check .`) |
| **Updated documentation** | No stale references to overlay in docs |
| **Working REPL** | REPL functions normally without `/overlay` command |

## Scope

### In Scope

- Delete `src/teambot/visualization/overlay.py` (~603 lines)
- Delete overlay-specific test files
- Delete overlay feature specification
- Remove `/overlay` REPL command and help entry
- Remove overlay configuration options from config loader
- Remove overlay event hooks from task executor
- Update documentation to remove overlay references

### Out of Scope

- Other visualization features (startup animation, console output)
- REPL refactoring beyond overlay removal
- Task execution system changes beyond hook removal

## Stakeholders

| Role | Interest |
|------|----------|
| **Developers** | Reduced maintenance burden, simpler codebase |
| **Users** | Cleaner REPL interface (one less command to learn) |
| **Maintainers** | Less code to review and update |

## Assumptions

1. No users actively depend on the overlay feature
2. Removing the feature will not break existing workflows
3. Related tests can be safely deleted

## Dependencies

- None - this is a pure removal operation with no external dependencies

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Incomplete removal leaves orphan code | Low | Thorough code search for overlay references |
| Broken imports after deletion | Low | Run full test suite to verify |
| Documentation becomes inconsistent | Low | Search docs for overlay mentions |

---

*Artifact created: 2026-02-13*
*Stage: BUSINESS_PROBLEM*
