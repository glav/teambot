<!-- markdownlint-disable-file -->
# Release Changes: SDD Prompt Renumbering

**Related Plan**: 20260308-sdd-prompt-renumbering-plan.instructions.md
**Implementation Date**: 2026-03-08

## Summary

Reorganization of SDD prompt files to remove obsolete test strategy prompt (sdd.4) and renumber all subsequent prompts sequentially, updating all configuration and documentation references across the repository.

## Changes

### Added

### Modified

* `.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md` → `sdd.4-task-planner-for-feature.prompt.md` - Renamed via git mv for sequential numbering
* `.agent/commands/sdd/sdd.6-review-plan.prompt.md` → `sdd.5-review-plan.prompt.md` - Renamed via git mv for sequential numbering
* `.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` → `sdd.6-task-implementer-for-feature.prompt.md` - Renamed via git mv for sequential numbering
* `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` → `sdd.6b-implementation-review.prompt.md` - Renamed via git mv for sequential numbering
* `.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` → `sdd.7-post-implementation-review.prompt.md` - Renamed via git mv for sequential numbering
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.5-task-planner-for-feature.prompt.md` → `sdd.4-task-planner-for-feature.prompt.md` - Renamed via git mv to mirror repository
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.6-review-plan.prompt.md` → `sdd.5-review-plan.prompt.md` - Renamed via git mv to mirror repository
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` → `sdd.6-task-implementer-for-feature.prompt.md` - Renamed via git mv to mirror repository
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` → `sdd.6b-implementation-review.prompt.md` - Renamed via git mv to mirror repository
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` → `sdd.7-post-implementation-review.prompt.md` - Renamed via git mv to mirror repository

* `stages.yaml` - Updated 5 prompt_template paths for PLAN, PLAN_REVIEW, IMPLEMENTATION, IMPLEMENTATION_REVIEW, and POST_REVIEW stages
* `src/teambot/scaffolds/stages.yaml` - Updated 5 prompt_template paths to mirror repository configuration

* `AGENTS.md` - Updated SDD command table to remove sdd.4 and renumber sdd.5→4, sdd.6→5, sdd.7→6, sdd.7b→6b, sdd.7c→6c, sdd.8→7
* `.agent/commands/sdd/README.md` - Updated workflow diagram and step descriptions to reflect new sequential numbering (steps 0-7, plus 6b and 6c)
* `src/teambot/scaffolds/AGENTS.md` - Updated SDD command table to mirror repository AGENTS.md
* `src/teambot/scaffolds/.agent/commands/sdd/README.md` - Updated workflow diagram to mirror repository README.md

* `.agent/commands/sdd/sdd.3-research-feature.prompt.md` - Updated 3 cross-references (Line 16 Quick Reference, Lines 391-393 handoff template, Lines 417-418 recommended next steps) to reference sdd.4-task-planner instead of sdd.4-determine-test-strategy and sdd.5-task-planner
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.3-research-feature.prompt.md` - Mirror updates from repository version

* `.agent/commands/sdd/sdd.4-task-planner-for-feature.prompt.md` - Updated Next Step references to point to Step 5 (sdd.5-review-plan) instead of Step 6
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.4-task-planner-for-feature.prompt.md` - Mirror updates from repository version

* `.agent/commands/sdd/sdd.5-review-plan.prompt.md` - Updated Next Step references to point to Step 6 (sdd.6-task-implementer) and Step 4 (sdd.4-task-planner) instead of Step 7 and Step 5
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.5-review-plan.prompt.md` - Mirror updates from repository version

* `.agent/commands/sdd/sdd.6-task-implementer-for-feature.prompt.md` - Updated Next Step references to point to Step 7 (sdd.7-post-implementation-review) instead of Step 8
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.6-task-implementer-for-feature.prompt.md` - Mirror updates from repository version

* `.agent/commands/sdd/sdd.7-post-implementation-review.prompt.md` - Updated Quick Reference Input reference from "Step 4" to "Step 6" (completed implementation)
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.7-post-implementation-review.prompt.md` - Mirror updates from repository version

* `tests/test_prompt_sync_acceptance_validation.py` - Updated file count expectations from 10→9, file list to remove sdd.4 and update numbering, changed sdd.8 and sdd.9 references to sdd.7 and sdd.8
* `tests/test_agents_md_update_acceptance.py` - Updated SDD workflow table comment from 10→9 entries, changed sdd.8 reference to sdd.7
* `tests/test_impl_review_prompt_acceptance.py` - Updated sdd.7b references to sdd.6b in prompt_path fixture and test assertions
* `tests/test_prompt_sync.py` - Updated test file reference from sdd.5 to sdd.4 in filename sorting test

### Removed

* `.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` - Deleted obsolete test strategy prompt from repository location
* `src/teambot/scaffolds/.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` - Deleted obsolete test strategy prompt from scaffold location

