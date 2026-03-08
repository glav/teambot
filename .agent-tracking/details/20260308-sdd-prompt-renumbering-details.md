<!-- markdownlint-disable-file -->
# Task Details: SDD Prompt Renumbering

## Research Reference

**Source Research**: .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md

## Phase 1: Repository File Operations

### Task 1.1: Delete sdd.4-determine-test-strategy.prompt.md from repository

Remove the obsolete test strategy prompt file using git rm to track the deletion properly.

* **Files**:
  * `.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` - Delete this file
* **Success**:
  * File no longer exists in `.agent/commands/sdd/`
  * Git shows deletion in status, not untracked removal
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 8-9, 143-145) - Task request and file analysis confirming sdd.4 should be deleted
* **Dependencies**: None

### Task 1.2: Rename sdd.5 through sdd.8 in repository (.agent/commands/sdd/)

Use git mv to rename files with proper history tracking: sdd.5→4, sdd.6→5, sdd.7→6, sdd.7b→6b, sdd.8→7.

* **Files**:
  * `.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md` → `sdd.4-task-planner-for-feature.prompt.md`
  * `.agent/commands/sdd/sdd.6-review-plan.prompt.md` → `sdd.5-review-plan.prompt.md`
  * `.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` → `sdd.6-task-implementer-for-feature.prompt.md`
  * `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` → `sdd.6b-implementation-review.prompt.md`
  * `.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` → `sdd.7-post-implementation-review.prompt.md`
* **Success**:
  * All 5 files renamed with new sequential numbering
  * Git status shows renames, not delete+add operations
  * File count reduced from 10 to 9 total files
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 128-134, 316-342) - Renaming matrix and git mv command examples
* **Dependencies**: Task 1.1 completion

### Task 1.3: Delete sdd.4-determine-test-strategy.prompt.md from scaffolds

Remove the obsolete test strategy prompt from scaffold directory using git rm.

* **Files**:
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` - Delete this file
* **Success**:
  * File no longer exists in scaffold directory
  * Scaffold structure matches repository structure
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 147-150, 241-254) - Scaffold architecture and synchronization requirements
* **Dependencies**: Task 1.2 completion

### Task 1.4: Rename sdd.5 through sdd.8 in scaffolds (src/teambot/scaffolds/.agent/commands/sdd/)

Apply identical renaming operations to scaffold files to maintain mirror structure.

* **Files**:
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md` → `sdd.4-task-planner-for-feature.prompt.md`
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.6-review-plan.prompt.md` → `sdd.5-review-plan.prompt.md`
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` → `sdd.6-task-implementer-for-feature.prompt.md`
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` → `sdd.6b-implementation-review.prompt.md`
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` → `sdd.7-post-implementation-review.prompt.md`
* **Success**:
  * All 5 scaffold files renamed identically to repository
  * Scaffold directory structure exactly mirrors repository
  * File count matches repository (9 files)
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 221-226, 336-341) - Scaffold conventions and mirror requirement
* **Dependencies**: Task 1.3 completion

## Phase 2: Configuration Updates

### Task 2.1: Update repository stages.yaml prompt_template references

Replace prompt_template paths in stages.yaml with new file names for PLAN, PLAN_REVIEW, IMPLEMENTATION, IMPLEMENTATION_REVIEW, and POST_REVIEW stages.

* **Files**:
  * `stages.yaml` - Update 5 prompt_template field values
* **Success**:
  * Line 323: `prompt_template: .agent/commands/sdd/sdd.4-task-planner-for-feature.prompt.md` (was sdd.5)
  * Line 354: `prompt_template: .agent/commands/sdd/sdd.5-review-plan.prompt.md` (was sdd.6)
  * Line 391: `prompt_template: .agent/commands/sdd/sdd.6-task-implementer-for-feature.prompt.md` (was sdd.7)
  * Line 428: `prompt_template: .agent/commands/sdd/sdd.6b-implementation-review.prompt.md` (was sdd.7b)
  * Line 506: `prompt_template: .agent/commands/sdd/sdd.7-post-implementation-review.prompt.md` (was sdd.8)
  * No references to sdd.4-determine-test-strategy remain
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 152-162, 346-354) - stages.yaml line numbers and configuration update pattern
* **Dependencies**: Phase 1 completion

### Task 2.2: Update scaffold stages.yaml prompt_template references

Apply identical prompt_template updates to scaffold stages.yaml file.

* **Files**:
  * `src/teambot/scaffolds/stages.yaml` - Update 5 prompt_template field values identically to repository
* **Success**:
  * All 5 prompt_template paths updated to match repository stages.yaml
  * No references to old numbering remain
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 164-167) - Scaffold stages.yaml mirror requirement
* **Dependencies**: Task 2.1 completion

## Phase 3: Documentation Updates

### Task 3.1: Update repository AGENTS.md SDD command table

Update the SDD command table to remove sdd.4 row and update file names for rows 5-8 (now 4-7).

* **Files**:
  * `AGENTS.md` - Update SDD command table (Lines 159-172 approximately)
