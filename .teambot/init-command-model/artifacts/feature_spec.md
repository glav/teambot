<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Init Command Model Configuration and Prerequisites - Feature Specification

**Version:** 1.0 | **Status:** Draft | **Owner:** Business Analyst | **Target:** Next Release

## Progress Tracker

| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-18 |
| Problem & Users | ✅ | None | 2026-02-18 |
| Scope | ✅ | None | 2026-02-18 |
| Requirements | ✅ | None | 2026-02-18 |
| Metrics & Risks | ✅ | None | 2026-02-18 |
| Operationalization | ✅ | None | 2026-02-18 |
| Finalization | ✅ | None | 2026-02-18 |

---

## 1. Executive Summary

### Context

TeamBot's `teambot init` command creates the initial project configuration and directory structure required for multi-agent AI workflows. The current implementation has usability gaps that impact new user onboarding:

- Uses outdated default model (`claude-sonnet-4` instead of `claude-sonnet-4.5`)
- Agent configurations lack explicit model fields, hiding customization options
- No model cache refresh or authentication verification during initialization
- No post-init guidance for optimization

### Core Opportunity

Enhance the init command to provide a smoother onboarding experience with optimal defaults, proactive validation, and actionable guidance for new users.

### Goals

| Goal ID | Statement | Type | Baseline | Target | Priority |
|---------|-----------|------|----------|--------|----------|
| G-001 | Update default model to `claude-sonnet-4.5` | Configuration | `claude-sonnet-4` | `claude-sonnet-4.5` | P0 |
| G-002 | Add explicit model field to each agent | Configuration | No explicit fields | All 6 agents have `model` field | P0 |
| G-003 | Auto-refresh model cache during init | Feature | No refresh | Auto-refresh with graceful failure | P1 |
| G-004 | Verify Copilot CLI authentication during init | Feature | Binary check only | Full auth verification | P1 |
| G-005 | Display post-init guidance | Feature | No guidance | Configurable next steps displayed | P2 |
| G-006 | Externalize guidance text | Maintainability | Hardcoded | Loaded from source file | P2 |

---

## 2. Problem Definition

### Current Situation

The `teambot init` command (`src/teambot/cli.py:cmd_init()`) creates:
- `teambot.json` configuration file with default model set to `claude-sonnet-4`
- `.teambot/` directory with `history/` and `state/` subdirectories
- Optional Telegram notification setup

The `check_copilot_cli()` function only verifies the `copilot` binary exists in PATH using `shutil.which()`. It does not verify authentication status.

The SDK client has `_check_auth()` and `is_authenticated()` methods, but these are not invoked during init.

### Problem Statement

New users complete initialization successfully but encounter failures later due to:
1. Suboptimal default model selection
2. Hidden customization capabilities
3. Missing model cache data
4. Authentication issues discovered only at runtime

### Root Causes

1. Default model value not updated when newer models became available
2. Agent definitions designed for implicit model inheritance, not explicit configuration
3. Init command scope limited to local file/directory creation
4. Authentication check only validates binary presence, not auth state

### Impact of Inaction

- **User Frustration:** Delayed discovery of auth/config issues
- **Suboptimal Results:** Users unknowingly use older models
- **Support Burden:** Increased troubleshooting for preventable issues
- **Adoption Risk:** Poor first-run experience may discourage continued use

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| New User | Quick setup, optimal defaults | Hidden config options, delayed auth failures | High |
| Power User | Fine-tune per-agent models | Must discover customization via docs | Medium |
| Maintainer | Easy updates to guidance text | Hardcoded strings require code changes | Medium |

### User Journey: New User Init Flow

```
1. User runs `teambot init`
2. [NEW] System checks Copilot CLI authentication
   - If not authenticated → Display guidance, continue init
3. Config created with claude-sonnet-4.5 default
4. Each agent has explicit model field for discoverability
5. [NEW] Model cache refreshed (with warning if fails)
6. [NEW] "Recommended Next Steps" guidance displayed
7. User sees clear path to customize and run workflows
```

---

## 4. Scope

### In Scope

