# README Simplification - Implementation Plan

**Objective**: `docs/objectives/readme-simplify.md`  
**Owner**: @builder-1  
**Status**: Ready for Implementation  
**Created**: 2025-02-05

---

## 1. Overview

Restructure the monolithic 850+ line README.md into a concise ~100-150 line overview with detailed documentation moved to `docs/guides/`.

### Reviewer Feedback Incorporated

| Feedback | Action |
|----------|--------|
| Add AGENTS.md update to success criteria | ✓ Added to Phase 3 |
| Consider consolidating 11 guides | ✓ Merging `troubleshooting.md` into `getting-started.md` (10 files total) |

---

## 2. Implementation Tasks

### Phase 1: Create Documentation Files

- [ ] **Task 1.1**: Create `docs/guides/` directory
  - Estimated: 1 min

- [ ] **Task 1.2**: Create `docs/guides/getting-started.md`
  - Content: Installation, prerequisites, init, first run, dependencies
  - Include troubleshooting FAQ section at end
  - Estimated: 15 min

- [ ] **Task 1.3**: Create `docs/guides/file-based-orchestration.md`
  - Content: Running objectives, execution flow, resume functionality
  - Estimated: 10 min

- [ ] **Task 1.4**: Create `docs/guides/interactive-mode.md`
  - Content: REPL, pipelines, multi-agent mode, $ref syntax
  - Estimated: 15 min

- [ ] **Task 1.5**: Create `docs/guides/cli-reference.md`
  - Content: All CLI commands with full options
  - Estimated: 10 min

- [ ] **Task 1.6**: Create `docs/guides/agent-personas.md`
  - Content: All 6 personas with detailed capabilities
  - Estimated: 10 min

- [ ] **Task 1.7**: Create `docs/guides/workflow-stages.md`
  - Content: 13-stage workflow, stage details, review process
  - Estimated: 15 min

- [ ] **Task 1.8**: Create `docs/guides/configuration.md`
  - Content: teambot.json, stages.yaml, model config
  - Estimated: 10 min

- [ ] **Task 1.9**: Create `docs/guides/objective-format.md`
  - Content: Objective file schema, SDD template
  - Estimated: 10 min

- [ ] **Task 1.10**: Create `docs/guides/shared-workspace.md`
  - Content: .teambot/ directory structure, history files
  - Estimated: 10 min

- [ ] **Task 1.11**: Create `docs/guides/development.md`
  - Content: Dev setup, project structure, testing, contributing
  - Estimated: 10 min

### Phase 2: Simplify README.md

- [ ] **Task 2.1**: Create new streamlined README.md structure
  - Keep: Title, badges, brief description, key features (1-line each)
  - Keep: Prerequisites (brief), quick install + first run (5 lines max)
  - Add: Documentation table with links to all guides
  - Keep: License and contributing (with links)
  - Target: 100-150 lines
  - Estimated: 20 min

- [ ] **Task 2.2**: Remove relocated content from README.md
  - Remove: Table of Contents (README too small to need)
  - Remove: Detailed sections (now in guides)
  - Estimated: 10 min

### Phase 3: Validation & Updates

- [ ] **Task 3.1**: Verify all internal links work
  - Check README → docs/guides links
  - Check cross-references within guides
  - Estimated: 10 min

- [ ] **Task 3.2**: Verify no content was lost
  - Compare original README sections to new guide files
  - Estimated: 15 min

- [ ] **Task 3.3**: Update AGENTS.md if needed
  - Check for references to README sections that moved
  - Update any affected references
  - Estimated: 10 min

- [ ] **Task 3.4**: Review for consistency
  - Heading styles, formatting, tone
  - Estimated: 10 min

---

## 3. File Mapping

| Original README Section | Target Guide File |
|------------------------|-------------------|
| Table of Contents | *(removed - README too short)* |
| Quick Start (expanded) | `getting-started.md` |
| Dependencies | `getting-started.md` |
| Troubleshooting | `getting-started.md` (FAQ section) |
| File-Based Orchestration | `file-based-orchestration.md` |
| Interactive Mode | `interactive-mode.md` |
| CLI Commands | `cli-reference.md` |
| Agent Personas | `agent-personas.md` |
| Prescriptive Workflow | `workflow-stages.md` |
| Configuration | `configuration.md` |
| Objective File Format | `objective-format.md` |
| Shared Workspace | `shared-workspace.md` |
| Development | `development.md` |

---

## 4. Target README Structure

```markdown
# TeamBot

[badges]

Autonomous AI Agent Teams for Software Development

## What is TeamBot?

One paragraph description (~3-4 sentences).

## Key Features

- 🤖 6 specialized AI agent personas
- 📋 13-stage prescriptive workflow
- 💬 Interactive REPL mode
- 📁 File-based orchestration
- ⚙️ Configurable stages and models

## Prerequisites

- Python 3.11+
- uv package manager
- GitHub Copilot CLI

## Quick Start

\`\`\`bash
uv sync
uv run teambot init
uv run teambot run objectives/my-task.md
\`\`\`

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation, setup, first run |
| [File-Based Orchestration](docs/guides/file-based-orchestration.md) | Running objectives |
| [Interactive Mode](docs/guides/interactive-mode.md) | REPL and pipelines |
| [CLI Reference](docs/guides/cli-reference.md) | All commands |
| [Agent Personas](docs/guides/agent-personas.md) | The 6 AI agents |
| [Workflow Stages](docs/guides/workflow-stages.md) | 13-stage process |
| [Configuration](docs/guides/configuration.md) | Settings and options |
| [Objective Format](docs/guides/objective-format.md) | Writing objectives |
| [Shared Workspace](docs/guides/shared-workspace.md) | .teambot/ structure |
| [Development](docs/guides/development.md) | Contributing guide |

## License

MIT - see [LICENSE](LICENSE)
```

---

## 5. Acceptance Criteria

- [ ] README.md is 100-150 lines
- [ ] README.md contains only: description, features, prerequisites, quick start, doc links
- [ ] 10 guide files created in `docs/guides/`
- [ ] All links from README to docs are valid
- [ ] No information lost from original README
- [ ] AGENTS.md updated if needed
- [ ] Consistent formatting across all new files

---

## 6. Estimated Effort

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | Create 10 guide files | ~105 min |
| Phase 2 | Simplify README | ~30 min |
| Phase 3 | Validation & updates | ~45 min |
| **Total** | | **~3 hours** |

---

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Broken cross-references | Validate all links manually |
| Missing content | Side-by-side comparison with original |
| AGENTS.md inconsistency | Check and update references |
| Inconsistent formatting | Review pass in Phase 3 |
