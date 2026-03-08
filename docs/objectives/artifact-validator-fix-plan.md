# Task Breakdown: Fix Artifact Path Resolution in PLAN Stage

## Problem Statement

The PLAN stage cannot find research documents because it's looking in the wrong directory:
- **Expected location**: `.agent-tracking/research/` (repository root)
- **Actual search location**: `.teambot/{feature}/artifacts/.agent-tracking/research/`
- **Evidence**: Research file exists at `.agent-tracking/research/20260305-remove-history-command-research.md` but PLAN stage reported it missing

## Root Cause Analysis

The `ArtifactValidator` class (lines 66-69) constructs `_agent_tracking_dir` as:
```python
self._agent_tracking_dir = self.teambot_dir.parent / ".agent-tracking"
```

Where `self.teambot_dir` is the base `.teambot` directory passed from `ExecutionLoop.__init__`. However, the PLAN stage output shows it's looking in `.teambot/{feature}/artifacts/.agent-tracking/` instead.

**Hypothesis**: Either:
1. The wrong `teambot_dir` is being passed to `ArtifactValidator` (feature-specific instead of base)
2. The `_agent_tracking_dir` calculation logic is incorrect
3. The PLAN stage prompt template is hardcoding an incorrect path in its instructions

## Task Breakdown

### Phase 1: Investigation (Priority: HIGH)

- [ ] **Task 1.1**: Verify `ArtifactValidator` initialization in `ExecutionLoop`
  - File: `src/teambot/orchestration/execution_loop.py` (lines 142-146)
  - Check if `teambot_dir` parameter (base) vs `self.teambot_dir` (feature-specific) is passed
  - Expected: Base `teambot_dir` should be passed, not `self.teambot_dir`
  - Acceptance: Understand exact value passed to validator constructor

- [ ] **Task 1.2**: Debug artifact path construction
  - File: `src/teambot/orchestration/artifact_validator.py` (lines 66-70)
  - Add logging to show actual paths being constructed
  - Verify `_agent_tracking_dir` resolves to repository root `.agent-tracking/`
  - Acceptance: Confirm path calculation logic is correct

- [ ] **Task 1.3**: Check PLAN stage prompt template
  - File: Search for PLAN stage prompt in `.agent/commands/sdd/` or similar
  - Look for hardcoded references to artifact paths
  - Check if prompt instructs agents to look in wrong location
  - Note: Issue might be combination of ExecutionLoop AND prompt problems
  - Acceptance: Identify if prompt contains incorrect path instructions

- [ ] **Task 1.4**: Document artifact search behavior (Reviewer Suggestion)
  - Document current search paths and order
  - Define expected search paths and precedence rules
  - Clarify if `.agent-tracking/` should be checked before/after feature artifacts
  - Determine if feature-specific artifacts in `.teambot/{feature}/artifacts/` should be searchable
  - Acceptance: Clear specification of artifact resolution behavior

### Phase 2: Fix Implementation (Priority: HIGH)

**Contingent on findings from Phase 1. Prioritize fixes in order A → B → C. Multiple fixes may be needed if issue is a combination.**

#### **Fix Option A**: ExecutionLoop passes wrong directory
- [ ] **Task 2A.1**: Correct `ArtifactValidator` initialization parameter
  - File: `src/teambot/orchestration/execution_loop.py` (line 143)
  - Change from: `teambot_dir=self.teambot_dir` (if that's what's there)
  - Change to: `teambot_dir=teambot_dir` (original parameter)
  - Acceptance: Validator receives base `.teambot` directory, not feature-specific

#### **Fix Option B**: Path construction logic is broken
- [ ] **Task 2B.1**: Fix `_agent_tracking_dir` calculation
  - File: `src/teambot/orchestration/artifact_validator.py` (lines 66-70)
  - Adjust calculation to correctly resolve to repository root
  - Consider edge cases (worktrees, nested directories)
  - Acceptance: Path resolves correctly in all scenarios

#### **Fix Option C**: PLAN prompt has hardcoded paths
- [ ] **Task 2C.1**: Update PLAN stage prompt template
  - File: Identified in Task 1.3
  - Remove hardcoded paths
  - Use dynamic artifact references
  - Acceptance: Prompt refers to artifacts without hardcoded paths

### Phase 3: Testing (Priority: HIGH)

- [ ] **Task 3.1**: Create unit test for artifact validator path resolution
  - File: `tests/test_orchestration/test_artifact_validator.py`
  - Test case: Verify `_agent_tracking_dir` resolves correctly
  - Test case: Verify `find_artifact()` finds research documents
  - Test case: Verify feature-specific vs base directory handling
  - Test case: Verify behavior when artifact doesn't exist (proper error) [Reviewer Suggestion]
  - Test case: Verify precedence when same filename exists in multiple locations [Reviewer Suggestion]
  - Test case: Verify case sensitivity handling (Windows vs Linux) [Reviewer Suggestion]
  - Test case: Verify search order matches documented precedence [Reviewer Suggestion]
  - Acceptance: Tests pass and prevent regression

- [ ] **Task 3.2**: Test with actual research artifact
  - Use existing file: `.agent-tracking/research/20260305-remove-history-command-research.md`
  - Create validator instance with `feature_name="remove-history-command"`
  - Call `find_artifact("research.md")` and verify expected search order/priority
  - Verify it returns the correct path
  - Acceptance: Artifact is found successfully with correct precedence

- [ ] **Task 3.3**: Integration test with PLAN stage
  - Run: `uv run teambot run docs/objectives/remove-history-command.md --resume`
  - Verify PLAN stage can find research document
  - Verify `implementation_plan.md` is created
  - Acceptance: PLAN stage completes without "missing artifact" error

