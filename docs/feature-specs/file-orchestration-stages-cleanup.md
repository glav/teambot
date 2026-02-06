## Objective

Simplify and clarify the `stages.yaml` configuration and REPL help options to improve usability and reduce confusion.

**Goal**: Make the `stages.yaml` schema more intuitive by consolidating redundant fields, clarifying semantics, and documenting implicit behaviors (especially artifact storage locations).

**Problem Statement**: The current `stages.yaml` has several usability issues:

1. **Confusing agent field semantics**: `work_agent` and `review_agent` have unclear meanings in certain contexts. For example, in `SPEC_REVIEW` stage:
   - `work_agent: ba` - What work is the BA doing in a *review* stage?
   - `review_agent: reviewer` - Expected, but what's the relationship to `work_agent`?
   - `is_review_stage: true` - How does this interact with the agent fields?

2. **Redundant/overlapping fields**:
   - `allowed_personas` lists roles, but `work_agent`/`review_agent` specify concrete agents
   - `is_review_stage` flag exists, but so does `work_to_review_mapping` at the file level
   - Some stages have both `work_agent` and `review_agent` set, while others have only one

3. **Undocumented artifact storage**:
   - `artifacts: [feature_spec.md]` lists filenames, but doesn't explain *where* they're stored
   - Code reveals: `.teambot/{feature-name}/artifacts/{artifact-file}` - this is implicit
   - Users/customizers have no way to know this without reading source code

4. **Inconsistent patterns**:
   - `IMPLEMENTATION` has `parallel_agents` but also `work_agent`
   - Some stages have `prompt_template: null` explicitly, others omit it entirely

---

## Current Analysis

### Confusing Example: SPEC_REVIEW Stage

```yaml
SPEC_REVIEW:
  name: Spec Review
  description: Review and approve the feature specification
  work_agent: ba          # Confusing: BA does work in a REVIEW stage?
  review_agent: reviewer  # Reviewer reviews...
  allowed_personas:       # Doesn't include 'ba' - so who uses work_agent?
    - reviewer
    - project_manager
    - pm
  is_review_stage: true   # Flag that changes execution behavior
```

**Actual Code Behavior** (from `execution_loop.py`):
- `is_review_stage: true` triggers `_execute_review_stage()` instead of `_execute_work_stage()`
- In review stages, `work_agent` = agent that addresses feedback/makes revisions
- In review stages, `review_agent` = agent that performs the review
- This creates an **iteration loop**: work → review → feedback → work (if not approved)

**The Issue**: This semantic isn't documented anywhere in `stages.yaml`.

### Artifact Storage (Implicit Behavior)

From `execution_loop.py` lines 100-107:
```python
self.feature_name = self.objective.feature_name
self.teambot_dir = teambot_dir / self.feature_name
self.teambot_dir.mkdir(parents=True, exist_ok=True)
(self.teambot_dir / "artifacts").mkdir(exist_ok=True)
```

**Actual path**: `.teambot/{feature-name}/artifacts/{artifact-filename}`

This is **never documented** in `stages.yaml` or its comments.

---

## Proposed Changes

### Option A: Documentation-Only (Minimal)
Add comprehensive comments to `stages.yaml` explaining:
- What `work_agent`/`review_agent` mean in review vs non-review stages
- Where artifacts are stored (path template)
- The iteration loop behavior for review stages

### Option B: Schema Simplification (Recommended)
Refactor the schema to be more explicit:

1. **Replace `work_agent`/`review_agent` with context-aware naming**:
   ```yaml
   # For non-review stages:
   executor: ba              # Agent that executes this stage

   # For review stages:
   reviser: ba               # Agent that addresses feedback
   approver: reviewer        # Agent that reviews and approves
   ```

2. **Add explicit artifact path configuration**:
   ```yaml
   artifacts:
     - name: feature_spec.md
       path: "{teambot_dir}/artifacts/{name}"  # Explicit path template
   ```

3. **Remove redundant fields**:
   - Remove `is_review_stage` if it can be inferred from `work_to_review_mapping`
   - Or vice-versa: keep `is_review_stage` and remove the mapping

4. **Consolidate `allowed_personas` with agent fields**:
   - Either derive allowed_personas from the agent assignments
   - Or document why both are needed

---

## Success Criteria

