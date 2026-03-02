# Problem Statement: SDD Prompt File Synchronization

## Business Problem

TeamBot's SDD workflow depends on a tight coupling between two configuration sources:

1. **`stages.yaml`** - Defines the 14 workflow stages, each with a `prompt_template` field pointing to an SDD prompt file
2. **SDD prompt files** - Located in `.agent/commands/sdd/`, these provide the instructions for each workflow stage

**The problem**: After initial `teambot init`, these two sources can drift out of sync over time, causing workflow failures or inconsistent behavior. This occurs in several scenarios:

### Scenario 1: Missing Prompt Files
A user's `stages.yaml` references prompt files that don't exist in their `.agent/commands/sdd/` directory. This can happen when:
- TeamBot is upgraded and ships new stages requiring new prompt files
- A user deletes or renames prompt files accidentally
- A user customizes `stages.yaml` to add stages but forgets to create the corresponding prompts

**Impact**: Runtime failures when the workflow attempts to load a non-existent prompt template.

### Scenario 2: Orphaned Prompt Files  
Prompt files exist in `.agent/commands/sdd/` but are no longer referenced by any stage in `stages.yaml`. This creates:
- Confusion about which files are active
- Maintenance burden for unused files
- Potential security/compliance concerns with stale content

### Scenario 3: User Customizations Lost
When a user has customized their `.agent/commands/sdd/` prompt files and TeamBot is upgraded, the current scaffold copy behavior presents a dilemma:
- **Without `--force`**: New prompt files won't be added (preserves customizations but blocks upgrades)
- **With `--force`**: All user customizations are overwritten (enables upgrades but destroys work)

**Impact**: Users must choose between losing their customizations or missing new functionality.

### Scenario 4: No Validation Feedback
Currently, TeamBot does not validate that `stages.yaml` and prompt files are synchronized. Users discover mismatches only when:
- A workflow fails at runtime
- They manually inspect both files

**Impact**: Silent failures and debugging friction.

---

## Business Goals

| ID | Goal | Measurable Outcome |
|----|------|-------------------|
| G1 | **Incremental sync during init** | New prompt files are added without overwriting existing customizations |
| G2 | **Runtime validation** | Mismatches between `stages.yaml` and prompt files are detected before workflow execution |
| G3 | **Actionable remediation** | Validation errors include specific commands or steps users can take to resolve issues |
| G4 | **Backward compatibility** | Existing scaffold copy behavior is preserved; new sync is additive |
| G5 | **Transparent change tracking** | Users can see what changed during sync operations |

---

## Success Criteria

### SC-1: Incremental Prompt Sync
**Given** a user has existing prompt files with customizations  
**When** they run `teambot init` (without `--force`)  
**Then** only missing prompt files are copied; existing files are preserved  
**And** a summary shows which files were added vs. skipped

### SC-2: Runtime Validation - Missing Prompts
**Given** `stages.yaml` references a prompt file that doesn't exist  
**When** `teambot run` is executed  
**Then** validation fails with an error listing:
- The missing file path
- The stage that requires it
- A remediation command (e.g., `teambot init --sync-prompts`)

### SC-3: Runtime Validation - Orphaned Prompts (Warning Only)
**Given** prompt files exist that are not referenced by any stage  
**When** `teambot run` is executed  
**Then** a warning is displayed (not a blocking error)  
**And** the orphaned files are listed

### SC-4: Validation Summary Command
**Given** a user wants to check sync status without running a workflow  
**When** they run `teambot status` or a new `teambot validate` subcommand  
**Then** they see a sync health report showing:
- ✓ Matched files (stage → prompt)
- ✗ Missing files
- ⚠ Orphaned files

### SC-5: Backward Compatibility
**Given** existing `copy_scaffold_directory()` behavior for `.agent/`  
**When** this feature is implemented  
**Then** the existing "copy if empty or missing" behavior is unchanged  
**And** the new incremental sync is an additional operation

### SC-6: Force Sync Option
**Given** a user wants to reset all prompt files to defaults  
**When** they run `teambot init --force`  
**Then** all prompt files are overwritten (existing behavior preserved)  
**And** a warning is shown listing customizations that will be lost

---

## Stakeholders

| Role | Interest |
|------|----------|
| **TeamBot users** | Seamless upgrades, preserved customizations, clear error messages |
| **TeamBot maintainers** | Ability to ship new stages/prompts without breaking existing users |
| **AI agents** | Reliable prompt loading during workflow execution |