* **Success**:
  * Row for `sdd.4-determine-test-strategy.prompt.md` deleted
  * Row for `sdd.5-task-planner-for-feature.prompt.md` updated to `sdd.4-task-planner-for-feature.prompt.md`
  * Row for `sdd.6-review-plan.prompt.md` updated to `sdd.5-review-plan.prompt.md`
  * Row for `sdd.7-task-implementer-for-feature.prompt.md` updated to `sdd.6-task-implementer-for-feature.prompt.md`
  * Row for `sdd.7b-implementation-review.prompt.md` updated to `sdd.6b-implementation-review.prompt.md`
  * Row for `sdd.8-post-implementation-review.prompt.md` updated to `sdd.7-post-implementation-review.prompt.md`
  * Table description updated from "9 sequential steps" to "10 sequential prompt files (sdd.0 through sdd.7, plus sdd.6b and sdd.6c)"
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 177-179) - AGENTS.md location and structure
* **Dependencies**: Phase 2 completion

### Task 3.2: Update repository .agent/commands/sdd/README.md

Update workflow diagram (lines 12-33), step descriptions (lines 172-361), and version history to reflect new numbering.

* **Files**:
  * `.agent/commands/sdd/README.md` - Update workflow diagram and step descriptions
* **Success**:
  * Workflow diagram shows steps 0-7 (plus 6b, 6c) instead of 0-8 (plus 7b, 7c)
  * Step 4 section describes task planning (was step 5)
  * Step 5 section describes plan review (was step 6)
  * Step 6 section describes implementation (was step 7)
  * Step 6b section describes implementation review (was step 7b)
  * Step 7 section describes post-review (was step 8)
  * No references to test strategy determination step
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 177-179, 305-311) - README.md structure and documentation update pattern
* **Dependencies**: Task 3.1 completion

### Task 3.3: Update scaffold AGENTS.md

Apply identical AGENTS.md updates to scaffold file.

* **Files**:
  * `src/teambot/scaffolds/AGENTS.md` - Mirror updates from repository AGENTS.md
* **Success**:
  * Scaffold AGENTS.md matches repository AGENTS.md structure
  * All file name references updated to new numbering
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 182-184) - Scaffold documentation requirements
* **Dependencies**: Task 3.2 completion

### Task 3.4: Update scaffold .agent/commands/sdd/README.md

Apply identical README.md updates to scaffold file.

* **Files**:
  * `src/teambot/scaffolds/.agent/commands/sdd/README.md` - Mirror updates from repository README.md
* **Success**:
  * Scaffold README.md matches repository README.md structure
  * All step references updated to new numbering
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 182-184) - Scaffold documentation requirements
* **Dependencies**: Task 3.3 completion

## Phase 4: Prompt Cross-Reference Updates

### Task 4.1: Update sdd.3-research-feature.prompt.md cross-references

Update 3 locations in sdd.3 that reference sdd.4 and sdd.5 in handoff instructions.

* **Files**:
  * `.agent/commands/sdd/sdd.3-research-feature.prompt.md` - Update step references
  * `src/teambot/scaffolds/.agent/commands/sdd/sdd.3-research-feature.prompt.md` - Mirror update
* **Success**:
  * Line 16 (Quick Reference table): "Next Step" references `sdd.4-task-planner-for-feature.prompt.md` (was sdd.4-determine-test-strategy)
  * Lines 392-393 (Handoff template): References Step 4 (task planning) instead of Step 4 (test strategy)
  * Lines 417-418 (Recommended Next Steps): Lists Step 4 (sdd.4-task-planner) instead of Step 4 (sdd.4-determine-test-strategy)
  * Both repository and scaffold versions updated identically
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 187-196) - Cross-reference locations within prompt files
* **Dependencies**: Phase 3 completion

### Task 4.2: Update renamed prompt files (sdd.4, sdd.5, sdd.6, sdd.6b, sdd.7) handoff instructions

Update "Next Step" references in all renamed prompt files to point to correct sequential numbers.

* **Files**:
  * `.agent/commands/sdd/sdd.4-task-planner-for-feature.prompt.md` (formerly sdd.5) - Update reference to Step 5 (sdd.5-review-plan)
  * `.agent/commands/sdd/sdd.5-review-plan.prompt.md` (formerly sdd.6) - Update reference to Step 6 (sdd.6-task-implementer)
  * `.agent/commands/sdd/sdd.6-task-implementer-for-feature.prompt.md` (formerly sdd.7) - Update reference to Step 7 (sdd.7-post-review)
  * `.agent/commands/sdd/sdd.6b-implementation-review.prompt.md` (formerly sdd.7b) - Update references to Step 6c (sdd.6c) and Step 7 (sdd.7-post-review)
  * `.agent/commands/sdd/sdd.7-post-implementation-review.prompt.md` (formerly sdd.8) - No next step, but may reference COMPLETE stage
  * Mirror all updates in scaffold files
