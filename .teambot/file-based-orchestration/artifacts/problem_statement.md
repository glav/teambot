# Problem Statement: File-Based Orchestration Critical Failure Handling

## Executive Summary

TeamBot's file-based orchestration currently exhibits **silent failure behavior** when critical artifacts are missing. Workflow stages continue execution without required inputs, leading to wasted time, confusing agent outputs, and ultimately failed objectives that could have been caught early.

## Problem Definition

### Primary Problem: Silent Continuation on Missing Required Artifacts

When a workflow stage requires artifacts from previous stages (e.g., implementation plans, feature specs, research documents), the orchestration system **silently continues execution** rather than immediately halting with actionable feedback.

**Current Behavior:**
1. Agent executes with incomplete context (missing artifact returns `None`)
2. Agent produces confused or incorrect output
3. User discovers the problem late in the workflow
4. Time and API costs are wasted

**Expected Behavior:**
1. Orchestration validates required artifacts exist before starting a stage
2. If critical artifacts are missing, workflow halts immediately
3. User receives clear error: what's missing, where it should be, and how to fix it
4. Notification channels (Telegram, etc.) receive failure alerts

### Secondary Problem: Artifact Path Mismatches

The codebase has multiple locations where artifacts can be stored and searched:
- `.teambot/{feature}/artifacts/{file}.md`
- `docs/feature-specs/*.md`

However, there are **inconsistencies** between:
1. Where agents are **instructed** to save artifacts (context prompts)
2. Where the orchestration **searches** for artifacts (lookup functions)
3. How **feature names** are normalized (hyphens, case sensitivity)

This mismatch means artifacts may exist but not be found, triggering false "missing artifact" conditions.

## Business Impact

| Impact Area | Description | Severity |
|-------------|-------------|----------|
| **Time Waste** | Full workflow stages execute without required inputs, producing unusable output | High |
| **Cost Waste** | API calls to LLM backend are consumed on doomed operations | Medium |
| **User Confusion** | Agents produce incoherent output when missing context, users don't understand why | High |
| **Debugging Difficulty** | No clear indication of what went wrong or when; failures manifest far from root cause | High |
| **Trust Erosion** | Users lose confidence in TeamBot when workflows fail mysteriously | High |

## Affected User Journeys

### Journey 1: Implementation Stage Missing Task Plan

**Scenario**: User runs objective through PLAN stage successfully, but task plan is saved to wrong location or with wrong filename.

**Current Experience:**
1. IMPLEMENTATION stage starts
2. Builder agent receives context without task plan
3. Agent either:
   - Asks "what should I implement?" (confused)
   - Invents its own plan (diverges from spec)
   - Produces partial/incorrect implementation
4. User discovers problem during review or acceptance tests
5. Significant time wasted

**Desired Experience:**
1. IMPLEMENTATION stage validates `task_plan.md` exists in expected location
2. If missing: immediate halt with error
3. Error message: "Critical artifact missing: `.teambot/my-feature/artifacts/task_plan.md`. This file should have been created during the PLAN stage. Please run the PLAN stage or manually create this file."
4. Notification sent to configured channels
5. User can fix and resume

### Journey 2: Feature Spec Lookup Failure

**Scenario**: Feature spec exists but isn't found due to naming/path mismatch.

**Current Experience:**
1. Stage needs feature spec
2. Lookup returns `None` (case mismatch, hyphen normalization issue)
3. Stage continues without spec context
4. Agent output is misaligned with requirements

**Desired Experience:**
1. Lookup includes diagnostic logging
2. If spec not found, error lists: where it searched, what patterns it tried
3. User can easily identify the mismatch

## Goals

### Goal 1: Fail-Fast on Missing Critical Artifacts
- Workflow MUST halt immediately when required artifacts are missing
- Halt MUST occur BEFORE any agent execution for that stage
- Zero tolerance for silent continuation on critical dependencies

### Goal 2: Actionable Error Messages
Error messages MUST include:
- What artifact is missing (full path)
- What stage requires it
- What stage should have created it
- How to resolve (create manually, rerun previous stage, etc.)

### Goal 3: Notification Integration
- Critical failures MUST trigger notification system
- New event type: `critical_failure` or `artifact_missing`
- Channels receive alert with same actionable details

### Goal 4: Consistent Artifact Path Resolution
- Single source of truth for artifact paths
- Diagnostic output when lookups fail
- Clear documentation of expected locations

## Success Criteria

| # | Criterion | Measurement |
|---|-----------|-------------|
| SC-1 | Missing critical artifacts halt workflow before agent execution | Unit tests demonstrate halt timing |
| SC-2 | Error messages include path, stage, and resolution guidance | Error message format validation |
| SC-3 | Notification system receives `critical_failure` events | Integration test with mock channel |
| SC-4 | Artifact path resolution is consistent across all lookup points | Code audit confirms single resolution strategy |
| SC-5 | Users report reduced confusion in failure scenarios | User feedback / issue reduction |

## Scope

### In Scope

1. **Critical artifact validation** before stage execution
2. **Actionable error message formatting** for missing artifacts
3. **Notification event** for critical failures
4. **Artifact path consistency** audit and fixes
5. **State persistence** of failure reason in `orchestration_state.json`
6. **Resume capability** after artifact is provided

### Out of Scope

1. Automatic artifact creation or recovery
2. Changes to artifact storage locations (only fixing lookup consistency)
3. Non-critical/optional artifact handling
4. Changes to agent prompt templates (beyond path references)
5. New notification channels

## Assumptions

1. The existing notification system (Telegram, etc.) is functioning and can receive new event types
2. `stages.yaml` can be extended to define required artifacts per stage
3. The current `orchestration_state.json` schema can accommodate failure reasons
4. Users prefer immediate failure with clear guidance over degraded-mode continuation

## Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Existing notification infrastructure | Available | Required for failure alerts |
| `orchestration_state.json` persistence | Available | Required for failure state storage |
| `stages.yaml` configuration | Available | May need schema extension for required artifacts |

## Key Stakeholders

| Role | Interest |
|------|----------|
| TeamBot Users | Clear feedback when things go wrong; reduced wasted time |
| TeamBot Developers | Maintainable, testable failure handling code |
| Agent Personas | Clear context with all required inputs available |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing workflows that tolerate missing artifacts | Medium | High | Introduce "strict mode" flag initially |
| Over-sensitive validation blocking legitimate workflows | Low | Medium | Clear documentation of which artifacts are critical |
| Notification spam on repeated failures | Low | Low | Deduplicate notifications for same failure |

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-25 | BA Agent | Initial problem statement |
