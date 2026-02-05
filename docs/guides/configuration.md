# Configuration

TeamBot configuration is managed through `teambot.json` and `stages.yaml`.

## teambot.json

Main configuration file created by `teambot init`:

```json
{
  "teambot_dir": ".teambot",
  "default_agent": "pm",
  "stages_config": "stages.yaml",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager"
    },
    {
      "id": "builder-1",
      "persona": "builder",
      "display_name": "Builder (Primary)"
    },
    {
      "id": "builder-2",
      "persona": "builder",
      "display_name": "Builder (Secondary)"
    }
  ]
}
```

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `teambot_dir` | string | No | Directory for TeamBot workspace (default: `.teambot`) |
| `default_agent` | string | No | Default agent for plain text input in interactive mode |
| `default_model` | string | No | Default AI model for all agents (can be overridden per-agent) |
| `stages_config` | string | No | Path to stages configuration file |
| `agents` | array | Yes | List of agent configurations |

### Default Agent

When `default_agent` is configured, plain text input without `@agent` or `/command` prefixes is automatically routed to the specified agent.

**Example:**
```json
{
  "default_agent": "pm",
  "agents": [...]
}
```

With this configuration:
- `Create a project plan` → routes to `@pm`
- `@ba Analyze requirements` → routes to `@ba` (explicit override)
- `/help` → system command (not affected)

### Agent Configuration

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique agent identifier |
| `persona` | string | Persona type |
| `display_name` | string | Human-readable name for UI |
| `model` | string | AI model for this agent (optional) |

## Model Configuration

TeamBot supports configuring which AI model each agent uses. Models can be set at multiple levels with the following priority (highest to lowest):

1. **Inline override**: `@pm --model gpt-5 create a plan`
2. **Session override**: `/model @pm gpt-5-mini` (lasts for current session)
3. **Agent config**: `model` field in agent definition
4. **Global default**: `default_model` field in teambot.json
5. **SDK default**: If none specified, uses Copilot SDK default

**Example configuration:**
```json
{
  "default_model": "claude-sonnet-4",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "model": "claude-opus-4.5"
    },
    {
      "id": "builder-1", 
      "persona": "builder"
    }
  ]
}
```

In this example:
- `pm` uses `claude-opus-4.5` (agent-specific)
- `builder-1` uses `claude-sonnet-4` (falls back to default_model)

**Interactive commands:**
- `/models` - List all available models
- `/model` - Show current session overrides
- `/model @agent <model>` - Set model for agent in current session
- `/model @agent clear` - Clear session override

## Stage Configuration (stages.yaml)

The workflow stages are configured in `stages.yaml`. This file defines which agents run at each stage, required artifacts, and exit criteria.

```yaml
stages:
  SPEC:
    name: Specification
    description: Create detailed feature specification
    work_agent: ba
    review_agent: reviewer
    allowed_personas:
      - business_analyst
      - ba
    artifacts:
      - feature_spec.md
    exit_criteria:
      - Complete specification with all required sections
    optional: false

  SPEC_REVIEW:
    name: Spec Review
    description: Review and approve the feature specification
    work_agent: ba
    review_agent: reviewer
    is_review_stage: true
    artifacts:
      - spec_review.md

stage_order:
  - SETUP
  - BUSINESS_PROBLEM
  - SPEC
  - SPEC_REVIEW
  # ... remaining stages

work_to_review_mapping:
  SPEC: SPEC_REVIEW
  PLAN: PLAN_REVIEW
```

### Stage Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name for the stage |
| `description` | string | Description of what the stage does |
| `work_agent` | string | Agent ID for work tasks |
| `review_agent` | string \| null | Agent ID for review tasks |
| `allowed_personas` | list | Personas allowed to work on this stage |
| `artifacts` | list | Files produced by this stage |
| `exit_criteria` | list | Conditions to complete the stage |
| `optional` | bool | Whether the stage can be skipped (default: false) |
| `is_review_stage` | bool | Whether this is a review gate (default: false) |
| `parallel_agents` | list | Agents that run in parallel |
| `prompt_template` | string \| null | Path to SDD prompt template |
| `include_objective` | bool | Include objective content in context (default: true) |

### Prompt Templates

The `prompt_template` field allows stages to use specialized prompt files from `.agent/commands/sdd/`.

**Available SDD Prompts:**

| Stage | Prompt File | Description |
|-------|-------------|-------------|
| SETUP | `sdd.0-initialize.prompt.md` | Project initialization |
| SPEC | `sdd.1-create-feature-spec.prompt.md` | Feature specification creation |
| SPEC_REVIEW | `sdd.2-review-spec.prompt.md` | Specification review |
| RESEARCH | `sdd.3-research-feature.prompt.md` | Technical research |
| TEST_STRATEGY | `sdd.4-determine-test-strategy.prompt.md` | Test approach planning |
| PLAN | `sdd.5-task-planner-for-feature.prompt.md` | Task breakdown |
| PLAN_REVIEW | `sdd.6-review-plan.prompt.md` | Plan review |
| IMPLEMENTATION | `sdd.7-task-implementer-for-feature.prompt.md` | Code implementation |
| POST_REVIEW | `sdd.8-post-implementation-review.prompt.md` | Final review |

### The `include_objective` Flag

Set `include_objective: false` for stages that don't need the objective document:

```yaml
SETUP:
  name: Setup
  prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
  include_objective: false  # Generic setup doesn't need objective

SPEC:
  name: Specification
  prompt_template: .agent/commands/sdd/sdd.1-create-feature-spec.prompt.md
  include_objective: true   # Needs objective to create spec
```

### Customizing the Workflow

1. Copy `stages.yaml` to your project
2. Modify stages, agents, or add custom exit criteria
3. Point to it in `teambot.json`:
   ```json
   {
     "stages_config": "path/to/custom-stages.yaml"
   }
   ```

If no `stages.yaml` exists, TeamBot uses built-in defaults.

---

## Next Steps

- [Workflow Stages](workflow-stages.md) - Stage details
- [Agent Personas](agent-personas.md) - Configuring agents
- [CLI Reference](cli-reference.md) - Command options
