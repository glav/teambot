# File-Based Orchestration Critical Failure Handling - TeamBot Objective

## Objective

**Goal**: Implement robust failure handling in TeamBot's file-based orchestration to ensure critical stage failures (like missing implementation plans) immediately halt the workflow with clear feedback, AND fix the root cause of artifact path mismatches that prevent artifacts from being found.

**Problem Statement**: File-based orchestration has four critical defects that undermine its reliability:

1. **Artifact Path Mismatch (Upstream Cause)**: Agents write artifacts to inconsistent paths. The TEST_STRATEGY agent writes to `.teambot/.../artifacts/test_strategy.md` but the PLAN agent looks in `.agent-tracking/test-strategies/`. This path mismatch means artifacts are "produced" but never found by subsequent stages. The orchestrator does not provide explicit artifact paths to agents, leaving path resolution to each agent's interpretation.

2. **Plan Generation Complete Failure (Critical)**: The PLAN stage fails to produce **any** `implementation_plan.md` artifact. Unlike path mismatch (where a file exists but in wrong location), the PLAN agent produced **no output file at all** - it bailed out after failing to find prerequisites, writing only a "Cannot Proceed" message to the stage output but creating no artifact file. Evidence: The file listing shows no plan artifact exists anywhere in the workspace (neither `.agent-tracking/plans/` nor `.teambot/.../artifacts/`).

3. **No Stage Output Validation**: When a stage agent reports "Cannot Proceed" or fails to create its required artifact, the orchestrator treats this as a successful stage completion. The orchestrator captures the agent's text output but does not validate that actual artifact files were created. The PLAN stage "completed" with no plan file.

4. **Silent Continuation on Critical Failure**: When the IMPLEMENTATION stage detects that no plan file exists, it logs the issue but continues execution rather than halting. Critical prerequisite failures must stop the workflow immediately, not proceed into undefined states.

Evidence from `docs/objectives/example-orchestration-state.json` and file listing:
- TEST_STRATEGY stage: Agent wrote `test_strategy.md` to `.teambot/.../artifacts/` (file exists)
- PLAN stage: Agent looked in `.agent-tracking/test-strategies/` (wrong path), found nothing, reported "Cannot Proceed with Planning" - **created NO artifact file** (no `implementation_plan.md` exists anywhere in the workspace)
- IMPLEMENTATION stage: Agent reported "Missing Prerequisites" and "Implementation Cannot Proceed" but workflow advanced to TEST stage anyway
- **Critical observation**: The PLAN failure is NOT just a path mismatch - the stage produced zero output files. The agent's text response was captured but no artifact was created.

**Success Criteria**:

*Root Cause Fix (Artifact Path Enforcement):*
- [ ] Orchestrator injects explicit artifact output paths into agent context before stage execution
- [ ] `stages.yaml` defines `required_artifacts` with full paths relative to `.agent-tracking/`
- [ ] Agents receive clear instructions on WHERE to write artifacts (not left to interpretation)
- [ ] Artifact paths are consistent between producing stage and consuming stage

*Failure Detection and Halt:*
- [ ] When a stage fails to produce a required artifact, the workflow MUST halt immediately (process exit, not continue)
- [ ] Orchestrator detects missing required artifacts after stage completion and stops execution
- [ ] Halted state includes clear explanation of what artifact was missing and which stage failed
- [ ] User receives feedback (console output, notifications) explaining the failure and recommended next steps

*Configuration and Resume:*
- [ ] IMPLEMENTATION stage validates that `implementation_plan.md` exists BEFORE executing
- [ ] Stage artifact requirements are configurable via `stages.yaml` using `required_artifacts` field
- [ ] Notifications include failure information when workflow halts due to missing prerequisites
- [ ] Resume functionality (`teambot run --resume`) can restart from halted stage after user intervention

*Quality:*
- [ ] All existing tests continue to pass
- [ ] New tests validate artifact path injection and failure detection

---

## Technical Context

**Target Codebase**: `/workspaces/teambot/src/teambot/`

**Primary Language/Framework**: Python

**Testing Preference**: TDD - these are critical safety mechanisms that must be thoroughly tested before implementation

**Key Constraints**:
- Must integrate with existing notification system (Telegram, etc.)
- Must work with existing orchestration state persistence (`orchestration_state.json`)
- Failure messages must be actionable (tell user exactly what to do to fix)

