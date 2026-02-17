<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# TeamBot Init Scaffolding - Feature Specification

Version 1.0 | Status DRAFT | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-17 |
| Problem & Users | ✅ | None | 2026-02-17 |
| Scope | ✅ | None | 2026-02-17 |
| Requirements | ✅ | None | 2026-02-17 |
| Metrics & Risks | ✅ | None | 2026-02-17 |
| Operationalization | ✅ | None | 2026-02-17 |
| Finalization | ✅ | None | 2026-02-17 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot is a CLI tool that wraps the GitHub Copilot CLI to enable collaborative, multi-agent AI workflows for software development. The `teambot init` command is the primary entry point for configuring a repository to use TeamBot's file-based orchestration and agent personas.

### Core Opportunity
Enhance `teambot init` to automatically copy all required scaffolding files from the installed package to the target repository, eliminating manual file copying and providing a seamless first-run experience.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Seamless first-run experience | User Experience | Manual 5+ step setup | Single-command setup | v0.2.0 | P0 |
| G-002 | Zero manual file copying required | Efficiency | Users copy 5 resources manually | 0 manual copies | v0.2.0 | P0 |
| G-003 | Safe re-initialization | Data Integrity | N/A (not supported) | Never overwrite existing files | v0.2.0 | P0 |
| G-004 | Cross-platform compatibility | Compatibility | N/A | Works on Windows/Linux/macOS | v0.2.0 | P1 |
| G-005 | Transparent operations | User Experience | Silent operations | Clear feedback per file | v0.2.0 | P1 |

---

## 2. Problem Definition

### Current Situation
When users run `teambot init`, the command creates:
- `teambot.json` (configuration file)
- `.teambot/` directory with `history/` and `state/` subdirectories

The command does **not** copy essential scaffolding files that TeamBot's workflow orchestration requires.

### Problem Statement
Users cannot use TeamBot's full workflow orchestration without manually locating and copying 5 resource sets from the installed package. This creates friction, requires tribal knowledge, and leads to inconsistent project scaffolding across repositories.

### Root Causes
- `cmd_init()` was designed for minimal configuration only
- No mechanism exists to bundle and extract non-Python resources from the package
- `pyproject.toml` does not include `.agent/` or `.github/agents/` in the distribution

### Impact of Inaction
- Users abandon TeamBot due to complex setup requirements
- Support burden increases from explaining missing file requirements
- Inconsistent project configurations cause workflow failures
- Competitive disadvantage against simpler-to-setup alternatives

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **New User** | Quick setup, start using TeamBot immediately | Multi-step manual setup is confusing | High - first impression determines adoption |
| **Existing User** | Re-run init without losing customizations | Fear of losing custom configurations | High - must preserve trust |
| **CI/CD Pipeline** | Predictable, reproducible initialization | Inconsistent state causes failures | Medium - automation reliability |
| **Package Maintainer** | Resources properly bundled in distribution | Missing files in pip installs | High - core functionality |

### User Journey: New User First-Run
1. User installs TeamBot via `pip install teambot` or `uvx install teambot`
2. User navigates to their repository root
3. User runs `teambot init`
4. **Current**: User sees config created but workflows fail due to missing files
5. **Desired**: User sees all scaffolding copied, can immediately run `teambot run`

---

## 4. Scope

### In Scope
- Copy `stages.yaml` to repository root if not present
- Copy `.github/agents/` directory with all 6 agent definitions if not present or empty
- Copy `.agent/` directory tree (commands, instructions, standards) if not present
- Copy `docs/sdd-objective-template.md` if not present (create `docs/` if needed)
- Copy `AGENTS.md` to repository root if not present
- Console output showing copied vs. skipped status for each resource
- Update `pyproject.toml` to bundle resources in package distribution
- TDD tests for all file copying behavior

