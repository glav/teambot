<!-- markdownlint-disable-file -->
# Test Strategy: Startup Animation

**Strategy Date**: 2026-02-09
**Feature Specification**: `.teambot/startup-animation/artifacts/`
**Research Reference**: `.agent-tracking/research/20260209-startup-animation-research.md`
**Strategist**: Test Strategy Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES — 10 success criteria clearly defined | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | LOW — primarily visual rendering, no complex algorithms | 0 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | LOW — cosmetic feature, failure = no animation, CLI still works | 0 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | YES — animation design needs visual iteration | 0 | 3 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | MIXED — `should_animate()` is simple; frame rendering is visual | 0 | 1 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | MODERATE — visual tuning needs fast feedback | 0 | 1 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE — spec is clear, animation design may iterate | 0 | 1 |

### Decision Scores

| Score | Value | Threshold |
|-------|-------|-----------|
| **TDD Score** | **3** | ≥ 6 for TDD |
| **Code-First Score** | **6** | ≥ 5 for Code-First |

### Decision: **CODE-FIRST** (with targeted TDD for `should_animate()` decision logic)

---

## Recommended Testing Approach

**Primary Approach**: CODE-FIRST (Hybrid — Code-First for animation rendering, TDD-style for decision logic)

### Rationale

The startup animation feature is fundamentally a **visual/rendering concern** where the majority of code (frame generation, ASCII art, color application, Rich Live rendering) cannot be meaningfully asserted via unit tests — the output is aesthetic, not algorithmic. The core value of testing here lies in verifying the **decision logic** (should animation play?) and **configuration integration** (CLI flags, config file, TTY detection), not pixel-perfect frame verification.

The feature has low business risk — if the animation fails, the CLI still functions perfectly with a static fallback banner. This makes comprehensive TDD inappropriate for the rendering code, where rapid visual iteration is more productive. However, the `should_animate()` gating logic and config validation are **deterministic decision paths** with clear boolean outcomes, making them ideal for thorough test coverage.

Following the established pattern from `test_console.py` (direct object instantiation, no Rich output mocking) and `test_overlay.py` (terminal support mocking), the test strategy focuses on testable logic paths while trusting Rich's rendering capabilities.

**Key Factors:**
* Complexity: **LOW** — visual rendering, simple gating logic
* Risk: **LOW** — cosmetic feature, graceful fallback exists
* Requirements Clarity: **CLEAR** — well-defined success criteria
* Time Pressure: **MODERATE** — visual design benefits from fast iteration

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low — no complex algorithms; frame generation is data-driven
* **Integration Depth**: Moderate — touches CLI parser, config loader, visualization module
* **State Management**: Minimal — stateless rendering; config is read-once
* **Error Scenarios**: Simple — all failures degrade to static banner

### Risk Profile
* **Business Criticality**: LOW — purely cosmetic enhancement
* **User Impact**: All users see it on startup, but failure = static banner (existing behavior)
* **Data Sensitivity**: None — no user data involved
* **Failure Cost**: Negligible — worst case is no animation, CLI still works

### Requirements Clarity
* **Specification Completeness**: COMPLETE — 10 acceptance criteria, clear scope
* **Acceptance Criteria Quality**: PRECISE — measurable (duration, flags, config)
* **Edge Cases Identified**: 8 documented (TTY, dumb terminal, narrow, CI, etc.)
* **Dependencies Status**: STABLE — Rich 14.2.0 API is mature

---

## Test Strategy by Component

### Component 1: `should_animate()` Decision Logic — CODE-FIRST

**Approach**: Code-First with thorough coverage (write logic, then comprehensive tests)
**Rationale**: Boolean decision function with clear inputs/outputs. All branches are deterministic and testable. Following `test_overlay.py` pattern for terminal mocking.

**Test Requirements:**
* Coverage Target: 100% branch coverage
* Test Types: Unit
* Critical Scenarios:
  * Returns `True` when TTY + config enabled + no flag
  * Returns `False` for each disable condition independently
* Edge Cases:
  * `show_startup_animation` missing from config (default `True`)
  * `config` is `None` (animation plays)
  * `TERM=dumb` environment variable
  * `TEAMBOT_NO_ANIMATION` environment variable
  * Terminal too small (<60 cols or <10 rows)
  * `sys.stdout.isatty()` returns `False` (CI/pipes)

