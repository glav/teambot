---
feature_name: sdd-prompt-renumbering
language: python
framework: ""
test_preference: hybrid
scope: medium
acceptance_scenarios:
  - name: "SDD prompt files renumbered correctly"
    steps:
      - "Verify sdd.4-determine-test-strategy.prompt.md is removed from .agent/commands/sdd/"
      - "Verify sdd.5 through sdd.8 files are renumbered to sdd.4 through sdd.7"
      - "Verify sdd.7b is renumbered to sdd.6b"
      - "Verify sdd.7c (acceptance-test) is removed — acceptance testing is code-driven via AcceptanceTestExecutor with no prompt file"
      - "Verify all files exist with new names in .agent/commands/sdd/"
    expected: "All SDD prompt files are sequentially numbered 0-7 (with 6b only, 9 files total) and the test strategy prompt is removed; no sdd.6c prompt file exists because ACCEPTANCE_TEST uses AcceptanceTestExecutor"
  - name: "Scaffold directory reflects prompt renumbering"
    steps:
      - "Verify sdd.4-determine-test-strategy.prompt.md is removed from src/teambot/scaffolds/.agent/commands/sdd/"
      - "Verify all other SDD prompt files are renumbered to match the new sequence"
      - "Run teambot init in a test directory"
      - "Verify initialized .agent/commands/sdd/ directory contains correctly numbered prompts"
    expected: "Scaffolds directory matches the new numbering and teambot init creates correctly numbered prompts"
  - name: "stages.yaml updated with new prompt paths"
    steps:
      - "Review stages.yaml prompt_template fields"
      - "Verify all prompt_template paths reference the new file names (sdd.5 → sdd.4-task-planner-for-feature, etc.)"
      - "Verify no references to sdd.4-determine-test-strategy.prompt.md exist"
      - "Run uv run pytest tests/test_config/ to verify stages.yaml is valid"
    expected: "stages.yaml references correct new prompt file paths and passes validation tests"
  - name: "Documentation updated with new numbering"
    steps:
      - "Review .agent/commands/sdd/README.md for updated workflow diagram and step numbers"
      - "Review AGENTS.md SDD table for correct file names and descriptions"
      - "Search docs/ directory for any other references to old numbering"
      - "Verify all documentation consistently references the new numbering scheme"
    expected: "All documentation reflects the new sequential numbering without the removed step 4"
  - name: "Existing references updated"
    steps:
      - "Search codebase for references to sdd.4-determine-test-strategy"
      - "Search codebase for references to old numbering (sdd.5, sdd.6, sdd.7, sdd.7b, sdd.7c, sdd.8)"
      - "Update any hardcoded references in tests or code"
      - "Run full test suite to verify no broken references"
    expected: "All code references use the new numbering and tests pass"
  - name: "Internal prompt file references updated"
    steps:
      - "Review each SDD prompt file for 'Next Step' references"
      - "Verify step numbers in cross-references match new numbering"
      - "Verify handoff messages reference correct step numbers"
      - "Check prerequisite validations reference correct file names"
    expected: "All internal references within prompt files use the new numbering scheme"
  - name: "Existing objectives continue to work"
    steps:
      - "Create a test objective file"
      - "Run teambot run with the objective using new prompt paths"
      - "Verify workflow progresses through all stages correctly"
      - "Verify stage outputs are generated successfully"
    expected: "TeamBot orchestration works correctly with renumbered prompts"
---

## Objective

**Goal**: Reorganize SDD prompt files to remove the obsolete test strategy prompt and renumber remaining prompts sequentially, updating all references across the codebase.

**Problem Statement**: The SDD workflow has evolved to integrate test strategy determination within the implementation process rather than as a separate stage. The `sdd.4-determine-test-strategy.prompt.md` file is no longer used by the file-based orchestration, but its presence and numbering causes confusion as it creates a gap in the sequence (0, 1, 2, 3, 4, 5, 6, 7, 7b, 7c, 8). This needs to be cleaned up to reflect the actual workflow and maintain sequential numbering.

**Success Criteria**:
- [ ] `sdd.4-determine-test-strategy.prompt.md` removed from both `.agent/commands/sdd/` and `src/teambot/scaffolds/.agent/commands/sdd/`
- [ ] All subsequent SDD prompts renumbered sequentially (5→4, 6→5, 7→6, 7b→6b, 8→7); `sdd.7c-acceptance-test.prompt.md` deleted (ACCEPTANCE_TEST stage is code-driven — no prompt file)
- [ ] `stages.yaml` updated with correct `prompt_template` paths for each stage
- [ ] `.agent/commands/sdd/README.md` updated with new workflow diagram and step numbers
- [ ] `AGENTS.md` updated with correct file names in the SDD table
- [ ] Scaffold files in `src/teambot/scaffolds/` match the new structure
- [ ] `teambot init` command creates correctly numbered prompt files
- [ ] All test references updated and passing
- [ ] No broken references to old numbering in documentation or code

---

## Technical Context

**Target Codebase**: `/workspaces/teambot`

**Primary Language/Framework**: Python / TeamBot CLI

**Testing Preference**: Hybrid (unit tests for file operations, acceptance tests for end-to-end validation)

**Key Constraints**:
- Must not break existing in-progress workflows (though they will continue using their original prompt paths until restarted)
- Must not break the orchestration workflow
- Must update both the repository and scaffold files consistently
- Must preserve the content and purpose of all remaining prompt files
- If issues are discovered post-merge, reverting should be straightforward since this is primarily a renaming operation with no logic changes