### Out of Scope (Justified)
- **Upgrade path for existing files**: Requires version tracking and migration strategy (future feature)
- **Interactive prompts for selective copying**: Adds complexity; users can delete unwanted files post-init
- **Rollback/undo functionality**: Users can use git to revert changes
- **Template customization during init**: Configuration-based customization is a separate feature
- **Copying files to non-repository directories**: Only git repositories supported

### Assumptions
1. All source files exist in the TeamBot package at predictable paths relative to `src/teambot/`
2. Users have write permissions to their repository root
3. Partial copying (some files exist, others don't) is a valid scenario requiring graceful handling
4. `.github/agents/` directory being empty is treated same as not existing
5. Hatchling build system can bundle non-Python files using explicit include rules

### Constraints
1. **Additive Only**: Must not change existing `cmd_init()` behavior; purely extends functionality
2. **Standard Library Only**: Use `shutil`, `pathlib`, `importlib.resources`; no new dependencies
3. **Package Resources**: Files must be accessible via `importlib.resources` when pip-installed
4. **Cross-Platform Paths**: All path handling must use `pathlib.Path` for Windows/Linux/macOS compatibility

---

## 5. Product Overview

### Value Proposition
A single `teambot init` command fully configures any repository for TeamBot workflows, requiring zero manual file copying and providing immediate readiness for multi-agent collaboration.

### Differentiators
- Idempotent: Safe to run multiple times without data loss
- Transparent: Clear console feedback shows exactly what happened
- Package-aware: Works correctly whether installed via pip, uvx, or development clone

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Copy stages.yaml | Copy workflow stages configuration to repo root | G-001, G-002 | New User | P0 | File exists at `./stages.yaml` after init; skipped if present | Single file copy |
| FR-002 | Copy agent definitions | Copy all 6 agent persona files to `.github/agents/` | G-001, G-002 | New User | P0 | Directory contains `pm.agent.md`, `ba.agent.md`, `writer.agent.md`, `builder-1.agent.md`, `builder-2.agent.md`, `reviewer.agent.md` | Create `.github/` if needed |
| FR-003 | Copy agent resources | Copy entire `.agent/` directory tree | G-001, G-002 | New User | P0 | `.agent/commands/`, `.agent/instructions/`, `.agent/standards/` exist with all files | Recursive directory copy |
| FR-004 | Copy SDD template | Copy objective template to `docs/sdd-objective-template.md` | G-001, G-002 | New User | P1 | File exists at `./docs/sdd-objective-template.md` | Create `docs/` if needed |
| FR-005 | Copy AGENTS.md | Copy agent documentation to repo root | G-001, G-002 | New User | P1 | File exists at `./AGENTS.md` | Single file copy |
| FR-006 | Conditional copying | Only copy resources that don't already exist | G-003 | Existing User | P0 | Existing files never modified; init returns success | Check before each copy |
| FR-007 | Empty directory handling | Treat empty `.github/agents/` as non-existent | G-003 | Existing User | P1 | If directory exists but is empty, populate it | Edge case handling |
| FR-008 | Console feedback | Display status for each resource (copied/skipped) | G-005 | All | P1 | Each resource shows "✓ Copied: X" or "○ Skipped: X (exists)" | Use Rich console |
| FR-009 | Package resource access | Access bundled files when installed via pip/uvx | G-001 | Package Maintainer | P0 | `importlib.resources` successfully locates all resources | Requires pyproject.toml update |
| FR-010 | Cross-platform paths | Handle file paths correctly on all platforms | G-004 | All | P0 | Tests pass on Windows, Linux, macOS | Use pathlib.Path |

### Feature Hierarchy
```
teambot init (enhanced)
├── Config Creation (existing)
│   ├── teambot.json
│   └── .teambot/ directories
└── Scaffolding Copy (new)
    ├── stages.yaml → ./
    ├── .github/agents/ → ./
    │   ├── pm.agent.md
    │   ├── ba.agent.md
    │   ├── writer.agent.md
    │   ├── builder-1.agent.md
    │   ├── builder-2.agent.md
    │   └── reviewer.agent.md
    ├── .agent/ → ./
    │   ├── commands/
    │   ├── instructions/
    │   └── standards/
    ├── docs/sdd-objective-template.md → ./docs/
    └── AGENTS.md → ./
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Init completes quickly | < 2 seconds for full scaffolding copy | P2 | Time `teambot init` on fresh repo | File I/O bound |
| NFR-002 | Reliability | Init never corrupts existing files | 0 data loss incidents | P0 | Fuzz test with random existing files | Critical for trust |
| NFR-003 | Maintainability | Resource paths defined in single location | 1 configuration source | P1 | Code review | Avoid scattered hardcoding |
| NFR-004 | Compatibility | Works with Python 3.9+ | All supported Python versions | P0 | CI matrix testing | Match project requirements |
| NFR-005 | Observability | Clear error messages on failure | User can diagnose without code inspection | P1 | Review error scenarios | Permission errors, disk full, etc. |
| NFR-006 | Testability | All copy operations have unit tests | 100% coverage of copy logic | P0 | pytest coverage report | TDD approach |

---

## 8. Data & Analytics

### Inputs
- Package resources: `stages.yaml`, `.github/agents/*`, `.agent/**/*`, `docs/sdd-objective-template.md`, `AGENTS.md`
- Target repository path (current working directory)
- Existing file state in target repository

### Outputs / Events
- Copied files in target repository
- Console output with copy status
- No telemetry or analytics events (privacy by design)

### Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Files copied per init | Quantitative | 0 | All missing files | Per invocation | Console output |
| Existing files preserved | Quantitative | N/A | 100% | Per invocation | File integrity check |
| Init success rate | Quantitative | N/A | 100% on valid repos | Post-release | Issue tracker |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| pyproject.toml update | Build Config | Critical | Builder | Resources not bundled in package | Verify wheel contents before release |
| hatchling include rules | Build System | Critical | Builder | Non-Python files excluded | Test pip install from TestPyPI |
| importlib.resources API | Python Stdlib | Critical | Python | API differences across versions | Use `importlib.resources.files()` (3.9+) |
| Rich console library | Display | Low | Existing | Already a dependency | N/A |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Package resources not bundled correctly | High | Medium | Add explicit include rules to pyproject.toml; verify wheel contents in CI | Builder | Open |
| R-002 | Path handling breaks on Windows | High | Low | Use pathlib.Path exclusively; add Windows CI runner | Builder | Open |
| R-003 | Large .agent/ directory increases package size | Low | High | Monitor package size; document expected size increase | Maintainer | Open |
| R-004 | User lacks write permissions | Medium | Low | Catch PermissionError; provide helpful error message | Builder | Open |
| R-005 | Existing partial .agent/ causes confusion | Medium | Medium | Document behavior; copy missing subdirectories only | Builder | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
- **Public**: All copied files are public documentation and configuration
- **No PII**: No personal data collected or processed
- **No Secrets**: Scaffolding files contain no credentials or sensitive data

### PII Handling
N/A - No PII involved in this feature

### Threat Considerations
- **Path Traversal**: Validate all paths stay within target repository
- **Symlink Attacks**: Use `shutil.copytree` with `symlinks=False` (default)
- **Resource Exhaustion**: Limit recursive depth if needed (unlikely given known structure)

### Regulatory / Compliance
N/A - No compliance requirements for documentation file copying

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Included in standard pip/uvx install | No separate deployment |
| Rollback | Users can delete copied files or use git revert | Self-service rollback |
| Monitoring | N/A for CLI tool | No runtime monitoring |
| Alerting | N/A for CLI tool | No alerting needed |
| Support | Document in README and --help | Self-service support |
| Capacity Planning | N/A | Local file operations only |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| TDD Tests | Sprint 1 | All test cases written and initially failing | Builder |
| Implementation | Sprint 1 | All tests passing | Builder |
| Documentation | Sprint 1 | README and help text updated | Writer |
| Release | Sprint 1 | v0.2.0 published to PyPI | Maintainer |

### Feature Flags
N/A - Feature is additive and always enabled

### Communication Plan
- Update README with new init behavior
- Add example output to documentation
- Release notes highlight seamless setup

---

## 14. Acceptance Test Scenarios

### AT-001: Fresh Repository Initialization
**Description**: User runs init on a repository with no TeamBot files
**Preconditions**: 
- Empty git repository (or repo without any TeamBot files)
- TeamBot installed via pip/uvx
**Steps**:
1. User navigates to repository root: `cd /path/to/repo`
2. User runs: `teambot init`
3. User observes console output
4. User verifies files exist
**Expected Result**: 
- `teambot.json` created
- `.teambot/` directory created with subdirectories
- `stages.yaml` copied to root
- `.github/agents/` created with 6 agent files
- `.agent/` directory tree copied
- `docs/sdd-objective-template.md` created
- `AGENTS.md` copied to root
- Console shows "✓ Copied: X" for each resource
**Verification**: 
- `ls -la` shows all expected files
- `teambot status` runs without errors
- `.agent/commands/sdd/` contains expected prompts

### AT-002: Re-initialization Preserves Existing Files
**Description**: User runs init on a repository already configured with TeamBot
**Preconditions**:
- Repository already initialized with `teambot init`
- User has customized `AGENTS.md` with project-specific content
**Steps**:
1. User modifies `AGENTS.md` with custom content
2. User runs: `teambot init`
3. User verifies `AGENTS.md` content unchanged
**Expected Result**:
- `AGENTS.md` retains user's custom content
- Console shows "○ Skipped: AGENTS.md (exists)" 
- All other existing files also preserved
**Verification**:
- `cat AGENTS.md` shows original custom content
- `git status` shows no changes to existing files

### AT-003: Partial Initialization Fills Gaps
**Description**: User runs init on a repository with some TeamBot files present
**Preconditions**:
- Repository has `stages.yaml` and `teambot.json` but nothing else
**Steps**:
1. User runs: `teambot init`
2. User observes console output
3. User verifies new files created, existing preserved
**Expected Result**:
- `stages.yaml` skipped (exists)
- `.github/agents/` created and populated
- `.agent/` copied
- `AGENTS.md` copied
- Console shows mixed "Copied" and "Skipped" messages
**Verification**:
- Original `stages.yaml` unchanged (check timestamp or content)
- New directories contain expected files

### AT-004: Package Installation Resource Access
**Description**: Resources are accessible when TeamBot installed via pip
**Preconditions**:
- Clean Python environment (venv)
- TeamBot not installed from source
**Steps**:
1. Create and activate virtual environment
2. Run: `pip install teambot` (or from TestPyPI for pre-release)
3. Navigate to empty directory
4. Run: `teambot init`
**Expected Result**:
- All scaffolding files copied successfully
- No "resource not found" errors
**Verification**:
- All expected files exist
- File contents match package source

### AT-005: Empty .github/agents/ Directory Handling
**Description**: Init populates an empty agents directory
**Preconditions**:
- Repository has empty `.github/agents/` directory
**Steps**:
1. Create empty `.github/agents/` directory
2. Run: `teambot init`
**Expected Result**:
- Directory populated with 6 agent definition files
- Console shows agents were copied
**Verification**:
- `ls .github/agents/` shows all 6 `.agent.md` files

### AT-006: Cross-Platform Path Handling
**Description**: Init works correctly on Windows, Linux, and macOS
**Preconditions**:
- Access to multiple OS platforms (or CI runners)
**Steps**:
1. Run `teambot init` on each platform
2. Verify file structure created correctly
**Expected Result**:
- Identical file structure on all platforms
- No path separator issues
- No permission errors on any platform
**Verification**:
- CI tests pass on all platform runners

---

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | - | - | - | All resolved |

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-17 | BA Agent | Initial feature specification | Creation |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Problem Statement | `.teambot/map-repo-files/artifacts/problem_statement.md` | Business problem definition | N/A |
| REF-002 | Codebase | `src/teambot/cli.py:190-231` | Current cmd_init() implementation | N/A |
| REF-003 | Codebase | `pyproject.toml` | Current build configuration | N/A |
| REF-004 | Directory | `.github/agents/` | 6 agent definition files to copy | N/A |
| REF-005 | Directory | `.agent/` | Commands, instructions, standards to copy | N/A |

---

## Appendix A: Resource Inventory

### Files to Bundle and Copy

| Source Path (Package) | Target Path (Repository) | Type |
|----------------------|--------------------------|------|
| `resources/stages.yaml` | `./stages.yaml` | Single File |
| `resources/.github/agents/pm.agent.md` | `./.github/agents/pm.agent.md` | Single File |
| `resources/.github/agents/ba.agent.md` | `./.github/agents/ba.agent.md` | Single File |
| `resources/.github/agents/writer.agent.md` | `./.github/agents/writer.agent.md` | Single File |
| `resources/.github/agents/builder-1.agent.md` | `./.github/agents/builder-1.agent.md` | Single File |
| `resources/.github/agents/builder-2.agent.md` | `./.github/agents/builder-2.agent.md` | Single File |
| `resources/.github/agents/reviewer.agent.md` | `./.github/agents/reviewer.agent.md` | Single File |
| `resources/.agent/` | `./.agent/` | Directory Tree |
| `resources/docs/sdd-objective-template.md` | `./docs/sdd-objective-template.md` | Single File |
| `resources/AGENTS.md` | `./AGENTS.md` | Single File |

### pyproject.toml Changes Required

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/teambot"]
include = [
    "src/teambot/**/*.css",
    "src/teambot/resources/**/*",  # Add this line
]
```

*Note: Resources should be placed in `src/teambot/resources/` subdirectory for clean separation.*

---

## Appendix B: Console Output Format

### Successful Fresh Init
```
TeamBot Init

Configuration:
  ✓ Created teambot.json
  ✓ Created .teambot/history/
  ✓ Created .teambot/state/

Scaffolding:
  ✓ Copied: stages.yaml
  ✓ Copied: .github/agents/ (6 files)
  ✓ Copied: .agent/ (3 directories, 45 files)
  ✓ Copied: docs/sdd-objective-template.md
  ✓ Copied: AGENTS.md

✓ Repository initialized successfully!
```

### Re-initialization
```
TeamBot Init

Configuration:
  ○ Skipped: teambot.json (exists, use --force to overwrite)

Scaffolding:
  ○ Skipped: stages.yaml (exists)
  ○ Skipped: .github/agents/ (exists)
  ○ Skipped: .agent/ (exists)
  ○ Skipped: docs/sdd-objective-template.md (exists)
  ○ Skipped: AGENTS.md (exists)

✓ Repository already initialized. No changes made.
```

---

## Appendix C: Technical Stack Summary

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| **Language** | Python 3.9+ | Match existing codebase |
| **File Operations** | `shutil`, `pathlib` | Standard library, cross-platform |
| **Package Resources** | `importlib.resources` | Standard library for accessing bundled files |
| **Build System** | Hatchling | Existing build system |
| **Testing Framework** | pytest | Existing test framework |
| **Testing Approach** | TDD | Per objective requirements |
| **Console Output** | Rich | Existing dependency |

---

VALIDATION_STATUS: PASS
- Placeholders: 0 remaining
- Sections Complete: 17/17
- Technical Stack: DEFINED (Python 3.9+, shutil, pathlib, importlib.resources)
- Testing Approach: DEFINED (TDD)
- Acceptance Tests: 6 scenarios defined

<!-- markdown-table-prettify-ignore-end -->
