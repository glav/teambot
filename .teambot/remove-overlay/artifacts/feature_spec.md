<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Remove Overlay Feature - Specification Document

Version 1.0 | Status Draft | Owner @ba | Team TeamBot | Target N/A | Lifecycle Deprecation

## Progress Tracker

| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-13 |
| Problem & Users | ✅ | None | 2026-02-13 |
| Scope | ✅ | None | 2026-02-13 |
| Requirements | ✅ | None | 2026-02-13 |
| Metrics & Risks | ✅ | None | 2026-02-13 |
| Operationalization | ✅ | None | 2026-02-13 |
| Finalization | ⏳ | Pending review | 2026-02-13 |

Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context

TeamBot includes a persistent status overlay feature (`/overlay`) that displays real-time agent and task status in a fixed terminal position. This feature was implemented to provide visual feedback during multi-agent operations but has not been adopted by users.

### Core Opportunity

Remove unused functionality to reduce codebase complexity, eliminate maintenance burden, and simplify the REPL interface. This is a **deprecation and removal** initiative, not a feature addition.

### Goals

| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Reduce codebase complexity | Technical Debt | ~600 lines overlay code | 0 lines overlay code | Immediate | High |
| G-002 | Eliminate maintenance burden | Operational | Ongoing maintenance required | No overlay maintenance | Immediate | High |
| G-003 | Simplify REPL interface | User Experience | 1 unused command `/overlay` | Command removed | Immediate | Medium |

---

## 2. Problem Definition

### Current Situation

The overlay feature exists in the codebase with the following components:
- `src/teambot/visualization/overlay.py` (~603 lines)
- REPL command handler for `/overlay`
- Configuration options in `teambot.json`
- Event hooks in TaskExecutor
- Test files and documentation

### Problem Statement

The persistent status overlay feature is **unused and adds unnecessary complexity** to the TeamBot codebase. Maintaining this feature requires:
- Code reviews for any visualization changes
- Test maintenance for ~600 lines of code
- Documentation upkeep
- Cognitive load for developers understanding the codebase

### Root Causes

- Feature was built speculatively without validated user demand
- Terminal overlay rendering is complex and adds dependencies
- Alternative status visibility exists through standard console output

### Impact of Inaction

Continuing to maintain unused code:
- Wastes developer time on reviews and maintenance
- Increases onboarding complexity for new contributors
- Creates risk of bugs in unused code paths
- Bloats the codebase unnecessarily

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| TeamBot Developer | Maintain clean, simple codebase | Unused code adds complexity | Positive - less code to maintain |
| TeamBot Contributor | Understand codebase quickly | Extra features to learn | Positive - simpler onboarding |
| TeamBot User | Use REPL effectively | N/A (feature unused) | Neutral - no change in workflow |

---

## 4. Scope

### In Scope

| Item | Description |
|------|-------------|
| Delete `overlay.py` | Remove core overlay renderer module (~603 lines) |
| Delete test files | Remove `test_overlay.py` and `test_commands_overlay.py` |
| Delete feature spec | Remove `docs/feature-specs/persistent-status-overlay.md` |
| Remove REPL command | Remove `/overlay` command handler and `/help` entry |
| Remove config options | Remove `overlay.enabled` and `overlay.position` validation |
| Remove event hooks | Remove overlay callbacks from TaskExecutor |
| Update `__init__.py` | Remove overlay exports from visualization module |
| Update documentation | Remove overlay references from guides |

### Out of Scope

| Item | Justification |
|------|---------------|
| Other visualization features | Startup animation, console output remain unchanged |
| REPL refactoring | Only remove overlay-specific code |
| Task executor refactoring | Only remove overlay hooks |
| Configuration schema changes | Only remove overlay-specific options |

### Assumptions

| ID | Assumption | Validation |
|----|------------|------------|
| A-001 | No users actively depend on the overlay feature | Feature usage analytics (none observed) |
| A-002 | Removing the feature will not break existing workflows | Test suite validates core functionality |
| A-003 | Related tests can be safely deleted | Tests are overlay-specific only |

