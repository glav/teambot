# Objective: Model Cache Auto-Setup and Login Validation

## Objective

**Goal**: Ensure `teambot run` validates Copilot CLI login status and automatically refreshes the model cache when missing, providing a seamless first-run experience.

**Problem Statement**:

Currently, when running `teambot run` after initialization:

1. **Missing Copilot Login Check**: If the user hasn't logged in via Copilot CLI (`copilot auth`), TeamBot fails with unclear errors rather than guiding the user to authenticate first.

2. **Missing Model Cache Stops Execution**: When no model cache exists, TeamBot errors out instead of automatically refreshing the cache:
   ```
   WARNING - No model cache available - run '/models --refresh' to fetch models
   WARNING - Cannot validate model 'claude-sonnet-4.5' - no models loaded from SDK
   [ERROR] Configuration error: Invalid model 'claude-sonnet-4.5' for agent 'pm'. Use '/models' command to see available models.
   ```

Users must manually run `/models --refresh` before TeamBot will work, which creates unnecessary friction.

**Success Criteria**:

- [ ] `teambot run` checks Copilot CLI authentication before proceeding
- [ ] If not authenticated, stops with clear error instructing user to run `copilot auth`
- [ ] `teambot run` detects when model cache is missing or empty
- [ ] When model cache is missing, automatically performs model refresh (equivalent to `/models --refresh`)
- [ ] User is informed that model cache refresh is occurring (e.g., "Refreshing model cache...")
- [ ] If model cache refresh fails, provides clear error with actionable guidance
- [ ] If model cache refresh succeeds, `teambot run` continues execution normally
- [ ] All existing tests pass
- [ ] New tests cover the login check and auto-refresh behavior

---

## Technical Context

**Target Codebase**:

- `src/teambot/cli.py` - CLI entry point with `cmd_run()` function
- `src/teambot/config/schema.py` - Model validation and cache loading
- `src/teambot/config/model_cache.py` - Cache file operations
- `src/teambot/config/loader.py` - Configuration loading (triggers model validation)

**Primary Language/Framework**:

- Python (existing codebase)

**Testing Preference**:

- Test-Driven Development (TDD)

**Key Constraints**:

- Must not break existing `teambot init` or `teambot run` behavior when cache exists
- Authentication check should be fast and not block unnecessarily
- Model refresh should display status to the user
- Must handle network failures gracefully with clear error messages
- Should not change the startup behavior when everything is correctly set up

---

## Current Implementation Analysis

### Authentication Check

The `cli.py` already has `_check_copilot_authentication()` which:
- Uses `CopilotSDKClient.is_authenticated()` to verify auth status
- Returns `True` if authenticated, `False` otherwise
- Displays guidance to run `copilot auth` if not authenticated

**Gap**: This is called during `cmd_init()` but NOT during `cmd_run()`.

### Model Cache

The `schema.py` has `_ensure_models_loaded()` which:
- Tries to load from cache via `model_cache.py`
- If no cache exists, logs warning and leaves models empty
- Model validation then fails because no models are available

**Gap**: There's no automatic refresh when cache is missing. The `refresh_models()` function exists but isn't called automatically.

### Key Functions to Modify

1. **`cmd_run()` in `cli.py`**: Add authentication check and model cache validation before loading config
2. **Create helper**: `_ensure_model_cache()` that checks cache existence and refreshes if needed
3. **`_refresh_model_cache()`**: Already exists, can be reused

---

## Implementation Approach

### Phase 1: Add Authentication Check to `cmd_run()`

Before attempting to load config or run orchestration:
1. Call `_check_copilot_authentication(display)`
2. If returns `False`, print clear error and return exit code 1
3. Error message should instruct: "Run 'copilot auth' to authenticate"

**Note**: Authentication must be checked BEFORE model cache refresh because cache refresh requires authentication to fetch models from the SDK.

### Phase 2: Add Model Cache Auto-Refresh

After authentication check, before config loading:
1. Check if model cache exists (use `model_cache.load_cache()`)
2. If cache is missing (returns `None`):
   - Display: "Model cache not found. Refreshing models..."
   - Call `_refresh_model_cache(display)`
   - If refresh fails, show warning and continue (allows execution with empty model list)
3. Continue with config loading (which will now have models available)

### Phase 3: Testing

- Add unit tests for the new pre-run checks
- Add integration tests for the full flow
- Test edge cases: network failure, partial cache, expired cache

---

## Acceptance Test Scenarios

### Scenario 1: Normal Run (Cache Exists, Authenticated)

**Given**: User is authenticated and model cache exists
**When**: User runs `teambot run objectives/my-task.md`
**Then**:
- No additional messages about auth or cache
- TeamBot runs normally

### Scenario 2: Not Authenticated

**Given**: Copilot CLI is installed but user is NOT authenticated
**When**: User runs `teambot run objectives/my-task.md`
**Then**:
- Clear error: "Copilot not authenticated"
- Instruction: "Run 'copilot auth' to authenticate"
- Exit code 1

### Scenario 3: Missing Model Cache

**Given**: User is authenticated but no model cache exists
**When**: User runs `teambot run objectives/my-task.md`
**Then**:
- Message: "Refreshing model cache..."
- Model cache is populated
- TeamBot continues with normal execution

### Scenario 4: Model Cache Refresh Fails

**Given**: User is authenticated, no cache, network unavailable
**When**: User runs `teambot run objectives/my-task.md`
**Then**:
- Message: "Refreshing model cache..."
- Warning: "Could not refresh model cache - models may not be available"
- Warning: "Run '/models --refresh' later to update model list"
- **Execution continues** (does not exit - allows user to work with potentially empty model list)

### Scenario 5: Expired Cache (Edge Case)

**Given**: User is authenticated, cache exists but is expired (older than 7 days)
**When**: User runs `teambot run objectives/my-task.md`
**Then**:
- Cache is detected as expired
- **Uses expired cache data** to allow immediate use of models
- Warning logged: "Using expired model cache - run '/models --refresh' to update"
- Execution continues normally with potentially stale model data
- User can manually refresh later via `/models --refresh` command

---

## Tasks Breakdown

### Phase 1: Authentication Check in cmd_run()

- [ ] Add authentication check at start of `cmd_run()` before config loading
- [ ] Ensure clear error message guides user to run `copilot auth`
- [ ] Add tests for authentication check in `cmd_run()`

### Phase 2: Model Cache Auto-Refresh

- [ ] Create `_ensure_model_cache(display)` helper function
- [ ] Check for cache existence before config load (expired caches are used with warning)
- [ ] Call `_refresh_model_cache()` when cache is missing
- [ ] Display user-friendly status messages during refresh
- [ ] Handle refresh failure with warning (execution continues)
- [ ] Add tests for auto-refresh behavior

### Phase 3: Integration Testing

- [ ] Test full flow: no auth → error
- [ ] Test full flow: no cache → auto-refresh → success
- [ ] Test full flow: no cache → refresh fails → warning + continue
- [ ] Verify existing functionality unchanged when cache exists

### Phase 4: Documentation

- [ ] Update README or user docs with new behavior
- [ ] Update troubleshooting guide if needed

---

## Notes

- **Stage configuration**: Workflow stages are defined in `stages.yaml`
- **Feature directory**: Artifacts will be saved to `.teambot/model-cache-setup/`
- **Related objective**: `objective-fix-init-models.md` covers init-time behavior; this objective covers run-time behavior. Note: PR #145 has already implemented the init-time features, so `_check_copilot_authentication()` and `_refresh_model_cache()` already exist in `cli.py` and can be reused.