### Phase 4: Verification (Priority: MEDIUM)

- [ ] **Task 4.1**: Verify all stage types
  - Check SPEC, SPEC_REVIEW, RESEARCH, PLAN, PLAN_REVIEW stages
  - Ensure all can find their prerequisite artifacts
  - Test with multiple features to ensure no cross-contamination
  - Acceptance: All stages resolve artifacts correctly

- [ ] **Task 4.2**: Test worktree scenario
  - Create worktree: `teambot run <objective> --worktree`
  - Verify artifact validator works in worktree context
  - Verify `.agent-tracking/` is found relative to repository root
  - Acceptance: Worktree mode artifact resolution works correctly

- [ ] **Task 4.3**: Run full test suite
  - Execute: `uv run pytest tests/test_orchestration/`
  - Verify no regressions in orchestration tests
  - Execute: `uv run pytest --cov=src/teambot`
  - Ensure coverage remains ≥80%
  - Verify git checkpoint functionality still works after fix [Reviewer Suggestion]
  - Acceptance: All tests pass, coverage maintained, checkpoints functional

- [ ] **Task 4.4**: Update documentation if needed (Reviewer Suggestion)
  - Check if `docs/guides/` mentions artifact locations
  - Update `AGENTS.md` if artifact resolution behavior changes
  - Verify examples in `docs/objectives/` still work with updated behavior
  - Document search order and precedence rules if changed
  - Acceptance: Documentation accurately reflects artifact behavior

## Dependencies

- **Blocker**: Must complete Phase 1 (Investigation) before starting Phase 2 (Fix)
- **Blocker**: Must complete Phase 2 (Fix) before Phase 3 (Testing)
- **Prerequisite**: Existing research file at `.agent-tracking/research/20260305-remove-history-command-research.md`
- **Prerequisite**: Existing orchestration state at `.teambot/remove-history-command/orchestration_state.json`

## Acceptance Criteria

### Primary Success Criteria
1. ✅ PLAN stage can find research documents in `.agent-tracking/research/`
2. ✅ `implementation_plan.md` is created when PLAN stage runs
3. ✅ PLAN_REVIEW stage no longer reports "missing artifact" error
4. ✅ All unit tests pass
5. ✅ Integration test completes successfully (PLAN stage runs to completion)

### Quality Criteria
1. ✅ Code changes are minimal and surgical (modify only what's needed)
2. ✅ Fix handles both normal and worktree scenarios
3. ✅ Solution prevents cross-feature artifact contamination
4. ✅ Test coverage remains ≥80%
5. ✅ No linting errors (`ruff check` passes)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fix breaks worktree mode | Low | High | Test worktree scenario in Phase 4.2 |
| Cross-feature contamination | Low | Medium | Verify feature_name filtering in Phase 4.1 |
| Regression in other stages | Low | High | Run full orchestration test suite in Phase 4.3 |
| Incorrect path on different OS | Very Low | Low | Path uses `Path` objects (cross-platform) |
| Git checkpoint integration breaks | Very Low | Medium | Verify checkpoint functionality in Phase 4.3 |

### Rollback Plan (Reviewer Suggestion)

If the fix causes regressions during integration testing:

1. **Create feature branch**: Before starting implementation, create branch `fix/artifact-validator-paths`
2. **Commit incrementally**: Each phase should have its own commit for easy rollback
3. **Rollback command**: `git checkout main && git branch -D fix/artifact-validator-paths`
4. **State restoration**: If needed, restore orchestration state from `.teambot/remove-history-command/orchestration_state.json` backup
5. **Re-plan**: Review what went wrong and update task breakdown before retry

## Estimated Scope

- **Complexity**: Low-Medium (isolated to artifact validator logic)
- **Files Changed**: 1-3 files (likely just `execution_loop.py` or `artifact_validator.py`)
- **Lines Changed**: 5-20 lines (minimal surgical fix)
- **Testing Time**: 15-30 minutes (unit + integration tests)

## Notes for Builder Agent

1. **Start with Task 1.1**: Check `execution_loop.py` line 143 first - this is most likely the issue
2. **Add debug logging**: Temporarily add logging to see actual paths being constructed
3. **Use existing test**: Research file already exists - leverage it for testing
4. **Verify git history**: Check if this worked before - git blame may reveal when it broke
5. **Consider resume scenario**: Fix must work both for fresh runs and `--resume` mode
6. **Create feature branch**: Work on `fix/artifact-validator-paths` branch for easy rollback
7. **Document search order**: If precedence rules change, document them clearly in code comments

## Definition of Done

- [ ] PLAN stage successfully finds `.agent-tracking/research/20260305-remove-history-command-research.md`
- [ ] `implementation_plan.md` is created in `.teambot/remove-history-command/artifacts/`
- [ ] User can run `teambot run docs/objectives/remove-history-command.md --resume` without artifact errors
- [ ] All unit tests pass (including new negative test cases)
- [ ] Integration test passes
- [ ] Git checkpoint functionality verified as working
- [ ] Documentation updated if artifact resolution behavior changed
- [ ] Code is linted and formatted (`ruff format` + `ruff check`)
- [ ] Changes committed with clear commit message on feature branch

---

## Review History

**Reviewed by**: @reviewer  
**Date**: 2026-03-06  
**Decision**: APPROVED WITH SUGGESTIONS  
**Changes Made**: Incorporated all reviewer suggestions:
- Added Task 1.4: Document artifact search behavior
- Enhanced Task 3.1 with negative test cases and precedence testing
- Added Task 4.4: Update documentation
- Clarified Phase 2 fix options (multiple may be needed)
- Added rollback plan to Risk Assessment
- Updated Notes for Builder Agent with branching strategy
- Enhanced Definition of Done with new requirements