### Constraints

| ID | Constraint | Impact |
|----|------------|--------|
| C-001 | Must not break existing REPL commands | Careful removal of only overlay code |
| C-002 | Must pass all remaining tests | Full test suite execution required |
| C-003 | Must pass linting | Code cleanup must be complete |

---

## 5. Technical Stack

| Aspect | Value |
|--------|-------|
| **Language** | Python 3.10+ |
| **Framework** | TeamBot CLI (Click-based) |
| **Testing Approach** | Test-last (removal operation - delete tests with code) |
| **Key Dependencies** | None removed (Rich library remains for other features) |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance Criteria |
|-------|-------|-------------|-------|----------|---------------------|
| FR-001 | Delete overlay module | Remove `src/teambot/visualization/overlay.py` | G-001 | High | File no longer exists |
| FR-002 | Delete overlay tests | Remove `tests/test_visualization/test_overlay.py` and `tests/test_repl/test_commands_overlay.py` | G-001 | High | Test files no longer exist |
| FR-003 | Delete overlay spec | Remove `docs/feature-specs/persistent-status-overlay.md` | G-001 | High | Doc file no longer exists |
| FR-004 | Remove REPL command | Remove `/overlay` from command handler | G-003 | High | `/overlay` returns "unknown command" |
| FR-005 | Remove help entry | Remove `/overlay` from `/help` output | G-003 | High | `/help` does not list overlay |
| FR-006 | Remove config validation | Remove overlay config from loader | G-001 | High | Config loads without overlay options |
| FR-007 | Remove config defaults | Remove overlay defaults from loader | G-001 | High | No overlay in default config |
| FR-008 | Remove visualization exports | Remove overlay from `__init__.py` | G-001 | High | No import errors |
| FR-009 | Remove REPL integration | Remove overlay from REPL loop | G-001 | High | REPL starts without overlay |
| FR-010 | Remove executor hooks | Remove overlay callbacks from TaskExecutor | G-001 | High | Executor runs without overlay |
| FR-011 | Update architecture docs | Remove overlay from `docs/guides/architecture.md` | G-001 | Medium | No overlay references |
| FR-012 | Update development docs | Remove overlay from `docs/guides/development.md` | G-001 | Medium | No overlay references |
| FR-013 | Remove config tests | Remove overlay tests from `tests/test_config/test_loader.py` | G-001 | High | Config tests pass |

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation |
|--------|----------|-------------|---------------|----------|------------|
| NFR-001 | Reliability | All existing tests pass | 100% pass rate | High | `uv run pytest` |
| NFR-002 | Maintainability | No orphan imports or references | 0 overlay references | High | `grep -r "overlay"` |
| NFR-003 | Code Quality | Linting passes | 0 errors | High | `uv run ruff check .` |
| NFR-004 | Documentation | No stale documentation | 0 overlay mentions in guides | Medium | Manual review |
| NFR-005 | Backward Compatibility | REPL functions normally | All other commands work | High | Manual testing |

---

## 8. Acceptance Test Scenarios

### AT-001: REPL Starts Successfully Without Overlay

**Description**: Verify REPL initializes and runs without overlay feature
**Preconditions**: Overlay code has been removed
**Steps**:
1. Run `uv run teambot init` in a test directory
2. Run `uv run teambot run` to start REPL
3. Observe REPL prompt appears
**Expected Result**: REPL starts successfully without errors
**Verification**: No import errors, no overlay-related exceptions

### AT-002: Unknown Command Response for /overlay

**Description**: Verify `/overlay` command is no longer recognized
**Preconditions**: REPL is running, overlay command removed
**Steps**:
1. Start REPL
2. Enter `/overlay`
3. Observe response
**Expected Result**: REPL responds with "Unknown command" or similar
**Verification**: No overlay functionality executes

### AT-003: Help Command Excludes Overlay

