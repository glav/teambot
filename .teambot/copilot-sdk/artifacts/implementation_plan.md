<!-- markdownlint-disable-file -->

# Implementation Plan: GitHub Copilot SDK Upgrade (0.1.16 → 0.1.23)

> This is the stage artifact summary. Full plan and details are in:
> - **Plan**: `.agent-tracking/plans/20260210-copilot-sdk-upgrade-plan.instructions.md`
> - **Details**: `.agent-tracking/details/20260210-copilot-sdk-upgrade-details.md`
> - **Research**: `.agent-tracking/research/20260210-copilot-sdk-upgrade-research.md`
> - **Test Strategy**: `.agent-tracking/test-strategies/20260210-copilot-sdk-upgrade-test-strategy.md`

## Summary

Upgrade `github-copilot-sdk` from `==0.1.16` to `==0.1.23` with minimal code changes for compatibility.

## Phases

### Phase 1: Dependency Update (2 tasks)
1. Update version pin in `pyproject.toml` (line 11)
2. Regenerate `uv.lock` and sync environment

### Phase 2: Compatibility Fixes (2 tasks)
3. Fix `_check_auth()` breaking change — `status.get()` → `getattr()` in `sdk_client.py` (line 125)
4. Update `list_sessions()` return type from `list[dict[str, Any]]` to `list[Any]` (line 477)

### Phase 3: Feature Enhancement (1 task)
5. Add SDK version display to `/help` command output using `importlib.metadata`

### Phase 4: Validation (4 tasks)
6. Run full test suite (`uv run pytest`) — expect ~1084 tests pass
7. Run linting (`uv run ruff check .`)
8. Add `test_help_shows_sdk_version` test assertion
9. CLI smoke test (`uv run teambot --help`)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth fix approach | `getattr()` | Works with both dataclass (prod) and dict (test mocks) |
| Version source | `importlib.metadata.version()` | SDK `__version__` is always `"0.1.0"` — metadata is accurate |
| Testing approach | Code-First | Low complexity, existing tests provide regression safety |
| list_sessions type | `list[Any]` | Honest passthrough — SDK now returns dataclass objects |

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `pyproject.toml` | Version pin `0.1.16` → `0.1.23` | 11 |
| `src/teambot/copilot/sdk_client.py` | `getattr()` fix + type annotation | 125, 477 |
| `src/teambot/repl/commands.py` | Add import + version in help | 1-7, 83-115 |
| `tests/test_repl/test_commands.py` | New test assertion | after 51 |
| `uv.lock` | Regenerated | auto |

## Risk Assessment

- **Overall Risk**: LOW
- **Breaking Changes**: 1 identified and documented (`GetAuthStatusResponse` dataclass)
- **Test Coverage**: ~1084 existing tests cover all SDK integration points
- **Rollback**: Revert `pyproject.toml` + `uv lock` to restore 0.1.16

## Success Criteria

- [ ] `pyproject.toml` → `github-copilot-sdk==0.1.23`
- [ ] `uv.lock` regenerated
- [ ] All tests pass, linting clean
- [ ] `/help` shows SDK version
- [ ] CLI starts successfully
