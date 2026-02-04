<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Model Selection Support - Feature Specification Document
Version 1.0 | Status **Draft** | Owner TBD | Team TeamBot | Target MVP | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-04 |
| Problem & Users | 100% | None | 2026-02-04 |
| Scope | 100% | None | 2026-02-04 |
| Requirements | 100% | None | 2026-02-04 |
| Metrics & Risks | 100% | None | 2026-02-04 |
| Acceptance Tests | 100% | None | 2026-02-04 |
| Finalization | 100% | None | 2026-02-04 |
Unresolved Critical Questions: 0 | TBDs: 1

---

## 1. Executive Summary

### Context
TeamBot orchestrates 6 specialized AI agent personas (pm, ba, writer, builder-1, builder-2, reviewer) through a 13-stage workflow. The underlying GitHub Copilot CLI supports multiple AI models via the `--model` flag, and TeamBot's `CopilotConfig` already has a `model` field—but this infrastructure is **completely unexposed** to users. There is no way to see which model agents use, configure defaults, or override models at runtime.

### Core Opportunity
Enable users to:
1. **See** which model each agent is using in real-time
2. **Configure** default models per agent in `teambot.json`
3. **Override** models at runtime via inline or session-level commands
4. **Discover** available models supported by the Copilot CLI
5. **Receive clear errors** when invalid models are selected

This transforms TeamBot from a black-box tool into a **transparent, customizable AI orchestration platform** where users can optimize for cost, performance, or capability per agent.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Priority |
|---------|-----------|------|----------|--------|----------|
| G-MS-001 | Provide model visibility in terminal UI | UX | No model display | Model shown for all active agents | P0 |
| G-MS-002 | Support per-agent default model configuration | Config | No per-agent defaults | All 6 agents configurable | P0 |
| G-MS-003 | Enable runtime model override | Flexibility | No override capability | Inline and session-level | P0 |
| G-MS-004 | Validate model selection with clear errors | Reliability | No validation | Descriptive errors with suggestions | P0 |
| G-MS-005 | Enable model discovery | Discoverability | No model list | List all available models | P1 |
| G-MS-006 | Respect agent defaults in file orchestration | Integration | Unknown model used | Agent defaults applied | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Add model to UI displays | Model visible in /status, /tasks, terminal UI | P0 | TBD |
| Extend teambot.json schema | `default_model` field per agent | P0 | TBD |
| Implement runtime override | `@agent --model X` syntax works | P0 | TBD |
| Add model validation | Invalid models show error with valid options | P0 | TBD |
| Add model listing command | `teambot models` or `/models` command | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Infrastructure exists but is unused**: `CopilotConfig.model` field passes `--model` to CLI (line 144-145 of `client.py`) but is never set
- **No configuration path**: `teambot.json` agent definitions include `id`, `persona`, `display_name`, `parallel_capable`, `workflow_stages` but no `default_model`
- **No visibility**: `AgentStatus` dataclass tracks `agent_id`, `state`, and `task` but not `model`
- **No override mechanism**: Agent directive parsing (`@agent task`) has no model selection syntax
- **No validation**: No mechanism to check if a model is valid before use

### Problem Statement
TeamBot users cannot see, configure, or control which AI models their agents use. This creates opacity around agent behavior, prevents cost optimization, and makes debugging model-specific issues impossible. The infrastructure to support model selection already exists in the `CopilotClient`, but the entire feature is inaccessible.

### Root Causes
* Model selection was deferred during initial development to focus on core orchestration
* No explicit requirement captured for model visibility/control
* `CopilotConfig.model` field added but never wired to configuration or UI

### Impact of Inaction
* Users cannot optimize cost vs. capability tradeoffs per agent
* No transparency into agent behavior characteristics
* Cannot debug model-specific issues (e.g., "why did builder-1 behave differently?")
* Cannot standardize on specific models for team consistency
* File-based orchestration uses unknown/inconsistent models

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Power User | Optimize model selection for cost/performance | Cannot choose faster models for routine tasks | High |
| Team Lead | Standardize models across team workflows | No way to enforce model consistency | High |
| Developer | Debug model-specific behaviors | Cannot see which model produced output | High |
| Budget-Conscious User | Control AI costs | No visibility into model costs being incurred | Medium |