| Item | Description |
|------|-------------|
| Default model update | Change `default_model` from `claude-sonnet-4` to `claude-sonnet-4.5` |
| Explicit agent model fields | Add `"model": "claude-sonnet-4.5"` to each agent definition in default config |
| Authentication check | Call `is_authenticated()` during init and display guidance if not authenticated |
| Model cache refresh | Invoke model list fetch during init to populate cache |
| Post-init guidance | Display "Recommended Next Steps" from external source file |
| Guidance source file | Create `src/teambot/scaffolds/init-next-steps.md` for guidance text |
| Tests | New unit tests for auth check and model refresh during init |
| Documentation | Update init command documentation with new behavior |

### Out of Scope

| Item | Rationale |
|------|-----------|
| Copilot CLI authentication flow | Using existing Copilot auth mechanism |
| Model billing/pricing changes | Not related to init enhancement |
| Interactive model selection wizard | Future enhancement |
| Multi-language/localization | Future enhancement |
| Changes to workflow execution | Separate concern |

### Assumptions

| ID | Assumption | Risk if Invalid |
|----|------------|-----------------|
| A-001 | `claude-sonnet-4.5` is available and stable | Config would reference unavailable model |
| A-002 | SDK client can be initialized during init | May require async handling |
| A-003 | `importlib.resources` pattern works for guidance file | Alternative loading mechanism needed |
| A-004 | Network available during init for model refresh | Graceful degradation handles this |

### Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| C-001 | Init must succeed even if auth check fails | Non-blocking validation |
| C-002 | Init must succeed even if model refresh fails | Graceful degradation |
| C-003 | Must not break existing init functionality | Backward compatibility |
| C-004 | Error messages must be actionable | User experience |

---

## 5. Product Overview

### Value Proposition

Enhanced init command that:
- **Optimizes defaults** with latest model and explicit agent configurations
- **Validates early** by checking authentication before workflow execution
- **Guides users** with actionable next steps for customization

### Differentiators

- Proactive auth validation (fail-fast philosophy)
- Self-documenting configuration (explicit model fields)
- Maintainable guidance (external source file)

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance Criteria |
|-------|-------|-------------|-------|----------|---------------------|
| FR-001 | Update default model | Change `default_model` value in `create_default_config()` from `claude-sonnet-4` to `claude-sonnet-4.5` | G-001 | P0 | Config file created with `"default_model": "claude-sonnet-4.5"` |
| FR-002 | Add explicit agent model fields | Add `"model": "claude-sonnet-4.5"` field to each agent definition (pm, ba, writer, builder-1, builder-2, reviewer) | G-002 | P0 | Each of 6 agents has explicit `model` field in generated config |
| FR-003 | Check authentication status | During init, verify Copilot CLI authentication via SDK `is_authenticated()` method | G-004 | P1 | Auth status checked and result stored |
| FR-004 | Display auth guidance | If not authenticated, display actionable message guiding user to `copilot auth` or `/login` | G-004 | P1 | Clear guidance shown when unauthenticated |
| FR-005 | Auth check non-blocking | Authentication check failure must not prevent init from completing | G-004, C-001 | P1 | Init succeeds regardless of auth status |
| FR-006 | Refresh model cache | During init, call SDK `list_models()` to populate model cache | G-003 | P1 | Model fetch attempted during init |
| FR-007 | Model refresh graceful failure | If model cache refresh fails (network error, SDK error), display warning and continue init | G-003, C-002 | P1 | Warning displayed, init succeeds |
| FR-008 | Display post-init guidance | After init completes successfully, display "Recommended Next Steps" section | G-005 | P2 | Guidance text displayed after success messages |
| FR-009 | Load guidance from file | Guidance text loaded from `src/teambot/scaffolds/init-next-steps.md` using `importlib.resources` | G-006 | P2 | Guidance file exists and is loaded at runtime |
| FR-010 | Guidance content | Guidance suggests per-agent model customization for better quality | G-005 | P2 | Content includes model customization recommendation |

### Feature Hierarchy

