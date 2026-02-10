# Acceptance Test Results

**Status**: ❌ FAILURES: 2/7 passed, 5 failed

## Scenarios

| ID | Name | Status | Details |
|-----|------|--------|---------|
| AT-001 | Simple Unknown Agent Command (Simple Path) | ❌ failed | RUNTIME VALIDATION FAILED: Command '@unknown-agent do something' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime) |
| AT-002 | Unknown Agent in Background Command (Advanced Path) | ❌ failed | RUNTIME VALIDATION FAILED: Command '@unknown-agent do something &' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime) |
| AT-003 | Multi-Agent Command with One Invalid ID | ✅ passed | - |
| AT-004 | Pipeline Command with Unknown Agent | ❌ failed | RUNTIME VALIDATION FAILED: Command '@fake -> @pm create a plan' failed: Pipeline stage 1 requires task content (Code tests may have passed but feature doesn't work at runtime) |
| AT-005 | Valid Alias Continues to Work | ✅ passed | - |
| AT-006 | All Six Valid Agents Work (Regression) | ❌ failed | RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: All 6 commands are accepted and dispatched to the correct agent (Code tests may have passed but feature doesn't work at runtime) |
| AT-007 | Typo Near Valid Agent ID | ❌ failed | RUNTIME VALIDATION FAILED: Command '@buidler-1 implement login' failed: Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime) |

## Summary

- **Total**: 7
- **Passed**: 2
- **Failed**: 5
- **Skipped**: 0

## Failed Scenarios

### AT-001: Simple Unknown Agent Command (Simple Path)

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@unknown-agent do something' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Error message: `Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`

### AT-002: Unknown Agent in Background Command (Advanced Path)

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@unknown-agent do something &' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Error message listing valid agents; no background task spawned

### AT-004: Pipeline Command with Unknown Agent

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@fake -> @pm create a plan' failed: Pipeline stage 1 requires task content (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Error message identifying "fake" as unknown; no pipeline stages execute

### AT-006: All Six Valid Agents Work (Regression)

**Failure Reason**: RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: All 6 commands are accepted and dispatched to the correct agent (Code tests may have passed but feature doesn't work at runtime)

**Expected**: All 6 commands are accepted and dispatched to the correct agent

### AT-007: Typo Near Valid Agent ID

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@buidler-1 implement login' failed: Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Error message: `Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`

## Validation Output (for debugging)

```


The acceptance tests already exist in `tests/test_acceptance_validation.py`. Let me run them directly:```pytest-output
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_001_router_rejects_unknown_agent_with_message PASSED [  4%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_001_no_status_entry_created PASSED [  9%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_001_no_task_dispatched PASSED [ 14%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_002_executor_rejects_unknown_background PASSED [ 19%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_002_no_status_entry_for_background_unknown PASSED [ 23%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_002_no_task_result_produced PASSED [ 28%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_003_multi_agent_rejects_when_one_invalid PASSED [ 33%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_003_no_tasks_dispatched_for_either_agent PASSED [ 38%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_003_no_status_entries_created PASSED [ 42%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_004_pipeline_unknown_agent_rejected_at_parse PASSED [ 47%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_004_error_lists_valid_agents PASSED [ 52%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_004_pm_does_not_receive_input PASSED [ 57%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_005_alias_resolves_to_canonical_id PASSED [ 61%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_005_all_aliases_valid PASSED  [ 66%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_005_alias_accepted_by_executor PASSED [ 71%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_006_all_six_agents_accepted_by_router PASSED [ 76%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_006_all_six_agents_accepted_by_executor PASSED [ 80%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_006_all_six_agents_have_status_entries PASSED [ 85%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_007_typo_rejected_by_router PASSED [ 90%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_007_typo_rejected_by_executor PASSED [ 95%]
tests/test_acceptance_validation.py::TestUnknownAgentValidationAcceptance::test_at_007_no_task_dispatched_for_typo PASSED [100%]

21 passed in 1.90s
```

```acceptance-results
AT-001: PASSED
AT-002: PASSED
AT-003: PASSED
AT-004: PASSED
AT-005: PASSED
AT-006: PASSED
AT-007: PASSED
```

## Runtime Validation Results

- ❌ AT-001-runtime: failed - Command '@unknown-agent do something' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer
- ❌ AT-002-runtime: failed - Command '@unknown-agent do something &' failed: Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer
- ❌ AT-003-runtime: skipped - No executable commands found in steps
- ❌ AT-004-runtime: failed - Command '@fake -> @pm create a plan' failed: Pipeline stage 1 requires task content
- ❌ AT-005-runtime: skipped - No executable commands found in steps
- ❌ AT-006-runtime: failed - Output did not match expected result. Expected: All 6 commands are accepted and dispatched to the correct agent
- ❌ AT-007-runtime: failed - Command '@buidler-1 implement login' failed: Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer

```
