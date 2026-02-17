## Objective

- Enhance `teambot init` to automatically set up prerequisite files for file-based orchestration and agent workflows.

**Goal**:

- Ensure that when `teambot init` is run, the repository is fully configured to use TeamBot's file-based orchestration and agent personas without requiring manual file copying
- Provide a seamless first-run experience where all required scaffolding is in place
- Preserve user customizations by only copying files that don't already exist

**Problem Statement**:

- Currently, `teambot init` only creates the `teambot.json` config and `.teambot/` directory structure
- Users must manually set up `stages.yaml`, agent definitions, and SDD prompts to use file-based orchestration
- This manual process is error-prone and creates friction for new users
- There's no automated way to bootstrap a repository with the complete TeamBot workflow

**Success Criteria**:

- [ ] `teambot init` copies `stages.yaml` to the repository root if not already present
- [ ] `teambot init` copies all agent definitions from `.github/agents/` if that directory doesn't exist or is empty
- [ ] `teambot init` copies the `.agent/` directory (commands, instructions, standards) if not already present
- [ ] `teambot init` copies `docs/sdd-objective-template.md` if not already present
- [ ] `teambot init` copies `AGENTS.md` to repository root if not already present
- [ ] Each file/directory copy operation is conditional - only copy if target doesn't exist
- [ ] Existing files are never overwritten (safe for re-running init)
- [ ] Clear console output indicates which files were copied vs. skipped
- [ ] Documentation is updated to reflect the enhanced init behavior

**Non-Goals** (explicitly out of scope):

- Merging or updating existing configuration files
- Providing interactive prompts to select which files to copy
- Version migration or upgrade logic for existing files
- Checking for partial/corrupt files (presence check is sufficient)

---

## Technical Context

**Target Codebase**:

- `src/teambot/cli.py` - Main CLI entry point containing `cmd_init()` function
- `src/teambot/config/` - Configuration loading and defaults

**Primary Language/Framework**:

- Python (existing codebase)

**Testing Preference**:

- Test-Driven Development (TDD) - write tests for file copying behavior first

**Key Constraints**:

- Must work when installed via pip/uvx (source files bundled with package)
- Must not break existing init behavior (additive enhancement only)
- Must handle cross-platform file paths (Windows, Linux, macOS)
- File copying should use appropriate Python standard library methods

---

## Source Files to Copy

The following files from the TeamBot package should be copied to the user's repository:

### 1. Stages Configuration

| Source (Package) | Destination (User Repo) |
|------------------|-------------------------|
| `stages.yaml` | `./stages.yaml` |

### 2. Agent Definitions

| Source (Package) | Destination (User Repo) |
|------------------|-------------------------|
| `.github/agents/ba.agent.md` | `./.github/agents/ba.agent.md` |
| `.github/agents/builder-1.agent.md` | `./.github/agents/builder-1.agent.md` |
| `.github/agents/builder-2.agent.md` | `./.github/agents/builder-2.agent.md` |
| `.github/agents/pm.agent.md` | `./.github/agents/pm.agent.md` |
| `.github/agents/reviewer.agent.md` | `./.github/agents/reviewer.agent.md` |
| `.github/agents/writer.agent.md` | `./.github/agents/writer.agent.md` |

### 3. Agent Directory (SDD Prompts & Instructions)

| Source (Package) | Destination (User Repo) |
|------------------|-------------------------|
| `.agent/commands/` | `./.agent/commands/` |
| `.agent/instructions/` | `./.agent/instructions/` |
| `.agent/standards/` | `./.agent/standards/` |

### 4. SDD Objective Template

| Source (Package) | Destination (User Repo) |
|------------------|-------------------------|
| `docs/sdd-objective-template.md` | `./docs/sdd-objective-template.md` |

### 5. AGENTS.md Instructions

| Source (Package) | Destination (User Repo) |
|------------------|-------------------------|
| `AGENTS.md` | `./AGENTS.md` |

**Note**: This file contains essential instructions that enable clean operation for TeamBot, including project context and conventions that agents reference during execution.

---

## Implementation Notes

### Package Data Access

When TeamBot is installed via pip/uvx, the scaffold files must be bundled with the package from their **existing locations** (single source of truth - no duplication in the repository).

**Approach**: Configure `pyproject.toml` to include files from their current repo locations, mapping them to a destination path inside the installed package:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/teambot"]

# Map repo files → package location (no repo duplication)
# Left side = source path in repo
# Right side = destination path in installed package
[tool.hatch.build.targets.wheel.force-include]
"stages.yaml" = "teambot/init_scaffold/stages.yaml"
"AGENTS.md" = "teambot/init_scaffold/AGENTS.md"
".github/agents" = "teambot/init_scaffold/.github/agents"
".agent" = "teambot/init_scaffold/.agent"
"docs/sdd-objective-template.md" = "teambot/init_scaffold/docs/sdd-objective-template.md"
```

**Clarification**: 
- **No new directories in the repo** - files stay at their current locations
- `init_scaffold/` only exists inside the built wheel/installed package
- At runtime, `importlib.resources` accesses the packaged files:

```python
from importlib import resources

