# Shared Workspace

All agents share the `.teambot/` directory for collaboration, state persistence, and artifact storage.

## Directory Structure

```
.teambot/
├── orchestration_state.json  # Current execution state
├── workflow_state.json       # Workflow progress
├── history/                  # Agent action history
│   └── *.md                  # Timestamped history files
├── failures/                 # Review failure reports
│   └── *.md                  # Detailed failure analysis
└── artifacts/                # Generated artifacts
    ├── spec.md
    ├── plan.md
    └── test-strategy.md
```

## Files

### orchestration_state.json

Tracks the current execution:
- Current stage
- Active agents
- Time elapsed
- Resume information

Used by `--resume` to continue interrupted executions.

### workflow_state.json

Tracks workflow progress:
- Completed stages
- Stage outputs
- Review iterations

### history/

Contains timestamped markdown files for each agent action.

### failures/

Contains detailed reports when review stages fail after 4 iterations.

### artifacts/

Contains generated documents like specifications, plans, and test strategies.

## History Files

Each agent action creates a history file with YAML frontmatter:

```markdown
---
title: Implemented user authentication
timestamp: 2026-01-22T08:30:00
agent_id: builder-1
action_type: task-complete
files_affected:
  - src/auth/login.py
---

## Task
Implement user authentication module.

## Output
Created login endpoint with JWT generation.
```

### Frontmatter Fields

| Field | Description |
|-------|-------------|
| `title` | Brief description of the action |
| `timestamp` | ISO 8601 timestamp |
| `agent_id` | Agent that performed the action |
| `action_type` | Type of action (task-complete, review, etc.) |
| `files_affected` | List of modified files |

## Agent Collaboration

Agents collaborate through the shared workspace:

1. **Artifacts**: One agent produces, others consume
2. **History**: Agents reference previous work
3. **State**: Workflow state coordinates handoffs
4. **Failures**: Review feedback guides revisions

## Cleaning Up

To reset TeamBot state:

```bash
# Remove all state (keeps configuration)
rm -rf .teambot/

# Reinitialize
uv run teambot init
```

To remove only execution state (keep history):

```bash
rm .teambot/orchestration_state.json
rm .teambot/workflow_state.json
```

---

## Next Steps

- [Workflow Stages](workflow-stages.md) - How stages produce artifacts
- [File-Based Orchestration](file-based-orchestration.md) - Execution details
- [Configuration](configuration.md) - Customizing the workspace
