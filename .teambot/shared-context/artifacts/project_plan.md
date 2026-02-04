# Project Plan: Shared Context Reference Syntax (`$agent`)

## Project Overview

Enable TeamBot users to reference another agent's output using intuitive `$agent` syntax (e.g., `$pm`, `$ba`, `$builder-1`), with automatic waiting and output injection.

## Goals

- [ ] Easy-to-use `$agent` syntax for referencing agent results
- [ ] Automatic waiting when referenced agent is still running
- [ ] Accurate status display (waiting/executing/idle)
- [ ] README documentation with syntax comparison

## Phases

### Phase 1: Parser & Models (~1 hour)
- [ ] Add WAITING status to TaskStatus enum
- [ ] Add `references` field to Command dataclass
- [ ] Implement `$agent` pattern detection

### Phase 2: Parser Tests (~30 min)
- [ ] Create reference parsing tests (95% coverage target)

### Phase 3: TaskManager (~1.5 hours)
- [ ] Add agent result storage
- [ ] Implement `get_agent_result()` method
- [ ] Implement `get_running_task_for_agent()` method

### Phase 4: Manager Tests (~30 min)
- [ ] Create result storage/retrieval tests (90% coverage target)

### Phase 5: TaskExecutor (~2 hours)
- [ ] Implement `_wait_for_references()` async method
- [ ] Implement `_inject_references()` method
- [ ] Update `_execute_simple()` to handle references

### Phase 6: Executor Tests (~1 hour)
- [ ] Create injection and waiting tests (85% coverage target)

### Phase 7: REPL & Overlay (~1 hour)
- [ ] Update routing condition for references
- [ ] Add waiting state to overlay display

### Phase 8: Documentation (~30 min)
- [ ] Add README section for `$agent` syntax
- [ ] Add `$ref` vs `->` comparison table

### Phase 9: Integration (~1 hour)
- [ ] Create end-to-end integration tests
- [ ] Validate coverage targets (overall ≥85%)

## Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Parser & Models | 1h | CRITICAL |
| Parser Tests | 30m | HIGH |
| TaskManager | 1.5h | CRITICAL |
| Manager Tests | 30m | HIGH |
| TaskExecutor | 2h | CRITICAL |
| Executor Tests | 1h | HIGH |
| REPL & Overlay | 1h | HIGH |
| Documentation | 30m | HIGH |
| Integration | 1h | MEDIUM |
| **Total** | **~9 hours** | |

## Success Criteria

- `@pm task $ba` syntax works and injects BA's latest output
- Referencing agent waits for running task to complete
- Status overlay shows waiting/executing/idle accurately
- README documents both syntaxes with comparison
- All existing tests pass
- Coverage targets met

## Key Files

| Component | File |
|-----------|------|
| Parser | `src/teambot/repl/parser.py` |
| Models | `src/teambot/tasks/models.py` |
| Manager | `src/teambot/tasks/manager.py` |
| Executor | `src/teambot/tasks/executor.py` |
| REPL | `src/teambot/repl/loop.py` |
| Overlay | `src/teambot/visualization/overlay.py` |
| Docs | `README.md` |

## Status

**Plan Status**: ✅ APPROVED  
**Ready for Implementation**: YES

## Next Step

Assign to `@builder-1` or `@builder-2` for implementation.
