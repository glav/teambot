# Problem Statement: AGENTS.md Objective Template Reference

## Business Problem

### Current State

When users run `teambot init` in their repositories, the command copies scaffold files including:
1. `teambot.json` - Configuration file
2. `stages.yaml` - Workflow stage definitions
3. `AGENTS.md` - Repository documentation for AI agents
4. `docs/sdd-objective-template.md` - Template for defining TeamBot objectives

The `sdd-objective-template.md` is a valuable resource that helps users structure their development objectives for TeamBot's multi-agent workflow. However, **users who already have an existing AGENTS.md file do not receive any indication that this template exists or how to use it**.

### Problem

1. **Discoverability Gap**: When `AGENTS.md` already exists (skipped during init), users miss the connection between their AGENTS.md and the newly copied objective template.

2. **Documentation Gap**: The bundled scaffold `AGENTS.md` template documents the objective template, but users with pre-existing AGENTS.md files never see this documentation.

3. **Onboarding Friction**: New users to an existing TeamBot project may not know that `docs/sdd-objective-template.md` exists or how to use it with `teambot run`.

### Impact

- Users don't leverage the objective template, leading to inconsistent objective file formats
- Teams miss the structured approach to defining development tasks
- AI agents receive poorly formatted objectives, reducing workflow effectiveness

---

## Business Goals

| # | Goal | Measurable Outcome |
|---|------|-------------------|
| 1 | **Improve template discoverability** | When AGENTS.md exists AND objective template is copied, AGENTS.md is updated with template reference |
| 2 | **Maintain data integrity** | Existing AGENTS.md content is fully preserved; only additive changes |
| 3 | **Ensure idempotency** | Running `teambot init` multiple times does not create duplicate references |
| 4 | **Document TeamBot's own template** | This repository's AGENTS.md includes the "Objective Template" section |

---

## Stakeholders

| Stakeholder | Need |
|-------------|------|
| **End Users** | Discover and use the objective template without manual exploration |
| **Project Teams** | Consistent objective format across team members |
| **AI Agents** | Well-structured objectives for better workflow execution |
| **TeamBot Maintainers** | Self-documenting repository with accurate AGENTS.md |

---

## Scope

### In Scope

1. Detect when AGENTS.md exists during `teambot init`
2. Detect when `sdd-objective-template.md` was successfully copied
3. Append/update AGENTS.md with objective template reference section
4. Prevent duplicate references on repeated init runs
5. Update TeamBot repository's own AGENTS.md to document the template
6. Update bundled scaffold AGENTS.md with template documentation

### Out of Scope

- Modifying other scaffold files
- Interactive prompts asking user permission to update AGENTS.md
- Complex AGENTS.md parsing/restructuring
- Updating AGENTS.md when objective template was NOT copied

---

## Success Criteria

| # | Criterion | Validation Method |
|---|-----------|-------------------|
| 1 | `teambot init` detects existing AGENTS.md + copied template | Unit test |
| 2 | AGENTS.md updated with template location and purpose | Integration test |
| 3 | Existing AGENTS.md content preserved completely | Comparison test |
| 4 | Duplicate reference prevention works | Idempotency test |
| 5 | TeamBot's AGENTS.md documents `docs/sdd-objective-template.md` | File inspection |
| 6 | All existing tests pass | Test suite run |
| 7 | New tests cover AGENTS.md update logic | Coverage report |

---

## Assumptions

1. AGENTS.md files use markdown format
2. Adding a new section at the end of AGENTS.md is acceptable behavior
3. A simple string-based check for existing template references is sufficient
4. Users expect `teambot init` to be additive, not destructive

## Dependencies

- `src/teambot/scaffolds.py` - Scaffold copy logic (provides copy results)
- `src/teambot/cli.py` - `cmd_init()` function (orchestrates initialization)
- Existing test infrastructure in `tests/`

## Risks

| Risk | Mitigation |
|------|-----------|
| Corrupting existing AGENTS.md | Read-only analysis first; append only; comprehensive tests |
| Breaking on unusual AGENTS.md formats | Simple append strategy; don't parse existing structure |
| Duplicate references | Check for marker text before appending |

---

## Acceptance Criteria (User Stories)

### US-1: Auto-Update Existing AGENTS.md

**As a** user running `teambot init` in a repository with an existing AGENTS.md  
**When** the sdd-objective-template.md is successfully copied  
**Then** my AGENTS.md is updated with a section documenting the template's location and usage  
**And** my existing AGENTS.md content remains unchanged  

### US-2: Idempotent Updates

**As a** user running `teambot init` multiple times  
**When** AGENTS.md already contains the objective template reference  
**Then** no duplicate reference is added  
**And** the command completes successfully  

### US-3: Repository Self-Documentation

**As a** TeamBot contributor  
**When** I read the repository's AGENTS.md  
**Then** I see documentation for `docs/sdd-objective-template.md` in the Objective Template section  

---

## Definition of Done

- [ ] Feature implementation complete
- [ ] All existing tests pass
- [ ] New unit tests for AGENTS.md detection logic
- [ ] New integration tests for update behavior
- [ ] Idempotency tests pass
- [ ] TeamBot repository AGENTS.md updated
- [ ] Bundled scaffold AGENTS.md updated
- [ ] Code reviewed and approved