**Testing Sequence** (Code-First):
1. Implement `should_animate()` method
2. Add test for each boolean branch (8 test cases)
3. Verify 100% branch coverage
4. Add edge case tests

### Component 2: Config Validation (`show_startup_animation`) — CODE-FIRST

**Approach**: Code-First following existing `_validate_overlay()` pattern
**Rationale**: Direct extension of existing config validation. Pattern is well-established in `test_loader.py` (Lines 186-268).

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Valid `true`/`false` boolean accepted
  * Non-boolean value raises `ConfigError`
  * Missing field gets default `True` via `_apply_defaults()`
* Edge Cases:
  * String `"true"` is invalid (must be JSON boolean)
  * Integer `1`/`0` is invalid

**Testing Sequence** (Code-First):
1. Add validation to `_validate()` and default to `_apply_defaults()`
2. Add tests matching existing `TestOverlayConfig` pattern
3. Use `pytest.raises(ConfigError, match="...")` for error cases

### Component 3: CLI `--no-animation` Flag — CODE-FIRST

**Approach**: Code-First
**Rationale**: Simple argparse addition. Following existing `--verbose`/`--force` flag patterns.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Flag present → `args.no_animation == True`
  * Flag absent → `args.no_animation == False`
  * Flag passed through to animation logic

**Testing Sequence** (Code-First):
1. Add `--no-animation` to `create_parser()`
2. Test parser recognizes flag
3. Test default value is `False`

### Component 4: `StartupAnimation` Class — CODE-FIRST

**Approach**: Code-First with smoke tests
**Rationale**: Visual rendering code where output verification is aesthetic, not algorithmic. Following `test_console.py` pattern of testing data structures, not Rich output.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit + Smoke
* Critical Scenarios:
  * `play()` dispatches to animated or static path correctly
  * Static banner contains version string
  * Static banner contains "TeamBot" text
  * Frame generation returns non-empty list
  * ASCII fallback contains no Unicode box-drawing characters
* Edge Cases:
  * Console with `color_system=None` (no color)
  * Console with non-UTF-8 encoding

**Testing Sequence** (Code-First):
1. Implement full animation module
2. Add dispatch tests (mock `should_animate` to control path)
3. Add static banner content assertions
4. Add frame generation smoke test
5. Add ASCII fallback verification

### Component 5: CLI Integration (animation in `cmd_run`/`cmd_init`) — CODE-FIRST

**Approach**: Code-First
**Rationale**: Integration wiring — verify animation function is called at correct points.

**Test Requirements:**
* Coverage Target: 70%
* Test Types: Integration
* Critical Scenarios:
  * `cmd_run()` calls animation before agent display
  * `cmd_init()` calls animation before config display
  * `--no-animation` suppresses animation call
