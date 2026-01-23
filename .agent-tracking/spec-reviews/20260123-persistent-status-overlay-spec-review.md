# Feature Spec Review: Persistent Status Overlay

**Spec:** `docs/feature-specs/persistent-status-overlay.md`  
**Reviewer:** AI Assistant  
**Date:** 2026-01-23  
**Verdict:** ✅ APPROVED WITH RECOMMENDATIONS

---

## Overall Score: 8.5/10

| Category | Score | Notes |
|----------|-------|-------|
| Clarity | 9/10 | Clear problem statement, well-structured requirements |
| Completeness | 8/10 | Covers most scenarios; some edge cases need attention |
| Technical Feasibility | 8/10 | Feasible with Rich; spinner animation needs more design |
| Testability | 8/10 | Clear success criteria; mocking terminal will be challenging |
| Alignment with Codebase | 9/10 | Builds on existing Rich usage and callback infrastructure |

---

## Strengths

### 1. Well-Defined Scope
The spec clearly separates what's in scope vs out of scope. Excluding mouse interaction, multiple overlays, and batch mode keeps the feature focused and achievable.

### 2. Event-Driven Architecture
Using state-change updates instead of polling aligns with the existing `on_task_complete` callback pattern in `TaskExecutor`. This is the right approach.

### 3. Graceful Degradation
NFR-PSO-003 addresses terminal compatibility proactively. This will prevent poor UX on unsupported terminals.

### 4. Configuration Flexibility
Both runtime (`/overlay position`) and config file options provide good UX for different user preferences.

### 5. Clear Visual Mockups
The mockups make the expected behavior unambiguous for both active and idle states.

---

## Gaps & Recommendations

### Gap 1: Spinner Animation Mechanism (Medium Priority)
**Issue:** FR-PSO-004 requires animated spinner, but state-change updates (FR-PSO-005) won't trigger frequently enough to animate. Spinners need ~100ms frame updates.

**Recommendation:** Add FR-PSO-012:
> The spinner animation SHALL use a separate async timer (100ms interval) that ONLY updates the spinner frame, not the full overlay content. The timer SHALL be active only when tasks are running.

### Gap 2: Missing `on_task_started` Event (High Priority)
**Issue:** The spec references `on_task_started(task)` in Technical Approach, but current `TaskExecutor` only has `on_task_complete` callback.

**Recommendation:** Add requirement:
> FR-PSO-013: TaskExecutor SHALL be extended to support `on_task_started` callback for overlay updates when tasks begin.

### Gap 3: Output Collision Handling (Medium Priority)
**Issue:** When output is printed while the overlay exists, how do we prevent visual artifacts?

**Recommendation:** Add FR-PSO-014:
> Before printing REPL output, the system SHALL clear the overlay region, print the output, then redraw the overlay to prevent visual artifacts.

### Gap 4: Multi-Line Output Overlap (Low Priority)
**Issue:** Long agent responses could scroll into the overlay region (especially for bottom positions).

**Recommendation:** Consider adding FR-PSO-015:
> The overlay SHALL reserve screen space by adjusting the printable region, OR reposition itself when output approaches its area.

### Gap 5: Minimum Terminal Size (Low Priority)
**Issue:** What happens if terminal is too small to fit overlay?

**Recommendation:** Add to NFR-PSO-003:
> If terminal width < 30 columns or height < 10 rows, overlay SHALL be automatically disabled.

### Gap 6: Test Strategy Not Specified
**Issue:** How will overlay rendering be tested? Terminal rendering is notoriously hard to unit test.

**Recommendation:** Add testing approach:
- Mock terminal dimensions
- Capture ANSI output strings and verify sequences
- Integration tests with Rich's `Console(force_terminal=True, record=True)`

---

## Open Questions Resolution

| Question | Recommendation |
|----------|----------------|
| Show elapsed time? | **No** - Keeps overlay compact. Users can `/task <id>` for details. |
| Keyboard shortcut (Ctrl+O)? | **Yes** - Add as P2 enhancement. Good for power users. |
| Auto-hide after inactivity? | **No** - Could confuse users. Let them explicitly toggle. |

---

## Technical Alignment

### Existing Infrastructure ✓
- Rich `Console` already in use
- Rich `Live` imported in `console.py` (not yet used - ready for this feature)
- `TaskExecutor.on_task_complete` callback exists
- `TaskManager.list_tasks()` provides task counts

### Changes Required
1. Add `on_task_started` callback to `TaskExecutor`
2. Create `OverlayRenderer` class in `src/teambot/visualization/`
3. Extend `SystemCommands` with `/overlay` handlers
4. Update `teambot.json` schema for overlay config

---

## Effort Estimate Validation

| Phase | Spec Estimate | Review Estimate | Notes |
|-------|---------------|-----------------|-------|
| Overlay renderer | 2h | 2.5h | Add collision handling |
| Event subscription | 1h | 1.5h | Need to add `on_task_started` |
| Spinner animation | 0.5h | 1h | Async timer complexity |
| Commands | 1h | 1h | ✓ |
| Configuration | 0.5h | 0.5h | ✓ |
| Terminal detection | 1h | 1h | ✓ |
| Testing | 2h | 2.5h | Terminal mocking adds complexity |
| **Total** | **8h** | **~10h** | +25% for identified gaps |

---

## Summary

The spec is well-written and aligns with existing codebase patterns. The main gaps are:
1. **Spinner animation timing** (needs separate timer)
2. **Missing `on_task_started` event** (needs implementation)
3. **Output collision handling** (needs explicit design)

**Recommendation:** Address Gap 1 and Gap 2 before implementation. Gap 3 can be handled during implementation. Gap 4 and 5 can be P2 enhancements.

---

## Checklist for Approval

- [x] Problem clearly stated
- [x] User stories defined
- [x] Functional requirements numbered and testable
- [x] Non-functional requirements specified
- [x] Technical approach outlined
- [x] Risks identified with mitigations
- [ ] Spinner animation timing addressed ← **Needs update**
- [ ] Event infrastructure requirements added ← **Needs update**
- [x] Configuration schema defined
- [x] Effort estimated

**Status:** Approved pending addition of FR-PSO-012 and FR-PSO-013.
