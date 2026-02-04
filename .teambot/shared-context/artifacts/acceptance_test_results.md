# Acceptance Test Results

**Status**: ❌ FAILURES: 1/8 passed, 7 failed

## Scenarios

| ID | Name | Status | Details |
|-----|------|--------|---------|
| AT-001 | Simple Reference After Completion | ✅ passed | - |
| AT-002 | Reference Triggers Wait | ❌ failed | RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: Builder-1 shows status `waiting for @pm`; once PM completes, Builder-1 executes (Code tests may have passed but feature doesn't work at runtime) |
| AT-003 | Multiple References | ❌ failed | RUNTIME VALIDATION FAILED: Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba (Code tests may have passed but feature doesn't work at runtime) |
| AT-004 | Invalid Agent Reference | ❌ failed | RUNTIME VALIDATION FAILED: Referenced agent $nonexistent output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime) |
| AT-005 | Reference Agent With No Output | ❌ failed | RUNTIME VALIDATION FAILED: Referenced agent $pm output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime) |
| AT-006 | Circular Dependency Detection | ❌ failed | RUNTIME VALIDATION FAILED: Referenced agent $builder-1 output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime) |
| AT-007 | Combined Pipeline and Reference | ❌ failed | RUNTIME VALIDATION FAILED: Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba (Code tests may have passed but feature doesn't work at runtime) |
| AT-008 | Escape Sequence | ❌ failed | RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: PM receives literal `$pm` in prompt, not treated as reference (Code tests may have passed but feature doesn't work at runtime) |

## Summary

- **Total**: 8
- **Passed**: 1
- **Failed**: 7
- **Skipped**: 0

## Failed Scenarios

### AT-002: Reference Triggers Wait

**Failure Reason**: RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: Builder-1 shows status `waiting for @pm`; once PM completes, Builder-1 executes (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Builder-1 shows status `waiting for @pm`; once PM completes, Builder-1 executes

### AT-003: Multiple References

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Builder-1 receives both PM and BA outputs in context

### AT-004: Invalid Agent Reference

**Failure Reason**: RUNTIME VALIDATION FAILED: Referenced agent $nonexistent output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Clear error message displayed

### AT-005: Reference Agent With No Output

**Failure Reason**: RUNTIME VALIDATION FAILED: Referenced agent $pm output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime)

**Expected**: System waits for PM or displays helpful message

### AT-006: Circular Dependency Detection

**Failure Reason**: RUNTIME VALIDATION FAILED: Referenced agent $builder-1 output not available. The feature may not be wired up correctly. (Code tests may have passed but feature doesn't work at runtime)

**Expected**: Circular dependency error displayed

### AT-007: Combined Pipeline and Reference

**Failure Reason**: RUNTIME VALIDATION FAILED: Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba (Code tests may have passed but feature doesn't work at runtime)

**Expected**: PM receives BA's output, then Builder-1 receives PM's output via pipeline

### AT-008: Escape Sequence

**Failure Reason**: RUNTIME VALIDATION FAILED: Output did not match expected result. Expected: PM receives literal `$pm` in prompt, not treated as reference (Code tests may have passed but feature doesn't work at runtime)

**Expected**: PM receives literal `$pm` in prompt, not treated as reference

## Validation Output (for debugging)

```
```pytest-output
================================================= test session starts ==================================================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0 -- /workspaces/teambot/.venv/bin/python
cachedir: .pytest_cache
rootdir: /workspaces/teambot
configfile: pyproject.toml
plugins: asyncio-1.3.0, cov-7.0.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 15 items                                                                                                     

tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_001_simple_reference_after_completion PASSED [  6%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_002_reference_triggers_wait PASSED         [ 13%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_003_multiple_references PASSED             [ 20%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_004_invalid_agent_reference_error PASSED   [ 26%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_005_reference_agent_with_no_output PASSED  [ 33%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_006_circular_dependency_behavior PASSED    [ 40%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_007_combined_pipeline_and_reference PASSED [ 46%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_008_escape_sequence_parsing PASSED         [ 53%]
tests/test_acceptance_validation.py::TestAcceptanceScenarios::test_at_008_dollar_non_alpha_not_reference PASSED  [ 60%]
tests/test_acceptance_validation.py::TestReferencePatternValidation::test_pattern_matches_simple_agent PASSED    [ 66%]
tests/test_acceptance_validation.py::TestReferencePatternValidation::test_pattern_matches_hyphenated_agent PASSED [ 73%]
tests/test_acceptance_validation.py::TestReferencePatternValidation::test_pattern_ignores_dollar_numbers PASSED  [ 80%]
tests/test_acceptance_validation.py::TestReferencePatternValidation::test_pattern_multiple_refs PASSED           [ 86%]
tests/test_acceptance_validation.py::TestExecutorReferenceIntegration::test_reference_injection_format PASSED    [ 93%]
tests/test_acceptance_validation.py::TestExecutorReferenceIntegration::test_multiple_tasks_same_agent_uses_latest PASSED [100%]

================================================== 15 passed in 0.62s ==================================================
```

```acceptance-results
AT-001: PASSED
AT-002: PASSED
AT-003: PASSED
AT-004: PASSED
AT-005: PASSED
AT-006: PASSED
AT-007: PASSED
AT-008: PASSED
```

## Runtime Validation Results

- ✅ AT-001-runtime: passed
- ❌ AT-002-runtime: failed - Output did not match expected result. Expected: Builder-1 shows status `waiting for @pm`; once PM completes, Builder-1 executes
- ❌ AT-003-runtime: failed - Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba
- ❌ AT-004-runtime: failed - Referenced agent $nonexistent output not available. The feature may not be wired up correctly.
- ❌ AT-005-runtime: failed - Referenced agent $pm output not available. The feature may not be wired up correctly.
- ❌ AT-006-runtime: failed - Referenced agent $builder-1 output not available. The feature may not be wired up correctly.
- ❌ AT-007-runtime: failed - Command '@ba Write requirements' failed: JSON-RPC Error -32603: Request session.send failed with message: Session not found: teambot-ba
- ❌ AT-008-runtime: failed - Output did not match expected result. Expected: PM receives literal `$pm` in prompt, not treated as reference

```
