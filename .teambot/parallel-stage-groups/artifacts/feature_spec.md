<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Parallel Stage Groups - Feature Specification Document
Version 1.0 | Status Draft | Owner TeamBot Team | Team Orchestration | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-10 |
| Problem & Users | ✅ | None | 2026-02-10 |
| Scope | ✅ | None | 2026-02-10 |
| Requirements | ✅ | None | 2026-02-10 |
| Metrics & Risks | ✅ | None | 2026-02-10 |
| Operationalization | ✅ | None | 2026-02-10 |
| Finalization | ✅ | None | 2026-02-10 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context

TeamBot's file-based orchestration workflow executes 14 stages sequentially, with each stage completing fully before the next begins. While this linear model ensures correctness and simplicity, it creates unnecessary wait time when independent stages could execute concurrently.

The existing `ParallelExecutor` handles agent-level parallelism (multiple agents within a single stage, e.g., `builder-1` and `builder-2` during IMPLEMENTATION), but there is no mechanism for stage-level parallelism.

### Core Opportunity

After `SPEC_REVIEW` completes, both `RESEARCH` and `TEST_STRATEGY` consume the approved specification but produce independent artifacts with no data dependencies on each other. Executing these concurrently can reduce elapsed time by 30-40% for this portion of the workflow.

This pattern applies to other stage groupings that may be identified in the future, making a configurable parallel groups mechanism valuable beyond the initial use case.

### Goals

| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Reduce elapsed time for independent stages | Efficiency | Sequential (sum of durations) | Concurrent (max of durations) | v0.2.0 | P0 |
| G-002 | Enable configuration-driven parallel groups | Extensibility | Hardcoded workflow | YAML-configurable | v0.2.0 | P0 |
| G-003 | Support mid-parallel-group resume | Reliability | Single-stage resume only | Per-stage tracking within groups | v0.2.0 | P0 |
| G-004 | Maintain backward compatibility | Stability | Current state format works | Old state files still load | v0.2.0 | P0 |
| G-005 | Provide clear parallel execution visibility | Usability | Single-stage status | Concurrent status indicators | v0.2.0 | P1 |

---

## 2. Problem Definition

### Current Situation

The `ExecutionLoop` in `src/teambot/orchestration/execution_loop.py` iterates through `stage_order` (defined in `stages.yaml`) one stage at a time:

```python
while self.current_stage != WorkflowStage.COMPLETE:
    # Execute current stage (work, review, or acceptance test)
    # Advance to next stage
    self.current_stage = self._get_next_stage(stage)
    self._save_state()
```

The state model tracks a single `current_stage`, making it impossible to represent multiple in-progress stages.

### Problem Statement

Independent workflow stages that could execute concurrently are forced to run sequentially, wasting time and resources. The current state persistence model cannot track multiple concurrent stages, preventing resume functionality for parallel execution scenarios.

### Root Causes

* **Single-stage tracking model**: `current_stage` field in `orchestration_state.json` is a scalar, not a set
* **Linear execution loop**: `_get_next_stage()` performs index-based progression through `stage_order` list
* **No parallel group abstraction**: Configuration has no concept of stage groupings
* **Agent-level parallelism only**: Existing `ParallelExecutor` operates on `AgentTask` objects, not stage dispatch

### Impact of Inaction

* Developers wait unnecessarily for sequential stages that have no dependencies
* Resource utilization remains suboptimal (one Copilot session active at a time for sequential stages)
* No foundation for future optimization of other independent stage pairs
* Competitive disadvantage as orchestration tools evolve toward more intelligent scheduling

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer | Fast feedback loops, minimal wait time | Watching sequential stages run when they could be parallel | High - primary user |
| Operator | Reliable orchestration, clear status visibility | Cannot tell if multiple stages are running | Medium - needs visibility |
| Maintainer | Clean architecture, testable code | Adding parallelism requires code changes | Medium - extensibility concern |

---

## 4. Scope

### In Scope