```
teambot init (enhanced)
├── Configuration Creation
│   ├── FR-001: Default model = claude-sonnet-4.5
│   └── FR-002: Explicit agent model fields
├── Pre-flight Validation
│   ├── FR-003: Check authentication
│   ├── FR-004: Display auth guidance (if needed)
│   └── FR-005: Non-blocking auth check
├── Model Cache Population
│   ├── FR-006: Refresh model cache
│   └── FR-007: Graceful failure handling
└── Post-init Guidance
    ├── FR-008: Display next steps
    ├── FR-009: Load from external file
    └── FR-010: Model customization content
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation |
|--------|----------|-------------|---------------|----------|------------|
| NFR-001 | Performance | Init command completes in reasonable time even with model refresh | < 10 seconds on good network | P1 | Timing test |
| NFR-002 | Reliability | Init succeeds when network unavailable | 100% success rate offline | P0 | Offline test |
| NFR-003 | Maintainability | Guidance text editable without code changes | Edit markdown file only | P2 | Manual verification |
| NFR-004 | Testability | All new functionality has unit test coverage | 90%+ coverage for new code | P1 | Coverage report |
| NFR-005 | Usability | Error messages are clear and actionable | User can resolve issue from message | P1 | UX review |
| NFR-006 | Compatibility | Existing init tests continue to pass | 0 test regressions | P0 | Test suite |

---

## 8. Data & Analytics

### Instrumentation Plan

| Event | Trigger | Purpose |
|-------|---------|---------|
| `init.auth_check.result` | Auth check completes | Track auth success rate |
| `init.model_refresh.result` | Model refresh completes | Track refresh success/failure |
| `init.completed` | Init finishes | Track overall success |

### Success Metrics

| Metric | Baseline | Target | Window |
|--------|----------|--------|--------|
| Init completion rate | Current | No regression | 30 days |
| Auth-related support tickets | Current | 50% reduction | 30 days |
| Time to first successful run | Unknown | Reduced | 30 days |

---

## 9. Dependencies

| Dependency | Type | Criticality | Risk | Mitigation |
|------------|------|-------------|------|------------|
| CopilotSDKClient `is_authenticated()` | Internal | High | Method signature change | Pin to current interface |
| CopilotSDKClient `list_models()` | Internal | Medium | May require async init | Use existing async patterns |
| `importlib.resources` | Python stdlib | Low | None | Standard library |
| `claude-sonnet-4.5` availability | External | Medium | Model unavailable | Verify before release |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation |
|---------|-------------|----------|------------|------------|
| R-001 | Model refresh adds latency to init | Medium | Medium | Timeout + async execution |
| R-002 | Auth check requires SDK initialization | Medium | Low | Lazy init or separate check |
| R-003 | Guidance file missing at runtime | Low | Low | Fallback to embedded default |
| R-004 | claude-sonnet-4.5 deprecated later | Low | Low | Abstract model constant |
| R-005 | Breaking existing test fixtures | Medium | Medium | Update fixtures as part of PR |

---

## 11. Privacy, Security & Compliance

### Data Classification

- No PII collected or stored
- Configuration files are local only
- Auth status checked but not persisted

### Security Considerations

- Auth guidance does not expose credentials
- Model list is non-sensitive data
- Guidance file is read-only resource

---

## 12. Operational Considerations

| Aspect | Requirement |
|--------|-------------|
| Deployment | Standard package update, no migration needed |
| Rollback | Revert to previous package version |
| Monitoring | Existing CLI error logging sufficient |
| Support | Document new behavior in troubleshooting guide |

---

## 13. Rollout & Launch Plan

### Phases

| Phase | Description | Gate Criteria |
|-------|-------------|---------------|
| 1 | Implementation | All FRs complete, tests pass |
| 2 | Review | PR approved, no regressions |
| 3 | Release | Merged to main, docs updated |

### Feature Flags

None required - changes are backward compatible.

---

## 14. Acceptance Test Scenarios

### AT-001: Fresh Init Creates Updated Default Config

**Description:** User runs init in a new project and gets optimal default configuration
**Preconditions:** No existing `teambot.json`, Copilot CLI authenticated
**Steps:**
1. User runs `teambot init` in a clean directory
2. Init completes successfully
3. User opens generated `teambot.json`
**Expected Result:**
- `"default_model": "claude-sonnet-4.5"` at top level
- Each agent (pm, ba, writer, builder-1, builder-2, reviewer) has `"model": "claude-sonnet-4.5"`
**Verification:** Parse JSON and assert field values

### AT-002: Init With Unauthenticated Copilot CLI

**Description:** User runs init without being authenticated to Copilot
**Preconditions:** Copilot CLI binary exists, user NOT authenticated
**Steps:**
1. User runs `teambot init`
2. Init checks authentication status
3. Init displays guidance message
4. Init continues and completes successfully
**Expected Result:**
- Warning message displayed mentioning `copilot auth` or `/login`
- Init completes successfully (exit code 0)
- `teambot.json` created correctly
**Verification:** Check console output for guidance, verify exit code, verify config created

### AT-003: Init With Network Failure During Model Refresh

**Description:** Model cache refresh fails due to network issues
**Preconditions:** Copilot CLI authenticated, network unavailable or SDK returns error
**Steps:**
1. User runs `teambot init`
2. Model refresh is attempted and fails
3. Warning displayed
4. Init continues
**Expected Result:**
- Warning message about model refresh failure
- Init completes successfully (exit code 0)
- `teambot.json` created correctly
**Verification:** Mock network failure, check warning displayed, verify init success

### AT-004: Post-Init Guidance Displayed

**Description:** User sees recommended next steps after init completes
**Preconditions:** Init completes successfully
**Steps:**
1. User runs `teambot init`
2. Init completes
3. Guidance text displayed
**Expected Result:**
- "Recommended Next Steps" section visible in output
- Content mentions per-agent model configuration
**Verification:** Check console output contains guidance text

### AT-005: Guidance Loaded From External File

**Description:** Guidance text comes from the scaffolds file, not hardcoded
**Preconditions:** `src/teambot/scaffolds/init-next-steps.md` exists
**Steps:**
1. Modify guidance file content
2. Run `teambot init`
3. Observe displayed guidance
**Expected Result:**
- Displayed text matches file content
**Verification:** Compare file content with console output

---

## 15. Open Questions

| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| Q-001 | What timeout should be used for model refresh? | Builder | Open |
| Q-002 | Should auth check be synchronous or async? | Builder | Open |
| Q-003 | Exact file path for guidance: `scaffolds/` or new `resources/` dir? | Builder | Resolved: `scaffolds/init-next-steps.md` |

---

## 16. Changelog

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2026-02-18 | Business Analyst | Initial specification |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Code | `src/teambot/config/loader.py:create_default_config()` | Current default config implementation |
| REF-002 | Code | `src/teambot/cli.py:cmd_init()` | Current init command implementation |
| REF-003 | Code | `src/teambot/cli.py:check_copilot_cli()` | Current binary check (no auth) |
| REF-004 | Code | `src/teambot/copilot/sdk_client.py:_check_auth()` | SDK auth check method |
| REF-005 | Code | `src/teambot/copilot/sdk_client.py:list_models()` | SDK model list method |
| REF-006 | Doc | `.teambot/init-command-model/artifacts/problem_statement.md` | Problem statement |

---

## Appendix A: Guidance File Content

**File:** `src/teambot/scaffolds/init-next-steps.md`

**Suggested Content:**

```markdown
## Recommended Next Steps

