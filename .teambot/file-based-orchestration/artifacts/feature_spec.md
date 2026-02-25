<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# File-Based Orchestration Critical Failure Handling - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-25 |
| Problem & Users | ✅ | None | 2026-02-25 |
| Scope | ✅ | None | 2026-02-25 |
| Requirements | ✅ | None | 2026-02-25 |
| Metrics & Risks | ✅ | None | 2026-02-25 |
| Operationalization | ✅ | None | 2026-02-25 |
| Finalization | ✅ | None | 2026-02-25 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot orchestrates multi-agent AI workflows through a file-based system where each workflow stage produces artifacts (markdown files) that subsequent stages depend upon. The orchestration relies on `stages.yaml` to define stage order, agents, and expected artifacts, with state persisted to `orchestration_state.json`.

### Core Opportunity
Currently, when critical artifacts are missing, TeamBot silently continues execution, leading to wasted time, API costs, and confused agent outputs. By implementing fail-fast validation with actionable error messages, users will immediately know what went wrong and how to fix it.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Halt workflow immediately when critical artifacts are missing | Safety | 0% validation | 100% pre-execution validation | v0.2.0 | P0 |
| G-002 | Provide actionable error messages with path, stage, and resolution guidance | UX | Generic errors | Structured actionable errors | v0.2.0 | P0 |
| G-003 | Integrate critical failures with notification system | Observability | No failure notifications | `critical_failure` events sent | v0.2.0 | P1 |
| G-004 | Ensure consistent artifact path resolution across all lookup points | Quality | Multiple inconsistent lookups | Single unified resolver | v0.2.0 | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Eliminate silent failures | Zero workflows proceed with missing critical artifacts | P0 | Builder |
| Improve user experience | 100% of failure messages include resolution steps | P0 | Builder |
| Enable monitoring | All critical failures trigger notifications | P1 | Builder |

## 2. Problem Definition

### Current Situation
TeamBot's `ExecutionLoop` in `src/teambot/orchestration/execution_loop.py` looks up artifacts via methods like `_find_feature_spec_content()`. When artifacts are not found:
- The method returns `None` instead of raising an error
- Execution continues with incomplete context
- Agents receive prompts missing critical information
- Users discover problems late (during review or acceptance tests)

### Problem Statement
**When a workflow stage requires artifacts from previous stages, TeamBot silently continues execution if those artifacts are missing, rather than immediately halting with actionable feedback.** This wastes time, API costs, and erodes user trust.

### Root Causes
* **No pre-execution validation**: The orchestration does not validate artifact existence before invoking agents
* **Graceful degradation by default**: Lookup functions return `None` on missing files, designed for optional artifacts
* **Path inconsistency**: Multiple search locations with different normalization rules (hyphens, case) cause false negatives
* **No critical vs. optional distinction**: All artifacts treated the same regardless of downstream dependency

### Impact of Inaction
Without addressing these issues:
- Users continue wasting 10-30+ minutes per failed workflow discovering problems late
- API costs accumulate on doomed operations
- User trust erodes as workflows fail mysteriously
- Support burden increases as users report confusing agent outputs

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| TeamBot User | Run successful multi-agent workflows with clear feedback | Workflows fail silently; errors are cryptic; don't know how to fix | Primary |
| TeamBot Developer | Maintain testable, debuggable orchestration code | Failure paths are implicit; hard to test silent failures | Secondary |
| Agent Persona (PM, BA, Builder) | Receive complete context to produce quality output | Missing artifacts lead to confused or divergent outputs | Tertiary |

### Journeys

**Journey 1: Implementation Stage Missing Task Plan**
1. User runs objective through PLAN stage
2. Task plan saved to wrong location (path mismatch)
3. IMPLEMENTATION stage starts without plan
4. Builder agent produces confused output
5. User discovers problem during review (wasted time)

**Desired Journey:**
1. IMPLEMENTATION stage validates `implementation_plan.md` exists
2. If missing: immediate halt with actionable error
3. User fixes path or creates file
4. Resume workflow from IMPLEMENTATION

**Journey 2: Feature Spec Lookup Failure**
1. Feature spec exists but naming doesn't match
2. `_find_feature_spec_content()` returns `None`
3. Acceptance tests run without spec context
4. Tests fail with confusing results

**Desired Journey:**
1. Lookup logs diagnostic info (paths searched, patterns tried)
2. Error clearly states spec not found and lists search locations
3. User identifies and fixes the mismatch

## 4. Scope