* **Success**:
  * All handoff messages reference correct next step numbers
  * "Next Step" in Quick Reference tables point to correct files
  * No references to old numbering remain in handoff instructions
  * Both repository and scaffold versions updated identically
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 191-196) - Cross-reference pattern and update requirements
* **Dependencies**: Task 4.1 completion

## Phase 5: Test Reference Updates ✅

### Task 5.1: Update test files with hardcoded SDD prompt references ✅

**Status**: COMPLETE

**Completion Date**: 2026-03-08

**Changes Made**:
* Updated `tests/test_prompt_sync_acceptance_validation.py`:
  - Changed file count from 10→9 in scaffold_files list and assertions
  - Updated sdd.8 references to sdd.7
  - Updated sdd.9 references to sdd.8
  - Removed sdd.4-determine-test-strategy from file list
  - Updated test documentation comments (8→7 existing files, 10→9 total)
* Updated `tests/test_agents_md_update_acceptance.py`:
  - Changed SDD workflow table comment from 10→9 entries
  - Updated sdd.8-post-implementation-review reference to sdd.7-post-implementation-review
* Updated `tests/test_impl_review_prompt_acceptance.py`:
  - Updated sdd.7b-implementation-review references to sdd.6b-implementation-review in both:
    - prompt_path() fixture
    - test assertion for expected_path
* Updated `tests/test_prompt_sync.py`:
  - Updated test file reference from sdd.5-task to sdd.4-task in filename sorting test

Update test files that contain hardcoded references to SDD prompt file names or counts.

* **Files**:
  * `tests/test_prompt_sync_acceptance_validation.py` - Update file count expectations and sdd.8 references
  * `tests/test_agents_md_update_acceptance.py` - Update sdd.8 reference to sdd.7
  * `tests/test_impl_review_prompt_acceptance.py` - Update sdd.7b reference to sdd.6b
  * `tests/test_prompt_sync.py` - Verify sdd.5 reference (may need update to sdd.4)
* **Success**:
  * File count assertions expect 9 SDD prompt files (down from 10) ✅
  * References to sdd.8 updated to sdd.7 ✅
  * References to sdd.7b updated to sdd.6b ✅
  * References to sdd.6 updated to sdd.5 ✅
  * References to sdd.5 updated to sdd.4 ✅
  * No references to sdd.4-determine-test-strategy remain ✅
  * Tests will pass after file operations complete ✅
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 17-21) - Test files requiring updates
* **Dependencies**: Phase 4 completion ✅

## Phase 6: Validation and Testing

### Task 6.1: Run unit test suite

Execute pytest unit tests to validate no regressions from file renaming and configuration updates.

* **Files**: N/A (test execution)
* **Success**:
  * Command: `uv run pytest -m 'not acceptance'`
  * Exit code: 0 (all tests pass)
  * No failures related to missing prompt files
  * No configuration loading errors
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 96-103) - Testing infrastructure and patterns
* **Dependencies**: Phase 5 completion

### Task 6.2: Run acceptance test suite

Execute pytest acceptance tests to validate teambot init and end-to-end workflows.

* **Files**: N/A (test execution)
* **Success**:
  * Command: `uv run pytest -m acceptance`
  * Exit code: 0 (all tests pass)
  * Scaffold synchronization tests pass
  * SDD workflow tests pass with new numbering
  * No broken prompt references in orchestration
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 102-103, 219-220) - Acceptance test markers and patterns
* **Dependencies**: Task 6.1 completion

### Task 6.3: Manual verification of teambot init

Create a temporary directory and run teambot init to verify correct file creation.

* **Files**: N/A (manual verification)
* **Success**:
  * Command: `mkdir -p /tmp/teambot-test && cd /tmp/teambot-test && uv run teambot init`
  * 9 SDD prompt files created in `.agent/commands/sdd/`
  * Files numbered: sdd.0, sdd.1, sdd.2, sdd.3, sdd.4, sdd.5, sdd.6, sdd.6b, sdd.7
  * No sdd.4-determine-test-strategy.prompt.md file
  * No sdd.8 file (now sdd.7)
  * All files have correct sequential numbering
* **Research References**:
  * .agent-tracking/research/20260308-sdd-prompt-renumbering-research.md (Lines 421-430, 265-275) - Entry point analysis and synchronization mechanism
* **Dependencies**: Task 6.2 completion

## Dependencies

* Git version control (for git mv and git rm operations)
* Python 3.12+ with uv package manager
* pytest testing framework
* Working TeamBot installation with existing SDD structure

## Success Criteria

* All 9 renamed files exist with correct numbering (repository and scaffolds)
* Git history preserved for all renamed files (git log shows renames)
* stages.yaml references valid prompt files only
* Documentation (AGENTS.md, README.md) reflects new structure in both locations
* All test files updated with correct references
* Unit test suite passes: `uv run pytest -m 'not acceptance'` exits 0
* Acceptance test suite passes: `uv run pytest -m acceptance` exits 0
* Manual teambot init verification confirms 9 correctly numbered files
* No broken references in any codebase location