### Journeys

1. **Configuration Journey**: User edits `teambot.json` → sets `default_model` per agent → runs TeamBot → sees configured models in UI
2. **Runtime Override Journey**: User enters `@builder-1 --model claude-sonnet-4 implement X` → sees model override in UI → task executes with specified model
3. **Discovery Journey**: User runs `teambot models` → sees list of available models → chooses appropriate model
4. **Error Recovery Journey**: User specifies invalid model → sees clear error with valid options → corrects selection

---

## 4. Scope

### In Scope
* **Configuration**: `default_model` field in `teambot.json` per agent
* **UI Visibility**: Model display in terminal UI, `/status`, `/tasks` commands
* **Runtime Override**: Inline `--model` flag in agent directives
* **Session Override**: Set model for remainder of session
* **Model Validation**: Check model validity, show descriptive errors
* **Model Discovery**: List available models via command
* **File Orchestration**: Respect agent default models during autonomous execution
* **Global Default**: Optional global `default_model` in config as fallback

### Out of Scope
* Model cost tracking or billing integration
* Model performance benchmarking
* Automatic model selection based on task type
* Multi-model orchestration within a single task
* Model caching or pooling
* Custom/fine-tuned model support (only Copilot SDK models)

### Assumptions
* GitHub Copilot CLI `--model` flag continues to work as documented
* Model list can be obtained from Copilot CLI or is documented
* Model availability may vary by subscription tier (graceful handling required)
* Users have authenticated Copilot CLI (`copilot` command works)

### Constraints
| Constraint | Description |
|------------|-------------|
| Model Source | Only models supported by GitHub Copilot CLI/SDK are valid |
| Backward Compatibility | Existing `teambot.json` files must work without modification |
| No Breaking Changes | Current CLI syntax (`@agent task`) must remain valid |
| Single Model Per Task | Each agent task uses exactly one model |

---

## 5. Product Overview

### Value Proposition
Model selection transforms TeamBot into a **transparent, customizable AI orchestration platform**. Users gain control over the cost/capability tradeoff for each agent role, enabling:
- Premium models (e.g., Claude Opus 4.5) for complex planning tasks
- Efficient models (e.g., GPT-5-mini) for routine documentation
- Specialized models (e.g., GPT-5.1-Codex) for code generation

### UX / UI

**Configuration (`teambot.json`):**
```json
{
  "default_model": "claude-sonnet-4",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager",
      "default_model": "claude-opus-4.5",
      "workflow_stages": ["setup", "planning", "coordination"]
    },
    {
      "id": "ba",
      "persona": "business_analyst",
      "display_name": "Business Analyst",
      "default_model": "gpt-5.2-codex",
      "workflow_stages": ["business_problem", "spec"]
    },
    {
      "id": "builder-1",
      "persona": "builder",
      "display_name": "Builder (Primary)",
      "default_model": "claude-sonnet-4",
      "workflow_stages": ["implementation", "testing"]
    }
  ]
}
```

**Terminal UI Display:**
```
╭─ TeamBot Status ────────────────────────────────────────────────╮
│ Agents                                                          │
│ ● pm         idle                          [claude-opus-4.5]    │
│ ● ba         idle                          [gpt-5.2-codex]      │
│ ● writer     idle                          [claude-sonnet-4]    │
│ ◉ builder-1  running → implementing auth   [claude-sonnet-4]    │
│ ● builder-2  idle                          [claude-sonnet-4]    │
│ ● reviewer   idle                          [claude-sonnet-4]    │
╰─────────────────────────────────────────────────────────────────╯
```

**/status Command Output:**
```
TeamBot Status
==============
Stage: IMPLEMENTATION (7/13)
Runtime: 01:23:45

Agents:
  pm         idle                     model: claude-opus-4.5
  ba         idle                     model: gpt-5.2-codex
  writer     idle                     model: claude-sonnet-4
  builder-1  running (implementing)   model: claude-sonnet-4 (override)
  builder-2  idle                     model: claude-sonnet-4
  reviewer   idle                     model: claude-sonnet-4
```

