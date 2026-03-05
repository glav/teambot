# SDD Prompt Schema Compliance Fix - Implementation Summary

**Date**: 2026-03-05  
**Implemented By**: @builder-1  
**Reviewed By**: @reviewer  
**Status**: ✅ APPROVED

---

## Problem Statement

8 out of 9 SDD prompt templates were missing JSON output format instructions, causing ExecutionLoop schema validation failures. The SPEC stage was failing because agents didn't know they needed to return structured JSON output.

### Root Cause
- `stages.yaml` defined `output_schema` for all stages
- Only `sdd.0-initialize.prompt.md` (SETUP) had JSON output instructions
- Other prompts had no guidance on producing JSON output

---

## Solution Implemented

Added comprehensive **JSON Output Format** sections to all 8 affected SDD prompt templates.

### Files Modified (in both locations)

#### Primary Location: `.agent/commands/sdd/`
1. `sdd.1-create-feature-spec.prompt.md` (SPEC stage)
2. `sdd.2-review-spec.prompt.md` (SPEC_REVIEW stage)
3. `sdd.3-research-feature.prompt.md` (RESEARCH stage)
4. `sdd.5-task-planner-for-feature.prompt.md` (PLAN stage)
5. `sdd.6-review-plan.prompt.md` (PLAN_REVIEW stage)
6. `sdd.7-task-implementer-for-feature.prompt.md` (IMPLEMENTATION stage)
7. `sdd.7b-implementation-review.prompt.md` (IMPLEMENTATION_REVIEW stage)
8. `sdd.8-post-implementation-review.prompt.md` (POST_REVIEW stage)

#### Scaffold Location: `src/teambot/scaffolds/.agent/commands/sdd/`
All 8 files copied to scaffold directory (verified identical with `diff`)

---

## Output Format Section Structure

Each prompt now includes a comprehensive **## Output Format** section at the end with:

### 1. Critical Notice
```markdown
**CRITICAL**: Your response MUST include both human-readable markdown (for logs) 
AND structured JSON (for validation).
```

### 2. Required JSON Output
- Example JSON matching the `output_schema` in stages.yaml
- Demonstrates correct structure and field names
- Shows proper placement instruction

### 3. JSON Field Requirements Table
| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| ... | ... | ... | ... | ... |

### 4. Output Structure Example
Shows complete pattern with markdown report + JSON code block

### 5. Status/Decision Field Logic
- When to use each enum value (COMPLETE/INCOMPLETE, APPROVED/NEEDS_REVISION/BLOCKED)
- How to populate the `blockers` array
- Clear decision criteria

### 6. Example: Failure/Revision Case
Demonstrates proper JSON structure for non-success scenarios

---

## Schema Alignment Verification

All JSON examples match the `output_schema` definitions in `stages.yaml` (lines 202-492):

| Stage | Key Fields | Verified |
|-------|-----------|----------|
| **SPEC** | stage, status, artifacts_produced, blockers | ✅ |
| **SPEC_REVIEW** | stage, decision, scores{4}, blockers, artifacts_produced | ✅ |
| **RESEARCH** | stage, status, artifacts_produced, key_findings, blockers | ✅ |
| **PLAN** | stage, status, total_phases, total_tasks, artifacts_produced, blockers | ✅ |
| **PLAN_REVIEW** | stage, decision, scores{4}, blockers, artifacts_produced | ✅ |
| **IMPLEMENTATION** | stage, status, tasks_completed, tasks_total, files_created, files_modified, tests_written, tests_passing, blockers | ✅ |
| **IMPLEMENTATION_REVIEW** | stage, decision, tasks_complete, tests_passing, coverage_met, linting_passed, blockers, artifacts_produced | ✅ |
| **POST_REVIEW** | stage, decision, all_tests_passing, acceptance_tests_passing, coverage_targets_met, ready_for_merge, blockers, artifacts_produced | ✅ |

### Score Dimensions Verified

**SPEC_REVIEW** scores object contains:
- `completeness` (0-10)
- `clarity` (0-10)
- `testability` (0-10)
- `technical_readiness` (0-10)

**PLAN_REVIEW** scores object contains:
- `completeness` (0-10)
- `actionability` (0-10)
- `test_integration` (0-10)
- `implementation_readiness` (0-10)

---

## Validation Results

### JSON Syntax Validation
```bash
✅ All 8 prompt JSON examples are syntactically valid
✅ All required fields present per schemas
✅ Stage const values match stages.yaml
```

