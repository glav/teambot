<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Fix Authentication Command Message - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.x | Lifecycle Implementation-Ready

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-22 |
| Problem & Users | ✅ | None | 2026-02-22 |
| Scope | ✅ | None | 2026-02-22 |
| Requirements | ✅ | None | 2026-02-22 |
| Metrics & Risks | ✅ | None | 2026-02-22 |
| Operationalization | ✅ | None | 2026-02-22 |
| Finalization | ✅ | None | 2026-02-22 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates multi-agent AI workflows for software development. When users are not authenticated with the GitHub Copilot CLI, TeamBot displays an error message guiding them to authenticate. Currently, this message references the incorrect command `copilot auth` instead of the correct command `copilot login`.

### Core Opportunity
Correct the authentication error messages across all user-facing outputs (CLI messages, documentation, and tests) to reference the valid `copilot login` command, eliminating user confusion and improving the first-run experience.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Display correct authentication command in all error messages | UX | 0% correct | 100% correct | Immediate | P0 |
| G-002 | Align documentation with CLI behavior | Documentation | Incorrect | Correct | Immediate | P0 |
| G-003 | Maintain test coverage with updated assertions | Quality | Passing (incorrect message) | Passing (correct message) | Immediate | P0 |

## 2. Problem Definition

### Current Situation
When users run `teambot run` or `teambot init` without being authenticated to GitHub Copilot CLI, they see:
```
[ERROR] Copilot not authenticated
Run 'copilot auth' to authenticate
```

The command `copilot auth` does not exist. The correct command is `copilot login`.

### Problem Statement
TeamBot displays incorrect authentication guidance (`copilot auth`) instead of the correct command (`copilot login`), causing user confusion, failed authentication attempts, and a poor first-run experience.

### Root Causes
* The original implementation used an assumed command name that does not match the actual Copilot CLI
* The error message was propagated to multiple locations without verification against `copilot --help`

### Impact of Inaction
* Users cannot authenticate following the displayed guidance
* Increased support burden as users seek correct instructions
* Negative first impression of TeamBot for new users
* Documentation inconsistency undermines user trust

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| New TeamBot User | Quickly set up and start using TeamBot | Sees incorrect command, authentication fails | High - blocks first use |
| Existing User (new machine) | Re-authenticate on new environment | Follows displayed guidance that doesn't work | Medium - causes confusion |
| Documentation Reader | Follow installation guide successfully | Instructions don't match actual CLI | Medium - erodes trust |

## 4. Scope

### In Scope
* User-facing error messages in `src/teambot/cli.py` (5 occurrences)
* Documentation files: `README.md` (1), `docs/guides/installation.md` (2)
* Test assertions: `tests/test_cli.py` (2), `tests/test_acceptance_validation.py` (4), `tests/test_init_model_config_acceptance.py` (2), `tests/test_model_cache_auto_acceptance.py` (1)

### Out of Scope
* Historical artifact files in `.teambot/*/artifacts/` and `.agent-tracking/` (these document past work)
* Logic changes to authentication checking mechanism
* Changes to the Copilot CLI itself
* Other objective documentation files referencing the old command

### Assumptions
* `copilot login` is the stable, correct command per Copilot CLI help output
* No breaking changes to test infrastructure from string updates
* Historical documentation does not need retroactive correction

### Constraints
* Must be a pure string replacement — no logic changes
* Must maintain 100% test pass rate after changes
* Must update all user-facing occurrences for consistency

## 5. Product Overview

### Value Proposition
Users receive accurate authentication guidance, enabling successful first-run setup and reducing friction in the onboarding experience.

### Technical Stack
* **Primary Language**: Python
* **Testing Framework**: pytest with pytest-mock
* **Package Manager**: uv

### Testing Approach
* **Preference**: Code-first with test assertion updates
* **Rationale**: Existing tests already validate the message content; only assertions need updating to match corrected strings

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Update `teambot run` auth message | Replace `copilot auth` with `copilot login` in unauthenticated error for `teambot run` | G-001 | New User | P0 | Error message contains `copilot login` not `copilot auth` | Lines 139, 144 in cli.py |
| FR-002 | Update `teambot init` auth message | Replace `copilot auth` with `copilot login` in unauthenticated error for `teambot init` | G-001 | New User | P0 | Error message contains `copilot login` not `copilot auth` | Lines 108, 114 in cli.py |
| FR-003 | Update installation warning | Replace `copilot auth` with `copilot login` in Copilot CLI installation warning | G-001, G-002 | New User | P0 | Warning message contains `copilot login` | Line 239 in cli.py |
| FR-004 | Update README documentation | Replace `copilot auth` with `copilot login` in README.md | G-002 | Documentation Reader | P0 | README shows `copilot login` | Line 17 |
| FR-005 | Update installation guide | Replace `copilot auth` with `copilot login` in installation.md | G-002 | Documentation Reader | P0 | Guide shows `copilot login` | Lines 17, 227 |
| FR-006 | Update test assertions | Update all test assertions to verify `copilot login` instead of `copilot auth` | G-003 | N/A | P0 | All tests pass with new assertions | 9 assertions across 4 test files |

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Maintainability | Changes should be minimal and surgical | <20 lines changed total | P0 | Code review | String replacement only |
| NFR-002 | Reliability | Test suite must pass after changes | 100% pass rate | P0 | `uv run pytest` | No regressions |
| NFR-003 | Consistency | All occurrences must use same string | 0 remaining `copilot auth` in scope | P0 | grep verification | No partial updates |

