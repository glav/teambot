# Problem Statement: AGENTS.md Update for `.agent` Directory Reference

## Business Problem

When users run `teambot init` on an existing repository that already has an `AGENTS.md` file, the `.agent/` directory is copied successfully, but the user's `AGENTS.md` is **not updated** to reflect the availability of this AI-assisted workflow tooling. This creates a **documentation gap** where:

1. Users are unaware of the `.agent/` directory capabilities
2. The SDD workflow commands, instructions, and standards remain undiscoverable
3. AI agents (Copilot CLI) cannot reference the `.agent/` structure in the user's AGENTS.md

## Current State

### Existing Pattern
TeamBot already handles a similar scenario for the objective template:
- When `sdd-objective-template.md` is copied and `AGENTS.md` was skipped (exists)
- `_update_agents_md_with_template_reference()` appends an "Objective Template" section
- Uses idempotent detection (`OBJECTIVE_TEMPLATE_MARKER`) to prevent duplicates
- Handles OSError gracefully with `logging.debug()`

### Gap
No equivalent logic exists for the `.agent/` directory. When `.agent/` is copied successfully but `AGENTS.md` exists (skipped), users don't receive documentation about:
- Commands (4 entries): `azdo`, `docs`, `project`, `setup` slash commands
- SDD workflow (10 entries): The 9-step Spec-Driven Development workflow
- Instructions (6 entries): bash and bicep contextual guidelines
- Standards (5 entries): Templates for decisions, specs, research, and planning

## Goals

| Goal | Measurable Outcome |
|------|-------------------|
| **Discoverability** | AGENTS.md contains full `.agent/` directory reference when directory is copied |
| **Safety** | Existing AGENTS.md content is preserved; no data corruption |
| **Idempotency** | Running `teambot init` multiple times produces same result (no duplicates) |
| **Graceful Handling** | File permission errors logged (debug), do not crash initialization |
| **Consistency** | Follows existing `_update_agents_md_with_template_reference()` pattern |

## Success Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| SC-1 | `teambot init` detects when AGENTS.md exists AND `.agent/` was copied | Unit test |
| SC-2 | When both conditions met, append `.agent` directory reference section | Integration test |
| SC-3 | Reference section matches `src/teambot/scaffolds/AGENTS.md` lines 130-191 | Content comparison |
| SC-4 | Section includes: Commands (4), SDD workflow (10), Instructions (6), Standards (5) | Count verification |
| SC-5 | No duplicate section added on re-run | Idempotency test |
| SC-6 | File permission errors handled gracefully (log warning, no crash) | Exception handling test |
| SC-7 | All existing tests continue to pass | `pytest` passes |
| SC-8 | New tests cover the update logic | Coverage report |

## Stakeholders

| Role | Interest |
|------|----------|
| **End Users** | Can discover and use `.agent/` directory workflows via AGENTS.md |
| **AI Agents** | Have accurate AGENTS.md context for repository interactions |
| **Maintainers** | Consistent pattern for scaffold file updates |

## Constraints

| Constraint | Rationale |
|------------|-----------|
| Must not corrupt existing AGENTS.md | User data preservation is paramount |
| Must be idempotent | Safe to run multiple times without side effects |
| Handle varied AGENTS.md structures | Users may have custom formats |
| Preserve all existing content | Append-only update strategy |
| Follow existing pattern | Code consistency and maintainability |
| Log errors via `logging.debug()` | Consistent with established error handling |

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `src/teambot/cli.py` | Code | Exists - target for enhancement |
| `src/teambot/scaffolds.py` | Code | Exists - provides `CopyResult` data |
| `src/teambot/scaffolds/AGENTS.md` | Data | Exists - canonical content source (lines 130-191) |
| Existing test infrastructure | Testing | Exists - pytest framework ready |

## Assumptions

1. The canonical `.agent/` directory reference content is in `src/teambot/scaffolds/AGENTS.md` lines 130-191
2. The existing `_update_agents_md_with_template_reference()` pattern is the approved approach
3. Content should be appended to the end of AGENTS.md (same as objective template)
4. Case-insensitive marker detection is acceptable (consistent with existing implementation)

## Out of Scope

- Modifying the `.agent/` directory structure itself
- Changing how scaffold directories are copied
- Updating AGENTS.md for other scaffold items
- Custom positioning of the appended section within AGENTS.md

## Business Value

| Benefit | Impact |
|---------|--------|
| **Improved Onboarding** | Users immediately understand available AI workflows |
| **Better AI Integration** | Copilot CLI agents have accurate repository context |
| **Reduced Support** | Self-documenting feature reduces "how do I use .agent?" questions |
| **Consistency** | All scaffold content documented in user's AGENTS.md |
