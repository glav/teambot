# Test Results - init-conflict-detection

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 125 |
| **Passing** | 125 |
| **Failing** | 0 |
| **Skipped** | 0 |
| **Duration** | 65.59s |

## New Tests Added

### scaffolds.py Tests (20 tests)

| Test Class | Count | Status |
|------------|-------|--------|
| TestExtractNumberedPrefix | 6 | ✅ All Pass |
| TestConflictInfo | 2 | ✅ All Pass |
| TestDetectSddConflicts | 7 | ✅ All Pass |
| TestBackupDirectory | 5 | ✅ All Pass |

### cli.py Tests (12 tests)

| Test Class | Count | Status |
|------------|-------|--------|
| TestInitConflictHandling | 7 | ✅ All Pass |
| TestPromptConflictResolution | 5 | ✅ All Pass |

## Coverage

| File | Coverage |
|------|----------|
| scaffolds.py | 88% |
| cli.py | 27% |
| **Overall** | 30% |

## Test Execution

```
pytest tests/test_scaffolds.py tests/test_cli.py -v
================== 125 passed, 1 warning in 65.59s ===================
```

## Linting Results

```
ruff check src/teambot/scaffolds.py src/teambot/cli.py
All checks passed!

ruff format --check src/teambot/scaffolds.py src/teambot/cli.py
2 files already formatted
```