**/tasks Command Output:**
```
Active Tasks
============
Task #1: @builder-1 (claude-sonnet-4) - implementing auth middleware
  Started: 2 minutes ago
  Status: streaming

Task #2: @builder-2 (claude-sonnet-4) - implementing user model
  Started: 1 minute ago  
  Status: running
```

**Inline Model Override:**
```
> @builder-1 --model claude-opus-4.5 refactor the authentication module
[builder-1] Using model: claude-opus-4.5 (override)
...
```

**Session Model Override:**
```
> @builder-1 --model claude-opus-4.5
[builder-1] Default model set to: claude-opus-4.5 (session)

> @builder-1 implement login
[builder-1] Using model: claude-opus-4.5
...
```

**Model Listing Command:**
```
> teambot models
Available Models
================
claude-sonnet-4.5     Claude Sonnet 4.5 (standard)
claude-haiku-4.5      Claude Haiku 4.5 (fast/cheap)
claude-opus-4.5       Claude Opus 4.5 (premium)
claude-sonnet-4       Claude Sonnet 4 (standard)
gpt-5.2-codex         GPT-5.2-Codex (standard)
gpt-5.2               GPT-5.2 (standard)
gpt-5.1-codex-max     GPT-5.1-Codex-Max (standard)
gpt-5.1-codex         GPT-5.1-Codex (standard)
gpt-5.1               GPT-5.1 (standard)
gpt-5                 GPT-5 (standard)
gpt-5.1-codex-mini    GPT-5.1-Codex-Mini (fast/cheap)
gpt-5-mini            GPT-5 mini (fast/cheap)
gpt-4.1               GPT-4.1 (fast/cheap)
gemini-3-pro-preview  Gemini 3 Pro Preview (standard)

Use: @agent --model <model-name> <task>
```

**Error Messages:**
```
> @builder-1 --model invalid-model implement X
Error: Invalid model 'invalid-model'

Available models:
  claude-sonnet-4, claude-opus-4.5, gpt-5.2-codex, ...

Use 'teambot models' to see all available models.
```

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance |
|-------|-------|-------------|-------|----------|------------|
| FR-MS-001 | Agent Default Model Config | Add `default_model` field to agent config in `teambot.json` | G-MS-002 | P0 | Each agent can have distinct default model |
| FR-MS-002 | Global Default Model Config | Add global `default_model` in `teambot.json` as fallback | G-MS-002 | P1 | Global default used when agent default not set |
| FR-MS-003 | Model Display in Terminal UI | Show current model next to each agent in status display | G-MS-001 | P0 | Model visible for all agents in terminal |
| FR-MS-004 | Model Display in /status | Include model in `/status` command output | G-MS-001 | P0 | Model shown for each agent in status |
| FR-MS-005 | Model Display in /tasks | Show agent and model for each active task | G-MS-001 | P0 | Tasks show agent + model combination |
| FR-MS-006 | Inline Model Override | Parse `@agent --model X task` syntax | G-MS-003 | P0 | Override applies to single task only |
| FR-MS-007 | Session Model Override | `@agent --model X` (no task) sets session default | G-MS-003 | P0 | Override persists for session |
| FR-MS-008 | Model Validation | Validate model against allowed list before use | G-MS-004 | P0 | Invalid models rejected with clear error |
| FR-MS-009 | Model Error Messages | Show descriptive error with valid options on invalid model | G-MS-004 | P0 | Error includes model name and alternatives |
| FR-MS-010 | Model Listing Command | `teambot models` or `/models` lists available models | G-MS-005 | P1 | All models listed with descriptions |
| FR-MS-011 | File Orchestration Model Support | Apply agent default models during autonomous execution | G-MS-006 | P0 | Each agent uses its configured model |
| FR-MS-012 | Model Priority Resolution | Resolve model from: inline override > session override > agent default > global default | G-MS-003 | P0 | Priority order respected |
| FR-MS-013 | AgentStatus Model Field | Add `model` field to `AgentStatus` dataclass | G-MS-001 | P0 | Model tracked in agent state |
| FR-MS-014 | CopilotConfig Model Propagation | Pass resolved model to `CopilotConfig` for CLI invocation | G-MS-006 | P0 | Model reaches `--model` flag in CLI command |
| FR-MS-015 | Model Override Indicator | Indicate when model is overridden vs. default in UI | G-MS-001 | P2 | Show "(override)" or "(session)" suffix |

