<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# SDD Prompt Renumbering - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Active

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-08 |
| Problem & Users | ✅ | None | 2026-03-08 |
| Scope | ✅ | None | 2026-03-08 |
| Requirements | ✅ | None | 2026-03-08 |
| Metrics & Risks | ✅ | None | 2026-03-08 |
| Operationalization | ✅ | None | 2026-03-08 |
| Finalization | ✅ | None | 2026-03-08 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary
### Context
The TeamBot SDD (Spec-Driven Development) workflow currently includes a dedicated test strategy determination step (step 4: `sdd.4-determine-test-strategy.prompt.md`). This step was intended to analyze specifications and research to recommend an optimal testing approach. However, recent workflow refinements have integrated test strategy considerations into earlier stages (specification creation in step 1 captures testing preference, and implementation review in step 7b validates test execution and coverage). The standalone test strategy step has become obsolete, creating unnecessary workflow overhead and maintenance burden.

### Core Opportunity
Streamline the SDD workflow by removing the redundant test strategy step and renumbering all subsequent prompts sequentially. This will reduce cognitive overhead for users, simplify workflow maintenance, and align the prompt numbering with the actual workflow stages.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Eliminate obsolete test strategy prompt | Efficiency | 11 SDD prompts (0-8, 7b, 7c) with step 4 unused | 9 SDD prompts (0-7, 6b) with sequential numbering | Immediate | P0 |
| G-002 | Update all references to use new numbering | Correctness | Multiple docs/code files reference old numbering | All references updated and validated | Immediate | P0 |
| G-003 | Ensure seamless scaffold generation | Quality | `teambot init` creates correctly numbered prompts | All scaffold operations use new structure | Immediate | P0 |
| G-004 | Maintain backward compatibility for in-progress workflows | Stability | In-progress workflows use existing prompt paths | In-progress workflows unaffected until restart | Immediate | P1 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Simplify SDD workflow | Reduce prompt count from 11 to 9 with clear sequential numbering | P0 | Builder |
| Improve documentation accuracy | 100% of documentation reflects new numbering scheme | P0 | Builder |
| Validate workflow integrity | All tests pass and scaffold operations work correctly | P0 | Reviewer |

## 2. Problem Definition
### Current Situation
The SDD workflow contains 11 prompt files:
- `sdd.0-initialize.prompt.md`
- `sdd.1-create-feature-spec.prompt.md`
- `sdd.2-review-spec.prompt.md`
- `sdd.3-research-feature.prompt.md`
- **`sdd.4-determine-test-strategy.prompt.md`** ← Obsolete
- `sdd.5-task-planner-for-feature.prompt.md`
- `sdd.6-review-plan.prompt.md`
- `sdd.7-task-implementer-for-feature.prompt.md`
- `sdd.7b-implementation-review.prompt.md`
- `sdd.8-post-implementation-review.prompt.md`

Note: The ACCEPTANCE_TEST stage (`sdd.7c-acceptance-test.prompt.md` in older documentation) is **code-driven** via `AcceptanceTestExecutor` and has never had an on-disk prompt file in the current codebase.

Step 4 (test strategy determination) is no longer executed in the workflow because:
1. Testing approach preference is captured during specification creation (step 1)
2. Test execution and coverage validation occurs during implementation review (step 7b)
3. The standalone test strategy document has no consumer in the current workflow

This creates confusion because:
- The numbering is non-sequential (jumps from 4 to 5)
- Documentation mentions 11 steps when only 9 have active prompt files (ACCEPTANCE_TEST is code-driven)
- Users may try to invoke an obsolete prompt
- Maintenance burden of keeping unused file in sync with workflow changes

### Problem Statement
**The SDD workflow contains an obsolete test strategy determination step (step 4) that is no longer executed, creating workflow confusion and maintenance overhead. Subsequent prompts are numbered non-sequentially (5, 6, 7, 7b, 8), making the workflow harder to understand and maintain.**

### Root Causes
* Test strategy determination was initially designed as a separate decision point but was later integrated into other stages for better workflow cohesion
* Testing preference questions were added to specification creation to gather this information upfront
* Implementation review stage was enhanced to validate test execution and coverage, eliminating need for separate test strategy phase
* No refactoring was performed to clean up the obsolete prompt after workflow changes

