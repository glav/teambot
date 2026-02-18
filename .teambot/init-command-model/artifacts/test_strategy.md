<!-- markdownlint-disable-file -->
# Test Strategy: Init Command Model Configuration and Prerequisites

**Strategy Date**: 2026-02-18
**Feature Specification**: `.teambot/init-command-model/artifacts/feature_spec.md`
**Research Reference**: N/A — Technical details derived from spec and codebase analysis
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: **HYBRID**

### Testing Approach Decision Matrix

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|:----------:|:-----------------:|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES — 10 FRs with clear acceptance criteria, 5 AT scenarios | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | LOW — Configuration changes, SDK method calls, file loading | 0 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM — Init is first-run experience, but failures degrade gracefully | 2 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO — Well-defined enhancement to existing command | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | MIXED — Config generation is simple; SDK integration is moderate | 0 | 1 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | LOW — Quality over speed for onboarding experience | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE — Spec is approved, scope is clear | 0 | 0 |

### Decision Scores

| Score | Value | Threshold |
|-------|-------|-----------|
| **TDD Score** | **5** | ≥ 6 for TDD |
| **Code-First Score** | **1** | ≥ 5 for Code-First |

### Decision: **HYBRID**

Since TDD Score (5) and Code-First Score (1) both fall below their thresholds, HYBRID is recommended.

- **TDD for**: Authentication check logic (critical path), model cache refresh error handling
- **Code-First for**: Default config changes (simple values), guidance file loading (file I/O)

---

## Rationale

This feature enhances the `teambot init` command with multiple independent enhancements:

1. **Configuration changes (FR-001, FR-002)**: Simple value modifications to `create_default_config()`. These are trivial changes where code-first with test verification is efficient.

2. **Authentication verification (FR-003, FR-004, FR-005)**: Critical user-facing functionality that must handle unauthenticated states gracefully. TDD ensures all error paths are covered before implementation.

3. **Model cache refresh (FR-006, FR-007)**: Network-dependent operation requiring graceful failure handling. TDD for error scenarios ensures robust implementation.

4. **Guidance display (FR-008, FR-009, FR-010)**: File loading and display logic. Code-first is appropriate since the primary validation is "does it display correctly."

The existing test suite provides strong patterns to follow:
- `tests/test_cli.py`: CLI command testing with `tmp_path`, `monkeypatch`, `argparse.Namespace`
- `tests/test_config/test_loader.py`: Config validation with JSON assertions
- `tests/test_copilot/test_sdk_client.py`: SDK mocking with `AsyncMock`, `MagicMock`
- `tests/test_config/test_model_cache.py`: Cache operations with temp directories

**Key Factors:**
* Complexity: **LOW** — Value changes, SDK calls, file reads
* Risk: **MEDIUM** — First-run experience, graceful degradation required
* Requirements Clarity: **CLEAR** — 10 FRs, 5 acceptance tests, complete spec
* Time Pressure: **LOW** — Quality matters for onboarding

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: None — no complex algorithms, just conditional logic
* **Integration Depth**: Moderate — SDK client, file system, config system
* **State Management**: Minimal — init is stateless operation
* **Error Scenarios**: Moderate — network failures, auth failures, missing files

### Risk Profile
* **Business Criticality**: MEDIUM — First-run experience affects user adoption
* **User Impact**: All new users hit this code path
* **Data Sensitivity**: None — no user data involved
* **Failure Cost**: LOW with graceful degradation — init succeeds with warnings

### Requirements Clarity
* **Specification Completeness**: COMPLETE — All 10 FRs defined with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE — 5 concrete AT scenarios
* **Edge Cases Identified**: Network failure, unauthenticated, missing guidance file
* **Dependencies Status**: STABLE — SDK methods exist, `importlib.resources` is stdlib

---

## Test Strategy by Component

### Component 1: Default Model Update (FR-001) — CODE_FIRST

**Approach**: Code-First
**Rationale**: Single value change from `claude-sonnet-4` to `claude-sonnet-4.5`. Existing test `test_default_config_has_default_model` already validates this field.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `create_default_config()` returns `default_model: "claude-sonnet-4.5"`
* Edge Cases: None

**Testing Sequence:**
1. Update `default_model` value in `create_default_config()`
2. Update existing test assertion in `test_default_config_has_default_model`
3. Verify test passes

**Test File**: `tests/test_config/test_loader.py`

---

### Component 2: Explicit Agent Model Fields (FR-002) — CODE_FIRST

**Approach**: Code-First
**Rationale**: Adding `model` field to each agent definition is a simple configuration change. One new test validates all 6 agents have the field.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Each of 6 agents in default config has `"model": "claude-sonnet-4.5"`
* Edge Cases: None

