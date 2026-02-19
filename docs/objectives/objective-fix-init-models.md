# Objective: Fix Init Command Model Configuration and Prerequisites

## Problem Statement

When running `teambot init` in a new repository, there are three issues that prevent TeamBot from working correctly after initialization:

1. **Incorrect Default Model**: The default model in `create_default_config()` is set to `claude-sonnet-4` but should be `claude-sonnet-4.5`
2. **Missing Model Cache**: After init, the model cache doesn't exist, causing TeamBot to fail on first run. A `/model --refresh` equivalent needs to be performed during init or first run
3. **No Copilot Login Check**: The init command doesn't verify that the user has authenticated with Copilot CLI (`copilot auth` or `/login`), leading to confusing errors when TeamBot tries to run

## Goals

1. Update the default model from `claude-sonnet-4` to `claude-sonnet-4.5` in the default configuration
2. Add explicit `"model"` field to each agent in the default config (set to default model) for easier user customization
3. Automatically refresh the model cache during `teambot init` or on first run to ensure models are available
4. Add a check during `teambot init` to verify the user is authenticated with Copilot CLI, with helpful guidance if not
5. Display "Recommended Next Steps" guidance after init completes, suggesting per-agent model configuration for better quality
6. Make the "Recommended Next Steps" guidance text configurable/maintainable from a source file in the TeamBot repository

## Success Criteria

- [ ] Default model in `create_default_config()` is `claude-sonnet-4.5`
- [ ] Each agent in the default config has an explicit `"model"` field (set to default model value)
- [ ] Running `teambot init` populates the model cache (equivalent to `/model --refresh`)
- [ ] If model cache population fails, a clear warning is shown but init continues
- [ ] Running `teambot init` checks for Copilot CLI authentication status
- [ ] If not authenticated, a helpful message guides the user to run `copilot auth` or `/login`
- [ ] All existing tests pass
- [ ] New tests cover the model cache refresh and authentication check functionality
- [ ] Documentation is updated to reflect the new init behavior
- [ ] After init completes, "Recommended Next Steps" guidance is displayed
- [ ] Next steps guidance suggests configuring per-agent models for better quality
- [ ] Next steps guidance text is loaded from a configurable source file in the TeamBot repo (not hardcoded)

## Constraints

- Must not break existing init functionality
- Must work when Copilot CLI is installed but not authenticated
- Must gracefully handle network failures during model cache refresh
- Should provide clear, actionable error messages
- Init should still succeed even if model refresh fails (with warning)

## Context

### Current Implementation

- `src/teambot/config/loader.py` contains `create_default_config()` with `default_model: "claude-sonnet-4"`
- `src/teambot/cli.py` contains `cmd_init()` and `check_copilot_cli()` functions
- `check_copilot_cli()` only checks if `copilot` binary exists, not if user is authenticated
- There's no model cache refresh during init

### Relevant Files

- `src/teambot/cli.py` - CLI entry point with init command
- `src/teambot/config/loader.py` - Configuration defaults
- `src/teambot/copilot/` - Copilot CLI wrapper (check for model refresh logic)
- `tests/test_cli.py` - CLI tests

### Model Cache

The model cache is likely refreshed via the Copilot CLI `/model --refresh` command. Investigate:
- How the model cache is stored
- How to trigger a refresh programmatically
- How to detect if the cache exists

### Authentication Check

The Copilot CLI authentication can be checked by:
- Running a command that requires auth and checking the exit code
- Looking for authentication tokens/credentials
- Running `copilot auth status` or similar command

---

## Tasks Breakdown

### Phase 1: Fix Default Model and Agent Config

- [ ] Update `create_default_config()` in `src/teambot/config/loader.py` to use `claude-sonnet-4.5`
- [ ] Add explicit `"model": "claude-sonnet-4.5"` field to each agent definition in the default config
- [ ] Update any tests that assert the default model value or agent structure
- [ ] Verify the change doesn't break existing functionality

### Phase 2: Model Cache Refresh on Init

- [ ] Investigate how the model cache works in the Copilot CLI wrapper
- [ ] Add model cache refresh logic to `cmd_init()`
- [ ] Handle failures gracefully with warning messages
- [ ] Add tests for the model cache refresh behavior

### Phase 3: Authentication Check

- [ ] Investigate how to check Copilot CLI authentication status
- [ ] Add authentication check to `cmd_init()` before proceeding
- [ ] Provide clear guidance if not authenticated
- [ ] Add tests for the authentication check

### Phase 4: Recommended Next Steps Display

- [ ] Create a source file for the next steps guidance text (e.g., `src/teambot/resources/init_next_steps.md` or similar)
- [ ] Load the guidance text from this file at runtime (bundled with package like other scaffolds)
- [ ] Add "Recommended Next Steps" section to init output after all setup completes
- [ ] Include guidance about configuring per-agent models for better quality
- [ ] Suggest example model assignments (e.g., `claude-opus-4.5` for PM, `gpt-5.2-codex` for builders)
- [ ] Format the output clearly with actionable instructions

### Phase 5: Testing and Documentation

- [ ] Ensure all existing tests pass
- [ ] Add acceptance tests for the new init behavior
- [ ] Update documentation to reflect the enhanced init command
- [ ] Update troubleshooting guide with new error scenarios

---

## Acceptance Test Scenarios

### Scenario 1: Fresh Init with Authenticated Copilot

**Given**: Copilot CLI is installed and authenticated
**When**: User runs `teambot init`
**Then**:
- Config is created with `default_model: "claude-sonnet-4.5"`
- Model cache is populated
- Success message is shown

### Scenario 2: Fresh Init without Copilot Authentication

**Given**: Copilot CLI is installed but NOT authenticated
**When**: User runs `teambot init`
**Then**:
- Clear message explains authentication is required
- User is guided to run `copilot auth` or `/login`
- Init may continue with warning or prompt user to authenticate first

### Scenario 3: Model Cache Refresh Failure

**Given**: Copilot CLI is authenticated but network is unavailable
**When**: User runs `teambot init`
**Then**:
- Config is created successfully
- Warning about model cache refresh failure is shown
- Init completes (non-blocking failure)

### Scenario 4: Re-running Init

**Given**: TeamBot already initialized
**When**: User runs `teambot init --force`
**Then**:
- Config is overwritten with correct default model
- Model cache is refreshed
- Authentication is re-verified
- Recommended next steps are displayed

### Scenario 5: Recommended Next Steps Display

**Given**: Copilot CLI is installed and authenticated
**When**: User runs `teambot init` and it completes successfully
**Then**:
- A "Recommended Next Steps" section is displayed (loaded from configurable source file)
- User is advised that while the default model works, per-agent models improve quality
- Example configuration is shown:
  ```
  While this configuration works with a single default model, we recommend 
  configuring different models for each agent for a better verified and 
  quality experience.
  
  To do this, add a "model" field to agents in teambot.json:
    - "model": "claude-opus-4.5" for the PM agent (planning/coordination)
    - "model": "gpt-5.2-codex" for builder agents (implementation)
  
  Configure specific models for each agent that match your preferences.
  ```