## 8. Acceptance Test Scenarios

### AT-001: Unauthenticated User Runs TeamBot
**Description**: Verify correct error message when running `teambot run` without authentication
**Preconditions**: User is not authenticated with Copilot CLI
**Steps**:
1. Ensure Copilot CLI authentication is not present
2. Run `uv run teambot run objectives/any-task.md`
3. Observe error output
**Expected Result**: Error message contains `copilot login` and does NOT contain `copilot auth`
**Verification**: Manual inspection of CLI output

### AT-002: Unauthenticated User Runs Init
**Description**: Verify correct error message when running `teambot init` without authentication
**Preconditions**: User is not authenticated with Copilot CLI
**Steps**:
1. Ensure Copilot CLI authentication is not present
2. Run `uv run teambot init`
3. Observe output during authentication check
**Expected Result**: Message contains `copilot login` and does NOT contain `copilot auth`
**Verification**: Manual inspection of CLI output

### AT-003: Test Suite Passes with Updated Assertions
**Description**: Verify all tests pass after updating assertions
**Preconditions**: All code and test changes applied
**Steps**:
1. Run `uv run pytest`
2. Observe test results
**Expected Result**: All tests pass (0 failures)
**Verification**: pytest output shows all tests passing

### AT-004: Documentation Shows Correct Command
**Description**: Verify documentation references correct authentication command
**Preconditions**: Documentation changes applied
**Steps**:
1. Open `README.md` and search for authentication instructions
2. Open `docs/guides/installation.md` and search for authentication instructions
**Expected Result**: All instances show `copilot login`
**Verification**: Manual review of documentation files

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| None | N/A | N/A | N/A | N/A | Self-contained change |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Missed occurrences | Low | Low | Comprehensive grep search performed identifying all 17 occurrences | Builder | Open |
| R-002 | Copilot CLI changes command again | Low | Low | Monitor Copilot CLI releases | Maintainer | Open |
| R-003 | Test failures from string mismatch | Low | Low | Update assertions simultaneously with code changes | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
N/A - This change affects only user-facing strings, no data handling changes.

### PII Handling
N/A - No PII involved.

### Threat Considerations
N/A - No security implications.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard release process | No special deployment requirements |
| Rollback | Git revert | Simple string change, easy rollback |
| Monitoring | N/A | No runtime monitoring needed |
| Alerting | N/A | No alerting changes |
| Support | N/A | Reduces support burden |
| Capacity Planning | N/A | No capacity impact |

## 13. Implementation Checklist

### Source Code (`src/teambot/cli.py`)
- [ ] Line 108: Change `copilot auth` to `copilot login`
- [ ] Line 114: Change `copilot auth` to `copilot login`
- [ ] Line 139: Change `copilot auth` to `copilot login`
- [ ] Line 144: Change `copilot auth` to `copilot login`
- [ ] Line 239: Change `copilot auth` to `copilot login`

### Documentation
- [ ] `README.md` line 17: Change `copilot auth` to `copilot login`
- [ ] `docs/guides/installation.md` line 17: Change `copilot auth` to `copilot login`
- [ ] `docs/guides/installation.md` line 227: Change `copilot auth` to `copilot login`

### Tests
- [ ] `tests/test_cli.py` line 609: Change assertion to `copilot login`
- [ ] `tests/test_cli.py` line 629: Change assertion to `copilot login`
- [ ] `tests/test_acceptance_validation.py` line 118: Update docstring reference
- [ ] `tests/test_acceptance_validation.py` line 155: Change assertion to `copilot login`
- [ ] `tests/test_acceptance_validation.py` line 156: Update error message reference
- [ ] `tests/test_acceptance_validation.py` line 408: Change assertion to `copilot login`
- [ ] `tests/test_init_model_config_acceptance.py` line 115: Change assertion to `copilot login`
- [ ] `tests/test_init_model_config_acceptance.py` line 135: Change assertion to `copilot login`
- [ ] `tests/test_model_cache_auto_acceptance.py` line 110: Change assertion to `copilot login`

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| None | N/A | N/A | N/A | N/A |

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-22 | BA Agent | Initial specification | Creation |

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | `.teambot/auth-message/artifacts/problem_statement.md` | Business problem and scope definition | N/A |
| REF-002 | CLI Help | `copilot --help` | Confirms `copilot login` is correct command | N/A |
| REF-003 | Grep Search | Repository search | Identified all 17 occurrences | N/A |

---

## Validation Status

```
VALIDATION_STATUS: PASS
- Placeholders: 0 remaining
- Sections Complete: 16/16
- Technical Stack: DEFINED (Python, pytest)
- Testing Approach: DEFINED (Code-first with assertion updates)
- Acceptance Tests: 4 scenarios defined
```

## Next Step

Run **Step 2** (`sdd.2-review-spec.prompt.md`) to validate the specification completeness and quality before proceeding to research phase.

<!-- markdown-table-prettify-ignore-end -->