### Impact of Inaction
* **User Confusion**: Users see references to 11 steps when only 10 are active, creating cognitive overhead
* **Documentation Drift**: Maintaining documentation for unused workflow steps increases error risk
* **Maintenance Burden**: Changes to workflow require updating unused file to maintain consistency
* **Workflow Clarity**: Non-sequential numbering (4→5→6→7→7b→8) obscures the actual workflow progression
* **Developer Onboarding**: New contributors struggle to understand which prompts are actually used

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| TeamBot End Users | Run SDD workflow smoothly without confusion | See 11-step workflow but only 10 execute; unclear why step 4 is skipped | Reduced confusion; clearer workflow documentation |
| TeamBot Developers | Maintain and extend SDD workflow | Must maintain unused files; non-sequential numbering complicates refactoring | Simplified maintenance; easier to add new stages |
| Documentation Writers | Keep workflow docs accurate and clear | Must explain why step 4 exists but isn't used; numbering inconsistencies | Cleaner documentation without special cases |
| New Contributors | Understand TeamBot architecture quickly | Confused by orphaned test strategy prompt and non-sequential numbering | Faster onboarding with simpler structure |

### Journeys (Optional)
**End User Journey**:
1. User runs `teambot init` to scaffold new project
2. Reads `.agent/commands/sdd/README.md` to understand workflow
3. Sees workflow diagram showing steps 0-8 (with 7b)
4. Begins executing prompts sequentially
5. Current state: Confused why step 4 is missing/skipped
6. Future state: Clear sequential progression through 0-7 (with 6b)

**Developer Maintenance Journey**:
1. Developer needs to update workflow logic
2. Reviews `stages.yaml` for stage configuration
3. Sees `prompt_template` references to various numbered prompts
4. Current state: Must navigate non-sequential numbering and skip unused step 4
5. Future state: Sequential numbering with no gaps or unused files

## 4. Scope
### In Scope
* Remove `sdd.4-determine-test-strategy.prompt.md` from both `.agent/commands/sdd/` and scaffold directory
* Rename prompt files to sequential numbering:
  - `sdd.5-task-planner-for-feature.prompt.md` → `sdd.4-task-planner-for-feature.prompt.md`
  - `sdd.6-review-plan.prompt.md` → `sdd.5-review-plan.prompt.md`
  - `sdd.7-task-implementer-for-feature.prompt.md` → `sdd.6-task-implementer-for-feature.prompt.md`
  - `sdd.7b-implementation-review.prompt.md` → `sdd.6b-implementation-review.prompt.md`
  - `sdd.8-post-implementation-review.prompt.md` → `sdd.7-post-implementation-review.prompt.md`
* Update `stages.yaml` with correct `prompt_template` paths for affected stages (PLAN, PLAN_REVIEW, IMPLEMENTATION, IMPLEMENTATION_REVIEW, POST_REVIEW)
* Update `.agent/commands/sdd/README.md` workflow diagram and step descriptions
* Update `AGENTS.md` SDD command table with new file names
* Update scaffold files in `src/teambot/scaffolds/.agent/commands/sdd/` to match repository structure
* Update test fixtures and references to use new file names
* Validate `teambot init` creates correctly numbered prompt files

### Out of Scope (justify if empty)
* Changes to workflow stage logic (RESEARCH stage still runs, only the unused TEST_STRATEGY determination is removed)
* Changes to prompt file content (content remains identical, only file names change)
* Migration of in-progress workflows (they will continue using their existing prompt paths until restarted)
* Changes to acceptance test execution logic (ACCEPTANCE_TEST stage is code-driven via `AcceptanceTestExecutor`; there is no on-disk prompt file for this stage)
* Modifications to objective template structure

### Assumptions
* In-progress workflows will continue using their existing prompt paths (stored in `.teambot/<feature>/workflow_state.json`) until workflow is restarted
* No users are actively developing custom extensions that hardcode old prompt file paths
* Test fixtures can be updated to reference new file names without breaking test logic
* Scaffold copy operations will work correctly with renamed source files
* Git history will preserve the rename operations for future reference

### Constraints
* Must preserve exact content of all prompt files (only file names change)
* Must maintain scaffold integrity so `teambot init` continues to work
* Must not break existing test suite
* Must be reversible via git revert if issues discovered post-merge
* Must not modify workflow stage execution logic in `orchestrator.py` or state machine