Your TeamBot project is initialized! Here are some tips to optimize your workflow:

### 1. Configure Per-Agent Models (Recommended)

For better quality, consider assigning premium models to critical agents:

```json
{
  "agents": [
    { "id": "pm", "model": "claude-opus-4.5" },
    { "id": "reviewer", "model": "claude-opus-4.5" },
    { "id": "builder-1", "model": "claude-sonnet-4.5" }
  ]
}
```

**Tip:** Use `/model list` to see available models and their capabilities.

### 2. Authenticate with Copilot CLI

If you haven't already, run `copilot auth` to authenticate.

### 3. Create Your First Objective

Create an objective file in `objectives/` and run:

```bash
teambot run objectives/my-task.md
```

For more information, see the documentation at `docs/guides/`.
```

---

## Appendix B: Expected Config Output

**Generated `teambot.json` structure (partial):**

```json
{
  "default_model": "claude-sonnet-4.5",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager",
      "model": "claude-sonnet-4.5",
      "parallel_capable": false,
      "workflow_stages": ["setup", "plan", "coordination"]
    },
    {
      "id": "ba",
      "persona": "business_analyst",
      "display_name": "Business Analyst",
      "model": "claude-sonnet-4.5",
      "parallel_capable": false,
      "workflow_stages": ["business_problem", "spec"]
    }
  ]
}
```

<!-- markdown-table-prettify-ignore-end -->