- [ ] `stages.yaml` includes header documentation explaining the schema
- [ ] `work_agent`/`review_agent` semantics are either renamed or documented clearly
- [ ] Artifact storage path is explicitly documented with template syntax
- [ ] `is_review_stage` relationship to `work_to_review_mapping` is clarified
- [ ] All implicit behaviors are made explicit or documented
- [ ] Existing tests continue to pass (no breaking changes unless Option B)
- [ ] A migration guide or backward compatibility notes if schema changes

---

## Technical Context

**Target Codebase**:
- `stages.yaml` (primary)
- `src/teambot/orchestration/stage_config.py` (loader)
- `src/teambot/orchestration/execution_loop.py` (consumer)

**Primary Language/Framework**: Python + YAML configuration

**Testing Preference**: Existing test suite validation

**Key Constraints**:
- Backward compatibility with existing `stages.yaml` files (if schema changes)
- Must not break the 192 existing tests

---

## Task Breakdown

- [ ] **Task 1**: Add schema documentation header to `stages.yaml`
- [ ] **Task 2**: Document `work_agent`/`review_agent` semantics for review vs non-review stages
- [ ] **Task 3**: Add artifact path documentation with explicit template
- [ ] **Task 4**: Clarify `is_review_stage` vs `work_to_review_mapping` relationship
- [ ] **Task 5**: Review and update `allowed_personas` usage
- [ ] **Task 6**: (Optional) Implement Option B schema refactoring if approved
- [ ] **Task 7**: Verify all tests pass
- [ ] **Task 8**: Update any related documentation in `docs/guides/`

---

## Open Questions

1. Should we pursue Option A (docs only) or Option B (schema refactor)?
2. Is backward compatibility required for custom `stages.yaml` files?
3. Should `allowed_personas` be deprecated in favor of deriving from agent fields?

---

## Help Options Audit

### Current Commands in `/help` Output

From `src/teambot/repl/commands.py`, the `/help` command displays:

| Command | Status | Notes |
|---------|--------|-------|
| `@agent <task>` | ✅ Active | Core functionality |
| `/help` | ✅ Active | Self-referential |
| `/help agent` | ✅ Active | Agent help topic |
| `/help parallel` | ✅ Active | Parallel execution help topic |
| `/status` | ✅ Active | Shows agent status with models |
| `/models` | ✅ Active | Lists available AI models |
| `/model <a> <m>` | ✅ Active | Sets model for agent in session |
| `/tasks` | ✅ Active | Lists running/completed tasks |
| `/task <id>` | ✅ Active | Views task details |
| `/cancel <id>` | ✅ Active | Cancels pending task |
| `/overlay` | ✅ Active | **Fully implemented** - toggles status overlay |
| `/history` | ✅ Active | Shows command history |
| `/quit` | ✅ Active | Exits interactive mode |

### Analysis

**Finding**: The `/overlay` command **is implemented and functional**:
- Implementation: `src/teambot/visualization/overlay.py` (603 lines)
- Command handler: `src/teambot/repl/commands.py` lines 446-512
- Tests: `tests/test_repl/test_commands_overlay.py` (142 lines)
- Integration: Used in `REPLLoop` for persistent status display
- However `/overlay` is not needed anymore since all display elements that were present in the overlay functionality are now implemented in other areas of the application within Teambot.
  - `/overlay` command, its implementation, tests and related documentation should be removed.

**Conclusion**: All commands listed in `/help` are actively implemented and supported except overlay. Only `/overlay` needs to be removed.

### Potential Documentation Improvements

The help text could be improved for clarity:

1. **Model selection examples could be consolidated**: Multiple examples are scattered

---

## Updated Task Breakdown

- [ ] **Task 1**: Add schema documentation header to `stages.yaml`
- [ ] **Task 2**: Document `work_agent`/`review_agent` semantics for review vs non-review stages
- [ ] **Task 3**: Add artifact path documentation with explicit template
- [ ] **Task 4**: Clarify `is_review_stage` vs `work_to_review_mapping` relationship
- [ ] **Task 5**: Review and update `allowed_personas` usage
- [ ] **Task 6**: (Optional) Implement Option B schema refactoring if approved
- [ ] **Task 7**: Verify all tests pass
- [ ] **Task 8**: Update any related documentation in `docs/guides/`
- [ ] **Task 9**: Remove `/overlay` command entirely - tests, implementation and documentation
- [ ] **Task 10**: (Optional) Review other help topics for similar clarity improvements

