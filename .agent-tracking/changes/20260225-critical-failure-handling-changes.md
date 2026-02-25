<!-- markdownlint-disable-file -->
# Release Changes: File-Based Orchestration Critical Failure Handling

**Related Plan**: 20260225-critical-failure-handling-plan.instructions.md
**Implementation Date**: 2026-02-25

## Summary

Implement robust critical failure handling in TeamBot's file-based orchestration to immediately halt workflow on missing artifacts with clear, actionable error messages.

## Changes

### Added

* `tests/test_orchestration/test_artifact_validator.py` - TDD tests for MissingArtifactError (8 tests), ArtifactValidator (8 tests), and ArtifactPathResolution (7 tests)
* `src/teambot/orchestration/exceptions.py` - New exception module with MissingArtifactError class
* `src/teambot/orchestration/artifact_validator.py` - New ArtifactValidator class with multi-location path resolution
* `tests/test_orchestration/test_execution_loop.py::TestExecutionLoopArtifactValidation` - 6 integration tests for artifact validation in ExecutionLoop
* `tests/test_notifications/test_templates.py` - 3 new tests for critical_failure notification template

### Modified

* `src/teambot/orchestration/__init__.py` - Export MissingArtifactError and ArtifactValidator
* `src/teambot/orchestration/execution_loop.py` - Add CRITICAL_FAILURE to ExecutionResult, add artifact validation to _execute_work_stage and _execute_review_stage, add _validate_required_artifacts method
* `src/teambot/orchestration/stage_config.py` - Default config now has empty artifacts list (validation only for explicit config)
* `src/teambot/notifications/templates.py` - Add critical_failure message template with recovery steps formatting
* `tests/test_orchestration/conftest.py` - Add autouse fixture to clear artifact requirements during tests

### Removed

None

## Release Summary

**Total Files Affected**: 8

### Files Created (3)

* `src/teambot/orchestration/exceptions.py` - MissingArtifactError exception for critical failures
* `src/teambot/orchestration/artifact_validator.py` - ArtifactValidator for pre-stage validation
* `tests/test_orchestration/test_artifact_validator.py` - 23 unit tests for artifact validation

### Files Modified (5)

* `src/teambot/orchestration/__init__.py` - Added exports
* `src/teambot/orchestration/execution_loop.py` - Integrated artifact validation
* `src/teambot/orchestration/stage_config.py` - Default config changes
* `src/teambot/notifications/templates.py` - Added critical_failure template
* `tests/test_orchestration/conftest.py` - Test fixture updates

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. The feature is backward-compatible:
- Default configuration has empty artifact lists, so no validation occurs unless explicitly configured
- The `stages.yaml` file has artifact requirements that will be validated
- Tests continue to pass with the new validation infrastructure
