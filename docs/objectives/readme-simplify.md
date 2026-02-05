# TeamBot Objective: Simplify README.md

## Objective

**Goal**: Restructure the README.md from a monolithic 850+ line document into a concise overview with links to detailed documentation in separate files.

**Problem Statement**: The current README.md is overwhelming for new users. It contains detailed information about every aspect of TeamBot—from quick start to configuration, workflow stages, troubleshooting, and development—all in one file. This makes it difficult to find specific information and intimidating for first-time users. A simplified README with linked documentation will improve discoverability and user experience.

**Success Criteria**:
- [ ] README.md is reduced to ~100-150 lines
- [ ] README.md contains only: project description, key features (brief), prerequisites, quick start, and navigation links
- [ ] All detailed documentation is preserved in separate files under `docs/`
- [ ] Each documentation file is self-contained and focused on one topic
- [ ] All links from README.md to docs are valid and working
- [ ] No information is lost during the restructuring

---

## Technical Context

**Target Codebase**: `/workspaces/teambot/`

**Primary Files**:
- `README.md` (source - to be simplified)
- `docs/` (destination - for detailed documentation)

**Testing Preference**: Manual verification of links and content completeness

**Key Constraints**:
- Preserve all existing information—move, don't delete
- Maintain consistent markdown formatting
- Use relative links for cross-referencing
- Ensure docs work on GitHub (standard markdown)

---

## Proposed Documentation Structure

### Simplified README.md (~100-150 lines)
Should contain:
1. Project title and badges
2. One-paragraph description of what TeamBot is
3. Key features (bullet list, 1 line each)
4. Prerequisites (brief)
5. Quick installation and first run
6. Links to detailed documentation
7. License and contributing (brief with links)

### New Documentation Files in `docs/`

Create a new subfolder `docs/guides/` for detailed documentation:

| File | Content (from current README sections) |
|------|----------------------------------------|
| `docs/guides/getting-started.md` | Detailed installation, init, first run |
| `docs/guides/file-based-orchestration.md` | Running objectives, execution flow, resume |
| `docs/guides/interactive-mode.md` | REPL, pipelines, multi-agent, $ref syntax |
| `docs/guides/cli-reference.md` | All CLI commands with full options |
| `docs/guides/agent-personas.md` | All 6 personas with detailed capabilities |
| `docs/guides/workflow-stages.md` | 13-stage workflow, stage details, review process |
| `docs/guides/configuration.md` | teambot.json, stages.yaml, model config |
| `docs/guides/objective-format.md` | Objective file schema, SDD template |
| `docs/guides/shared-workspace.md` | .teambot/ directory structure, history files |
| `docs/guides/development.md` | Dev setup, project structure, testing |
| `docs/guides/troubleshooting.md` | Common issues and solutions |

---

## Implementation Approach

### Phase 1: Create Documentation Files
1. Create `docs/guides/` directory
2. Extract each section from README.md into its respective guide file
3. Add proper headings and navigation links to each file

### Phase 2: Simplify README.md
1. Reduce to essential quick-start content
2. Add "Documentation" section with links to all guides
3. Keep badges and brief feature list

### Phase 3: Validation
1. Verify all links work
2. Confirm no content was lost
3. Review for consistency

---

## Additional Context

### Current README.md Sections to Relocate

| Current Section | Target File |
|-----------------|-------------|
| Table of Contents | Remove (README too small to need) |
| Quick Start (expanded) | `getting-started.md` |
| File-Based Orchestration | `file-based-orchestration.md` |
| Interactive Mode | `interactive-mode.md` |
| CLI Commands | `cli-reference.md` |
| Agent Personas | `agent-personas.md` |
| Prescriptive Workflow | `workflow-stages.md` |
| Configuration | `configuration.md` |
| Objective File Format | `objective-format.md` |
| Shared Workspace | `shared-workspace.md` |
| Development | `development.md` |
| Troubleshooting | `troubleshooting.md` |
| Dependencies | Merge into `getting-started.md` |

### Example Simplified README Structure

```markdown
# TeamBot

Autonomous AI Agent Teams for Software Development

[badges]

## What is TeamBot?

One paragraph description.

## Key Features

- Feature 1
- Feature 2
- ...

## Quick Start

\`\`\`bash
# 4-5 lines only
\`\`\`

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | ... |
| [Interactive Mode](docs/guides/interactive-mode.md) | ... |
| ... | ... |

## License

MIT - see [LICENSE](LICENSE)

## Contributing

See [Contributing Guide](docs/guides/development.md#contributing)
```

---

## Notes

- The `docs/feature-specs/` directory already exists for feature specifications
- The `docs/objectives/` directory is for SDD objective files
- The new `docs/guides/` directory will be for user documentation
- Ensure the AGENTS.md file is updated if it references README sections