**Description**: Verify `/help` no longer lists overlay command
**Preconditions**: REPL is running, overlay removed from help
**Steps**:
1. Start REPL
2. Enter `/help`
3. Review command list
**Expected Result**: No `/overlay` entry in help output
**Verification**: Grep output for "overlay" returns nothing

### AT-004: Full Test Suite Passes

**Description**: Verify all remaining tests pass after removal
**Preconditions**: Overlay code and tests removed
**Steps**:
1. Run `uv run pytest`
2. Review test results
**Expected Result**: All tests pass (excluding deleted overlay tests)
**Verification**: Exit code 0, no failures

### AT-005: Linting Passes

**Description**: Verify no linting errors after removal
**Preconditions**: Overlay code removed, imports cleaned
**Steps**:
1. Run `uv run ruff check .`
2. Review output
**Expected Result**: No errors (exit code 0)
**Verification**: Clean linting output

### AT-006: Config Loads Without Overlay Options

**Description**: Verify configuration loads without overlay-specific options
**Preconditions**: Overlay config validation removed
**Steps**:
1. Create a `teambot.json` without overlay settings
2. Run `uv run teambot init`
3. Verify no errors about missing overlay config
**Expected Result**: Config loads successfully
**Verification**: No validation errors for overlay options

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| None | N/A | N/A | N/A | N/A | Pure removal - no external dependencies |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Incomplete removal leaves orphan code | Medium | Low | Thorough grep search for "overlay" references | Builder | Open |
| R-002 | Broken imports after deletion | Medium | Low | Run full test suite after each file deletion | Builder | Open |
| R-003 | Documentation inconsistency | Low | Low | Search all docs for overlay mentions | Builder | Open |
| R-004 | Missed test file dependencies | Medium | Low | Review test imports before deletion | Builder | Open |

---

## 11. Files to Modify

### Files to Delete

| File Path | Lines | Description |
|-----------|-------|-------------|
| `src/teambot/visualization/overlay.py` | ~603 | Core overlay renderer module |
| `tests/test_visualization/test_overlay.py` | TBD | Overlay unit tests |
| `tests/test_repl/test_commands_overlay.py` | TBD | REPL overlay command tests |
| `docs/feature-specs/persistent-status-overlay.md` | TBD | Feature specification |

### Files to Modify

| File Path | Changes Required |
|-----------|------------------|
| `src/teambot/visualization/__init__.py` | Remove overlay exports |
| `src/teambot/repl/commands.py` | Remove `/overlay` handler and `/help` entry |
| `src/teambot/repl/loop.py` | Remove overlay integration |
| `src/teambot/config/loader.py` | Remove overlay config validation/defaults |
| `src/teambot/tasks/executor.py` | Remove overlay event callbacks |
| `docs/guides/architecture.md` | Remove overlay references |
| `docs/guides/development.md` | Remove overlay references |
| `tests/test_config/test_loader.py` | Remove overlay config tests |

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard release | No special deployment needed |
| Rollback | Git revert | Can restore from version control if needed |
| Monitoring | N/A | No runtime monitoring changes |
| Alerting | N/A | No alerting changes |
| Support | N/A | No support model changes |

---

## 13. Rollout Plan

| Phase | Description | Gate Criteria |
|-------|-------------|---------------|
| 1. Delete files | Remove overlay.py, tests, and spec | Files deleted |
| 2. Remove integrations | Clean up imports and references | No import errors |
| 3. Update config | Remove overlay config handling | Config loads |
| 4. Update docs | Remove overlay from guides | No stale refs |
| 5. Validate | Run full test suite and linting | All pass |

---

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| None | All questions resolved | N/A | N/A | N/A |

---

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-13 | @ba | Initial specification | Created |

---

## 16. References

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Objective | `docs/objectives/objective-remove-overlay.md` | Original removal objective |
| REF-002 | Problem Statement | `.teambot/remove-overlay/artifacts/problem_statement.md` | Business problem definition |
| REF-003 | Feature Spec | `docs/feature-specs/persistent-status-overlay.md` | Original feature specification |

---

Generated 2026-02-13 by @ba (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