## 5. Product Overview
### Value Proposition
**Simplified, maintainable SDD workflow with clear sequential numbering and no obsolete artifacts.**

This refactoring delivers immediate value by:
- **Eliminating confusion** about missing or unused workflow steps
- **Improving maintainability** by removing dead code and simplifying references
- **Enhancing developer experience** with intuitive sequential numbering
- **Reducing cognitive load** for users learning the SDD workflow
- **Future-proofing** the workflow structure for easier additions/modifications

### Differentiators (Optional)
* This is a structural cleanup, not a feature addition
* Focus on developer experience and workflow clarity
* Minimal risk due to straightforward file renaming with no logic changes

### UX / UI (Conditional)
**Command-line interface impact**: None (users invoke prompts via slash commands which remain unchanged)

**Documentation impact**: Significant - all workflow documentation must be updated to reflect new numbering

**Error messages**: Any error messages referencing prompt file names should use new numbering

UX Status: Documentation updates required

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|-----------|-------|
| FR-001 | Remove obsolete test strategy prompt | Delete `sdd.4-determine-test-strategy.prompt.md` from `.agent/commands/sdd/` and `src/teambot/scaffolds/.agent/commands/sdd/` | G-001 | Developers, End Users | P0 | File does not exist in either location after changes | Verify no references remain in code or docs |
| FR-002 | Renumber task planner prompt | Rename `sdd.5-task-planner-for-feature.prompt.md` to `sdd.4-task-planner-for-feature.prompt.md` in both locations | G-001 | Developers, End Users | P0 | File exists with new name; content unchanged | Update `stages.yaml` PLAN stage prompt_template |
| FR-003 | Renumber plan review prompt | Rename `sdd.6-review-plan.prompt.md` to `sdd.5-review-plan.prompt.md` in both locations | G-001 | Developers, End Users | P0 | File exists with new name; content unchanged | Update `stages.yaml` PLAN_REVIEW stage prompt_template |
| FR-004 | Renumber implementation prompt | Rename `sdd.7-task-implementer-for-feature.prompt.md` to `sdd.6-task-implementer-for-feature.prompt.md` in both locations | G-001 | Developers, End Users | P0 | File exists with new name; content unchanged | Update `stages.yaml` IMPLEMENTATION stage prompt_template |
| FR-005 | Renumber implementation review prompt | Rename `sdd.7b-implementation-review.prompt.md` to `sdd.6b-implementation-review.prompt.md` in both locations | G-001 | Developers, End Users | P0 | File exists with new name; content unchanged | Update `stages.yaml` IMPLEMENTATION_REVIEW stage prompt_template |
| FR-006 | Acknowledge ACCEPTANCE_TEST has no prompt file | The ACCEPTANCE_TEST stage is code-driven via `AcceptanceTestExecutor`; there is no `sdd.7c-acceptance-test.prompt.md` or `sdd.6c-acceptance-test.prompt.md` file on disk. No file rename or `stages.yaml` update is required for this stage. | G-001 | Developers | P0 | No `sdd.*c-acceptance-test.prompt.md` file exists; `stages.yaml` ACCEPTANCE_TEST stage has no `prompt_template` | Verify `AcceptanceTestExecutor` handles stage execution |
| FR-007 | Renumber post-review prompt | Rename `sdd.8-post-implementation-review.prompt.md` to `sdd.7-post-implementation-review.prompt.md` in both locations | G-001 | Developers, End Users | P0 | File exists with new name; content unchanged | Update `stages.yaml` POST_REVIEW stage prompt_template |
| FR-008 | Update stages.yaml references | Update all `prompt_template` fields in `stages.yaml` to reference new file names | G-002 | Developers | P0 | All prompt_template paths point to new file names; workflow executes correctly | Affects PLAN, PLAN_REVIEW, IMPLEMENTATION, IMPLEMENTATION_REVIEW, POST_REVIEW stages; ACCEPTANCE_TEST has no prompt_template |
| FR-009 | Update README workflow diagram | Update `.agent/commands/sdd/README.md` workflow diagram to show new numbering (0, 1, 2, 3, 4, 5, 6, 6b, 7) | G-002 | End Users, Documentation Writers | P0 | README shows 9-step workflow with sequential numbering; no references to step 4 test strategy or step 6c | Update step descriptions and quick reference tables |
| FR-010 | Update AGENTS.md SDD table | Update `AGENTS.md` SDD command table with new file names | G-002 | Developers, New Contributors | P0 | AGENTS.md table shows correct new file paths | Located in repository root |
| FR-011 | Update test fixtures | Update test files that reference old prompt file names to use new names | G-002 | Developers | P0 | All tests pass with new file names | Search for hardcoded references to old file names |
| FR-012 | Validate scaffold operations | Ensure `teambot init` command creates correctly numbered prompt files in user projects | G-003 | End Users | P0 | Running `teambot init` creates prompt files with new numbering; no step 4 test strategy file | Test in clean environment |

