# Implementation Plan Review: Persistent Status Overlay

**Plan Location:** `plan.md` (session state)  
**Feature Spec:** `docs/feature-specs/persistent-status-overlay.md`  
**Reviewer:** AI Assistant  
**Date:** 2026-01-23  
**Verdict:** ✅ APPROVED WITH MINOR RECOMMENDATIONS

---

## Overall Score: 8.7/10

| Category | Score | Notes |
|----------|-------|-------|
| Completeness | 9/10 | All FRs covered; one minor gap |
| Task Granularity | 8/10 | Good breakdown; some tasks could be split |
| Dependency Management | 9/10 | Clear phase dependencies |
| Risk Identification | 7/10 | Missing some edge case considerations |
| Testability | 9/10 | Good test coverage planned |
| Estimate Accuracy | 8/10 | Realistic; recommend small buffer |

---

## Requirements Coverage Matrix

| Requirement | Plan Task | Status |
|-------------|-----------|--------|
| FR-PSO-001 (Fixed position) | 1.2, 1.3 | ✅ Covered |
| FR-PSO-002 (Default top-right) | 1.3 | ✅ Covered |
| FR-PSO-003 (Compact format) | 1.1, 1.2 | ✅ Covered |
| FR-PSO-004 (Spinner) | 3.1, 3.2 | ✅ Covered |
| FR-PSO-005 (State-change updates) | 2.2, 2.3 | ✅ Covered |
| FR-PSO-006 (Toggle command) | 5.2 | ✅ Covered |
| FR-PSO-007 (Position command) | 5.3 | ✅ Covered |
| FR-PSO-008 (Config file) | 6.1, 6.2 | ✅ Covered |
| FR-PSO-009 (Status unchanged) | Implicit | ✅ No change needed |
| FR-PSO-010 (Idle state) | 1.1 (OverlayState) | ⚠️ Implicit, add explicit task |
| FR-PSO-011 (Resize handling) | 4.3 | ✅ Covered |
| FR-PSO-012 (Spinner timer) | 3.1 | ✅ Covered |
| FR-PSO-013 (on_task_started) | 2.1 | ✅ Covered |
| FR-PSO-014 (Collision handling) | 4.1, 4.2 | ✅ Covered |
| NFR-PSO-001 (Performance) | Implicit | ⚠️ Add perf validation task |
| NFR-PSO-002 (Terminal compat) | 1.4 | ✅ Covered |
| NFR-PSO-003 (Graceful degradation) | 1.4 | ✅ Covered |

---

## Strengths

### 1. Clear Phase Structure
7 phases with logical dependencies. Phases 2-5 can partially parallelize after Phase 1 core is done.

### 2. TDD Approach
Each phase includes explicit test tasks (1.5, 2.4, 3.3, 4.4, 5.5, 6.3).

### 3. Good Technical Detail
ANSI escape sequences and position calculation code provided upfront - reduces implementation ambiguity.

### 4. Realistic File Impact
Clear separation of files to create vs modify. No unnecessary refactoring.

### 5. Architecture Diagram
Visual shows data flow between TaskExecutor → Console → OverlayRenderer.

---

## Gaps & Recommendations

### Gap 1: Idle State Display Not Explicit (Low Priority)
**Issue:** FR-PSO-010 requires idle indicator, but no explicit task mentions implementing it.

**Recommendation:** Add to Phase 1:
> - [ ] 1.6 Implement idle state rendering (✓ Idle display)

### Gap 2: Performance Validation Missing (Medium Priority)
**Issue:** NFR-PSO-001 requires < 10ms render time, but no task validates this.

**Recommendation:** Add to Phase 7:
> - [ ] 7.5 Validate overlay render time < 10ms (add simple benchmark)

### Gap 3: Edge Case - Empty Agent List (Low Priority)
**Issue:** What if no agents are configured? Overlay should handle gracefully.

**Recommendation:** Include in Phase 1 tests:
> Test: OverlayRenderer handles zero agents gracefully