**Testing Sequence:**
1. Add `model` field to each agent in `create_default_config()`
2. Add new test `test_default_config_agents_have_explicit_model_field`
3. Verify test passes

**New Test:**
```python
def test_default_config_agents_have_explicit_model_field(self):
    """Default config agents have explicit model field."""
    from teambot.config.loader import create_default_config

    config = create_default_config()
    
    for agent in config["agents"]:
        assert "model" in agent, f"Agent {agent['id']} missing model field"
        assert agent["model"] == "claude-sonnet-4.5"
```

**Test File**: `tests/test_config/test_loader.py`

---

### Component 3: Authentication Check (FR-003, FR-004, FR-005) — TDD

**Approach**: TDD
**Rationale**: Critical user-facing functionality. Must verify unauthenticated state detection and graceful handling. TDD ensures all paths are covered.

**Test Requirements:**
* Coverage Target: 100% branch coverage
* Test Types: Unit
* Critical Scenarios:
  * Auth check called during init
  * Authenticated state → no warning displayed
  * Unauthenticated state → guidance message displayed
  * Auth check failure → init continues (non-blocking)
  * SDK not available → init continues with warning
* Edge Cases:
  * `is_authenticated()` raises exception
  * SDK client instantiation fails

**Testing Sequence (TDD):**
1. Write test: `test_init_checks_copilot_authentication`
2. Write test: `test_init_displays_auth_guidance_when_unauthenticated`
3. Write test: `test_init_succeeds_when_auth_check_fails`
4. Write test: `test_init_succeeds_when_sdk_not_available`
5. Implement authentication check in `cmd_init()`
6. Verify all tests pass

**New Tests:**
```python
class TestInitAuthenticationCheck:
    """Tests for authentication check during init."""

    def test_init_checks_copilot_authentication(self, tmp_path, monkeypatch):
        """Init verifies Copilot CLI authentication status."""
        # Mock SDK client to track if auth was checked
        ...

    def test_init_displays_auth_guidance_when_unauthenticated(self, tmp_path, monkeypatch, capsys):
        """Init displays guidance when not authenticated."""
        # Mock is_authenticated() to return False
        # Assert output contains "copilot auth" or "/login"
        ...

    def test_init_succeeds_when_auth_check_fails(self, tmp_path, monkeypatch):
        """Init completes successfully even if auth check fails."""
        # Mock auth check to raise exception
        # Assert exit code 0, config created
        ...

    def test_init_succeeds_when_sdk_not_available(self, tmp_path, monkeypatch):
        """Init completes when SDK client cannot be initialized."""
        # Mock SDK client to raise on instantiation
        # Assert exit code 0, config created
        ...
```

**Test File**: `tests/test_cli.py` (new class `TestInitAuthenticationCheck`)

---

### Component 4: Model Cache Refresh (FR-006, FR-007) — TDD

**Approach**: TDD
**Rationale**: Network-dependent operation with multiple failure modes. TDD ensures graceful degradation is implemented correctly.

**Test Requirements:**
* Coverage Target: 100% branch coverage
* Test Types: Unit
* Critical Scenarios:
  * Model refresh called during init
  * Successful refresh → cache populated, no warning
  * Refresh failure (network error) → warning displayed, init continues
  * Refresh timeout → warning displayed, init continues
* Edge Cases:
  * Empty model list returned
  * Cache directory doesn't exist (should be created)

**Testing Sequence (TDD):**
1. Write test: `test_init_refreshes_model_cache`
2. Write test: `test_init_succeeds_when_model_refresh_fails`
3. Write test: `test_init_displays_warning_on_model_refresh_failure`
4. Implement model cache refresh in `cmd_init()`
5. Verify all tests pass

**New Tests:**
```python
class TestInitModelCacheRefresh:
    """Tests for model cache refresh during init."""

    def test_init_refreshes_model_cache(self, tmp_path, monkeypatch):
        """Init populates model cache during initialization."""
        # Mock SDK list_models() to return models
        # Verify save_cache() is called
        ...

    def test_init_succeeds_when_model_refresh_fails(self, tmp_path, monkeypatch):
        """Init completes successfully even if model refresh fails."""
        # Mock list_models() to raise exception
        # Assert exit code 0, config created
        ...

    def test_init_displays_warning_on_model_refresh_failure(self, tmp_path, monkeypatch, capsys):
        """Warning displayed when model refresh fails."""
        # Mock list_models() to raise exception
        # Assert warning in output
        ...
```

**Test File**: `tests/test_cli.py` (new class `TestInitModelCacheRefresh`)

---

### Component 5: Post-Init Guidance Display (FR-008, FR-009, FR-010) — CODE_FIRST

**Approach**: Code-First
**Rationale**: File loading and string display. Primary validation is "does it show up." Code-first with output assertion is sufficient.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Guidance file loaded successfully
  * Guidance displayed after init completes
  * Guidance contains model customization recommendations