---

## Constraints

1. **No breaking changes** - Existing `scaffolds.py` and `cli.py` behavior must remain intact
2. **Python 3.11+ only** - Can use modern Python features
3. **Click CLI framework** - Must integrate with existing CLI patterns
4. **No external dependencies** - Should not introduce new package dependencies
5. **Testable** - All new code must be covered by unit and acceptance tests

---

## Out of Scope

The following are explicitly **not** part of this feature:

- **Automatic conflict resolution** - When files conflict, user decides (no merge logic)
- **Prompt file versioning** - No tracking of prompt file versions across TeamBot releases
- **Schema validation of prompt content** - Only file existence is checked, not file contents
- **Custom stages.yaml paths** - Validation assumes `stages.yaml` is at repo root
- **Remote prompt repositories** - No fetching prompts from external sources

---

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `stages.yaml` | Input | Source of truth for stage → prompt mappings |
| `scaffolds.py` | Integration | Existing copy infrastructure to extend |
| `cli.py` | Integration | `init` command to enhance, `run` command to add validation |
| `workflow/state_machine.py` | Consumer | May benefit from validation hooks |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users unaware of sync feature | Medium | Low | Document in `--help` and display sync summary during init |
| False positives in orphan detection | Low | Medium | Only flag files matching `sdd.*.prompt.md` pattern |
| Performance overhead at runtime | Low | Low | Cache validation results per workflow run |

---

## Open Questions

1. **Q1**: Should the validation be a hard blocker or allow `--skip-validation` override?
   - **Recommendation**: Hard blocker for missing prompts, warning-only for orphans

2. **Q2**: Should we support partial sync (e.g., `--sync-prompts=sdd.5-*`)?
   - **Recommendation**: Out of scope for MVP; add if user feedback requests it

3. **Q3**: Should orphaned file detection include all `.agent/commands/sdd/` files or only `sdd.*.prompt.md`?
   - **Recommendation**: Only `sdd.*.prompt.md` to avoid false positives on README.md or custom files

---

## Appendix: Current State Analysis

### Stages with prompt_template (10 stages)

| Stage | Prompt File | Required |
|-------|-------------|----------|
| SETUP | `sdd.0-initialize.prompt.md` | Yes |
| SPEC | `sdd.1-create-feature-spec.prompt.md` | Yes |
| SPEC_REVIEW | `sdd.2-review-spec.prompt.md` | Yes |
| RESEARCH | `sdd.3-research-feature.prompt.md` | Yes |
| TEST_STRATEGY | `sdd.4-determine-test-strategy.prompt.md` | Yes |
| PLAN | `sdd.5-task-planner-for-feature.prompt.md` | Yes |
| PLAN_REVIEW | `sdd.6-review-plan.prompt.md` | Yes |
| IMPLEMENTATION | `sdd.7-task-implementer-for-feature.prompt.md` | Yes |
| IMPLEMENTATION_REVIEW | `sdd.7b-implementation-review.prompt.md` | Yes |
| POST_REVIEW | `sdd.8-post-implementation-review.prompt.md` | Yes |

### Stages without prompt_template (4 stages)

| Stage | Reason |
|-------|--------|
| BUSINESS_PROBLEM | Optional stage, no standardized prompt |
| TEST | Uses general test execution |
| ACCEPTANCE_TEST | Uses general test execution |
| COMPLETE | Terminal stage, no execution |

### Current SDD Prompt Files (10 files + README)

All files follow naming pattern: `sdd.{N}-{description}.prompt.md`

```
.agent/commands/sdd/
├── README.md
├── sdd.0-initialize.prompt.md
├── sdd.1-create-feature-spec.prompt.md
├── sdd.2-review-spec.prompt.md
├── sdd.3-research-feature.prompt.md
├── sdd.4-determine-test-strategy.prompt.md
├── sdd.5-task-planner-for-feature.prompt.md
├── sdd.6-review-plan.prompt.md
├── sdd.7-task-implementer-for-feature.prompt.md
├── sdd.7b-implementation-review.prompt.md
└── sdd.8-post-implementation-review.prompt.md
```

---

*Document created: 2026-03-02*  
*Stage: BUSINESS_PROBLEM*  
*Next stage: SPEC*
