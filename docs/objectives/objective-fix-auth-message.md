## Objective

- Fix the incorrect authentication error message displayed when Copilot CLI is not authenticated.

**Goal**:

- Update the error message to show the correct command `copilot login` instead of the incorrect `copilot auth`.
- Currently, when users run `teambot run` without being authenticated, they see:
  ```
  [ERROR] Copilot not authenticated
  Run 'copilot auth' to authenticate
  ```
- The correct command per `copilot --help` is `copilot login`, which authenticates via OAuth device flow.

**Problem Statement**:

- The CLI displays `copilot auth` in multiple authentication-related messages throughout `src/teambot/cli.py`.
- This is incorrect — the Copilot CLI uses `copilot login` for authentication.
- Users following the incorrect guidance will see an error, causing confusion and a poor user experience.

**Success Criteria**:

- [ ] All instances of `copilot auth` in user-facing messages are replaced with `copilot login`.
- [ ] The `teambot run` command shows the correct authentication message when not authenticated.
- [ ] The `teambot init` command shows the correct authentication message when not authenticated.
- [ ] All test assertions referencing `copilot auth` are updated to `copilot login`.
- [ ] Existing tests pass after updating assertions.
- [ ] Manual verification confirms the correct message is displayed.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `src/teambot/cli.py` (authentication check functions and messages).

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:

- This is a simple string replacement fix — no logic changes required.
- Must update all occurrences to maintain consistency.

---

## Additional Context

### Affected Code Locations

Based on grep search, the following lines in `src/teambot/cli.py` need updating:

| Line | Current Text | Replacement |
|------|--------------|-------------|
| 108 | `Run 'copilot auth' to authenticate` | `Run 'copilot login' to authenticate` |
| 114 | `Run 'copilot auth' to ensure you're authenticated` | `Run 'copilot login' to ensure you're authenticated` |
| 139 | `Run 'copilot auth' to authenticate` | `Run 'copilot login' to authenticate` |
| 144 | `Run 'copilot auth' to ensure you're authenticated` | `Run 'copilot login' to ensure you're authenticated` |
| 239 | `After installing, authenticate with: copilot auth` | `After installing, authenticate with: copilot login` |

### Copilot CLI Reference

```
$ copilot login --help
Usage: copilot login [options]

Authenticate with Copilot via OAuth device flow

Options:
  --host <host>             GitHub host URL (default: https://github.com)
  --config-dir <directory>  Set the configuration directory (default: ~/.copilot)
  -h, --help                display help for command
```

---

## Task Breakdown

### Phase 1: Core Fix

- [ ] Update line 108: Change `copilot auth` to `copilot login`
- [ ] Update line 114: Change `copilot auth` to `copilot login`
- [ ] Update line 139: Change `copilot auth` to `copilot login`
- [ ] Update line 144: Change `copilot auth` to `copilot login`
- [ ] Update line 239: Change `copilot auth` to `copilot login`

### Phase 2: Testing

Update test assertions in the following files:

| File | Lines |
|------|-------|
| `tests/test_cli.py` | 609, 629 |
| `tests/test_init_model_config_acceptance.py` | 115, 135 |
| `tests/test_model_cache_auto_acceptance.py` | 110 |
| `tests/test_acceptance_validation.py` | 118, 154-156, 408 |

- [ ] Update `test_cli.py` assertions (lines 609, 629)
- [ ] Update `test_init_model_config_acceptance.py` assertions (lines 115, 135)
- [ ] Update `test_model_cache_auto_acceptance.py` assertion (line 110)
- [ ] Update `test_acceptance_validation.py` assertions (lines 118, 154-156, 408)
- [ ] Verify all tests pass

### Phase 3: Documentation

Update documentation files that reference the incorrect command:

| File | Lines |
|------|-------|
| `docs/guides/installation.md` | 17, 227 |

- [ ] Update `installation.md` line 17: Change `copilot auth` to `copilot login`
- [ ] Update `installation.md` line 227: Change `copilot auth` to `copilot login`

**Note**: The following objective files also reference `copilot auth` but are historical context and may not need updating (review on case-by-case basis):
- `objective-model-cache-setup.md` (6 references)
- `objective-fix-init-models.md` (4 references)

### Phase 4: Verification

- [ ] Manually test `teambot run` without authentication
- [ ] Confirm correct message is displayed

---
