# Implementation Plan: SDD Prompt Renumbering

## Executive Summary

This plan addresses the removal of the obsolete `sdd.4-determine-test-strategy.prompt.md` file and sequential renumbering of all subsequent SDD prompt files (5→4, 6→5, 7→6, 7b→6b, 8→7). The changes affect both repository and scaffold locations, with corresponding updates to configuration files, documentation, cross-references, and test files.

## Overview

**Objective**: Reorganize SDD prompt files to eliminate numbering gaps and maintain sequential consistency after removing the obsolete test strategy prompt.

**Scope**: 
- 10 prompt files in repository (9 after deletion)
- 10 prompt files in scaffolds (9 after deletion)
- 2 configuration files (stages.yaml in repository and scaffolds)
- 4 documentation files (AGENTS.md and SDD README.md in both locations)
- Multiple test files with hardcoded references
- Internal cross-references within prompt files

**Approach**: Sequential file operations using `git mv` for history preservation, followed by configuration updates, documentation updates, cross-reference fixes, test updates, and comprehensive validation.

## Implementation Phases

### Phase 1: Repository File Operations (Critical Path)
**Objective**: Remove sdd.4 and rename remaining prompts in repository using git operations.

**Tasks**:
1. Delete `.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` with `git rm`
2. Rename sdd.5→4, sdd.6→5, sdd.7→6, sdd.7b→6b, sdd.8→7 with `git mv`
3. Verify file count (9 files) and git status shows renames

**Duration Estimate**: 15 minutes  
**Risk**: LOW - Straightforward file operations  
**Dependencies**: None

### Phase 2: Scaffold File Operations (Critical Path)
**Objective**: Apply identical operations to scaffold directory.

**Tasks**:
1. Delete `src/teambot/scaffolds/.agent/commands/sdd/sdd.4-determine-test-strategy.prompt.md` with `git rm`
2. Rename all files identically to repository with `git mv`
3. Verify scaffold structure mirrors repository

**Duration Estimate**: 10 minutes  
**Risk**: LOW - Mirror operations of Phase 1  
**Dependencies**: Phase 1 completion

### Phase 3: Configuration Updates (Critical Path)
**Objective**: Update stages.yaml prompt_template references.

**Tasks**:
1. Update 5 prompt_template paths in repository `stages.yaml` (lines 323, 354, 391, 428, 506)
2. Apply identical updates to `src/teambot/scaffolds/stages.yaml`
3. Verify no references to old numbering remain

**Duration Estimate**: 15 minutes  
**Risk**: MEDIUM - Configuration errors could break orchestration  
**Dependencies**: Phase 2 completion

### Phase 4: Documentation Updates (Critical Path)
**Objective**: Update AGENTS.md and README.md in both locations.

**Tasks**:
1. Update repository AGENTS.md SDD command table (remove sdd.4 row, update 5-8 rows)
2. Update repository `.agent/commands/sdd/README.md` (workflow diagram and step descriptions)
3. Mirror updates to scaffold AGENTS.md
4. Mirror updates to scaffold SDD README.md

**Duration Estimate**: 20 minutes  
**Risk**: LOW - Documentation changes don't affect functionality  
**Dependencies**: Phase 3 completion

### Phase 5: Cross-Reference Updates (Critical Path)
**Objective**: Fix internal references within prompt files.

**Tasks**:
1. Update `sdd.3-research-feature.prompt.md` (3 locations referencing sdd.4 and sdd.5)
2. Update handoff instructions in renamed prompts (sdd.4, sdd.5, sdd.6, sdd.6b, sdd.7)
3. Apply identical updates to scaffold prompt files

**Duration Estimate**: 20 minutes  
**Risk**: MEDIUM - Incorrect references could confuse workflow  
**Dependencies**: Phase 4 completion

### Phase 6: Test Updates (Critical Path)
**Objective**: Update test files with hardcoded prompt references.

**Tasks**:
1. Update `tests/test_prompt_sync_acceptance_validation.py` (file count and sdd.8 references)
2. Update `tests/test_agents_md_update_acceptance.py` (sdd.8 → sdd.7)
3. Update `tests/test_impl_review_prompt_acceptance.py` (sdd.7b → sdd.6b)
4. Update `tests/test_prompt_sync.py` (sdd.5 references if needed)

