# Fix SETUP Stage JSON Output Validation Failure

## Problem Statement

The SETUP stage fails with "Output does not contain valid JSON" because:
- `stages.yaml` defines an `output_schema` requiring JSON with fields: `stage`, `status`, `environment_ready`, `blockers`
- The prompt template `.agent/commands/sdd/sdd.0-initialize.prompt.md` instructs the agent to return markdown reports
- This mismatch causes validation failure and prevents the workflow from starting

## Root Cause

Configuration mismatch between two files:
1. **stages.yaml** (lines 174-181): Expects structured JSON output
2. **sdd.0-initialize.prompt.md**: Instructs agent to produce markdown tables and reports

## Proposed Solution

**Option A (Recommended)**: Update the prompt template to return JSON
- Modify `.agent/commands/sdd/sdd.0-initialize.prompt.md` to instruct the agent to return structured JSON matching the schema
- Keep the schema validation for structured data
- **Hybrid Approach**: Return both markdown (for readability in logs) AND a JSON code block for validation
  - Markdown report for human-readable logs
  - JSON in code fence at end for schema validation
  - Example format:
    ```
    ## Setup Complete
    [markdown report here]
    
    ```json
    {"stage": "SETUP", "status": "complete", ...}
    ```
    ```
  - This provides best of both worlds - debuggable logs + structured validation
- **JSON Placement**: Add JSON requirements as a dedicated "Output Format" section at the end of the prompt template, after all task instructions
- **Format Specification**: JSON must be in a code fence and include all required fields from output_schema

**Option B**: Remove output_schema from SETUP stage
- Remove the `output_schema` section from SETUP stage in `stages.yaml`
- Allow the agent to continue returning markdown reports
- Less structured but simpler fix

## Work Plan

### Investigation Phase
- [x] Review SETUP stage configuration in stages.yaml
- [x] Examine output_schema requirements (JSON with stage, status, environment_ready, blockers)
- [x] Review prompt template sdd.0-initialize.prompt.md
- [x] Confirm mismatch between expected (JSON) and actual (markdown) output

### Implementation Phase (Option A - Recommended)
- [ ] Update sdd.0-initialize.prompt.md to include JSON output instructions
  - Add section explaining required JSON output format
  - Provide example JSON structure
  - Instruct agent to return JSON after markdown report (for debugging) or instead of markdown
- [ ] Test the fix by running an objective through SETUP stage
- [ ] Verify JSON validation passes
- [ ] Verify workflow continues to next stage

### Implementation Phase (Option B - Alternative)
- [ ] Remove or comment out `output_schema` section in stages.yaml SETUP stage (lines 174-181)
- [ ] Test the fix by running an objective
- [ ] Verify stage completes without validation error

### Validation Phase
- [ ] Run the original failing objective: `docs/objectives/remove-history-command.md`
- [ ] Confirm SETUP stage completes successfully
- [ ] Verify subsequent stages can execute
- [ ] Check that other stages with output_schema still work correctly
- [ ] **Test fresh objective**: Run a completely new objective (not just the failing one) to ensure no side effects
- [ ] **Verify JSON persistence**: Check that `.teambot/stage_outputs/SETUP.json` is correctly created and contains valid JSON
- [ ] **Test downstream dependencies**: If other stages consume SETUP output, verify they can parse the new format
- [ ] **Version compatibility check**: Test with existing `.teambot/` directories that have old markdown outputs - verify replay/status commands still work

## Notes & Considerations

- **Other stages affected**: All 10 stages in stages.yaml have `output_schema` defined - they may have the same issue
- **Consistency**: If we fix SETUP, we should audit all other prompt templates for similar mismatches
- **Schema benefits**: Keeping schemas provides structured data for automation and validation
- **Backward compatibility**: Changes to prompt templates affect all objectives using SDD workflow
- **Schema Evolution**: Consider version compatibility - existing `.teambot/` directories with old markdown outputs may not be compatible with new validation. The system should handle gracefully or provide migration path.

## Future Work

After completing this fix, the following broader improvements should be addressed:

- [ ] **Systematic Audit**: Review all 10 remaining SDD prompt templates (sdd.1-*.prompt.md through sdd.8-*.prompt.md) for output_schema alignment
- [ ] **Create Tracking Issue**: Document findings from audit and create issues for any mismatches
- [ ] **Establish Convention**: Document standard pattern for hybrid output (markdown + JSON) in prompt writing guidelines
- [ ] **Version Migration**: If needed, create utility to migrate old markdown outputs to JSON format
- [ ] **Schema Documentation**: Add comments in stages.yaml linking each output_schema to its corresponding prompt template for easier maintenance

## Files to Modify

### Option A (Recommended):
- `.agent/commands/sdd/sdd.0-initialize.prompt.md` - Add JSON output instructions

### Option B (Alternative):
- `stages.yaml` - Remove output_schema from SETUP stage

## Delegation

This task requires code/configuration changes:
- **File editing**: Delegate to `@builder-1` or `@builder-2`
- **Testing**: Builder can test after making changes
- **Review**: I can review the plan execution and results

## Success Criteria

- [ ] SETUP stage completes without "Output does not contain valid JSON" error
- [ ] Agent returns data matching the output_schema
- [ ] Original failing objective runs past SETUP stage
- [ ] No regression in other stages with output_schema