* **FR-001 to FR-008**: Core parallel stage group functionality (see Section 6)
* **Configuration schema**: New `parallel_groups` section in `stages.yaml`
* **State model evolution**: Track per-stage completion within parallel groups
* **ParallelStageExecutor**: New executor class for stage-level concurrency
* **State machine updates**: Fan-out transitions in `STAGE_METADATA.next_stages`
* **Visualization**: Rich console concurrent status indicators
* **Resume logic**: Re-execute only incomplete stages within groups
* **Backward compatibility**: Old state files load without error
* **First parallel group**: `RESEARCH` and `TEST_STRATEGY` after `SPEC_REVIEW`

### Out of Scope

* **Refactoring `ParallelExecutor`**: Agent-level parallelism remains separate
* **Review stage parallelism**: Stages with `is_review_stage: true` are excluded
* **Dynamic dependency analysis**: Groups are statically configured
* **Cross-group dependencies**: Stages within a group are assumed independent
* **DAG-based scheduling**: No topological sort; parallel groups are predefined

### Assumptions

* A-001: Stages within a parallel group have no data dependencies on each other
* A-002: Each stage writes to unique artifact paths (no write conflicts)
* A-003: Review stages (`is_review_stage: true`) are never included in parallel groups
* A-004: The sequential `stage_order` backbone remains authoritative
* A-005: asyncio is available and sufficient for concurrent stage execution

### Constraints

* C-001: Must not break existing sequential workflow behavior
* C-002: `ParallelStageExecutor` and `ParallelExecutor` remain separate classes
* C-003: Parallel groups defined in `stages.yaml`, not hardcoded
* C-004: Persona validation enforced independently for each stage in a group
* C-005: Work-to-review pairings (`SPEC` → `SPEC_REVIEW`) must complete before consumers run

---

## 5. Product Overview

### Value Proposition

Parallel stage groups reduce orchestration time by executing independent stages concurrently, while maintaining the reliability and resumability that TeamBot users depend on. Configuration-driven groups enable future optimizations without code changes.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ExecutionLoop                             │
├─────────────────────────────────────────────────────────────────┤
│  Sequential Stages    │  Parallel Groups        │  Sequential   │
│  ──────────────────   │  ─────────────────────  │  ──────────── │
│  SETUP               │                          │               │
│  BUSINESS_PROBLEM    │                          │               │
│  SPEC                │                          │               │
│  SPEC_REVIEW ────────┼──► ParallelStageExecutor │               │
│                      │    ├─ RESEARCH           │               │
│                      │    └─ TEST_STRATEGY      │               │
│                      │    (concurrent via       │               │
│                      │     asyncio.gather)      │               │
│  ◄───────────────────┼── All complete ──────────┼─► PLAN        │
│                      │                          │  PLAN_REVIEW  │
│                      │                          │  ...          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `ParallelStageExecutor` | `src/teambot/orchestration/parallel_stage_executor.py` (new) | Execute stage callables concurrently, aggregate results |
| `StagesConfiguration` | `src/teambot/workflow/stage_config.py` | Parse `parallel_groups` from YAML |
| `ExecutionLoop` | `src/teambot/orchestration/execution_loop.py` | Detect parallel groups, dispatch to executor, update state |
| `orchestration_state.json` | `.teambot/{feature}/` | Track parallel group status with per-stage completion |
| Rich visualization | `src/teambot/visualization/` | Display concurrent stage status |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance Criteria |
|-------|-------|-------------|-------|----------|---------------------|
| FR-001 | Parallel group configuration | Define parallel groups in `stages.yaml` under a new `parallel_groups` key | G-002 | P0 | Groups parsed at load time; validation errors surface clearly |
| FR-002 | ParallelStageExecutor creation | New executor class that wraps stage dispatch callables and executes them concurrently via `asyncio.gather()` | G-001 | P0 | Executor handles 2+ stages; returns dict of stage→result |
| FR-003 | Parallel group detection | `ExecutionLoop` detects when current stage is the trigger for a parallel group | G-001 | P0 | On reaching group trigger, dispatch to `ParallelStageExecutor` |
| FR-004 | Concurrent stage execution | `RESEARCH` and `TEST_STRATEGY` execute concurrently after `SPEC_REVIEW` | G-001 | P0 | Overlapping timestamps in logs; elapsed time ≈ max(stage times) |
| FR-005 | Per-stage state tracking | `orchestration_state.json` tracks individual stage status within parallel groups | G-003 | P0 | State file contains `parallel_group_status` with per-stage `status` and `output` |
| FR-006 | Partial resume | Resuming mid-parallel-group re-executes only incomplete stages | G-003 | P0 | Completed stages skipped; incomplete stages re-run |
| FR-007 | Backward compatibility | Old `orchestration_state.json` files (without `parallel_group_status`) load correctly | G-004 | P0 | Legacy state files resume without error; treated as sequential |
| FR-008 | Graceful failure handling | If a stage in a parallel group fails, siblings complete; failure surfaced before blocking | G-001 | P1 | Failing stage logged; other stages complete; aggregate error prevents advancement |