---

## Additional Context

### Current SDD Prompt Structure
The current SDD workflow includes these files:
- `sdd.0-initialize.prompt.md` → SETUP stage
- `sdd.1-create-feature-spec.prompt.md` → SPEC stage
- `sdd.2-review-spec.prompt.md` → SPEC_REVIEW stage
- `sdd.3-research-feature.prompt.md` → RESEARCH stage
- `sdd.4-determine-test-strategy.prompt.md` → **OBSOLETE (to be removed)**
- `sdd.5-task-planner-for-feature.prompt.md` → PLAN stage
- `sdd.6-review-plan.prompt.md` → PLAN_REVIEW stage
- `sdd.7-task-implementer-for-feature.prompt.md` → IMPLEMENTATION stage
- `sdd.7b-implementation-review.prompt.md` → IMPLEMENTATION_REVIEW stage
- `sdd.7c-acceptance-test.prompt.md` → **NOT USED** (AcceptanceTestExecutor builds its own prompt)
- `sdd.8-post-implementation-review.prompt.md` → POST_REVIEW stage

### Desired SDD Prompt Structure
After renumbering, the structure should be:
- `sdd.0-initialize.prompt.md` → SETUP stage
- `sdd.1-create-feature-spec.prompt.md` → SPEC stage
- `sdd.2-review-spec.prompt.md` → SPEC_REVIEW stage
- `sdd.3-research-feature.prompt.md` → RESEARCH stage
- `sdd.4-task-planner-for-feature.prompt.md` → PLAN stage (was sdd.5)
- `sdd.5-review-plan.prompt.md` → PLAN_REVIEW stage (was sdd.6)
- `sdd.6-task-implementer-for-feature.prompt.md` → IMPLEMENTATION stage (was sdd.7)
- `sdd.6b-implementation-review.prompt.md` → IMPLEMENTATION_REVIEW stage (was sdd.7b)
- `sdd.7-post-implementation-review.prompt.md` → POST_REVIEW stage (was sdd.8)

**Note**: There is no `sdd.6c-acceptance-test.prompt.md`. The ACCEPTANCE_TEST stage is handled entirely by `AcceptanceTestExecutor` in code, which builds its own prompt from the feature spec scenarios. The old `sdd.7c-acceptance-test.prompt.md` file is deleted (not renamed) as part of this renumbering.

### Affected Files and Locations

**Prompt files (to rename/remove)**:
- `.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` → DELETE
- `.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md` → RENAME to sdd.4-task-planner-for-feature.prompt.md
- `.agent/commands/sdd/sdd.6-review-plan.prompt.md` → RENAME to sdd.5-review-plan.prompt.md
- `.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` → RENAME to sdd.6-task-implementer-for-feature.prompt.md
- `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` → RENAME to sdd.6b-implementation-review.prompt.md
- `.agent/commands/sdd/sdd.7c-acceptance-test.prompt.md` → DELETE (ACCEPTANCE_TEST is code-driven, no prompt file needed)
- `.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` → RENAME to sdd.7-post-implementation-review.prompt.md

**Scaffold files (same changes)**:
- `src/teambot/scaffolds/.agent/commands/sdd/` → Apply identical renames/deletes

**Configuration**:
- `stages.yaml` → Update `prompt_template` fields for PLAN, PLAN_REVIEW, IMPLEMENTATION, IMPLEMENTATION_REVIEW, POST_REVIEW stages
- `src/teambot/scaffolds/stages.yaml` → Update if exists

**Documentation**:
- `.agent/commands/sdd/README.md` → Update workflow diagram (lines 12-33), step descriptions (lines 172-361), version history
- `AGENTS.md` → Update SDD command table (lines 159-172)
- `src/teambot/scaffolds/.agent/commands/sdd/README.md` → Same updates
- `src/teambot/scaffolds/AGENTS.md` → Same updates
- Any other documentation in `docs/` that references the old numbering

**Tests**:
- Search for hardcoded references to `sdd.4`, `sdd.5`, `sdd.6`, `sdd.7`, `sdd.7b`, `sdd.7c`, `sdd.8` in test files
- Update any prompt path assertions or validation tests

### Internal File References to Update

Each SDD prompt file contains internal references to other steps. These need updating:
- "Next Step" references in each prompt file
- Cross-references in prerequisite validations
- Handoff messages that mention step numbers

### Notes

- The `sdd.7c-acceptance-test.prompt.md` file exists but is **not actually used** by the orchestrator. The `ACCEPTANCE_TEST` stage uses `AcceptanceTestExecutor` which builds its own prompt from feature spec scenarios. Because acceptance testing is entirely code-driven, **this file should be deleted rather than renamed** — there is no `sdd.6c` prompt in the final structure.
- The `.agent/commands/sdd/README.md` file notes on line 7: "There is no separate TEST stage — test verification is merged into the IMPLEMENTATION_REVIEW stage." This is correct and should be preserved.
- The stages.yaml file does not reference `sdd.4-determine-test-strategy.prompt.md` in any `prompt_template` field, confirming it's truly obsolete.
- The AGENTS.md table on line 161 says "9 sequential steps" but there are actually 11 prompt files. After renumbering, there will be **9 prompt files** (0–7, plus 6b only), so the description should state '9 sequential prompt files' rather than '9 sequential steps'.