**Duration Estimate**: 15 minutes  
**Risk**: LOW - Test updates are straightforward  
**Dependencies**: Phase 5 completion

### Phase 7: Validation and Testing
**Objective**: Execute comprehensive test suite and manual verification.

**Tasks**:
1. Run unit tests: `uv run pytest -m 'not acceptance'`
2. Run acceptance tests: `uv run pytest -m acceptance`
3. Manual teambot init verification in temporary directory

**Duration Estimate**: 10 minutes (execution time)  
**Risk**: LOW - Tests validate all changes  
**Dependencies**: Phase 6 completion

## Total Estimated Duration
**Critical Path**: 105 minutes (1 hour 45 minutes)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Git history loss on renames | LOW | HIGH | Use `git mv` exclusively, verify git status shows renames |
| Broken stages.yaml references | MEDIUM | HIGH | Validate file existence after config updates |
| Test failures | MEDIUM | MEDIUM | Update all test references before running validation |
| Documentation inconsistency | LOW | LOW | Use checklist to ensure all locations updated |
| Cross-reference errors | MEDIUM | MEDIUM | Systematic verification of all handoff instructions |

## Rollback Plan

If issues are discovered post-implementation:
1. **Immediate**: `git revert` of the commit(s) containing the changes
2. **Quick**: Rename operations are easily reversible (reverse the mapping)
3. **Safe**: No logic changes mean reversal is straightforward
4. **Validation**: Re-run test suite after rollback to confirm restoration

## Success Metrics

- [ ] 9 SDD prompt files exist with sequential numbering (0-7, plus 6b)
- [ ] Both repository and scaffold locations have identical structure
- [ ] All stages.yaml prompt_template paths reference existing files
- [ ] All documentation reflects new numbering scheme
- [ ] All test files reference correct file names
- [ ] Unit test suite passes: 0 failures
- [ ] Acceptance test suite passes: 0 failures
- [ ] Manual teambot init creates 9 correctly numbered files
- [ ] Git log shows rename tracking for all moved files
- [ ] No grep matches for old numbering patterns (sdd.5-task-planner, etc.)

## Detailed Task Breakdown

Refer to:
- **Plan File**: `.agent-tracking/plans/20260308-sdd-prompt-renumbering-plan.instructions.md`
- **Details File**: `.agent-tracking/details/20260308-sdd-prompt-renumbering-details.md`
- **Research File**: `.agent-tracking/research/20260308-sdd-prompt-renumbering-research.md`

## Validation Commands

```bash
# Verify file count
ls -1 .agent/commands/sdd/sdd.*.prompt.md | wc -l  # Should be 9

# Verify git tracking
git status | grep renamed  # Should show 5 renames per location

# Verify no old references in config
grep -r "sdd\.4-determine-test-strategy" stages.yaml  # Should be empty
grep -r "sdd\.[5-8]-" stages.yaml  # Should be empty

# Verify no old references in docs
grep -r "sdd\.5-task-planner" AGENTS.md .agent/commands/sdd/README.md  # Should be empty

# Run tests
uv run pytest -m 'not acceptance'  # Should pass
uv run pytest -m acceptance  # Should pass

# Manual verification
mkdir -p /tmp/teambot-test && cd /tmp/teambot-test
uv run teambot init
ls -1 .agent/commands/sdd/sdd.*.prompt.md  # Should list 9 files with correct numbering
```

## Implementation Notes

- **File Operations**: Always use `git mv` and `git rm` to preserve history
- **Configuration**: Update both repository and scaffold stages.yaml identically
- **Documentation**: Maintain consistency between repository and scaffold locations
- **Testing**: Update test expectations before running validation
- **Verification**: Use grep patterns to confirm no old references remain

## Handoff to Implementation

This plan is ready for implementation by a builder agent. All tasks are atomic, actionable, and include specific file paths and line number references. The validation strategy ensures comprehensive coverage of all affected areas.

**Recommended Implementer**: `@builder-1` (primary) or `@builder-2` (if parallel work needed)

**Next Step**: Run **Step 6** (`sdd.6-review-plan.prompt.md`) to validate this implementation plan before proceeding to execution.