---

## Clarifications (from Review)

### Artifact Path Resolution

**Decision**: All artifacts are stored in `.agent-tracking/` directory structure, NOT `.teambot/`.

- `.agent-tracking/` - Primary artifact storage for all workflow outputs (specs, research, plans, etc.)
- `.teambot/` - Working files and orchestration state only (e.g., `orchestration_state.json`)

Artifact paths in `required_artifacts` are resolved relative to `.agent-tracking/`:
```yaml
required_artifacts:
  - plans/implementation_plan.md  # Resolves to .agent-tracking/plans/implementation_plan.md
  - test-strategies/test_strategy.md  # Resolves to .agent-tracking/test-strategies/test_strategy.md
```

The `stages.yaml` must be updated to reflect this path resolution, and documentation should clearly state this convention.

### Schema Field Consolidation

**Decision**: Replace existing `artifacts` field with `required_artifacts` for clarity of intent.

The current `artifacts` field is ambiguous - it lists outputs but doesn't enforce their creation. Renaming to `required_artifacts` makes the validation intent explicit:

```yaml
# BEFORE (ambiguous)
artifacts:
  - implementation_plan.md

# AFTER (clear intent)
required_artifacts:
  - plans/implementation_plan.md  # MUST exist after stage completes, or halt
```

This is a **breaking change** to `stages.yaml` schema. Migration:
1. Rename `artifacts` → `required_artifacts` in all stage definitions
2. Update paths to include subdirectory (e.g., `plans/`, `research/`, `specs/`)
3. Add schema version field to `stages.yaml` for future compatibility

### Parallel Stage Failure Semantics

**Decision**: If ANY stage in a parallel group fails, the ENTIRE group fails.

When a parallel group (e.g., RESEARCH + TEST_STRATEGY) executes:
- If one stage fails to produce required artifacts, both are considered failed
- Workflow halts immediately
- Artifacts from the successful stage ARE preserved (not deleted)
- Failure message indicates which specific stage(s) failed

No partial success - the gate stage (e.g., PLAN) cannot proceed unless ALL parallel stages succeed.

### Halt Behavior

**Decision**: `halt_workflow()` stops execution IMMEDIATELY (process exit).

- Workflow does NOT transition to a "FAILED state" and continue processing
- Process exits with non-zero exit code after logging failure
- Orchestration state is persisted with `status: "halted"`, `halt_reason`, and `halted_at_stage`
- Resume (`--resume`) reads halted state and restarts from the failed stage

This is a hard stop, not a soft transition. The distinction:
- ❌ "Transition to FAILED state" implies continued orchestrator execution but only where retries are applicable otherwise a hard stop
- ✅ "Halt and exit" means immediate process termination after cleanup

### Resume Documentation

When workflow halts, the failure message MUST include:
1. **What failed**: Stage name and missing artifact
2. **Where to fix**: Exact path where artifact should be created (e.g., `.agent-tracking/plans/implementation_plan.md`)
3. **How to resume**: Exact command (`teambot run --resume objectives/my-objective.md`)

Example failure output:
```
❌ WORKFLOW HALTED: Missing required artifact

Stage: PLAN
Missing: .agent-tracking/plans/implementation_plan.md
Cause: Agent completed but did not create required artifact

To fix:
  1. Manually create the implementation plan at the path above, OR
  2. Run the planning prompt directly: /sdd:5-task-planner-for-feature

To resume after fixing:
  teambot run --resume docs/objectives/my-objective.md
```

---

## Additional Context

### Root Cause Analysis

From the orchestration state and file listing, three distinct failure modes occurred:

**Failure Mode 1: Artifact Path Mismatch (Upstream)**
```
TEST_STRATEGY agent → writes to .teambot/.../artifacts/test_strategy.md
PLAN agent → looks in .agent-tracking/test-strategies/ → NOT FOUND
```
The TEST_STRATEGY stage completed successfully and produced an artifact, but at a different path than where PLAN looked. **Resolution**: Orchestrator must inject explicit artifact paths.

