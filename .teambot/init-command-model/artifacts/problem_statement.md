# Problem Statement: Init Command Model Configuration and Prerequisites

## Executive Summary

The `teambot init` command has several usability gaps that create friction for new users and limit customization flexibility. Users encounter outdated default models, incomplete agent configurations, and potential authentication failures that could be prevented with upfront checks.

---

## Business Problem

### Problem 1: Outdated Default Model

**Current State:** The default model is set to `claude-sonnet-4` in `create_default_config()`.

**Impact:** Users start with an older model when newer, higher-quality options (e.g., `claude-sonnet-4.5`) are available. This results in suboptimal output quality and requires manual intervention to upgrade.

**Business Value Lost:** Reduced initial user satisfaction; extra configuration steps before achieving optimal results.

---

### Problem 2: Missing Explicit Agent Model Configuration

**Current State:** Individual agents in the default configuration do not have explicit `"model"` fields. Model resolution falls back to the global `default_model` setting.

**Impact:** 
- Users who want to customize models per-agent must discover this capability through documentation
- No visual indication in the config file that per-agent customization is possible
- Makes it harder for users to experiment with different models for different roles

**Business Value Lost:** Reduced customization discoverability; users may not realize they can optimize quality by assigning premium models to critical agents (e.g., reviewer, PM).

---

### Problem 3: No Model Cache Refresh During Init

**Current State:** The `teambot init` command does not refresh or populate the model cache. Users must manually run `/model --refresh` to see available models.

**Impact:**
- First-run experience is incomplete
- Model selection commands may fail or show stale data
- Users may not know which models are available

**Business Value Lost:** Poor first-run experience; potential confusion when model commands fail.

---

### Problem 4: No Authentication Check During Init

**Current State:** `check_copilot_cli()` only verifies that the `copilot` binary exists in PATH. It does not check whether the user is authenticated.

**Impact:**
- Users can complete init successfully but encounter authentication failures during actual workflow execution
- Delayed failure creates frustration and confusion
- Error messages during workflow execution are less actionable than proactive guidance during init

**Business Value Lost:** Poor user experience; wasted time discovering auth issues late in the process.

---

### Problem 5: No Post-Init Guidance

**Current State:** After init completes, users see the configured agents but receive no guidance on recommended next steps for optimization.

**Impact:**
- Users may not know about optimization opportunities (e.g., assigning premium models to critical agents)
- Reduced adoption of best practices
- Users must consult external documentation

**Business Value Lost:** Missed opportunity to guide users toward optimal configuration.

---

### Problem 6: Hardcoded Guidance Text

**Current State:** Any guidance text would need to be hardcoded in CLI code.

**Impact:**
- Difficult to update guidance without code changes
- Cannot be localized or customized easily
- Maintenance burden on developers

**Business Value Lost:** Reduced maintainability; slower iteration on user guidance.

---

## Goals

| # | Goal | Measurable Outcome |
|---|------|-------------------|
| G1 | Update default model | Default model is `claude-sonnet-4.5` |
| G2 | Explicit agent model fields | Each agent has `"model"` field in default config |
| G3 | Auto-populate model cache | `teambot init` refreshes model cache automatically |
| G4 | Pre-flight auth check | Init verifies Copilot CLI authentication and guides users |
| G5 | Post-init guidance | "Recommended Next Steps" displayed after successful init |
| G6 | Configurable guidance text | Next steps loaded from external source file |

---

## Success Criteria

### Functional Requirements

- [ ] **SC-1:** Default model in `create_default_config()` is `claude-sonnet-4.5`
- [ ] **SC-2:** Each agent in default config has explicit `"model"` field (set to default model value)
- [ ] **SC-3:** Running `teambot init` populates model cache (equivalent to `/model --refresh`)
- [ ] **SC-4:** If model cache population fails, warning shown but init continues successfully
- [ ] **SC-5:** Running `teambot init` checks Copilot CLI authentication status
- [ ] **SC-6:** If not authenticated, helpful message guides user to `copilot auth` or `/login`
- [ ] **SC-7:** After init completes, "Recommended Next Steps" guidance is displayed
- [ ] **SC-8:** Next steps guidance suggests per-agent model configuration for quality
- [ ] **SC-9:** Next steps text loaded from configurable source file in TeamBot repo

### Non-Functional Requirements

- [ ] **SC-10:** All existing tests pass
- [ ] **SC-11:** New tests cover model cache refresh functionality
- [ ] **SC-12:** New tests cover authentication check functionality
- [ ] **SC-13:** Documentation updated to reflect new init behavior

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| Must not break existing init functionality | Existing users depend on current behavior |
| Must work when Copilot CLI installed but not authenticated | Graceful degradation required |
| Must handle network failures during model cache refresh | Offline/restricted network scenarios |
| Init must succeed even if model refresh fails | Non-blocking enhancement |
| Error messages must be clear and actionable | User experience requirement |

---

## Stakeholders

| Role | Interest |
|------|----------|
| New Users | Smooth onboarding, clear guidance |
| Existing Users | No breaking changes, improved defaults |
| Maintainers | Easy-to-update guidance text, testable code |

---

## Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| Copilot CLI authentication mechanism | External | Need to identify reliable auth check method |
| Model cache refresh mechanism | Internal | Need to verify refresh logic exists |
| Guidance text source file location | Design Decision | Must define file format and location |

---

## Assumptions

1. The `claude-sonnet-4.5` model is available and stable for production use
2. Copilot CLI provides a mechanism to check authentication status (e.g., exit code, command output)
3. Model cache refresh can be triggered programmatically from Python
4. A markdown or text file is an acceptable format for guidance text
5. Users have internet connectivity during initial setup (required for auth and model refresh)

---

## Out of Scope

- Changes to the Copilot CLI itself
- New authentication mechanisms (using existing Copilot auth)
- Changes to workflow execution logic
- Model billing or pricing changes
- Multi-language/localization of guidance text (future enhancement)

---

## Acceptance Criteria Summary

The init command enhancement is complete when:

1. ✅ Running `teambot init` creates config with `claude-sonnet-4.5` default model
2. ✅ Each agent in generated config has explicit `"model": "claude-sonnet-4.5"` field
3. ✅ Model cache is automatically refreshed during init (with graceful failure handling)
4. ✅ Authentication status is checked with clear guidance if not authenticated
5. ✅ "Recommended Next Steps" displayed from external source file
6. ✅ All tests pass (existing + new coverage)
7. ✅ Documentation reflects new behavior

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-18 | Business Analyst | Initial problem statement |
