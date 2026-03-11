# Implementation Plan: Init Conflict Detection

## Summary

This plan implements conflict detection for `teambot init` when the target `.agent/` directory contains SDD prompt files with the same numbered prefix but different names than the current scaffolds.

## Phases Overview

| Phase | Name | Tasks | Approach | Estimated Effort |
|-------|------|-------|----------|------------------|
| 1 | Test Core Logic | 3 | TDD | 30 min |
| 2 | Implement Core Logic | 2 | Code | 45 min |
| 3 | Test Backup | 1 | TDD | 20 min |
| 4 | Implement Backup | 1 | Code | 30 min |
| 5 | CLI Integration | 3 | Code | 60 min |
| 6 | Integration Tests | 2 | Test | 45 min |

**Total: 12 tasks across 6 phases (~4 hours)**

## Key Deliverables

1. **Core Functions** (`src/teambot/scaffolds.py`):
   - `ConflictInfo` dataclass
   - `extract_numbered_prefix()` - Parse `sdd.N-` patterns
   - `detect_sdd_conflicts()` - Find conflicting files
   - `backup_directory()` - Timestamped backup

2. **CLI Integration** (`src/teambot/cli.py`):
   - `prompt_conflict_resolution()` - Interactive menu
   - `--on-conflict` flag - Non-interactive mode
   - Updated `cmd_init()` - Conflict detection flow

3. **Tests**:
   - `TestExtractNumberedPrefix` - Prefix parsing
   - `TestDetectSddConflicts` - Conflict detection
   - `TestBackupDirectory` - Backup operations
   - `TestInitConflictHandling` - CLI integration

## Critical Path

```
T1.2 (Test conflicts) → T2.2 (Implement conflicts) → T5.3 (Update cmd_init) → T6.1 (Integration tests)
```

## Files Modified

| File | Changes |
|------|---------|
| `src/teambot/scaffolds.py` | Add ConflictInfo, extract_numbered_prefix, detect_sdd_conflicts, backup_directory |
| `src/teambot/cli.py` | Add prompt_conflict_resolution, --on-conflict flag, update cmd_init |
| `tests/test_scaffolds.py` | Add TestExtractNumberedPrefix, TestDetectSddConflicts, TestBackupDirectory |
| `tests/test_cli.py` | Add TestInitConflictHandling |

## Validation Commands

```bash
# Run conflict detection tests
uv run pytest tests/test_scaffolds.py -v -k "conflict or prefix or backup"

# Run CLI integration tests
uv run pytest tests/test_cli.py -v -k "conflict"

# Full test suite
uv run pytest --cov=src/teambot --cov-report=term-missing

# Lint check
uv run ruff check . && uv run ruff format --check .
```

## Detailed Plan Files

- **Plan**: `.agent-tracking/plans/20260310-init-conflict-detection-plan.instructions.md`
- **Details**: `.agent-tracking/details/20260310-init-conflict-detection-details.md`
- **Research**: `.agent-tracking/research/20260310-init-conflict-detection-research.md`