### Configuration Schema (FR-001)

```yaml
# stages.yaml (additions)
parallel_groups:
  post_spec:
    trigger: SPEC_REVIEW        # Execute this group after trigger stage completes
    stages:
      - RESEARCH
      - TEST_STRATEGY
    next_stage: PLAN            # Stage to advance to after group completes
```

### State Model Evolution (FR-005)

```json
{
  "current_stage": "PARALLEL_GROUP:post_spec",
  "parallel_group_status": {
    "group_name": "post_spec",
    "trigger_stage": "SPEC_REVIEW",
    "stages": {
      "RESEARCH": {
        "status": "complete",
        "started_at": "2026-02-10T10:00:00Z",
        "completed_at": "2026-02-10T10:05:00Z",
        "output": "Research output content..."
      },
      "TEST_STRATEGY": {
        "status": "in_progress",
        "started_at": "2026-02-10T10:00:00Z",
        "completed_at": null,
        "output": null
      }
    }
  },
  "status": "in_progress",
  "stage_outputs": { "SPEC": "...", "SPEC_REVIEW": "..." }
}
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Target | Priority | Validation |
|--------|----------|-------------|--------|----------|------------|
| NFR-001 | Performance | Parallel group execution time | ≤ max(stage durations) + 5% overhead | P0 | Timing comparison tests |
| NFR-002 | Reliability | State persistence atomicity | Per-stage updates survive crashes | P0 | Resume tests after simulated interruption |
| NFR-003 | Maintainability | Separation of concerns | `ParallelStageExecutor` has no knowledge of `ParallelExecutor` | P1 | Code review; no imports between them |
| NFR-004 | Extensibility | Adding new parallel groups | YAML-only change; no code modifications | P0 | Add test group via config; verify execution |
| NFR-005 | Observability | Parallel stage visibility | Rich console shows concurrent stage status | P1 | Visual inspection; automated console tests |
| NFR-006 | Compatibility | Legacy state files | v0.1.x state files load in v0.2.0 | P0 | Migration tests with sample legacy files |

---

## 8. Data & Analytics

### Inputs

* `stages.yaml`: Parallel group definitions
* `orchestration_state.json`: Resume state with parallel group status
* Stage outputs from prior stages (e.g., spec content for RESEARCH/TEST_STRATEGY)

### Outputs

* Updated `orchestration_state.json` with per-stage tracking
* Stage artifacts written to unique paths (`research.md`, `test_strategy.md`)
* Console output showing parallel execution progress

### Success Metrics

| Metric | Type | Baseline | Target | Source |
|--------|------|----------|--------|--------|
| Parallel group elapsed time | Latency | Sum of stage durations | Max of stage durations | Timing logs |
| Resume correctness | Accuracy | N/A (new feature) | 100% correct stage selection | Resume tests |
| Configuration errors caught | Quality | N/A | 100% at load time | Validation tests |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `asyncio` | Runtime | High | Python stdlib | Low | Standard library, well-tested |
| `stages.yaml` schema | Configuration | High | TeamBot | Medium | Schema validation at load time |
| `WorkflowStage` enum | Code | High | `stages.py` | Low | Existing, stable |
| `STAGE_METADATA.next_stages` | Code | Medium | `stages.py` | Medium | Update fan-out for parallel transitions |
| Copilot CLI | External | High | GitHub | Low | Each stage spawns independent session |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Status |
|---------|-------------|----------|------------|------------|--------|
| R-001 | Artifact write conflicts during concurrent execution | High | Low | Unique paths per stage enforced by existing pattern | Accepted |
| R-002 | State corruption if process killed mid-parallel-group | High | Medium | Atomic per-stage updates; resume handles partial state | Mitigated |
| R-003 | Regression in sequential workflow behavior | High | Low | Comprehensive existing test suite; new parallel-specific tests | Mitigated |
| R-004 | Invalid parallel group configuration | Medium | Medium | Validate at load time: no review stages, stages exist, no cycles | Mitigated |
| R-005 | Increased complexity in execution loop | Medium | Medium | Clear separation via `ParallelStageExecutor`; well-documented | Accepted |

---

## 11. Privacy, Security & Compliance

### Data Classification

No change to existing data handling. Parallel execution does not introduce new data flows.

### PII Handling

Not applicable. Orchestration state contains stage metadata and outputs, no user PII.

### Threat Considerations

* **Denial of Service**: Parallel execution could theoretically spawn more concurrent Copilot sessions, but groups are statically configured and limited
* **State Tampering**: Existing file-based state has same trust model; no new attack surface

---

## 12. Operational Considerations

| Aspect | Requirement |
|--------|-------------|
| Deployment | Standard pip install; no infrastructure changes |
| Rollback | Feature is additive; removing `parallel_groups` from config reverts to sequential |
| Monitoring | Existing logging captures stage start/end times; parallel stages show concurrent timestamps |
| Alerting | No new alerting required; failures surface via existing error handling |
| Support | Documentation updates for parallel groups configuration |

---

## 13. Rollout & Launch Plan

### Phases

| Phase | Description | Gate Criteria |
|-------|-------------|---------------|
| 1. Implementation | Build `ParallelStageExecutor`, config parsing, state evolution | Unit tests pass |
| 2. Integration | Wire into `ExecutionLoop`, update state machine | Integration tests pass |
| 3. Validation | End-to-end testing with first parallel group | RESEARCH + TEST_STRATEGY run concurrently |
| 4. Release | Merge to main, update documentation | All tests pass, docs updated |

### Feature Flags

Not applicable. Feature is controlled by `parallel_groups` presence in configuration.

---

## 14. Acceptance Test Scenarios

### AT-001: Concurrent Execution of RESEARCH and TEST_STRATEGY

**Description**: After SPEC_REVIEW completes, RESEARCH and TEST_STRATEGY execute concurrently

**Preconditions**: 
- Workflow has completed through SPEC_REVIEW
- `parallel_groups.post_spec` configured in `stages.yaml`

**Steps**:
1. Run orchestration with an objective that reaches SPEC_REVIEW
2. Wait for SPEC_REVIEW to complete successfully
3. Observe RESEARCH and TEST_STRATEGY execution

**Expected Result**: 
- Both stages start within 1 second of each other
- Execution logs show overlapping timestamps
- Total elapsed time ≈ max(RESEARCH time, TEST_STRATEGY time)

**Verification**: 
- Parse logs for stage start/end times
- Verify overlap exists
- Verify elapsed time < sum of individual durations

---

### AT-002: Resume Mid-Parallel-Group with One Stage Complete

**Description**: Interrupt a parallel group after one stage completes, resume re-runs only incomplete stage

**Preconditions**:
- Parallel group execution in progress
- RESEARCH has completed, TEST_STRATEGY in progress

**Steps**:
1. Start orchestration that triggers parallel group
2. Wait for RESEARCH to complete
3. Interrupt execution (simulated crash or Ctrl+C) while TEST_STRATEGY in progress
4. Resume orchestration using saved state

**Expected Result**:
- Resume detects RESEARCH as complete
- Only TEST_STRATEGY is re-executed
- RESEARCH output preserved from prior run

**Verification**:
- Check state file shows RESEARCH complete
- Observe only TEST_STRATEGY runs on resume
- Verify RESEARCH artifact unchanged

---

### AT-003: Parallel Group Failure Handling

**Description**: One stage in a parallel group fails; sibling completes successfully

**Preconditions**:
- Parallel group configured with two stages
- One stage designed to fail (e.g., via test fixture)

**Steps**:
1. Configure test where RESEARCH will fail
2. Start orchestration that triggers parallel group
3. Wait for both stages to reach completion/failure

**Expected Result**:
- TEST_STRATEGY completes successfully despite RESEARCH failure
- RESEARCH failure is logged with error details
- Workflow does not advance past parallel group
- Aggregate error message shows which stage(s) failed

**Verification**:
- TEST_STRATEGY artifact exists and is valid
- Error log contains RESEARCH failure
- Workflow state shows group failed with partial completion

---

### AT-004: Backward Compatibility with Legacy State File

**Description**: Resume works correctly with state file from before parallel groups feature

**Preconditions**:
- State file from v0.1.x (no `parallel_group_status` field)
- Current code includes parallel groups support

**Steps**:
1. Create legacy state file at RESEARCH stage (sequential model)
2. Run resume with current codebase

**Expected Result**:
- State file loads without error
- Workflow resumes from RESEARCH sequentially
- No crash or missing field errors

**Verification**:
- Resume completes successfully
- Logs show sequential execution (not parallel)
- No exceptions thrown during state parsing

---

### AT-005: Configuration Validation Rejects Invalid Parallel Groups

**Description**: Invalid parallel group configurations are caught at load time

**Preconditions**: 
- Various invalid configurations prepared

**Steps**:
1. Configure parallel group containing a review stage (`SPEC_REVIEW`)
2. Attempt to load configuration

**Expected Result**:
- Clear validation error at load time
- Error message identifies the invalid stage and reason

**Verification**:
- Exception raised during config parsing
- Error message mentions `is_review_stage` constraint

---

## 15. Open Questions

| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| Q-001 | Should parallel groups support max concurrency limits? | Team | Resolved: Not for v0.2.0; groups are small |
| Q-002 | How should visualization distinguish parallel stages? | Team | Resolved: Multi-row display with concurrent indicators |
| Q-003 | Should failed parallel groups support partial advancement? | Team | Resolved: No; all stages must succeed to advance |

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-10 | TeamBot | Initial specification | New |

---

## 17. References

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Problem Statement | `.teambot/parallel-stage-groups/artifacts/problem_statement.md` | Business problem and goals |
| REF-002 | Codebase | `src/teambot/orchestration/execution_loop.py` | Current execution loop implementation |
| REF-003 | Codebase | `src/teambot/orchestration/parallel_executor.py` | Existing agent-level parallel executor |
| REF-004 | Configuration | `stages.yaml` | Current stage configuration schema |
| REF-005 | Codebase | `src/teambot/workflow/stages.py` | Stage metadata and state machine |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Parallel Group | A set of stages configured to execute concurrently at a defined point in the workflow |
| Trigger Stage | The stage whose completion initiates parallel group execution |
| ParallelStageExecutor | New component for concurrent stage execution (distinct from ParallelExecutor) |
| ParallelExecutor | Existing component for concurrent agent execution within a single stage |
| Stage Order | Linear list in `stages.yaml` defining sequential workflow progression |
| Fan-out Transition | A state machine transition from one stage to multiple concurrent stages |

## Appendix B: State Machine Transition Updates

The `STAGE_METADATA` in `src/teambot/workflow/stages.py` must be updated to reflect parallel transitions:

**Before (sequential):**
```python
SPEC_REVIEW: StageMetadata(next_stages=[RESEARCH])
RESEARCH: StageMetadata(next_stages=[TEST_STRATEGY])
TEST_STRATEGY: StageMetadata(next_stages=[PLAN])
```

**After (parallel fan-out):**
```python
SPEC_REVIEW: StageMetadata(next_stages=[RESEARCH, TEST_STRATEGY])  # Fan-out
RESEARCH: StageMetadata(next_stages=[PLAN])  # Fan-in (both converge to PLAN)
TEST_STRATEGY: StageMetadata(next_stages=[PLAN])  # Fan-in
```

This enables the state machine to validate that transitions from `SPEC_REVIEW` to either `RESEARCH` or `TEST_STRATEGY` are legal.

## Appendix C: Implementation File Structure

```
src/teambot/orchestration/
├── execution_loop.py          # Modify: detect parallel groups, dispatch
├── parallel_executor.py       # Unchanged: agent-level parallelism
├── parallel_stage_executor.py # NEW: stage-level parallelism
└── ...

src/teambot/workflow/
├── stages.py                  # Modify: update next_stages for fan-out
├── stage_config.py            # Modify: parse parallel_groups from YAML
└── ...

stages.yaml                    # Modify: add parallel_groups section
```

<!-- markdown-table-prettify-ignore-end -->