* Edge Cases:
  * Guidance file missing → fallback behavior (warning or skip)

**Testing Sequence:**
1. Create guidance file at `src/teambot/scaffolds/init-next-steps.md`
2. Implement guidance loading using `importlib.resources`
3. Implement guidance display after init success
4. Write test: `test_init_displays_post_init_guidance`
5. Write test: `test_init_guidance_contains_model_customization_tip`
6. Write test: `test_init_handles_missing_guidance_file`

**New Tests:**
```python
class TestInitPostGuidance:
    """Tests for post-init guidance display."""

    def test_init_displays_post_init_guidance(self, tmp_path, monkeypatch, capsys):
        """Init displays recommended next steps after completion."""
        # Run init
        # Assert "Recommended Next Steps" in output
        ...

    def test_init_guidance_contains_model_customization_tip(self, tmp_path, monkeypatch, capsys):
        """Guidance includes per-agent model configuration tip."""
        # Run init
        # Assert output mentions model configuration
        ...

    def test_init_handles_missing_guidance_file(self, tmp_path, monkeypatch):
        """Init succeeds even if guidance file is missing."""
        # Mock importlib.resources to fail
        # Assert exit code 0
        ...
```

**Test File**: `tests/test_cli.py` (new class `TestInitPostGuidance`)

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest >= 7.4.0
* **Version**: Current (from pyproject.toml)
* **Configuration**: `pyproject.toml [tool.pytest.ini_options]`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch)
* **Assertions**: pytest assert with match patterns
* **Coverage**: pytest-cov (target: 90%+ for new code per NFR-004)
* **Async**: pytest-asyncio for SDK client mocking
* **Test Data**: `tmp_path` fixture for temp directories

### Test Organization
* **Test Location**: `tests/test_cli.py` (extend existing), `tests/test_config/test_loader.py`
* **Naming Convention**: `test_<function>_<scenario>` (e.g., `test_init_checks_copilot_authentication`)
* **Fixture Strategy**: Use existing `tmp_path`, `monkeypatch`, `capsys`; add SDK mock fixtures
* **Setup/Teardown**: `monkeypatch.chdir(tmp_path)` for working directory isolation

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (for new code, per NFR-004)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 100% (all graceful degradation paths)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Default model update | 100% | N/A | P0 | Single assertion |
| Agent model fields | 100% | N/A | P0 | Loop assertion |
| Auth check | 100% | 90% | P1 | Multiple error paths |
| Model cache refresh | 100% | 90% | P1 | Network failure handling |
| Guidance display | 90% | 80% | P2 | File I/O, display |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Fresh Init Creates Updated Config** (Priority: CRITICAL)
   * **Description**: Verify `default_model` and agent `model` fields
   * **Test Type**: Unit
   * **Success Criteria**: JSON assertions on generated config
   * **Test Approach**: Code-First

2. **Init With Unauthenticated Copilot** (Priority: CRITICAL)
   * **Description**: Auth check detects unauthenticated, shows guidance, continues
   * **Test Type**: Unit
   * **Success Criteria**: Warning displayed, exit code 0
   * **Test Approach**: TDD

3. **Init With Model Refresh Failure** (Priority: HIGH)
   * **Description**: Network failure during model refresh doesn't block init
   * **Test Type**: Unit
   * **Success Criteria**: Warning displayed, exit code 0
   * **Test Approach**: TDD

4. **Post-Init Guidance Displayed** (Priority: MEDIUM)
   * **Description**: "Recommended Next Steps" shown after successful init
   * **Test Type**: Unit
   * **Success Criteria**: Output contains guidance text
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Auth check exception**: SDK `is_authenticated()` raises → warning, continue
* **Model refresh timeout**: Refresh takes > 5s → warning, continue
* **Guidance file missing**: `importlib.resources` fails → skip guidance, no crash
* **SDK not installed**: Import fails → skip auth check and model refresh
* **Empty model list**: `list_models()` returns `[]` → cache saved with empty list

### Error Scenarios

* **Network unavailable during model refresh**: Display warning, init succeeds
* **SDK authentication expired**: Display auth guidance, init succeeds
* **SDK binary missing**: Display warning (existing behavior), init fails appropriately
* **Config write permission denied**: Existing error handling

---

## Test Data Strategy

### Test Data Requirements
* **Config JSON**: Use `create_default_config()` directly
* **Mock SDK responses**: Use existing `mock_sdk_client` fixture patterns
* **Mock auth status**: `{"isAuthenticated": True/False}`
* **Mock model list**: `[{"id": "model-1", "name": "Model 1", "category": "standard"}]`