* Edge Cases:
  * Resume mode still shows animation

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest (with pytest-cov, pytest-mock, pytest-asyncio)
* **Version**: pytest 8.x (via `uv run pytest`)
* **Configuration**: `pyproject.toml` Lines 42-48
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` — `patch`, `patch.object`, `MagicMock` (already used in `test_overlay.py`)
* **Assertions**: Built-in `assert` statements (pytest style)
* **Coverage**: `pytest-cov` — Target: 85%+ for new module
* **Test Data**: Inline — no external test data files needed

### Test Organization
* **Test Location**: `tests/test_visualization/test_animation.py` (NEW)
* **Naming Convention**: `Test<Feature>` classes, `test_<scenario>` methods
* **Fixture Strategy**: Minimal — direct instantiation preferred (following `test_console.py`)
* **Setup/Teardown**: `unittest.mock.patch` context managers for environment mocking

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% for `should_animate()` + config validation
* **Integration Coverage**: 70% for CLI wiring
* **Critical Path Coverage**: 100% for all disable/enable conditions
* **Error Path Coverage**: 100% for config validation errors

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `should_animate()` | 100% | — | CRITICAL | All boolean branches |
| Config validation | 100% | — | HIGH | Error + default paths |
| CLI `--no-animation` | 100% | — | HIGH | Parser + flag propagation |
| `StartupAnimation` class | 80% | — | MEDIUM | Smoke tests, no visual assertion |
| CLI integration | — | 70% | MEDIUM | Verify wiring |

### Critical Test Scenarios

1. **Animation Disable — Config** (Priority: CRITICAL)
   * **Description**: `show_startup_animation: false` in `teambot.json` prevents animation
   * **Test Type**: Unit
   * **Success Criteria**: `should_animate()` returns `False`
   * **Test Approach**: Code-First

2. **Animation Disable — CLI Flag** (Priority: CRITICAL)
   * **Description**: `--no-animation` flag prevents animation
   * **Test Type**: Unit
   * **Success Criteria**: `should_animate()` returns `False`
   * **Test Approach**: Code-First

3. **Animation Disable — Non-TTY** (Priority: CRITICAL)
   * **Description**: Piped output / CI environment auto-disables animation
   * **Test Type**: Unit
   * **Success Criteria**: `should_animate()` returns `False` when `isatty()` is `False`
   * **Test Approach**: Code-First

4. **Graceful Degradation** (Priority: HIGH)
   * **Description**: Non-animated path produces static banner without errors
   * **Test Type**: Unit
   * **Success Criteria**: `_show_static_banner()` completes without exception, output contains "TeamBot"
   * **Test Approach**: Code-First

5. **Config Validation Error** (Priority: HIGH)
   * **Description**: Non-boolean `show_startup_animation` raises `ConfigError`
   * **Test Type**: Unit
   * **Success Criteria**: `ConfigError` with descriptive message
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **`TERM=dumb`**: Animation disabled, static banner shown
* **Terminal < 60 cols**: Animation disabled, compact/static banner
* **`TEAMBOT_NO_ANIMATION=1`**: Environment variable override
* **Config missing `show_startup_animation`**: Defaults to `True`
* **Config is `None`**: Animation plays (no config to check)
* **ASCII-only terminal**: Fallback logo without Unicode box-drawing

### Error Scenarios

* **Invalid `show_startup_animation` type**: `ConfigError("'show_startup_animation' must be a boolean")`
* **Rich `Live` failure**: Should be caught, fall back to static banner
* **Terminal size query failure**: Should default to no-animation (safe fallback)

---

## Test Data Strategy

### Test Data Requirements
* Config dicts: Inline Python dicts in test methods
* Agent colors: Imported from `AGENT_COLORS` constant
* ASCII art: Verified by checking for/against Unicode characters

### Test Data Management
* **Storage**: Inline in test file (no external fixtures needed)
* **Generation**: Manual — simple dicts and strings
* **Isolation**: Each test creates fresh objects
* **Cleanup**: No cleanup needed — no file/state side effects

---

## Example Test Patterns

### Example from Codebase — Console Display Tests

**File**: `tests/test_visualization/test_console.py` (Lines 7-14)
**Pattern**: Direct instantiation, no mocking

```python
def test_create_display(self):
    """Display initializes with empty agents."""
    from teambot.visualization.console import ConsoleDisplay

    display = ConsoleDisplay()

    assert display.agents == {}
    assert display.console is not None
```

### Example from Codebase — Terminal Support Mocking

**File**: `tests/test_visualization/test_overlay.py` (Lines 76-91)
**Pattern**: `patch.object()` for terminal capability isolation

```python
def test_init_with_position(self):
    """OverlayRenderer initializes with given position."""
    with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
        renderer = OverlayRenderer(position=OverlayPosition.BOTTOM_LEFT)
        assert renderer.state.position == OverlayPosition.BOTTOM_LEFT
```

### Example from Codebase — Config Error Testing

**File**: `tests/test_config/test_loader.py` (Lines ~236-250)
**Pattern**: `pytest.raises` with message matching

```python
def test_invalid_overlay_enabled_type(self, tmp_path):
    """Non-boolean overlay.enabled raises ConfigError."""
    config = {..., "overlay": {"enabled": "yes"}}
    config_file = tmp_path / "teambot.json"
    config_file.write_text(json.dumps(config))

    loader = ConfigLoader()
    with pytest.raises(ConfigError, match="'overlay.enabled' must be a boolean"):
        loader.load(config_file)
```

### Recommended Test Structure for Animation

```python
"""Tests for startup animation module — Code-First approach."""

from unittest.mock import MagicMock, patch


