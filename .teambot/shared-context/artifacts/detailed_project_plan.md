# Detailed Project Plan: Shared Context Reference Syntax (`$agent`)

## Executive Summary

This project implements a new `$agent` syntax for TeamBot that allows users to reference another agent's most recent output within prompts. This enables intuitive, dependency-based workflows where one agent can wait for and consume another agent's results.

**Project Code**: TEAMBOT-SHARED-CONTEXT  
**Status**: APPROVED FOR IMPLEMENTATION  
**Estimated Effort**: ~9 hours  
**Priority**: HIGH

---

## Business Objectives

### Problem Statement
Currently, TeamBot users must manually copy/paste agent outputs or use explicit pipeline syntax (`->`) to chain agent work. There's no simple way to reference a previous agent's completed work.

### Solution
Implement `$agent` syntax (e.g., `$pm`, `$ba`, `$builder-1`) that:
1. Automatically detects references in user prompts
2. Waits for referenced agents if they're still running
3. Injects referenced output into the prompt
4. Updates status overlay to show waiting state

### Success Criteria
- [ ] `$agent` syntax parses correctly (e.g., `@pm task $ba`)
- [ ] Referencing agent waits for running referenced agent
- [ ] Status overlay shows waiting/executing/idle accurately
- [ ] README documents both `$ref` and `->` syntax with comparison
- [ ] All existing tests pass
- [ ] Coverage targets met (85% overall)

---

## Stakeholders

| Role | Responsibility |
|------|---------------|
| Project Manager | Planning, coordination, progress tracking |
| Builder Agent(s) | Implementation, testing |
| Reviewer Agent | Code review, QA |
| End Users | Feature validation |

---

## Technical Scope

### In Scope
- Parser changes for `$agent` reference detection
- TaskManager agent result storage and retrieval
- TaskExecutor waiting and injection logic
- REPL routing updates for referenced commands
- Overlay status display for waiting state
- README documentation updates

### Out of Scope
- Changes to pipeline (`->`) syntax
- Multi-session result persistence
- Result expiration/cleanup policies
- UI changes beyond overlay updates

### Key Files to Modify

| Component | File | Changes |
|-----------|------|---------|
| Parser | `src/teambot/repl/parser.py` | Add REFERENCE_PATTERN, Command.references field |
| Models | `src/teambot/tasks/models.py` | Add TaskStatus.WAITING |
| Manager | `src/teambot/tasks/manager.py` | Add _agent_results, lookup methods |
| Executor | `src/teambot/tasks/executor.py` | Add wait/inject methods, update _execute_simple |
| REPL | `src/teambot/repl/loop.py` | Update routing condition |
| Overlay | `src/teambot/visualization/overlay.py` | Add waiting_count, waiting_for display |
| Docs | `README.md` | Add syntax section, comparison table |

---

## Detailed Phase Breakdown

### Phase 1: Parser & Model Extensions
**Objective**: Enable parsing of `$agent` references in command content  
**Effort**: 1 hour  
**Test Strategy**: TDD  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 1.1 Add WAITING status to TaskStatus enum | models.py | HIGH | None |
| 1.2 Add `references` field to Command dataclass | parser.py | CRITICAL | None |
| 1.3 Add REFERENCE_PATTERN regex constant | parser.py | CRITICAL | None |
| 1.4 Implement reference detection in _parse_agent_command() | parser.py | CRITICAL | 1.2, 1.3 |

**Phase Gate Criteria**:
- [ ] `TaskStatus.WAITING` exists in enum
- [ ] `Command.references` field available
- [ ] `parse_command("@pm task $ba")` returns `references=["ba"]`
- [ ] Validation: `uv run pytest tests/test_repl/test_parser.py -v`

---

### Phase 2: Parser Tests (TDD)
**Objective**: Ensure parser reference detection is fully tested  
**Effort**: 30 minutes  
**Coverage Target**: 95%  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 2.1 Create tests for reference parsing | test_parser.py | HIGH | Phase 1 |
| 2.2 Create tests for Command.references field | test_parser.py | HIGH | 2.1 |

**Test Cases**:
- Single reference: `@pm task $ba` → references=["ba"]
- Multiple references: `@reviewer Check $builder-1 against $pm`
- Hyphenated agent: `$builder-1`
- No reference: `@pm task` → references=[]
- Duplicate deduplication: `$ba $ba` → references=["ba"]
- Dollar amount not reference: `$100`

