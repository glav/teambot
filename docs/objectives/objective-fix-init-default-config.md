## Objective

- Fix `teambot init` to include `default_model` and `default_agent` in the generated `teambot.json` file.

**Goal**:

- Ensure that when `teambot init` is run, the generated `teambot.json` includes the `default_model` and `default_agent` fields with sensible defaults
- Provide consistency between the example `teambot.json` in the repository and what `teambot init` generates

**Problem Statement**:

- Currently, `teambot init` generates a `teambot.json` that is missing the `default_model` and `default_agent` configuration fields
- The example `teambot.json` in the repository root includes these fields:
  ```json
  "default_model": "claude-sonnet-4",
  "default_agent": "pm",
  ```
- Users who run `teambot init` get an incomplete config compared to the documented example
- These fields are used throughout the codebase (model resolution, REPL routing) but aren't being generated

**Success Criteria**:

- [ ] `create_default_config()` in `src/teambot/config/loader.py` includes `default_model` with value `"claude-sonnet-4"`
- [ ] `create_default_config()` includes `default_agent` with value `"pm"`
- [ ] Existing tests continue to pass
- [ ] New tests validate the presence of these fields in the default config
- [ ] Documentation (if any references the init output) is consistent

**Non-Goals** (explicitly out of scope):

- Changing the interactive init wizard prompts (fields should be included in defaults)
- Modifying validation logic for these fields (already exists)
- Changing the values in the example `teambot.json` in the repo root

---

## Technical Context

**Target Codebase**:

- `src/teambot/config/loader.py` - Contains `create_default_config()` function (line 33)

**Primary Language/Framework**:

- Python (existing codebase)

**Testing Preference**:

- Test-Driven Development (TDD) preferred

**Key Constraints**:

- Must not break existing config loading or validation
- Default values should match the example `teambot.json`:
  - `default_model`: `"claude-sonnet-4"`
  - `default_agent`: `"pm"` (must be a valid agent ID from the agents list)

---

## Root Cause Analysis

The `create_default_config()` function in `src/teambot/config/loader.py` (lines 33-95) returns a dictionary with:
- `teambot_dir`
- `agents` (list of 6 agents)
- `workflow` (with stages)

But it's **missing**:
- `default_model` - used by `cli.py` (lines 246, 299) for model resolution
- `default_agent` - used by `repl/router.py` and `repl/loop.py` for command routing

---

## Implementation Notes

### Simple Fix

Add two lines to the `create_default_config()` function return dictionary:

```python
def create_default_config() -> dict[str, Any]:
    """Create default configuration with MVP agents."""
    return {
        "teambot_dir": ".teambot",
        "default_model": "claude-sonnet-4",  # ADD THIS
        "default_agent": "pm",               # ADD THIS
        "agents": [
            # ... existing agents ...
        ],
        # ... rest of config ...
    }
```

### Field Placement

Place the new fields after `teambot_dir` but before `agents` for consistency with the example `teambot.json`.

---

## Acceptance Test Scenarios

### Scenario 1: New Init Creates Complete Config

**Given**: A directory with no `teambot.json`
**When**: User runs `teambot init`
**Then**: 
- Generated `teambot.json` contains `"default_model": "claude-sonnet-4"`
- Generated `teambot.json` contains `"default_agent": "pm"`

### Scenario 2: Verify Default Values

**Given**: A freshly initialized project
**When**: The config is loaded
**Then**:
- `config.get("default_model")` returns `"claude-sonnet-4"`
- `config.get("default_agent")` returns `"pm"`

### Scenario 3: REPL Uses Default Agent

**Given**: A project initialized with `teambot init`
**When**: User enters a command without specifying an agent
**Then**: Command is routed to the `pm` agent (the default)

---

## Tasks Breakdown

### Phase 1: Implementation

- [ ] Add `"default_model": "claude-sonnet-4"` to `create_default_config()` return dict
- [ ] Add `"default_agent": "pm"` to `create_default_config()` return dict
- [ ] Run existing tests to verify no regressions

### Phase 2: Testing

- [ ] Add unit test verifying `create_default_config()` returns both new fields
- [ ] Add integration test verifying `teambot init` generates config with these fields

### Phase 3: Validation

- [ ] Run full test suite: `uv run pytest`
- [ ] Manually test `teambot init` in a temp directory
- [ ] Compare generated config with example `teambot.json`

---
