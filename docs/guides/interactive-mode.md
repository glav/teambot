# Interactive Mode

For ad-hoc tasks without an objective file, TeamBot provides an interactive REPL:

```bash
uv run teambot run
```

## Basic Commands

```bash
# Send a task to an agent
teambot: @pm Create a project plan for the new feature

# Check agent status
teambot: /status

# Get help
teambot: /help
```

## Pipelines with Dependencies

Use `->` to chain tasks where each depends on the previous output:

```bash
# Two-stage pipeline: plan then implement
teambot: @pm Create a plan for user authentication -> @builder-1 Implement based on this plan

# Three-stage pipeline: requirements -> implementation -> review
teambot: @ba Write requirements for the API -> @builder-1 Implement this API -> @reviewer Review the implementation
```

The output from each stage is automatically injected into the next agent's context:

```
# Stage 1: @ba produces requirements
=== @ba ===
Requirements: 1. REST API endpoint...

# Stage 2: @builder-1 receives @ba's output
[Context: "=== Output from @ba ===\n{requirements}\n\n=== Your Task ===\nImplement this API"]
Implementation complete...

# Stage 3: @reviewer receives @builder-1's output
[Context includes implementation from @builder-1]
Code review feedback...
```

## Multi-Agent Same Prompt

Use `,` to send the same prompt to multiple agents simultaneously:

```bash
# Ask multiple agents to analyze the same thing
teambot: @pm,ba,writer Analyze the requirements for the login feature
```

All agents work in parallel and results are combined:

```
=== @pm ===
From a project management perspective...

=== @ba ===
The business requirements include...

=== @writer ===
Documentation needs for this feature...
```

## Combined Syntax

Combine `,` and `->` for complex workflows:

```bash
# Multiple analysts work in parallel, then results go to builder
teambot: @pm,ba Analyze the feature -> @builder-1 Implement based on analysis
```

## Task Management

```bash
# List all tasks
teambot: /tasks

# View task details
teambot: /task 1

# Cancel a task
teambot: /cancel 1
```

## Syntax Quick Reference

| Syntax | Description | Example |
|--------|-------------|---------|
| `@agent task` | Single agent task | `@pm Create a plan` |
| `@a,b,c task` | Multi-agent parallel, same prompt | `@pm,ba,writer Analyze feature` |
| `@a task -> @b task` | Pipeline with dependency | `@pm Plan -> @builder-1 Implement` |
| `@a,b t1 -> @c t2` | Parallel then pipeline | `@pm,ba Analyze -> @builder-1 Build` |
| `@a task $b` | Reference agent output | `@pm Summarize $ba` |
| `/tasks` | List all tasks | |
| `/task <id>` | View task details | `/task 1` |
| `/cancel <id>` | Cancel task | `/cancel 3` |
| `/status` | Show agent status | |

## Shared Context References (`$agent`)

Reference another agent's most recent output using `$agent` syntax:

```bash
# Reference PM's last output
teambot: @builder-1 Implement based on $pm

# Reference multiple agents
teambot: @reviewer Check $builder-1 against $pm requirements

# Wait for running task
teambot: @pm Summarize $ba  # Waits if @ba is still running
```

**How It Works**:
1. Parser detects `$agent` references in your prompt
2. If referenced agent has a running task, waits for completion
3. Referenced agent's latest output is prepended to your prompt
4. Your agent receives full context automatically

## Comparing `$ref` vs `->` Syntax

| Feature | `$ref` Syntax | `->` Pipeline |
|---------|---------------|---------------|
| **Use Case** | Reference existing output | Chain new tasks |
| **Example** | `@pm Summarize $ba` | `@ba Analyze -> @pm Summarize` |
| **Producer Task** | Uses last completed output | Runs new task |
| **Direction** | Consumer pulls | Producer pushes |
| **Multiple Sources** | `@pm Use $ba and $writer` | `@ba,writer Analyze -> @pm` |
| **Best For** | Building on previous work | Designing new workflows |

**When to Use Which**:
- **`$ref`**: When you want to reference work an agent already completed
- **`->`**: When you want to define a complete workflow from scratch

## Agent Validation

TeamBot validates agent IDs at every entry point. If you reference an unknown agent, you get a clear error listing all valid agents:

```bash
teambot: @designer Create a mockup
# Error: Unknown agent: 'designer'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer
```

This validation applies to all command forms — single agent, multi-agent, pipelines, and `$ref` references.

### Valid Agent IDs

| Agent ID | Aliases |
|----------|---------|
| `pm` | `project_manager` |
| `ba` | `business_analyst` |
| `writer` | `technical_writer` |
| `builder-1` | — |
| `builder-2` | — |
| `reviewer` | — |

You can use either the short ID or the alias form (e.g., `@project_manager` resolves to `@pm`).

## Multi-Line Input

### Split-Pane Mode (Textual)

In the default split-pane interface, use these key combos to insert newlines without submitting:

| Key Combo | Terminal Support |
|-----------|----------------|
| **Alt+Enter** | Most terminals (recommended) |
| **Ctrl+Enter** | Terminals with CSI u / kitty keyboard protocol |
| **Shift+Enter** | Terminals with CSI u / kitty keyboard protocol |

Press **Enter** alone to submit your input.

> **Tip:** If Shift+Enter or Ctrl+Enter acts like plain Enter, your terminal likely
> doesn't support the [kitty keyboard protocol](https://sw.kovidgoyal.net/kitty/keyboard-protocol/).
> Use **Alt+Enter** instead, or switch to a terminal that supports the protocol
> (kitty, WezTerm, Ghostty, foot, recent iTerm2/Windows Terminal).

### Legacy Mode

In legacy mode (`TEAMBOT_LEGACY_MODE=true`), end a line with `\` to continue on the next line:

```bash
teambot: @builder-1 Implement the login feature \
   ...: with JWT authentication and \
   ...: password hashing using bcrypt
```

## Split-Pane Interface

TeamBot features a split-pane terminal interface (powered by [Textual](https://textual.textualize.io/)):

- **Left pane**: Command input with live agent status display
- **Right pane**: Agent output displayed asynchronously

The interface automatically falls back to legacy (single-pane) mode when:
- `TEAMBOT_LEGACY_MODE=true` environment variable is set
- Terminal width is less than 80 columns
- stdout is not a TTY

---

## Next Steps

- [Agent Personas](agent-personas.md) - The 6 specialized agents
- [CLI Reference](cli-reference.md) - All available commands
- [File-Based Orchestration](file-based-orchestration.md) - Running objectives