### In Scope
* FR-001: Pre-execution validation of critical artifacts
* FR-002: Actionable error message formatting
* FR-003: New `critical_failure` notification event
* FR-004: Failure reason persistence in `orchestration_state.json`
* FR-005: Resume capability after artifact is provided
* FR-006: Unified artifact path resolution function
* FR-007: Diagnostic logging for artifact lookups

### Out of Scope
* Automatic artifact creation or recovery
* Changes to artifact storage locations (only fixing lookup consistency)
* Non-critical/optional artifact handling changes
* Changes to agent prompt templates (beyond path references)
* New notification channels (only new event type)
* UI changes

### Assumptions
* The existing notification system (Telegram) is functioning and can receive new event types without code changes to channel implementations
* `stages.yaml` already has an `artifacts` field per stage that can serve as the source of truth for required artifacts
* Users prefer immediate failure with clear guidance over degraded-mode continuation
* The current `orchestration_state.json` schema can accommodate a new `failure_reason` field

### Constraints
* Must maintain backward compatibility with existing workflows that complete successfully
* Must integrate with existing `EventBus.emit_sync()` pattern
* Must use TDD approach per user preference
* Must not increase orchestration startup time significantly (<100ms overhead)

## 5. Product Overview

### Value Proposition
For TeamBot users who experience confusing workflow failures, the Critical Failure Handling feature provides immediate, actionable feedback when required artifacts are missing, unlike the current silent continuation behavior, because it validates artifact existence before agent execution and provides clear resolution guidance.

### Differentiators
* **Fail-fast safety**: Zero tolerance for missing critical dependencies
* **Actionable errors**: Every error tells you exactly what to do
* **Notification integration**: Critical failures reach you via Telegram
* **Resume-friendly**: Fix the issue and continue from where you stopped

### UX / UI
No UI changes. This feature affects:
- Terminal output: New error message format for missing artifacts
- Notification messages: New `critical_failure` event template
- State file: New `failure_reason` field

UX Status: Not Applicable (CLI-only changes)

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Pre-execution artifact validation | Before executing any stage, validate all artifacts listed in `stages.yaml` for that stage's dependencies exist | G-001 | User, Agent | P0 | Stage halts before agent execution when artifact missing | Validation occurs in `ExecutionLoop` |
| FR-002 | Actionable error message format | Error messages must include: artifact path, requiring stage, creating stage, and resolution guidance | G-002 | User | P0 | Error message contains all 4 elements | Template-based formatting |
| FR-003 | Critical failure notification event | Emit `critical_failure` event via `EventBus` when artifact validation fails | G-003 | User | P1 | Telegram receives notification with error details | Use existing `emit_sync` pattern |
| FR-004 | Failure state persistence | Save failure reason to `orchestration_state.json` with `status: "failed"` and `failure_reason` field | G-001 | User | P0 | State file contains failure details for resume | Extend existing `_save_state()` |
| FR-005 | Resume after failure | When resuming a failed workflow, re-validate artifacts before continuing | G-001 | User | P1 | Resume validates artifacts, proceeds if present | Extend `ExecutionLoop.resume()` |
| FR-006 | Unified artifact path resolver | Single function to resolve artifact paths, used by all lookup points | G-004 | Developer | P1 | All lookups use same resolver | Replaces scattered path logic |
| FR-007 | Diagnostic artifact logging | When artifact lookup fails, log: paths searched, patterns tried, files found | G-004 | Developer, User | P2 | Debug logs show lookup details | Use `logging.debug()` |
| FR-008 | Define required artifacts per stage | Extend stage config to distinguish required vs optional artifacts | G-001 | Developer | P0 | `stages.yaml` specifies `required_artifacts` | May use existing `artifacts` field |

