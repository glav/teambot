# Problem Statement: Incorrect Authentication Command in Error Messages

## Business Problem

TeamBot currently displays **incorrect authentication guidance** to users. When users run `teambot run` or `teambot init` without being authenticated, they see:

```
[ERROR] Copilot not authenticated
Run 'copilot auth' to authenticate
```

However, the **correct command** per `copilot --help` is `copilot login`, which authenticates via OAuth device flow.

This inconsistency causes:
1. **User confusion** — Users following the displayed guidance receive "command not found" or similar errors
2. **Increased support burden** — Users must search documentation or ask for help to find the correct command
3. **Poor first-run experience** — New users encounter friction immediately when setting up TeamBot

## Scope

### In Scope
- User-facing error messages in `src/teambot/cli.py`
- Documentation files (`README.md`, `docs/guides/installation.md`)
- Test assertions that verify error message content

### Out of Scope
- Historical objective/artifact files (`.teambot/*/artifacts/`, `.agent-tracking/`)
- Logic changes to authentication checking
- Changes to the Copilot CLI itself

## Affected Files

| Category | File | Count of Occurrences |
|----------|------|---------------------|
| Source Code | `src/teambot/cli.py` | 5 |
| Documentation | `README.md` | 1 |
| Documentation | `docs/guides/installation.md` | 2 |
| Tests | `tests/test_cli.py` | 2 |
| Tests | `tests/test_acceptance_validation.py` | 4 |
| Tests | `tests/test_init_model_config_acceptance.py` | 2 |
| Tests | `tests/test_model_cache_auto_acceptance.py` | 1 |

**Total: 17 occurrences** requiring update

## Goals

| ID | Goal | Measurable Outcome |
|----|------|-------------------|
| G-001 | Correct authentication guidance | All user-facing messages display `copilot login` |
| G-002 | Consistent documentation | All docs reference `copilot login` |
| G-003 | Passing test suite | All test assertions updated and passing |

## Success Criteria

| ID | Criterion | Verification Method |
|----|-----------|-------------------|
| SC-001 | All instances of `copilot auth` in user-facing messages replaced with `copilot login` | Code review of `src/teambot/cli.py` |
| SC-002 | `teambot run` shows correct authentication message when not authenticated | Manual verification |
| SC-003 | `teambot init` shows correct authentication message when not authenticated | Manual verification |
| SC-004 | All test assertions referencing `copilot auth` updated to `copilot login` | Code review of test files |
| SC-005 | Existing tests pass after updating assertions | `uv run pytest` passes |
| SC-006 | Documentation updated to reference `copilot login` | Review of README.md and installation.md |

## User Stories

### US-001: Unauthenticated User Running TeamBot
**As a** new TeamBot user  
**I want** to see the correct authentication command when I'm not logged in  
**So that** I can authenticate without confusion or searching for documentation

**Acceptance Criteria:**
- Given I am not authenticated with Copilot CLI
- When I run `teambot run objectives/my-task.md`
- Then I see an error message containing `copilot login`
- And the message does NOT contain `copilot auth`

### US-002: User Following Documentation
**As a** user following the installation guide  
**I want** documentation to reference the correct command  
**So that** I can successfully authenticate on first attempt

**Acceptance Criteria:**
- Given I am reading the installation documentation
- When I follow the authentication instructions
- Then the command shown is `copilot login`

## Assumptions

1. The `copilot login` command is the stable, correct command for authentication
2. No logic changes are required — this is purely a string replacement
3. Historical artifact files do not need updating (they document past work)

## Dependencies

- None — this is a self-contained text change

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Copilot CLI changes command again | Low | Medium | Monitor Copilot CLI releases |
| Missed occurrences | Low | Low | Comprehensive grep search performed |

## Priority

**P0 — High Priority**

Incorrect guidance causes immediate user friction and poor first-run experience. Simple fix with high impact on user satisfaction.

---

**Document Version:** 1.0  
**Status:** Ready for Spec Phase  
**Exit Criteria Met:** ✅ Clear problem definition with measurable goals