### Feature Hierarchy
```
Model Selection Support
├── Configuration
│   ├── Agent Default Model (FR-001)
│   ├── Global Default Model (FR-002)
│   └── Model Priority Resolution (FR-012)
├── UI Visibility
│   ├── Terminal UI Display (FR-003)
│   ├── /status Command (FR-004)
│   ├── /tasks Command (FR-005)
│   ├── AgentStatus Model Field (FR-013)
│   └── Override Indicator (FR-015)
├── Runtime Control
│   ├── Inline Override (FR-006)
│   ├── Session Override (FR-007)
│   └── CopilotConfig Propagation (FR-014)
├── Validation & Discovery
│   ├── Model Validation (FR-008)
│   ├── Error Messages (FR-009)
│   └── Model Listing (FR-010)
└── Integration
    └── File Orchestration Support (FR-011)
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Target | Priority |
|--------|----------|-------------|--------|----------|
| NFR-MS-001 | Performance | Model validation latency | < 100ms | P0 |
| NFR-MS-002 | Performance | UI update on model change | < 500ms | P0 |
| NFR-MS-003 | Reliability | Config parsing error handling | Graceful fallback to defaults | P0 |
| NFR-MS-004 | Usability | Model names in UI | Human-readable, not truncated | P1 |
| NFR-MS-005 | Compatibility | Existing config files | Must work without `default_model` | P0 |
| NFR-MS-006 | Maintainability | Model list source | Single source of truth (AVAILABLE_MODELS) | P1 |
| NFR-MS-007 | Observability | Model usage logging | Log model used for each task | P1 |

---

## 8. Data & Analytics

### Inputs
* `teambot.json` agent configuration with optional `default_model` fields
* User input: `@agent --model X task` commands
* Copilot CLI: Available models list (or hardcoded known models)

### Outputs
* Terminal UI: Model display per agent
* `/status`: Model per agent
* `/tasks`: Agent + model per task
* Error messages: Invalid model with suggestions
* Model list: All available models with descriptions

### Model Resolution Algorithm
```
function resolve_model(agent_id, inline_model, session_overrides, config):
    # Priority 1: Inline override
    if inline_model:
        return inline_model
    
    # Priority 2: Session override
    if agent_id in session_overrides:
        return session_overrides[agent_id]
    
    # Priority 3: Agent default
    agent_config = config.get_agent(agent_id)
    if agent_config and agent_config.default_model:
        return agent_config.default_model
    
    # Priority 4: Global default
    if config.default_model:
        return config.default_model
    
    # Priority 5: No model specified (Copilot CLI uses its default)
    return None