**Failure Mode 2: Complete Stage Output Failure (Critical)**
```
PLAN agent → prerequisite lookup fails → outputs "Cannot Proceed" text → CREATES NO FILE
```
Unlike path mismatch (file exists but in wrong place), the PLAN stage produced **zero artifact files**. The file listing confirms no `implementation_plan.md` exists anywhere:
- ❌ Not in `.agent-tracking/plans/`
- ❌ Not in `.teambot/.../artifacts/`
- ❌ Not anywhere in the workspace

The orchestrator captured the agent's "Cannot Proceed" text response but has no mechanism to distinguish this from success. **Resolution**: Validate required artifact file existence after stage completion.

**Failure Mode 3: No Exit Gate**
The orchestrator has no mechanism to:
1. Validate that required artifacts were actually created
2. Stop workflow progression when validation fails
3. Halt execution immediately with clear error

### Implementation Approach

**Phase 1: Artifact Path Injection (Root Cause Fix)**
- Add `artifact_context` generation in orchestrator before stage execution
- Inject explicit output paths into agent context: "Write your output to: `.agent-tracking/plans/implementation_plan.md`"
- Add `input_artifacts` field to stages.yaml (artifacts from prior stages the agent needs to read)
- Generate context block with both input paths (to read) and output paths (to write)

**Phase 2: Schema Migration**
- Rename `artifacts` field to `required_artifacts` in stage schema
- Add `input_artifacts` field (list of artifact paths this stage needs from prior stages)
- Add path resolution logic for `.agent-tracking/` base directory
- Update all stage definitions in `stages.yaml` with full paths
- Add schema version field for future migrations

**Phase 3: Artifact Validation**
- Implement `validate_required_artifacts(stage)` in orchestrator
- Check artifact existence after stage completion, before transition
- For parallel groups, validate ALL stages before proceeding to gate stage

**Phase 4: Halt Mechanism**
- Implement `halt_workflow(reason, stage)` method in orchestrator
- Persist halt state to `orchestration_state.json` with `status: "halted"`
- Exit process with non-zero exit code
- Emit `workflow_halted` notification event

**Phase 5: User Feedback**
- Format actionable error messages with exact paths and fix instructions
- Update notification handlers to include halt details
- Ensure console output is clear and helpful

**Phase 6: Resume Capability**
- Update `--resume` to detect `status: "halted"` state
- Re-validate prerequisites before resuming halted stage
- Clear halt state on successful stage completion

### Key Files to Modify

| File | Changes |
|------|---------|
| `src/teambot/orchestrator.py` | Add artifact path injection, validation, halt logic |
| `src/teambot/workflow/stages.py` | Add `required_artifacts`, `input_artifacts`, path resolution |
| `src/teambot/agent_runner.py` | Receive and include artifact context in agent prompts |
| `src/teambot/notifications/events.py` | Add `workflow_halted` event (consistent with existing naming) |
| `src/teambot/cli.py` | Update resume logic to handle `status: "halted"` |
| `stages.yaml` | Add fields, update all artifact paths to `.agent-tracking/` structure |

### Relevant Existing Code

The orchestrator currently handles stage transitions in `orchestrator.py`. Stage configuration parsing is in `workflow/stages.py`.

Current stage output capture happens but artifact validation is not performed. The `stage_outputs` dict captures agent responses but doesn't verify file creation.

---

## Out of Scope