**Phase Gate Criteria**:
- [ ] All parser reference tests pass
- [ ] Coverage for parser.py reference logic ≥95%
- [ ] Validation: `uv run pytest tests/test_repl/test_parser.py::TestParseReferences -v`

---

### Phase 3: TaskManager Agent Result Storage
**Objective**: Store and retrieve agent results for `$ref` lookup  
**Effort**: 1.5 hours  
**Test Strategy**: TDD  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 3.1 Add `_agent_results` dictionary | manager.py | CRITICAL | None |
| 3.2 Implement `get_agent_result()` method | manager.py | CRITICAL | 3.1 |
| 3.3 Implement `get_running_task_for_agent()` method | manager.py | HIGH | 3.1 |

**Implementation Details**:
- `_agent_results: dict[str, TaskResult]` stores latest result by agent_id
- Results stored on task completion in `execute_task()`
- `get_agent_result()` returns None if agent hasn't run

**Phase Gate Criteria**:
- [ ] `_agent_results` populated on task completion
- [ ] `get_agent_result("ba")` returns latest result
- [ ] `get_running_task_for_agent("ba")` finds running task
- [ ] Validation: `uv run pytest tests/test_tasks/test_manager.py -v -k agent`

---

### Phase 4: TaskManager Tests (TDD)
**Objective**: Ensure agent result storage/retrieval is fully tested  
**Effort**: 30 minutes  
**Coverage Target**: 90%  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 4.1 Create tests for agent result storage | test_manager.py | HIGH | Phase 3 |
| 4.2 Create tests for running task lookup | test_manager.py | HIGH | 4.1 |

**Test Cases**:
- Result stored on task completion
- Latest result overwrites previous
- None returned when no result exists
- Running task found correctly
- None returned when agent is idle

**Phase Gate Criteria**:
- [ ] All manager agent result tests pass
- [ ] Latest result overwrites previous correctly
- [ ] Validation: `uv run pytest tests/test_tasks/test_manager.py -v`

---

### Phase 5: TaskExecutor Reference Handling
**Objective**: Implement waiting and output injection for references  
**Effort**: 2 hours  
**Test Strategy**: TDD  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 5.1 Implement `_wait_for_references()` async method | executor.py | CRITICAL | Phase 3, 4 |
| 5.2 Implement `_inject_references()` method | executor.py | CRITICAL | 5.1 |
| 5.3 Update `_execute_simple()` to handle references | executor.py | CRITICAL | 5.1, 5.2 |

**Implementation Details**:
- `_wait_for_references()`: Polls running tasks with `asyncio.sleep(0.1)`
- `_inject_references()`: Prepends outputs with `=== Output from @{agent} ===` headers
- Placeholder `[No output available]` when agent hasn't run

**Phase Gate Criteria**:
- [ ] Commands with `$ref` wait for running tasks
- [ ] Referenced output is injected into prompt
- [ ] Placeholder used when no output available
- [ ] Validation: `uv run pytest tests/test_tasks/test_executor.py -v -k reference`

---

### Phase 6: TaskExecutor Tests (TDD)
**Objective**: Ensure reference handling is fully tested  
**Effort**: 1 hour  
**Coverage Target**: 85%  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 6.1 Create tests for reference output injection | test_executor.py | HIGH | Phase 5 |
| 6.2 Create tests for waiting on running tasks | test_executor.py | HIGH | 6.1 |
| 6.3 Create tests for no output available scenario | test_executor.py | HIGH | 6.2 |

**Test Cases**:
- Output prepended with correct header
- Multiple references handled
- Waits for running task to complete
- Placeholder injected when no output

**Phase Gate Criteria**:
- [ ] All executor reference tests pass
- [ ] Async waiting behavior verified
- [ ] Validation: `uv run pytest tests/test_tasks/test_executor.py -v`

---

### Phase 7: REPL Routing & Overlay Updates
**Objective**: Route referenced commands and display waiting status  
**Effort**: 1 hour  
**Test Strategy**: Code-First  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 7.1 Update REPL routing condition for references | loop.py | CRITICAL | Phase 5, 6 |
| 7.2 Add waiting fields to OverlayState | overlay.py | HIGH | 7.1 |
| 7.3 Update overlay display for waiting state | overlay.py | HIGH | 7.2 |

**Implementation Details**:
- Add `command.references` to routing condition
- Add `waiting_count: int` and `waiting_for: dict[str, str]` to OverlayState
- Display format: `⏳ Waiting: @pm→@ba`

**Phase Gate Criteria**:
- [ ] `@pm task $ba` routes through TaskExecutor
- [ ] Waiting count displayed in overlay
- [ ] Waiting relationship shown
- [ ] Validation: Manual REPL testing

