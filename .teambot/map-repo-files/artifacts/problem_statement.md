# Business Problem Statement: TeamBot Init Scaffolding

## Problem Definition

**Current State:**
When users run `teambot init` to configure a repository for TeamBot, the command only creates:
- `teambot.json` (configuration file)
- `.teambot/` directory structure (history, state subdirectories)

The command does **not** copy essential scaffolding files that TeamBot's orchestration system requires to function. Users must manually locate and copy these files from the installed package or documentation, creating friction in the onboarding experience.

**Required Files Currently Missing from Init:**
| File/Directory | Purpose |
|----------------|---------|
| `stages.yaml` | Defines the 14-stage workflow state machine |
| `.github/agents/` | Contains 6 agent persona definitions (pm, ba, writer, builders, reviewer) |
| `.agent/` | Commands, instructions, and standards for agent operations |
| `AGENTS.md` | Repository-level agent documentation |
| `docs/sdd-objective-template.md` | Template for creating SDD objectives |

**Impact:**
- Users cannot use TeamBot's full workflow orchestration without manual setup
- First-run experience requires tribal knowledge of what files to copy
- Inconsistent project scaffolding across repositories
- Increased support burden explaining missing file requirements

---

## Business Goals

1. **Seamless First-Run Experience** - A single `teambot init` command fully configures a repository for TeamBot workflows
2. **Zero Manual File Copying** - All required scaffolding is automatically placed in the correct locations
3. **Safe Re-Initialization** - Running `init` multiple times never destroys user customizations
4. **Cross-Platform Compatibility** - Works identically on Windows, Linux, and macOS
5. **Transparent Operations** - Users see clear feedback about what was created vs. skipped

---

## Success Criteria

| ID | Criterion | Measurable Outcome |
|----|-----------|-------------------|
| SC-1 | `stages.yaml` is copied to repo root | File exists after init; skipped if present |
| SC-2 | Agent definitions populated | `.github/agents/` contains all 6 agent files |
| SC-3 | Agent standards installed | `.agent/` directory structure copied |
| SC-4 | SDD template available | `docs/sdd-objective-template.md` exists |
| SC-5 | AGENTS.md present | Root-level documentation file exists |
| SC-6 | Idempotent behavior | Existing files never overwritten |
| SC-7 | Clear user feedback | Console shows "Copied: X" or "Skipped: X (exists)" for each item |
| SC-8 | pip/uvx compatibility | Works when TeamBot installed as package (not cloned repo) |

---

## Stakeholders

| Role | Interest |
|------|----------|
| **New Users** | Quick, error-free setup experience |
| **Existing Users** | Re-running init doesn't break customizations |
| **Package Maintainers** | Resources properly bundled with distribution |
| **CI/CD Pipelines** | Predictable init behavior in automated setups |

---

## Constraints

1. **Additive Only** - Must not change existing init behavior; purely extends functionality
2. **Standard Library** - Use Python's `shutil`, `pathlib` for file operations
3. **Package Resources** - Files must be accessible via `importlib.resources` when pip-installed
4. **No External Dependencies** - Cannot add new package dependencies for this feature

---

## Assumptions

1. All source files exist in the TeamBot package at predictable paths
2. Users have write permissions to their repository root
3. Partial copying (some files exist, others don't) is a valid scenario
4. `.github/agents/` directory being empty is treated same as not existing

---

## Dependencies

- `pyproject.toml` must include resource files in package distribution
- Build system (hatchling) must bundle non-Python files correctly

---

## Out of Scope

- Updating existing files to newer versions (upgrade path)
- Interactive prompts for selective file copying
- Rollback/undo functionality
- Template customization during init

---

## Acceptance Test Scenarios

### Scenario 1: Fresh Repository
**Given** a repository with no TeamBot files  
**When** user runs `teambot init`  
**Then** all scaffolding files are copied and `teambot.json` is created

### Scenario 2: Re-initialization
**Given** a repository already initialized with TeamBot  
**When** user runs `teambot init`  
**Then** existing files are preserved, only missing files are copied

### Scenario 3: Partial Initialization
**Given** a repository with only `stages.yaml` present  
**When** user runs `teambot init`  
**Then** `stages.yaml` is skipped, all other files are copied

### Scenario 4: Package Installation
**Given** TeamBot installed via `pip install teambot`  
**When** user runs `teambot init` in any directory  
**Then** scaffolding files are correctly copied from package resources

---

*Document Version: 1.0*  
*Stage: BUSINESS_PROBLEM*  
*Next Stage: SPEC (Feature Specification)*