### Gap 4: Spinner Cleanup on Crash (Low Priority)
**Issue:** If REPL crashes mid-spinner, terminal could be left in bad state.

**Recommendation:** Add cleanup in Phase 3:
> - [ ] 3.4 Ensure spinner timer cancellation in all exit paths (finally block)

### Gap 5: Test File Location (Minor)
**Issue:** Plan mentions `tests/test_visualization/test_overlay.py` but current test structure may not have this directory.

**Recommendation:** Verify directory exists or create `tests/test_visualization/__init__.py`.

---

## Suggested Task Refinements

### Phase 1 - Split Task 1.2
Task 1.2 "Create OverlayRenderer class with ANSI positioning" is large. Consider:
- 1.2a: Create OverlayRenderer skeleton with render() and clear() methods
- 1.2b: Implement ANSI escape sequence output
- 1.2c: Implement box drawing (borders)

### Phase 4 - Clarify 4.2
"Integrate with REPLLoop console output" is vague. Specify:
- Replace `self._console.print()` calls with overlay-aware wrapper
- Or: Inject overlay renderer into console output path

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation in Plan? |
|------|------------|--------|---------------------|
| ANSI codes don't work in some terminals | Medium | High | ✅ Task 1.4 |
| Spinner causes flicker | Medium | Medium | ⚠️ Not explicit |
| Output collision artifacts | High | Medium | ✅ Task 4.1 |
| Config schema breaks existing configs | Low | High | ⚠️ Need migration |
| Async spinner conflicts with REPL input | Medium | Medium | ⚠️ Not addressed |

### New Risk: Async Spinner + Input Conflict
**Issue:** The 100ms spinner timer runs while user is typing. Could cause cursor jumping.

**Recommendation:** Add to Phase 3:
> - [ ] 3.5 Ensure spinner rendering doesn't interfere with prompt input (cursor save/restore)

---

## Estimate Validation

| Phase | Plan Estimate | Review Estimate | Delta |
|-------|---------------|-----------------|-------|
| Phase 1 | 3h | 3.5h | +0.5h (split 1.2) |
| Phase 2 | 1.5h | 1.5h | ✓ |
| Phase 3 | 1h | 1.5h | +0.5h (cursor safety) |
| Phase 4 | 1.5h | 1.5h | ✓ |
| Phase 5 | 1h | 1h | ✓ |
| Phase 6 | 0.5h | 0.5h | ✓ |
| Phase 7 | 1.5h | 2h | +0.5h (perf validation) |
| **Total** | **10h** | **11.5h** | +15% buffer |

---

## Parallel Execution Opportunities

After Phase 1 completes:
- **Phase 2** (events) and **Phase 3** (spinner) can run in parallel
- **Phase 5** (commands) and **Phase 6** (config) can run in parallel
- **Phase 4** (output integration) should wait for Phase 2

```
Phase 1 ──┬── Phase 2 ──┬── Phase 4 ──┬── Phase 7
          │             │             │
          └── Phase 3 ──┘             │
          │                           │
          └── Phase 5 ────────────────┤
          │                           │
          └── Phase 6 ────────────────┘
```

---

## Summary

The plan is well-structured and covers all major requirements. Key additions:

1. **Add task 1.6:** Idle state rendering
2. **Add task 3.4:** Spinner cleanup on exit
3. **Add task 3.5:** Cursor safety during spinner
4. **Add task 7.5:** Performance validation
5. **Verify:** `tests/test_visualization/` directory exists

**Recommendation:** Proceed with implementation. Consider the ~11.5h revised estimate.

---

## Checklist for Approval

- [x] All functional requirements mapped to tasks
- [x] Test tasks included for each phase
- [x] Dependencies clearly stated
- [x] Files to create/modify listed
- [x] Technical approach documented
- [ ] Idle state task explicit ← **Minor addition needed**
- [ ] Performance validation included ← **Minor addition needed**
- [x] Estimate provided and reasonable

**Status:** ✅ APPROVED - Ready for implementation with minor additions