---

### Phase 8: Documentation
**Objective**: Document syntax with comparison to pipeline syntax  
**Effort**: 30 minutes  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 8.1 Add "Shared Context References" section to README | README.md | HIGH | Phase 7 |
| 8.2 Add syntax comparison table | README.md | HIGH | 8.1 |

**Documentation Content**:
- Syntax examples: `@pm Summarize $ba`, `@reviewer Check $builder-1 against $pm`
- How it works (4-step explanation)
- Comparison table: `$ref` vs `->` syntax
- When to use which guidance

**Phase Gate Criteria**:
- [ ] README includes `$agent` syntax documentation
- [ ] Comparison table explains differences
- [ ] Usage examples provided

---

### Phase 9: Integration & Validation
**Objective**: End-to-end validation of complete feature  
**Effort**: 1 hour  

| Task | File | Priority | Dependencies |
|------|------|----------|--------------|
| 9.1 Create integration tests | test_shared_context.py | MEDIUM | Phase 7, 8 |
| 9.2 Validate coverage targets | - | MEDIUM | 9.1 |

**Integration Test Workflow**:
1. BA analyzes requirements
2. PM references BA: `@pm Create plan based on $ba`
3. Builder references PM: `@builder-1 Implement $pm`

**Phase Gate Criteria**:
- [ ] Full workflow test passes
- [ ] Coverage targets met per component
- [ ] All existing tests still pass
- [ ] Validation: `uv run pytest --cov=src/teambot --cov-report=term-missing`

---

## Dependencies

### Technical Dependencies
| Dependency | Status | Notes |
|------------|--------|-------|
| pytest | ✅ Existing | Test framework |
| pytest-asyncio | ✅ Existing | Async test support |
| pytest-cov | ✅ Existing | Coverage reporting |
| unittest.mock | ✅ Standard | Mocking support |

### Internal Dependencies
| Component | Status |
|-----------|--------|
| TaskStatus enum | ✅ Exists |
| Command dataclass | ✅ Exists |
| TaskManager | ✅ Exists |
| TaskExecutor | ✅ Exists |
| OverlayState | ✅ Exists |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Async wait loop timing issues | MEDIUM | LOW | Add configurable timeout |
| Integration test directory missing | LOW | MEDIUM | Create directory or use existing location |
| Breaking existing tests | HIGH | LOW | Run full suite after each phase |

---

## Coverage Targets

| Component | Target | Approach |
|-----------|--------|----------|
| Parser (references) | 95% | TDD |
| Command dataclass | 100% | TDD |
| TaskManager (agent results) | 90% | TDD |
| TaskExecutor (ref handling) | 85% | TDD |
| REPL Loop (routing) | 70% | Code-First |
| Overlay (waiting display) | 70% | Code-First |
| **Overall** | **85%** | Hybrid |

---

## Effort Summary

| Phase | Effort | Cumulative |
|-------|--------|------------|
| Phase 1: Parser & Models | 1h | 1h |
| Phase 2: Parser Tests | 30m | 1.5h |
| Phase 3: TaskManager | 1.5h | 3h |
| Phase 4: Manager Tests | 30m | 3.5h |
| Phase 5: TaskExecutor | 2h | 5.5h |
| Phase 6: Executor Tests | 1h | 6.5h |
| Phase 7: REPL & Overlay | 1h | 7.5h |
| Phase 8: Documentation | 30m | 8h |
| Phase 9: Integration | 1h | **9h** |

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Implementation Plan | `.agent-tracking/plans/20260203-shared-context-reference-plan.instructions.md` |
| Task Details | `.agent-tracking/details/20260203-shared-context-reference-details.md` |
| Research Document | `.agent-tracking/research/20260203-shared-context-research.md` |
| Test Strategy | `.agent-tracking/test-strategies/20260203-shared-context-test-strategy.md` |
| Plan Review | `.agent-tracking/plan-reviews/20260203-shared-context-reference-plan-review.md` |
| Project Plan | `.teambot/shared-context/artifacts/project_plan.md` |

---

## Approval

**Plan Status**: ✅ APPROVED  
**Review Date**: 2026-02-03  
**Implementation Ready**: YES  

---

## Next Steps

1. **Assign to Builder**: `@builder-1` or `@builder-2`
2. **Begin Phase 1**: Parser & Model Extensions
3. **Follow Phase Gates**: Validate at each milestone
4. **Run Tests**: `uv run pytest` after each phase