```

---

## 9. Dependencies

| Dependency | Type | Criticality | Status | Mitigation |
|------------|------|-------------|--------|------------|
| Copilot CLI `--model` flag | External | High | ✅ Confirmed in client.py | N/A |
| CopilotConfig.model field | Internal | High | ✅ Exists (unused) | Wire to config |
| AgentStatus dataclass | Internal | High | ✅ Exists | Add model field |
| teambot.json config loader | Internal | High | ✅ Exists | Extend schema |
| Available models list | External | Medium | ⚠️ To verify | Hardcode known models |

---

## 10. Risks & Mitigations

| Risk ID | Description | Probability | Impact | Mitigation | Owner |
|---------|-------------|-------------|--------|------------|-------|
| R-MS-001 | Copilot CLI model list API unavailable | Medium | Medium | Hardcode known models, update periodically |TBD |
| R-MS-002 | Model availability varies by subscription | High | Low | Validate dynamically, graceful error handling | TBD |
| R-MS-003 | Breaking changes to Copilot CLI `--model` | Low | High | Version pin, test in CI | TBD |
| R-MS-004 | Config migration for existing users | Medium | Low | `default_model` is optional, defaults work | TBD |
| R-MS-005 | Model name inconsistency (display vs CLI) | Medium | Medium | Use CLI names consistently | TBD |

---

## 11. Privacy, Security & Compliance

### Data Classification
* Model selection preferences: Non-sensitive configuration data
* Model names: Public information (Copilot SDK documentation)

### PII Handling
* No PII involved in model selection feature

### Threat Considerations
* **Model injection**: Validate model names against allowlist
* **Config tampering**: Standard file permission handling (existing)

---

## 12. Operational Considerations

| Aspect | Requirement |
|--------|-------------|
| Deployment | No special deployment requirements |
| Rollback | Remove `default_model` fields from config to revert |
| Monitoring | Log model used per task for debugging |
| Support | Document available models in README |

---

## 13. Acceptance Test Scenarios

### AT-MS-001: Configure Default Model Per Agent
**Description**: User configures different default models for different agents
**Preconditions**: Clean `teambot.json` with no model settings
**Steps**:
1. Edit `teambot.json` to add `"default_model": "claude-opus-4.5"` to pm agent
2. Edit `teambot.json` to add `"default_model": "gpt-5.2-codex"` to ba agent
3. Run `teambot init`
4. Run `/status` command
**Expected Result**: Status shows `claude-opus-4.5` for pm and `gpt-5.2-codex` for ba
**Verification**: Visual confirmation in `/status` output

### AT-MS-002: Inline Model Override
**Description**: User overrides model for a single task
**Preconditions**: TeamBot running with default models configured
**Steps**:
1. Enter `@builder-1 --model claude-opus-4.5 implement user authentication`
2. Observe terminal output
3. After task completes, enter `@builder-1 implement login form`
**Expected Result**: 
- First task shows "Using model: claude-opus-4.5 (override)"
- Second task uses agent's default model (not claude-opus-4.5)
**Verification**: Model indicator in output, task uses specified model

### AT-MS-003: Session Model Override
**Description**: User sets model override for remainder of session
**Preconditions**: TeamBot running with default models
**Steps**:
1. Enter `@builder-1 --model claude-opus-4.5` (no task)
2. Observe confirmation message
3. Enter `@builder-1 implement feature X`
4. Enter `@builder-1 implement feature Y`
**Expected Result**:
- Confirmation: "Default model set to: claude-opus-4.5 (session)"
- Both subsequent tasks use `claude-opus-4.5`
**Verification**: Tasks show model in output

### AT-MS-004: Invalid Model Error
**Description**: User specifies invalid model name
**Preconditions**: TeamBot running
**Steps**:
1. Enter `@builder-1 --model invalid-model-name implement X`
**Expected Result**:
- Error message: "Invalid model 'invalid-model-name'"
- Shows list of valid models
- Suggests using `teambot models` command
**Verification**: Task does not execute, clear error displayed

### AT-MS-005: Model Listing Command
**Description**: User lists available models
**Preconditions**: TeamBot running
**Steps**:
1. Enter `/models` or run `teambot models`
**Expected Result**:
- List of all available models with descriptions
- Shows model ID and category (standard/fast/premium)
**Verification**: All known models listed

### AT-MS-006: File Orchestration Respects Defaults
**Description**: Autonomous execution uses agent default models
**Preconditions**: 
- `teambot.json` with distinct models per agent
- Valid objective file
**Steps**:
1. Configure pm with `claude-opus-4.5`, builder-1 with `claude-sonnet-4`
2. Run `teambot run objectives/test-objective.md`
3. Observe progress display
**Expected Result**:
- Progress display shows configured models per agent
- Logs confirm each agent uses its configured model
**Verification**: UI shows correct models, logs confirm model usage

### AT-MS-007: Model Priority Resolution
**Description**: Verify inline > session > agent default > global default
**Preconditions**: Global default set to `claude-sonnet-4`, agent default set to `gpt-5.2-codex`
**Steps**:
1. Run `/status` - agent should show `gpt-5.2-codex` (agent default)
2. Enter `@agent --model claude-haiku-4.5` (session override)
3. Run `/status` - agent should show `claude-haiku-4.5`
4. Enter `@agent --model claude-opus-4.5 do task` (inline override)
5. Observe task uses `claude-opus-4.5`
6. Enter `@agent do another task`
7. Task should use `claude-haiku-4.5` (session override)
**Expected Result**: Priority order respected at each step
**Verification**: UI and logs confirm model at each step

---

## 14. Open Questions

| Q ID | Question | Status | Decision |
|------|----------|--------|----------|
| OQ-MS-001 | How to obtain model list from Copilot CLI? | Resolved | Hardcode known models, update with CLI versions |
| OQ-MS-002 | Should model override persist across TeamBot restarts? | Resolved | No - session only, config persists |
| OQ-MS-003 | What's the default behavior when no model is specified? | Resolved | Let Copilot CLI use its default |

---

## 15. Changelog

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | BA Agent | Initial specification |

---

## 16. References

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Internal | `src/teambot/copilot/client.py:144-145` | Existing `--model` flag support |
| REF-002 | Internal | `src/teambot/ui/agent_state.py` | AgentStatus dataclass (needs model field) |
| REF-003 | Internal | `teambot.json` | Current agent config schema |
| REF-004 | Internal | `.teambot/model-select/artifacts/problem_statement.md` | Problem statement |

---

## Appendix A: Available Models (Known)

Based on Copilot CLI SDK:

| Model ID | Display Name | Category |
|----------|--------------|----------|
| claude-sonnet-4.5 | Claude Sonnet 4.5 | standard |
| claude-haiku-4.5 | Claude Haiku 4.5 | fast/cheap |
| claude-opus-4.5 | Claude Opus 4.5 | premium |
| claude-sonnet-4 | Claude Sonnet 4 | standard |
| gemini-3-pro-preview | Gemini 3 Pro Preview | standard |
| gpt-5.2-codex | GPT-5.2-Codex | standard |
| gpt-5.2 | GPT-5.2 | standard |
| gpt-5.1-codex-max | GPT-5.1-Codex-Max | standard |
| gpt-5.1-codex | GPT-5.1-Codex | standard |
| gpt-5.1 | GPT-5.1 | standard |
| gpt-5 | GPT-5 | standard |
| gpt-5.1-codex-mini | GPT-5.1-Codex-Mini | fast/cheap |
| gpt-5-mini | GPT-5 mini | fast/cheap |
| gpt-4.1 | GPT-4.1 | fast/cheap |

---

## Appendix B: Extended teambot.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "teambot_dir": { "type": "string" },
    "default_agent": { "type": "string" },
    "default_model": { 
      "type": "string",
      "description": "Global default model for all agents (fallback)"
    },
    "agents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "persona": { "type": "string" },
          "display_name": { "type": "string" },
          "default_model": { 
            "type": "string",
            "description": "Default model for this agent"
          },
          "parallel_capable": { "type": "boolean" },
          "workflow_stages": { 
            "type": "array", 
            "items": { "type": "string" } 
          }
        },
        "required": ["id", "persona", "display_name"]
      }
    }
  }
}
```

---

## Appendix C: Implementation Components

| Component | File | Changes Required |
|-----------|------|------------------|
| Config Loader | `src/teambot/config/loader.py` | Parse `default_model` fields |
| AgentStatus | `src/teambot/ui/agent_state.py` | Add `model` field |
| CopilotConfig | `src/teambot/copilot/client.py` | Already has `model` field |
| Agent Directive Parser | `src/teambot/repl/` | Parse `--model` flag |
| Status Display | `src/teambot/visualization/` | Add model to display |
| Commands | `src/teambot/cli.py` | Add `/models` command |
| Orchestrator | `src/teambot/orchestrator.py` | Pass model to agent tasks |

<!-- markdown-table-prettify-ignore-end -->
