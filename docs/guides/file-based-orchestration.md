# File-Based Orchestration

The primary way to use TeamBot is with objective files. Define your goals in markdown, and TeamBot autonomously executes the 14-stage workflow.

## Running an Objective

```bash
# Run an objective file
uv run teambot run objectives/my-task.md

# Set custom time limit (default: 8 hours)
uv run teambot run objectives/task.md --max-hours 4

# Resume interrupted execution
uv run teambot run --resume
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Review Iteration** | Each review stage iterates up to 4 times until approval |
| **Parallel Builders** | builder-1 and builder-2 execute concurrently during IMPLEMENTATION |
| **Time Limits** | Configurable timeout prevents runaway execution (default: 8 hours) |
| **State Persistence** | State saved on completion, cancellation, or timeout |
| **Progress Display** | Real-time stage and agent status updates |

## Execution Flow

1. Parse objective file (goals, success criteria, constraints)
2. Progress through 14 workflow stages
3. For review stages: iterate until approval or 4 failures
4. Run acceptance tests to validate end-to-end behavior
5. Save state on completion, cancellation, or timeout

## Cancellation & Resume

- Press `Ctrl+C` to gracefully cancel execution
- State is saved automatically to `.teambot/orchestration_state.json`
- Resume later with `uv run teambot run --resume`

## Review Failure Handling

If a review stage fails after 4 iterations:
- Execution stops with error message
- Detailed failure report saved to `.teambot/failures/`
- Report contains all iteration feedback and suggestions

---

## Next Steps

- [Objective Format](objective-format.md) - How to write objective files
- [Workflow Stages](workflow-stages.md) - Understanding the 14-stage workflow
- [Interactive Mode](interactive-mode.md) - Ad-hoc tasks without objectives
