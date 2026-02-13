<!-- markdownlint-disable-file -->

# Remove Overlay Feature - Implementation Plan

**Feature**: Remove Overlay
**Date**: 2026-02-13
**Status**: Ready for Implementation

---

## Summary

Remove the unused persistent status overlay feature from TeamBot to reduce codebase complexity. This involves deleting ~1,315 lines of code across 4 files and modifying 8 integration points.

---

## Implementation Phases

| Phase | Description | Tasks | Est. Effort |
|-------|-------------|-------|-------------|
| 1 | Delete Overlay Tests | 2 | 10 min |
| 2 | Delete Core Module | 2 | 10 min |
| 3 | REPL Cleanup | 2 | 30 min |
| 4 | Config Cleanup | 2 | 15 min |
| 5 | Documentation | 3 | 15 min |
| 6 | Final Validation | 3 | 15 min |
| **Total** | | **14 tasks** | **~1.5 hours** |

---

## Task Checklist

### Phase 1: Delete Overlay Tests
- [ ] Task 1.1: Delete `tests/test_visualization/test_overlay.py`
- [ ] Task 1.2: Delete `tests/test_repl/test_commands_overlay.py`
- [ ] Verify: No import errors in remaining tests

### Phase 2: Delete Core Module
- [ ] Task 2.1: Delete `src/teambot/visualization/overlay.py`
- [ ] Task 2.2: Update `src/teambot/visualization/__init__.py` - remove exports
- [ ] Verify: `uv run ruff check src/teambot/visualization/`

### Phase 3: REPL Integration Cleanup
- [ ] Task 3.1: Update `src/teambot/repl/commands.py` - remove overlay handler
- [ ] Task 3.2: Update `src/teambot/repl/loop.py` - remove overlay integration
- [ ] Verify: `uv run pytest tests/test_repl/`

### Phase 4: Config Loader Cleanup
- [ ] Task 4.1: Update `src/teambot/config/loader.py` - remove validation
- [ ] Task 4.2: Update `tests/test_config/test_loader.py` - remove overlay tests
- [ ] Verify: `uv run pytest tests/test_config/`

### Phase 5: Documentation Cleanup
- [ ] Task 5.1: Update `docs/guides/architecture.md` - remove overlay section
- [ ] Task 5.2: Update `docs/guides/development.md` - remove overlay mention
- [ ] Task 5.3: Delete `docs/feature-specs/persistent-status-overlay.md`
- [ ] Verify: `grep -ri "overlay" docs/`

### Phase 6: Final Validation
- [ ] Task 6.1: Run full test suite: `uv run pytest`
- [ ] Task 6.2: Run linting: `uv run ruff check . && uv run ruff format -- .`
- [ ] Task 6.3: Verify no orphan refs: `grep -ri "overlay" src/teambot/`

---

## Files Summary

### Files to Delete (4)
| File | Lines |
|------|-------|
| `src/teambot/visualization/overlay.py` | 603 |
| `tests/test_visualization/test_overlay.py` | 571 |
| `tests/test_repl/test_commands_overlay.py` | 141 |
| `docs/feature-specs/persistent-status-overlay.md` | TBD |

### Files to Modify (8)
| File | Changes |
|------|---------|
| `src/teambot/visualization/__init__.py` | Remove overlay exports |
| `src/teambot/repl/commands.py` | Remove handler, help entry |
| `src/teambot/repl/loop.py` | Remove integration |
| `src/teambot/config/loader.py` | Remove validation |
| `tests/test_config/test_loader.py` | Remove overlay tests |
| `docs/guides/architecture.md` | Remove overlay section |
| `docs/guides/development.md` | Remove overlay mention |

---

## Success Criteria

- [ ] All overlay code deleted (0 lines remaining)
- [ ] Full test suite passes (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] No orphan imports (`grep -ri "overlay" src/` returns empty)
- [ ] Documentation updated (no stale references)
- [ ] Coverage maintained (≥ 80%)

---

## References

- **Plan Details**: `.agent-tracking/plans/20260213-remove-overlay-plan.instructions.md`
- **Implementation Details**: `.agent-tracking/details/20260213-remove-overlay-details.md`
- **Research**: `.teambot/remove-overlay/artifacts/research.md`
- **Test Strategy**: `.teambot/remove-overlay/artifacts/test_strategy.md`
- **Feature Spec**: `.teambot/remove-overlay/artifacts/feature_spec.md`