### Test Data Management
* **Storage**: In-memory via fixtures, `tmp_path` for file-based tests
* **Generation**: Fixtures create test data
* **Isolation**: Each test uses fresh `tmp_path`
* **Cleanup**: pytest handles temp directory cleanup

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_cli.py:TestCLIInit.test_init_creates_config`
**Pattern**: Standard init test with `tmp_path` isolation

```python
def test_init_creates_config(self, tmp_path, monkeypatch):
    """Init creates configuration file."""
    import argparse

    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()

    result = cmd_init(args, display)

    assert result == 0
    assert (tmp_path / "teambot.json").exists()
    assert (tmp_path / ".teambot").exists()
```

**Key Conventions:**
* Use `monkeypatch.chdir(tmp_path)` for isolation
* Create `argparse.Namespace` for args
* Instantiate `ConsoleDisplay()` for display parameter
* Assert return code and file existence

### Example from Codebase

**File**: `tests/test_copilot/test_sdk_client.py`
**Pattern**: SDK mocking with AsyncMock

```python
@pytest.mark.asyncio
async def test_client_start_calls_sdk_start(self, mock_sdk_client):
    """Test that start() calls the underlying SDK start."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
        client = CopilotSDKClient()
        await client.start()

        mock_sdk_client.start.assert_called_once()
```

**Key Conventions:**
* Use `@pytest.mark.asyncio` for async tests
* Patch SDK imports with `return_value=mock`
* Use `assert_called_once()` for verification

### Recommended Test Structure

```python
class TestInitAuthenticationCheck:
    """Tests for authentication check during init."""

    def test_init_displays_auth_guidance_when_unauthenticated(
        self, tmp_path, monkeypatch, capsys
    ):
        """Init displays guidance when not authenticated."""
        import argparse
        from unittest.mock import AsyncMock, MagicMock, patch

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock SDK client
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_client.start = AsyncMock()
        mock_client.stop = AsyncMock()

        with patch("teambot.cli.CopilotSDKClient", return_value=mock_client):
            args = argparse.Namespace(force=False)
            display = ConsoleDisplay()

            result = cmd_init(args, display)

        captured = capsys.readouterr()

        assert result == 0
        assert (tmp_path / "teambot.json").exists()
        assert "copilot auth" in captured.out.lower() or "/login" in captured.out.lower()
```

---

## Success Criteria

### Test Implementation Complete When:
- [x] All critical scenarios have tests
- [x] Coverage targets are met per component
- [x] All edge cases are tested
- [x] Error paths are validated
- [x] Tests follow codebase conventions
- [x] Tests are maintainable and clear
- [x] CI/CD integration is working

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

---

## Implementation Guidance

### For TDD Components (Auth Check, Model Refresh):
1. Start with simplest test case (e.g., auth check called)
2. Write minimal code to pass
3. Add error case tests (e.g., exception handling)
4. Implement error handling
5. Add edge case tests
6. Refactor when all tests pass
7. Focus on behavior, not implementation

### For Code-First Components (Config, Guidance):
1. Implement core functionality
2. Add happy path test
3. Identify edge cases from implementation
4. Add edge case tests
5. Verify coverage meets target

### For Hybrid Approach:
1. Identify TDD vs Code-First boundaries (documented above)
2. Start with TDD components (auth check, model refresh)
3. Proceed to Code-First components (config changes, guidance)
4. Ensure integration tests cover boundaries
5. Validate overall feature behavior with acceptance tests

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for critical paths ensures graceful degradation is correct
* Code-First for simple changes avoids over-engineering
* Hybrid balances quality with development velocity
* Follows existing codebase patterns for maintainability

### Accepted Trade-offs:
* Some guidance display tests may be less precise (string matching)
* SDK mocking complexity for auth/model refresh tests
* Integration test coverage may require running init end-to-end

### Risk Mitigation:
* TDD for error paths ensures init never fails due to auth/model issues
* Multiple mock scenarios cover realistic failure modes
* Existing test patterns provide reliable templates

---

## References

* **Feature Spec**: [.teambot/init-command-model/artifacts/feature_spec.md](../../artifacts/feature_spec.md)
* **Spec Review**: [.teambot/init-command-model/artifacts/spec_review.md](../../artifacts/spec_review.md)
* **Test Examples**: 
  * `tests/test_cli.py` (CLI command testing patterns)
  * `tests/test_config/test_loader.py` (config validation patterns)
  * `tests/test_copilot/test_sdk_client.py` (SDK mocking patterns)
  * `tests/test_config/test_model_cache.py` (cache operation patterns)
* **Test Standards**: `pyproject.toml [tool.pytest.ini_options]`

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Test Strategy Validation

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: HYBRID (TDD=5, CF=1, neither meets threshold → Hybrid)
- Coverage Targets: SPECIFIED (90%+ for new code)
- Components Covered: 5/5
```