### Feature Hierarchy (Optional)
```plain
SDD Prompt Renumbering
├── File Operations
│   ├── Delete obsolete test strategy prompt (FR-001)
│   └── Rename subsequent prompts (FR-002 through FR-005, FR-007; FR-006 documents code-driven ACCEPTANCE_TEST)
├── Configuration Updates
│   └── Update stages.yaml prompt_template paths (FR-008)
├── Documentation Updates
│   ├── Update README workflow diagram (FR-009)
│   └── Update AGENTS.md table (FR-010)
└── Validation
    ├── Update test fixtures (FR-011)
    └── Validate scaffold operations (FR-012)
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Correctness | All renamed files must have identical content to originals | 100% content preservation (verified via diff) | P0 | Compare file contents before/after rename | Only file names change |
| NFR-002 | Completeness | All references in code and docs must use new file names | 0 references to old file names (verified via grep) | P0 | Search codebase for old file name patterns | Check .py, .md, .yaml files |
| NFR-003 | Testability | All existing tests must pass after renumbering | 100% test pass rate | P0 | Run full test suite | May need to update test fixtures |
| NFR-004 | Maintainability | Changes should be easy to revert if issues arise | Single git revert restores old structure | P1 | Test revert operation | Primarily rename operations |
| NFR-005 | Backward Compatibility | In-progress workflows must continue to function | Existing workflow state files unaffected | P1 | Verify workflows in-progress are not disrupted | They use stored prompt paths |
| NFR-006 | Performance | Scaffold operations must not be slower | No measurable performance degradation | P2 | Benchmark `teambot init` before/after | File operations should be identical |
| NFR-007 | Observability | Changes should be logged for audit trail | Git commit shows all file renames clearly | P2 | Review git log/diff after merge | Use `git mv` for renames |

Categories: Performance, Reliability, Scalability, Security, Privacy, Accessibility, Observability, Maintainability, Localization (if), Compliance (if).

## 8. Data & Analytics (Conditional)
### Inputs
* Current SDD prompt files (0-8, including 7b, with 4 obsolete; ACCEPTANCE_TEST stage has no on-disk prompt file—it is code-driven via `AcceptanceTestExecutor`)
* `stages.yaml` configuration with prompt_template mappings
* Documentation files (README.md, AGENTS.md)
* Test fixtures referencing old file names
* Scaffold template files in `src/teambot/scaffolds/`

### Outputs / Events
* Deleted file: `sdd.4-determine-test-strategy.prompt.md` (both locations)
* Renamed files: 5 prompt files with new sequential numbering
* Updated files: `stages.yaml`, `README.md`, `AGENTS.md`, test fixtures
* Git commit showing all file operations

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| N/A | N/A | N/A | This is a structural refactoring with no runtime instrumentation needed | N/A |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Test pass rate | Quality | 100% (before changes) | 100% (after changes) | Immediate | pytest output |
| File rename count | Correctness | 0 | 6 files renamed, 1 deleted | Immediate | Git diff |
| Reference update count | Completeness | N/A | All references updated (verified via grep) | Immediate | Code search |
| Scaffold integrity | Quality | `teambot init` works | `teambot init` works with new numbering | Immediate | Manual test |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `stages.yaml` schema | Internal | Critical | TeamBot Core | Breaking workflow if paths incorrect | Validate syntax and test workflow execution |
| Git rename tracking | Tool | High | Git | History loss if rename not detected | Use `git mv` for file operations |
| Test suite fixtures | Internal | High | TeamBot Tests | Tests may fail if fixtures not updated | Search all test files for old references |
| Scaffold copy logic | Internal | Medium | TeamBot Core | Scaffold may fail if source files missing | Verify scaffold directory structure after changes |
| Active development branches | Process | Low | Developers | Merge conflicts if others modifying same files | Communicate changes; prefer off-hours merge |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Missed reference to old file names causing runtime errors | High | Medium | Comprehensive grep search for all old file name patterns; manual code review | Reviewer | Open |
| R-002 | Test failures due to outdated fixtures | Medium | High | Update all test fixtures before running full test suite; verify pytest passes | Builder | Open |
| R-003 | Scaffold operations fail due to missing source files | High | Low | Verify scaffold directory structure matches repository after renaming | Builder | Open |
| R-004 | Documentation becomes inconsistent with implementation | Medium | Medium | Update all documentation files atomically with code changes; review before merge | Writer | Open |
| R-005 | In-progress workflows disrupted | Low | Low | In-progress workflows use stored paths and are unaffected until restart | N/A | Accepted |
| R-006 | Custom user extensions broken by hardcoded paths | Medium | Low | Document breaking change in changelog; provide migration guide if needed | PM | Open |
| R-007 | Git merge conflicts with parallel development | Low | Medium | Coordinate with team; prefer off-hours merge; communicate in advance | PM | Open |

## 11. Privacy, Security & Compliance
### Data Classification
**Public**: All files involved are part of the open-source TeamBot repository with no sensitive data.

### PII Handling
**Not Applicable**: No PII is processed, stored, or transmitted as part of this refactoring.

### Threat Considerations
**Not Applicable**: This is a structural refactoring with no security implications. No changes to authentication, authorization, data handling, or external interfaces.

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| N/A | N/A | N/A | N/A | N/A |

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard git merge to main branch | No special deployment steps required |
| Rollback | Single `git revert` of merge commit | Changes are primarily file renames, easy to revert |
| Monitoring | Standard CI/CD pipeline (pytest, linting) | No additional monitoring needed |
| Alerting | Test failures in CI/CD trigger notifications | Standard GitHub Actions alerts |
| Support | Update FAQ/docs if users report confusion | Unlikely, as change is internal refactoring |
| Capacity Planning | N/A | No infrastructure changes |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Development | TBD | All file renames complete; stages.yaml updated | Builder |
| Testing | TBD | All tests passing; manual scaffold validation complete | Builder |
| Documentation | TBD | README.md, AGENTS.md updated and reviewed | Writer |
| Review | TBD | Code review approved; no outstanding concerns | Reviewer |
| Merge | TBD | All gate criteria met; CI/CD pipeline green | PM |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| N/A | N/A | N/A | N/A |

**Note**: No feature flags needed - this is a one-time structural refactoring with no runtime configuration.

### Communication Plan (Optional)
* **Internal Team**: Notify in team chat/standup before merge to minimize conflicts
* **Users**: Document change in CHANGELOG.md as "Breaking change for custom extensions referencing old prompt file paths"
* **Contributors**: Update contribution guide if it references SDD workflow steps

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| Q-001 | Are there any known users with custom extensions that hardcode SDD prompt paths? | PM | Pre-merge | Open |
| Q-002 | Should we add a deprecation notice in old locations before deletion (e.g., symlinks with warnings)? | PM | Pre-implementation | Open |
| Q-003 | Should CHANGELOG.md explicitly list this as a breaking change for extensions? | Writer | Pre-merge | Open |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-03-08 | BA Agent | Initial specification created | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|-------------------|
| REF-001 | Objective File | User-provided objective | Goals and success criteria for SDD prompt renumbering | N/A - source of truth |
| REF-002 | Code | `.agent/commands/sdd/README.md` | Current workflow documentation showing 11 steps | Will be updated as part of FR-009 |
| REF-003 | Code | `stages.yaml` | Current stage configuration with prompt_template mappings | Will be updated as part of FR-008 |
| REF-004 | Code | `AGENTS.md` | Current agent documentation with SDD file paths | Will be updated as part of FR-010 |

### Citation Usage
* REF-001 used to define goals (Section 1) and scope (Section 4)
* REF-002 used to understand current workflow structure (Section 2)
* REF-003 used to identify prompt_template update requirements (Section 6)
* REF-004 used to identify documentation update requirements (Section 6)

## 17. Appendices (Optional)
### Glossary
| Term | Definition |
|------|-----------|
| SDD | Spec-Driven Development - TeamBot's structured workflow for feature development |
| Prompt Template | Markdown file containing instructions for AI agents at specific workflow stages |
| Scaffold | Template files copied during `teambot init` to initialize new projects |
| Stage | Discrete phase in the TeamBot workflow (e.g., SPEC, RESEARCH, PLAN) |
| Acceptance Test | ACCEPTANCE_TEST workflow stage validated via `AcceptanceTestExecutor` (code-driven); there is no on-disk prompt file for this stage |

### Additional Notes
**Implementation Strategy**:
1. Create feature branch from main
2. Use `git mv` for all file renames to preserve history
3. Update `stages.yaml` immediately after renames
4. Update documentation files (README.md, AGENTS.md)
5. Search for and update all test references
6. Run full test suite (`pytest`)
7. Manually test `teambot init` in clean environment
8. Grep entire codebase for old file name patterns
9. Code review with focus on completeness of reference updates
10. Merge to main via PR

**Revert Plan**:
* If issues discovered post-merge: `git revert <merge-commit>`
* All changes are in a single merge commit for easy reversion
* No database migrations or persistent state changes to roll back

## Acceptance Test Scenarios

### AT-001: Repository File Renumbering
**Description**: Verify all SDD prompt files in `.agent/commands/sdd/` are correctly renumbered
**Preconditions**: Repository is on feature branch with changes applied
**Steps**:
1. List all prompt files in `.agent/commands/sdd/` directory
2. Verify `sdd.4-determine-test-strategy.prompt.md` does not exist
3. Verify `sdd.4-task-planner-for-feature.prompt.md` exists (renamed from step 5)
4. Verify `sdd.5-review-plan.prompt.md` exists (renamed from step 6)
5. Verify `sdd.6-task-implementer-for-feature.prompt.md` exists (renamed from step 7)
6. Verify `sdd.6b-implementation-review.prompt.md` exists (renamed from step 7b)
7. Verify `sdd.7-post-implementation-review.prompt.md` exists (renamed from step 8)
8. Verify no `sdd.6c-acceptance-test.prompt.md` exists (ACCEPTANCE_TEST stage is code-driven, not prompt-based)
**Expected Result**: File listing shows 9 prompt files (0-7, with 6b) with no step 4 and no step 6c
**Verification**: `ls .agent/commands/sdd/sdd.*.prompt.md | wc -l` returns 9; no file matches `sdd.4-determine-test-strategy` or `sdd.*c-acceptance-test`

### AT-002: Scaffold File Renumbering
**Description**: Verify scaffold directory mirrors repository structure with new numbering
**Preconditions**: Repository is on feature branch with changes applied
**Steps**:
1. List all prompt files in `src/teambot/scaffolds/.agent/commands/sdd/` directory
2. Verify structure matches repository `.agent/commands/sdd/` directory
3. Verify `sdd.4-determine-test-strategy.prompt.md` does not exist in scaffold
4. Verify all other renamed files exist with new numbering
**Expected Result**: Scaffold directory has identical structure to repository (9 files, no step 4, no step 6c)
**Verification**: `diff <(ls .agent/commands/sdd/) <(ls src/teambot/scaffolds/.agent/commands/sdd/)` shows no differences

### AT-003: stages.yaml Configuration Validation
**Description**: Verify stages.yaml references correct new prompt file paths
**Preconditions**: stages.yaml has been updated with new paths
**Steps**:
1. Parse `stages.yaml` to extract all `prompt_template` values
2. For each prompt_template path, verify file exists at that location
3. Check PLAN stage references `sdd.4-task-planner-for-feature.prompt.md`
4. Check PLAN_REVIEW stage references `sdd.5-review-plan.prompt.md`
5. Check IMPLEMENTATION stage references `sdd.6-task-implementer-for-feature.prompt.md`
6. Check IMPLEMENTATION_REVIEW stage references `sdd.6b-implementation-review.prompt.md`
7. Check POST_REVIEW stage references `sdd.7-post-implementation-review.prompt.md`
8. Verify ACCEPTANCE_TEST stage has no `prompt_template` entry (it is code-driven via `AcceptanceTestExecutor`)
9. Verify no stage references `sdd.4-determine-test-strategy.prompt.md`
**Expected Result**: All prompt_template paths point to existing files with new numbering; ACCEPTANCE_TEST stage has no prompt_template; no references to old step 4
**Verification**: `grep 'sdd\.[0-9]' stages.yaml` shows only new numbering; `grep 'sdd.4-determine-test-strategy\|sdd.*c-acceptance-test' stages.yaml` returns no matches

### AT-004: Full Workflow Execution
**Description**: Run complete SDD workflow from SETUP to COMPLETE to verify orchestration works
**Preconditions**: Test environment with changes applied; sample objective file available
**Steps**:
1. Initialize test workflow with `teambot run <test-objective.md>`
2. Let orchestrator progress through stages automatically (or step through manually)
3. Observe PLAN stage loads correct prompt (sdd.4-task-planner-for-feature.prompt.md)
4. Observe PLAN_REVIEW stage loads correct prompt (sdd.5-review-plan.prompt.md)
5. Observe IMPLEMENTATION stage loads correct prompt (sdd.6-task-implementer-for-feature.prompt.md)
6. Observe IMPLEMENTATION_REVIEW stage loads correct prompt (sdd.6b-implementation-review.prompt.md)
7. Observe POST_REVIEW stage loads correct prompt (sdd.7-post-implementation-review.prompt.md)
8. Verify no errors related to missing prompt files
**Expected Result**: Workflow executes successfully with all stages loading correct prompts; no file-not-found errors
**Verification**: Check `.teambot/<feature>/workflow_state.json` shows all stages completed; review agent logs for any errors

### AT-005: Test Suite Validation
**Description**: Verify all existing tests pass after renumbering changes
**Preconditions**: All code and test fixture updates completed
**Steps**:
1. Run full test suite: `uv run pytest`
2. Check for any failures related to prompt file paths
3. Review test output for deprecated references to old file names
**Expected Result**: 100% test pass rate; no references to old file names in test output
**Verification**: `pytest` exit code 0; `grep -r "sdd.4-determine-test-strategy\|sdd.5-task-planner\|sdd.6-review-plan\|sdd.7-task-implementer\|sdd.7b-implementation\|sdd.8-post" tests/` returns no matches

### AT-006: Scaffold Initialization Test
**Description**: Verify `teambot init` creates correctly numbered prompt files in new project
**Preconditions**: Clean test directory; TeamBot with changes installed
**Steps**:
1. Create empty test directory: `mkdir /tmp/test-teambot-init && cd /tmp/test-teambot-init`
2. Run: `teambot init`
3. List created SDD prompt files: `ls .agent/commands/sdd/sdd.*.prompt.md`
4. Verify `sdd.4-determine-test-strategy.prompt.md` does NOT exist
5. Verify `sdd.4-task-planner-for-feature.prompt.md` DOES exist
6. Verify all other renamed files exist with new numbering
7. Count total prompt files created
**Expected Result**: 9 prompt files created (0-7, with 6b); no step 4 test strategy file; no step 6c acceptance test file (ACCEPTANCE_TEST is code-driven)
**Verification**: `ls .agent/commands/sdd/sdd.*.prompt.md | wc -l` returns 9; specific check for absence of old step 4 and any `*c-acceptance-test` file

### AT-007: Documentation Accuracy Validation
**Description**: Verify all documentation reflects new numbering scheme
**Preconditions**: README.md, AGENTS.md, and other docs updated
**Steps**:
1. Read `.agent/commands/sdd/README.md` workflow diagram
2. Verify diagram shows steps 0-7 (with 6b) with no reference to step 4 test strategy and no step 6c
3. Read `AGENTS.md` SDD workflow table
4. Verify all file paths use new numbering
5. Search all markdown files for old file name patterns: `grep -r "sdd.4-determine-test-strategy\|sdd.5-task-planner\|sdd.6-review-plan\|sdd.7-task-implementer\|sdd.7b-implementation\|sdd.8-post" docs/ .agent/`
**Expected Result**: No references to old file names in documentation; workflow diagrams show 9-step process; ACCEPTANCE_TEST noted as code-driven with no prompt file
**Verification**: Grep search returns zero matches; manual review of README confirms new numbering

Generated 2026-03-08T23:01:11Z by BA Agent (mode: interactive)
<!-- markdown-table-prettify-ignore-end -->
<!-- </template-feature-spec> -->