class TestShouldAnimate:
    """Tests for animation eligibility decision logic."""

    def test_returns_true_when_tty_and_enabled(self):
        """Animation plays when TTY, config enabled, no flags."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            result = anim.should_animate(config={"show_startup_animation": True})
        assert result is True

    def test_returns_false_when_no_animation_flag(self):
        """--no-animation flag disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        result = anim.should_animate(no_animation_flag=True)
        assert result is False

    def test_returns_false_when_config_disabled(self):
        """show_startup_animation=false disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        result = anim.should_animate(config={"show_startup_animation": False})
        assert result is False

    def test_returns_false_when_not_tty(self):
        """Non-TTY environment disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            result = anim.should_animate()
        assert result is False


class TestStartupAnimation:
    """Tests for animation rendering."""

    def test_play_calls_static_when_should_animate_false(self):
        """play() shows static banner when animation disabled."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with patch.object(anim, "should_animate", return_value=False):
            with patch.object(anim, "_show_static_banner") as mock_static:
                anim.play()
                mock_static.assert_called_once()

    def test_static_banner_contains_teambot(self):
        """Static banner includes TeamBot text."""
        # Verify renderable content includes branding
        ...


class TestAnimationConfig:
    """Tests for show_startup_animation config validation."""

    def test_default_is_true(self, tmp_path):
        """Missing show_startup_animation defaults to True."""
        import json
        from teambot.config.loader import ConfigLoader

        config = {"agents": [{"id": "pm", "persona": "project_manager"}]}
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config))

        loader = ConfigLoader()
        result = loader.load(config_file)
        assert result["show_startup_animation"] is True

    def test_invalid_type_raises_error(self, tmp_path):
        """Non-boolean show_startup_animation raises ConfigError."""
        import json
        from teambot.config.loader import ConfigError, ConfigLoader

        config = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "show_startup_animation": "yes",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'show_startup_animation' must be a boolean"):
            loader.load(config_file)
```

**Key Conventions:**
* Local imports inside test methods (matches `test_console.py`)
* Class-per-concern grouping
* `MagicMock()` for Rich Console (no real terminal output)
* `patch.object()` for method isolation
* `pytest.raises(match=...)` for error messages

---

## Success Criteria

### Test Implementation Complete When:
- [ ] All 8 `should_animate()` branches have tests
- [ ] Config validation has 3+ tests (valid, invalid type, default)
- [ ] CLI flag parsing has 2 tests (present, absent)
- [ ] Static banner smoke test passes
- [ ] Frame generation smoke test passes
- [ ] Coverage targets met (90%+ for decision logic, 80%+ for animation class)
- [ ] Tests follow `test_console.py` / `test_overlay.py` conventions
- [ ] All 920 existing tests still pass

### Test Quality Indicators:
* Tests are readable with descriptive docstrings
* Tests are fast (no `time.sleep` in tests — mock or skip animation)
* Tests are independent (no test order dependencies)
* Failures clearly indicate which condition broke
* Mock usage is minimal and targeted

---

## Implementation Guidance

### For Decision Logic (`should_animate`):
1. Implement all gating conditions
2. Write one test per boolean branch
3. Verify 100% branch coverage with `pytest --cov`

### For Animation Rendering:
1. Implement full animation with Rich Live
2. Add smoke test (no crash on `play()`)
3. Verify static banner content
4. Skip visual output verification (trust Rich library)

### For Config Integration:
1. Add `_validate` check following overlay pattern
2. Add `_apply_defaults` entry
3. Test with `pytest.raises(ConfigError, match=...)` pattern

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* Fast visual iteration during animation design
* Focus testing effort on testable logic paths
* Follows existing codebase test conventions
* Minimal test infrastructure needed

### Accepted Trade-offs:
* No automated visual regression testing (animation appearance is manual QA)
* Frame rendering coverage is smoke-level, not assertion-level
* Relies on Rich library correctness for terminal output

### Risk Mitigation:
* 100% branch coverage on `should_animate()` ensures all disable paths work
* Config validation tests prevent invalid settings from reaching animation code
* Static banner fallback tested as safety net for all degraded environments

---

## References

* **Research Doc**: [.agent-tracking/research/20260209-startup-animation-research.md](../research/20260209-startup-animation-research.md)
* **Test Examples**: `tests/test_visualization/test_console.py`, `tests/test_visualization/test_overlay.py`, `tests/test_config/test_loader.py`
* **Config Pattern**: `src/teambot/config/loader.py` Lines 198-236

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow Code-First approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