### File Synchronization
```bash
✅ Files identical in both locations (primary + scaffold)
✅ Verified with `diff` (exit code 0 for all 8 files)
```

### Code Quality
```bash
✅ Linting passed: `uv run ruff check . --fix`
✅ Formatting passed: `uv run ruff format --check .`
```

---

## Reference Implementation

The working reference implementation (`sdd.0-initialize.prompt.md`) was used as the template for:
- Overall structure and section ordering
- Writing style and tone
- Table formatting
- Example patterns

---

## Testing Performed

### Automated Validation Script
Created Python script to validate:
1. JSON examples are syntactically valid
2. Required fields from `stages.yaml` are present
3. `stage` const values match expected values

**Result**: 8/8 stages passed all checks ✅

### Manual Verification
- Reviewed each prompt file visually
- Checked JSON field names against schemas
- Verified enum values match stages.yaml
- Confirmed placement at end of files

---

## Future Maintenance Guidelines

### When Modifying Schemas in `stages.yaml`

**⚠️ CRITICAL**: If you modify an `output_schema` in `stages.yaml`, you MUST:

1. **Update the prompt template** in `.agent/commands/sdd/sdd.X-*.prompt.md`
   - Modify the JSON example in "Required JSON Output"
   - Update the field requirements table
   - Adjust the failure example if needed

2. **Copy to scaffold location**: 
   ```bash
   cp .agent/commands/sdd/sdd.X-*.prompt.md \
      src/teambot/scaffolds/.agent/commands/sdd/
   ```

3. **Validate the changes**:
   ```bash
   # Verify JSON syntax
   python3 -c "import json; json.loads(open('.agent/commands/sdd/sdd.X-*.prompt.md').read().split('```json')[1].split('```')[0])"
   
   # Verify files match
   diff .agent/commands/sdd/sdd.X-*.prompt.md \
        src/teambot/scaffolds/.agent/commands/sdd/sdd.X-*.prompt.md
   ```

### Schema Evolution Strategy

Consider implementing a CI check that:
- Parses `stages.yaml` to extract `output_schema` definitions
- Parses prompt templates to extract JSON examples
- Validates that required fields match
- Fails build if schemas drift

---

## Review Outcome

**Reviewer**: @reviewer  
**Decision**: ✅ APPROVED  
**Confidence Level**: High  
**Risk Level**: Low

### Reviewer Comments
> "The implementation is thorough, consistent, and well-validated. All JSON examples are syntactically valid, and the schemas precisely match the definitions in stages.yaml. This is ready for merge."

### Minor Suggestions Implemented
1. ✅ **Documentation**: Preserved implementation summary in `.agent-tracking/`
2. 🔄 **Testing**: Consider integration tests for LLM output validation (future work)
3. 📝 **Process**: Added schema evolution guidelines above

---

## Impact

### Before
- ❌ SPEC stage failed with `OutputSchemaValidationError`
- ❌ Agents produced markdown-only output
- ❌ ExecutionLoop rejected stage outputs

### After
- ✅ Agents receive clear JSON output instructions
- ✅ Required fields and formats documented
- ✅ Examples show both success and failure cases
- ✅ Schema validation should pass

---

## Next Steps

1. ✅ **Changes merged**
2. 🧪 **Test with real workflow**: Run a complete SDD workflow to verify all stages produce valid JSON
3. 📊 **Monitor logs**: Check ExecutionLoop for any schema validation errors
4. 🔄 **Iterate if needed**: If issues persist, consider enhancing system prompts

---

## Related Files

- **Schemas**: `stages.yaml` (lines 202-492)
- **Reference**: `.agent/commands/sdd/sdd.0-initialize.prompt.md`
- **Validation**: `src/teambot/orchestration/execution_loop.py` (schema validation logic)
- **Error Handling**: `src/teambot/orchestration/exceptions.py` (`OutputSchemaValidationError`)

---

## Lessons Learned

1. **Prompt-Schema Alignment**: When defining output schemas, ensure prompts explicitly instruct agents on format
2. **Dual Locations**: TeamBot maintains prompts in both primary and scaffold locations - both must be updated
3. **Comprehensive Examples**: Agents benefit from seeing both success and failure examples
4. **Field Documentation**: Tables with valid values help agents produce correct output

---

**Implementation Complete**: 2026-03-05 22:51 UTC  
**Status**: ✅ Production Ready