- Automatic retry of failed stages (future enhancement)
- Agent prompt template modifications (orchestrator injects paths, but doesn't change prompt files)
- UI/UX improvements beyond console and notification messages
- Granular `on_failure` options for parallel groups (always fail entire group for now)

---

## References

- **Evidence**: `docs/objectives/example-orchestration-state.json` - orchestration state showing the failures
- **Objective that triggered failures**: `docs/objectives/example-problem-objective.md`
- **Stage definitions**: `stages.yaml`
- **Orchestration code**: `src/teambot/orchestrator.py`

---

## Acceptance Test Scenarios

### AT-001: Missing Required Artifact Halts Workflow
**Given** a stage is configured with `required_artifacts: [plans/implementation_plan.md]`
**And** the agent completes the stage without creating `.agent-tracking/plans/implementation_plan.md`
**When** the orchestrator validates stage completion
**Then** the workflow halts immediately (process exits with non-zero code)
**And** orchestration state shows `status: "halted"` with `halt_reason` and `halted_at_stage`
**And** a `workflow_halted` notification is sent

### AT-002: Missing Input Artifact Prevents Stage Start
**Given** IMPLEMENTATION stage has `input_artifacts: [plans/implementation_plan.md]`
**And** `.agent-tracking/plans/implementation_plan.md` does not exist
**When** the orchestrator attempts to start IMPLEMENTATION stage
**Then** the workflow halts immediately before the stage agent is invoked
**And** the halt reason indicates "Input artifact 'plans/implementation_plan.md' missing for IMPLEMENTATION stage"

### AT-003: Resume From Halted State
**Given** the workflow is in halted state at PLAN stage
**And** the user has manually created the missing prerequisite at `.agent-tracking/test-strategies/test_strategy.md`
**When** the user runs `teambot run --resume objectives/my-objective.md`
**Then** prerequisite validation passes
**And** the PLAN stage is retried
**And** the workflow continues normally

### AT-004: Console Output Shows Actionable Failure Message
**Given** the workflow halts due to missing artifact
**When** the failure is displayed to the user
**Then** the message includes:
  - Which stage failed (e.g., "Stage: PLAN")
  - Which artifact was missing with FULL PATH (e.g., ".agent-tracking/plans/implementation_plan.md")
  - Recommended action (e.g., "Run /sdd:5-task-planner-for-feature to create the plan")
  - Exact resume command (e.g., "teambot run --resume docs/objectives/my-objective.md")

### AT-005: Notification Includes Failure Details
**Given** notifications are configured
**When** the workflow halts due to missing artifact
**Then** a `workflow_halted` notification is sent with:
  - Stage name that failed
  - Missing artifact name with path
  - Timestamp of failure

### AT-006: Parallel Stage Failure Halts Entire Group
**Given** RESEARCH and TEST_STRATEGY are configured to run in parallel (post_spec_review group)
**And** TEST_STRATEGY fails to produce `.agent-tracking/test-strategies/test_strategy.md`
**When** the orchestrator validates the parallel group completion
**Then** the workflow halts immediately
**And** the halt reason indicates TEST_STRATEGY failed
**And** RESEARCH artifacts (if created) are preserved
**And** PLAN stage is NOT started

### AT-007: Agent Receives Explicit Artifact Output Path
**Given** PLAN stage is configured with `required_artifacts: [plans/implementation_plan.md]`
**When** the orchestrator prepares context for the PLAN agent
**Then** the agent context includes explicit instruction: "Write your implementation plan to: `.agent-tracking/plans/implementation_plan.md`"
**And** the full resolved path is provided (not relative)

### AT-008: Agent Receives Input Artifact Paths
**Given** PLAN stage is configured with `input_artifacts: [test-strategies/test_strategy.md, research/research.md]`
**When** the orchestrator prepares context for the PLAN agent
**Then** the agent context includes: "Read test strategy from: `.agent-tracking/test-strategies/test_strategy.md`"
**And** the agent context includes: "Read research from: `.agent-tracking/research/research.md`"

### AT-009: Artifact Written to Correct Path is Found
**Given** TEST_STRATEGY stage is configured with `required_artifacts: [test-strategies/test_strategy.md]`
**And** the agent writes to `.agent-tracking/test-strategies/test_strategy.md` (the injected path)
**When** the orchestrator validates stage completion
**Then** validation passes
**And** PLAN stage receives the correct input path for the test strategy
**And** workflow continues normally

### AT-010: Stage Producing No Artifact File Halts Workflow
**Given** PLAN stage is configured with `required_artifacts: [plans/implementation_plan.md]`
**And** the agent completes but creates NO artifact file (regardless of text output content)
**When** the orchestrator validates stage completion
**Then** the workflow halts immediately (artifact file existence check fails)
**And** orchestration state shows `status: "halted"` with reason "Required artifact not created"
**And** validation is based solely on file existence, not agent output text parsing

### AT-011: Text Output Content Does Not Affect Artifact Validation
**Given** PLAN stage is configured with `required_artifacts: [plans/implementation_plan.md]`
**And** the agent outputs "Cannot Proceed with Planning" in its text response
**But** the agent ALSO creates `.agent-tracking/plans/implementation_plan.md` file
**When** the orchestrator validates stage completion
**Then** validation passes (file exists)
**And** workflow continues normally
**Note** This confirms validation is file-based only; agent text content is informational, not authoritative