# Access files from installed package (not from repo)
init_files = resources.files("teambot").joinpath("init_scaffold")
stages_yaml = init_files.joinpath("stages.yaml")
```

**Key principle**: Single source of truth in repo. Build process copies files into the package structure.

**Build Flow Diagram**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEAMBOT REPOSITORY                                  │
│                     (single source of truth)                                │
│                                                                             │
│  ├── AGENTS.md                    ← maintained here                         │
│  ├── stages.yaml                  ← maintained here                         │
│  ├── .agent/                      ← maintained here                         │
│  ├── .github/agents/              ← maintained here                         │
│  ├── docs/sdd-objective-template.md                                         │
│  └── src/teambot/                 ← Python code                             │
│                                                                             │
│  NO init_scaffold/ directory exists here!                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  uv build / pip wheel
                                    │  (pyproject.toml force-include)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BUILT WHEEL (teambot-x.y.z.whl)                          │
│                                                                             │
│  teambot/                                                                   │
│  ├── __init__.py                                                            │
│  ├── cli.py                                                                 │
│  ├── ...                                                                    │
│  └── init_scaffold/               ← created during build, NOT in repo       │
│      ├── AGENTS.md                                                          │
│      ├── stages.yaml                                                        │
│      ├── .agent/                                                            │
│      ├── .github/agents/                                                    │
│      └── docs/sdd-objective-template.md                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  pip install / uvx
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      USER'S PROJECT (after teambot init)                    │
│                                                                             │
│  ├── AGENTS.md                    ← copied from package                     │
│  ├── stages.yaml                  ← copied from package                     │
│  ├── .agent/                      ← copied from package                     │
│  ├── .github/agents/              ← copied from package                     │
│  ├── docs/sdd-objective-template.md                                         │
│  ├── teambot.json                 ← created by init                         │
│  └── .teambot/                    ← created by init                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Summary**: One copy in repo → packaged into wheel at build time → copied to user's project at init time.

### File Copy Logic

Pseudocode for the conditional copy behavior:

```python
def copy_if_not_exists(src: Path, dst: Path) -> bool:
    """Copy source to destination if destination doesn't exist.
    
    Returns True if copied, False if skipped.
    """
    if dst.exists():
        return False  # Skipped
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True
```

### Console Output

Example output during init:

```
✓ Created teambot.json
✓ Created .teambot/ directory
✓ Copied stages.yaml
✓ Copied .github/agents/ (6 files)
✓ Copied .agent/ directory
  - commands/ (9 files)
  - instructions/ (2 files)
  - standards/ (1 file)
✓ Copied docs/sdd-objective-template.md
✓ Copied AGENTS.md
```

Or if files already exist:

```
✓ Created teambot.json
✓ Created .teambot/ directory
⊘ Skipped stages.yaml (already exists)
⊘ Skipped .github/agents/ (already exists)
⊘ Skipped .agent/ (already exists)
⊘ Skipped docs/sdd-objective-template.md (already exists)
⊘ Skipped AGENTS.md (already exists)
```

---

## Acceptance Test Scenarios

### Scenario 1: Fresh Repository (No Existing Files)

**Given**: A repository with no TeamBot configuration
**When**: User runs `teambot init`
**Then**: 
- `teambot.json` is created
- `.teambot/` directory is created
- `stages.yaml` is copied
- `.github/agents/` is created with all 6 agent files
- `.agent/` is created with all subdirectories
- `docs/sdd-objective-template.md` is copied
- `AGENTS.md` is copied

### Scenario 2: Partial Setup (Some Files Exist)

**Given**: A repository with existing `stages.yaml` but no `.agent/` directory
**When**: User runs `teambot init`
**Then**:
- `stages.yaml` is NOT overwritten
- `.agent/` directory IS copied
- Console shows "Skipped stages.yaml (already exists)"

### Scenario 3: Re-running Init (All Files Exist)

**Given**: A fully configured TeamBot repository
**When**: User runs `teambot init` again
**Then**:
- No files are overwritten
- Console shows all prerequisite files were skipped
- Existing configurations remain unchanged

### Scenario 4: Custom Agent Definitions

**Given**: A repository with custom agent definitions in `.github/agents/`
**When**: User runs `teambot init`
**Then**:
- Custom agent files are preserved
- No TeamBot defaults overwrite user customizations

---

## Tasks Breakdown

### Phase 1: Package Build Configuration

- [ ] Update `pyproject.toml` with `force-include` mappings for scaffold files
- [ ] Verify files are included in built wheel (`uv build && unzip -l dist/*.whl`)
- [ ] Test `importlib.resources` access to scaffold files
- [ ] Verify files are accessible when installed via `pip install` and `uvx`

### Phase 2: File Copy Implementation

- [ ] Create helper function for conditional file copying
- [ ] Create helper function for conditional directory copying
- [ ] Add file copy logic to `cmd_init()` in `cli.py`
- [ ] Implement console output for copy/skip status

### Phase 3: Testing

- [ ] Write unit tests for conditional copy helpers
- [ ] Write integration tests for init with various file states
- [ ] Test cross-platform compatibility (paths, permissions)

### Phase 4: Documentation

- [ ] Update README.md to reflect new init behavior
- [ ] Update installation guide with init details
- [ ] Add troubleshooting section for common issues

---