### Feature Hierarchy
```plain
Critical Failure Handling
├── Artifact Validation (FR-001, FR-008)
│   ├── Pre-execution check
│   └── Required artifact definition
├── Error Messaging (FR-002)
│   ├── Error message template
│   └── Resolution guidance generator
├── Notification Integration (FR-003)
│   ├── New event type: critical_failure
│   └── Message template for Telegram
├── State Management (FR-004, FR-005)
│   ├── Failure reason persistence
│   └── Resume validation
└── Path Resolution (FR-006, FR-007)
    ├── Unified resolver
    └── Diagnostic logging
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Artifact validation overhead | <100ms per stage | P1 | Benchmark test | File existence checks only |
| NFR-002 | Reliability | Validation must not raise unhandled exceptions | 0 crashes from validation logic | P0 | Unit tests with edge cases | Catch and report all errors |
| NFR-003 | Maintainability | Single source of truth for artifact paths | 1 resolver function | P1 | Code review | No duplicated path logic |
| NFR-004 | Observability | All validation failures logged | 100% failures have debug logs | P1 | Log inspection tests | Use structured logging |
| NFR-005 | Security | No sensitive data in error messages | 0 secrets exposed | P0 | Security review | Paths are safe to log |
| NFR-006 | Compatibility | Existing workflows unaffected | 0 regressions in passing workflows | P0 | Integration tests | Run existing test suite |

## 8. Data & Analytics

### Inputs
* `stages.yaml`: Stage definitions including artifact lists
* File system: Artifact file existence checks
* `orchestration_state.json`: Current workflow state

### Outputs / Events
* `critical_failure` event: Emitted when validation fails
* Updated `orchestration_state.json`: With `failure_reason` field
* Console error output: Actionable error message

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| critical_failure | Artifact validation fails | `{artifact_path, stage, expected_from_stage, resolution, feature_name}` | Alert user via notifications | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Workflows halted early on missing artifacts | Count | 0 | 100% of relevant cases | Per release | Unit tests |
| Mean time to resolution after failure | Duration | Unknown (late discovery) | <5 minutes | Post-release | User feedback |
| False positive validation failures | Rate | N/A | <1% | Per release | Issue reports |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `EventBus.emit_sync()` | Internal | High | Existing | Low - stable API | Use existing pattern |
| `stages.yaml` artifacts field | Internal | High | Existing | Low - already present | Document expected format |
| `orchestration_state.json` | Internal | High | Existing | Low - extend schema | Add `failure_reason` field |
| Telegram channel | External | Medium | Existing | Low - already tested | Add new event template |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Breaking existing workflows that tolerate missing optional artifacts | High | Medium | Use `required_artifacts` field separate from `artifacts`; existing workflows unchanged | Builder | Open |
| R-002 | Over-sensitive validation blocking legitimate workflows | Medium | Low | Document which artifacts are critical; allow workflow-level override | Builder | Open |
| R-003 | Notification spam on repeated validation failures | Low | Low | Deduplicate notifications for same failure within session | Builder | Open |
| R-004 | Path normalization edge cases (unicode, special chars) | Medium | Low | Comprehensive test cases for edge cases | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
All data handled is **Internal** - file paths, stage names, workflow state. No PII involved.

### PII Handling
Not applicable. No personally identifiable information is processed by this feature.

### Threat Considerations
* **Path traversal**: Ensure artifact paths are validated and constrained to expected directories
* **Information disclosure**: Error messages include file paths which are safe for CLI users but should not expose system internals

### Regulatory / Compliance
Not applicable. No regulatory requirements for this feature.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Revert to previous version | State files remain compatible |
| Monitoring | Debug logging for validation | Existing logging infrastructure |
| Alerting | Via notification system | Telegram receives critical_failure events |
| Support | Error messages are self-documenting | Reduced support burden expected |
| Capacity Planning | Negligible overhead | File existence checks are fast |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | All FR and NFR tests passing | Builder |
| Integration Testing | TBD | Existing workflows unaffected | Builder |
| Documentation | TBD | AGENTS.md updated if needed | Writer |
| Release | TBD | Merged to main | PM |

### Feature Flags
Not applicable. Feature is always active once deployed.

### Communication Plan
* Update CHANGELOG.md with new behavior
* Document new error message format in docs/

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| - | None | - | - | - |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-25 | BA Agent | Initial specification | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Code | `src/teambot/orchestration/execution_loop.py` | Current artifact lookup implementation | N/A |
| REF-002 | Code | `src/teambot/notifications/templates.py` | Existing notification templates | N/A |
| REF-003 | Config | `stages.yaml` | Stage definitions with artifacts | N/A |
| REF-004 | Doc | `.teambot/file-based-orchestration/artifacts/problem_statement.md` | Problem definition | N/A |

## 17. Acceptance Test Scenarios

### AT-001: Missing Implementation Plan Halts IMPLEMENTATION Stage
**Description**: Workflow halts before agent execution when required artifact is missing
**Preconditions**: 
- Workflow state is at IMPLEMENTATION stage
- `implementation_plan.md` does NOT exist at expected path
**Steps**:
1. Start orchestration loop for IMPLEMENTATION stage
2. Pre-execution validation checks for `implementation_plan.md`
3. Validation fails (file not found)
**Expected Result**: 
- Stage execution halts BEFORE any agent is invoked
- Error message displayed to console
- `critical_failure` notification emitted
- `orchestration_state.json` updated with `status: "failed"` and `failure_reason`
**Verification**: 
- No agent execution occurs (check logs/mocks)
- Error message contains: artifact path, "IMPLEMENTATION", "PLAN", resolution guidance

### AT-002: Error Message Contains All Required Elements
**Description**: Verify error message format includes all actionable information
**Preconditions**: 
- Any stage with missing required artifact
**Steps**:
1. Trigger artifact validation failure
2. Capture error message output
**Expected Result**: Error message contains:
- Full artifact path (e.g., `.teambot/my-feature/artifacts/implementation_plan.md`)
- Requiring stage name (e.g., "IMPLEMENTATION")
- Creating stage name (e.g., "PLAN")
- Resolution guidance (e.g., "Run the PLAN stage or create this file manually")
**Verification**: Parse error message and assert all 4 elements present

### AT-003: Critical Failure Triggers Notification
**Description**: Notification system receives `critical_failure` event
**Preconditions**: 
- Notification system configured (Telegram channel enabled)
- EventBus connected
**Steps**:
1. Trigger artifact validation failure
2. Observe EventBus emissions
**Expected Result**: 
- `critical_failure` event emitted via `emit_sync`
- Event payload contains: `artifact_path`, `stage`, `expected_from_stage`, `feature_name`
**Verification**: Mock EventBus and assert `emit_sync` called with correct event type and payload

### AT-004: Orchestration State Persists Failure Reason
**Description**: Failed state is saved with details for debugging and resume
**Preconditions**: 
- Workflow running
**Steps**:
1. Trigger artifact validation failure
2. Read `orchestration_state.json`
**Expected Result**: 
- `status` field is `"failed"`
- `failure_reason` field contains artifact details
**Verification**: Parse JSON and assert fields present with expected values

### AT-005: Resume Workflow After Artifact Provided
**Description**: User can fix missing artifact and resume workflow
**Preconditions**: 
- Workflow failed due to missing artifact
- `orchestration_state.json` exists with failed status
**Steps**:
1. Create the missing artifact file
2. Run `teambot resume` (or equivalent)
3. Validation re-runs
**Expected Result**: 
- Validation passes (artifact now exists)
- Workflow continues from failed stage
- Agent execution proceeds normally
**Verification**: Workflow completes successfully after resume

### AT-006: Existing Workflows With All Artifacts Pass Validation
**Description**: Ensure no regression for workflows that have all required artifacts
**Preconditions**: 
- Complete set of artifacts exist for all stages
**Steps**:
1. Run full orchestration workflow
2. All stages execute
**Expected Result**: 
- No validation errors
- Workflow completes as before
**Verification**: Run existing integration test suite; all pass

### AT-007: Unified Path Resolver Finds Artifacts in All Expected Locations
**Description**: Single resolver checks all configured paths consistently
**Preconditions**: 
- Feature spec exists in `docs/feature-specs/my-feature.md`
**Steps**:
1. Call unified path resolver for `feature_spec.md`
2. Resolver checks `.teambot/{feature}/artifacts/` first
3. Resolver checks `docs/feature-specs/` second
**Expected Result**: 
- Artifact found in secondary location
- No false "missing" error
**Verification**: Unit test with artifact in each location confirms discovery

## 18. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| Critical Artifact | An artifact that MUST exist for a stage to execute successfully |
| Fail-Fast | Design principle where errors are detected and reported as early as possible |
| Orchestration | The process of coordinating multiple agents through workflow stages |

### Additional Notes

#### Error Message Template
```
❌ CRITICAL: Missing required artifact

  Artifact:  {artifact_path}
  Stage:     {requiring_stage}
  Created by: {creating_stage}

  Resolution:
  - Run the {creating_stage} stage to generate this artifact, OR
  - Create the file manually at the path above

  Workflow halted. Fix the issue and resume with: teambot resume
```

#### Notification Template for `critical_failure`
```
❌ <b>Critical Failure</b>
📂 <code>{feature_name}</code>
📌 Stage: {stage}
❗ Missing: <code>{artifact_path}</code>

Run: teambot resume (after fixing)
```

#### Stage-to-Artifact Mapping (from stages.yaml)
| Stage | Required Artifact From | Artifact |
|-------|------------------------|----------|
| SPEC_REVIEW | SPEC | feature_spec.md |
| PLAN | SPEC_REVIEW, RESEARCH, TEST_STRATEGY | feature_spec.md, research.md, test_strategy.md |
| PLAN_REVIEW | PLAN | implementation_plan.md |
| IMPLEMENTATION | PLAN_REVIEW | implementation_plan.md |
| IMPLEMENTATION_REVIEW | IMPLEMENTATION | (code changes - N/A) |
| ACCEPTANCE_TEST | IMPLEMENTATION | feature_spec.md (for scenarios) |

<!-- markdown-table-prettify-ignore-end -->
