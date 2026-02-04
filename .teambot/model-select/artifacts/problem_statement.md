# Problem Statement: Model Selection Support for TeamBot

## Business Problem

TeamBot users currently have **no visibility or control over which AI models** their agents use when performing tasks. This creates several critical gaps:

1. **Lack of Transparency** - Users cannot see which model is processing their requests, making it impossible to understand or predict agent behavior characteristics.

2. **No Customization** - Different tasks have different needs. Complex planning may benefit from more capable models (e.g., Claude Opus 4.5), while routine tasks can use faster, cheaper models. Users cannot optimize for their use case.

3. **No Cost Management** - Without model visibility or selection, users cannot make informed decisions about cost/performance tradeoffs.

4. **Inconsistent Experience** - When model defaults change upstream, users have no way to ensure consistent behavior or to deliberately select specific models.

## Current State Analysis

| Aspect | Current State | Gap |
|--------|---------------|-----|
| Model configuration | `CopilotConfig` has `model` field (unused) | Not exposed via CLI or config |
| Agent defaults | Agents have `id`, `persona`, `display_name` | No `default_model` field |
| Terminal UI | Shows agent status only | No model information displayed |
| CLI commands | `/status`, `/tasks` show agent info | No model visibility |
| User input | Agent directives work | No model selection syntax |
| File orchestration | Processes objective files | Inherits unknown model |

## Stakeholder Impact

| Stakeholder | Pain Point |
|-------------|------------|
| **Power Users** | Cannot optimize model selection for cost/performance |
| **Teams** | Cannot standardize on specific models for consistency |
| **Developers** | Cannot debug model-specific behaviors |
| **Project Managers** | Cannot budget or forecast AI costs |

## Goals

### Primary Goals

1. **Visibility**: Users can always see which model each agent is using
2. **Configurability**: Default models can be set per-agent in configuration
3. **Flexibility**: Users can override models at runtime (per-command or session)
4. **Validation**: Invalid model selections produce clear error messages
5. **Discovery**: Users can list all available models supported by Copilot CLI

### Measurable Outcomes

| Goal | Metric | Target |
|------|--------|--------|
| Visibility | Model shown in UI/status | 100% of agent displays |
| Configurability | Per-agent defaults work | All 6 agents configurable |
| Flexibility | Runtime override works | Inline and session-level |
| Validation | Error on invalid model | Clear message within 1s |
| Discovery | Model list available | `teambot models` command |

## Success Criteria

- [ ] **SC-1**: Terminal UI displays current model next to each active agent
- [ ] **SC-2**: `/status` command shows model assignment for each agent
- [ ] **SC-3**: `/tasks` command shows agent and model for each task
- [ ] **SC-4**: Users can specify model inline: `@builder-1 --model claude-sonnet-4 implement X`
- [ ] **SC-5**: Users can set session-level model: `@builder-1 --model claude-sonnet-4` (persists)
- [ ] **SC-6**: `teambot.json` supports `default_model` per agent configuration
- [ ] **SC-7**: Invalid model selection shows descriptive error with valid options
- [ ] **SC-8**: `teambot models` or equivalent lists all available models
- [ ] **SC-9**: File-based orchestration respects agent default models

## Constraints

| Constraint | Description |
|------------|-------------|
| **Model Source** | Only models supported by GitHub Copilot CLI/SDK are valid |
| **Backward Compatibility** | Existing configurations must continue to work |
| **No Breaking Changes** | Current CLI syntax must remain valid |

## Assumptions

1. GitHub Copilot CLI provides a mechanism to query available models (or documentation lists them)
2. Model selection via `--model` flag is supported by the underlying Copilot CLI
3. Model availability may vary by user/organization based on Copilot subscription tier

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Copilot CLI `--model` support | External | ✅ Confirmed in `client.py` |
| Model list from Copilot SDK | External | ⚠️ To be verified |
| `CopilotConfig.model` field | Internal | ✅ Exists but unused |

## Out of Scope

- Model cost tracking or billing integration
- Model performance benchmarking
- Automatic model selection based on task type
- Multi-model orchestration within a single task

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Copilot CLI model list API unavailable | Medium | Medium | Hardcode known models with version check |
| Model availability varies by subscription | High | Low | Show available models dynamically, graceful error |
| Breaking changes to Copilot CLI `--model` | Low | High | Version pin, test in CI |

---

## Document Information

| Field | Value |
|-------|-------|
| Author | Business Analyst Agent |
| Created | 2026-02-04 |
| Status | Draft |
| Stage | Business Problem |
| Objective | Model Selection Support |
