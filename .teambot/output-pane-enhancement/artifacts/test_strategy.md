<!-- markdownlint-disable-file -->
# Test Strategy: Output Pane Enhancement

**Strategy Date**: 2026-02-05  
**Feature Specification**: `.teambot/output-pane-enhancement/artifacts/feature_spec.md`  
**Research Reference**: `.agent-tracking/research/20260205-output-pane-enhancement-research.md`  
**Strategist**: Test Strategy Agent

---

## Recommended Testing Approach

**Primary Approach**: **HYBRID**

### Rationale

This feature enhances an existing, well-tested UI component (OutputPane) with new visual styling capabilities. The work combines both clearly-defined requirements (color mapping, icons, word wrap) and modifications to existing working code. A hybrid approach optimizes for:

1. **TDD for new pure functions** - `get_agent_style()`, `_check_handoff()`, and data mappings benefit from test-first development since they are pure functions with well-defined inputs/outputs
2. **Code-First for existing method modifications** - The `write_*` methods already work and have tests; enhancing them with styling is lower risk and benefits from quick iteration

The feature has clear acceptance criteria from the spec (FR-001 through FR-008), making TDD viable for core logic, while the UI integration aspects are better suited to code-first with visual verification.

**Key Factors:**
* Complexity: **MEDIUM** - String formatting and state tracking, not algorithm-heavy
* Risk: **MEDIUM** - UI-only changes, no data loss risk, but user-facing
* Requirements Clarity: **CLEAR** - Well-defined spec with exact colors, icons, and behaviors
* Time Pressure: **LOW** - Enhancement feature, not blocking release

---

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points For |
|--------|----------|-------|------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | **YES** | TDD +3 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | **LOW** | TDD +0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | **MEDIUM** | TDD +1 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | **NO** | Code-First +0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | **PARTIAL** | Code-First +1 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | **NO** | Code-First +0 |
| **Requirements Stability** | Are requirements likely to change during development? | **STABLE** | Code-First +0 |

### Decision Calculation

```
TDD Score:      3 (clarity) + 0 (complexity) + 1 (risk) = 4
Code-First:     0 (exploratory) + 1 (simplicity) + 0 (time) + 0 (stability) = 1

Result: TDD Score (4) and Code-First Score (1) → Falls in HYBRID range (4-5 TDD, 4-5 CF)
        But since TDD=4 and CF=1, lean toward TDD for core, Code-First for modifications

Decision: HYBRID (TDD for new components, Code-First for existing method enhancements)
```

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - String formatting, dictionary lookups, simple conditionals
* **Integration Depth**: MEDIUM - Integrates with Rich markup, RichLog widget, existing OutputPane
* **State Management**: LOW - Only `_last_agent_id` for handoff tracking
* **Error Scenarios**: LOW - Graceful fallbacks for unknown agents (default color/icon)

### Risk Profile
* **Business Criticality**: MEDIUM - User-facing UX improvement but not core functionality
* **User Impact**: HIGH - All users see output pane; poor formatting affects everyone
* **Data Sensitivity**: NONE - No PII, no sensitive data, display-only
* **Failure Cost**: LOW - Visual glitches only, no data loss or corruption

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All 8 functional requirements defined
* **Acceptance Criteria Quality**: PRECISE - Exact colors, icons, and behaviors specified
* **Edge Cases Identified**: 5 documented (unknown agent, same agent continues, code blocks, etc.)
* **Dependencies Status**: STABLE - Rich/Textual are pinned, PERSONA_COLORS exists

---

## Test Strategy by Component

### 1. `AGENT_PERSONAS` and `AGENT_ICONS` Constants - **TDD**

**Approach**: TDD  
**Rationale**: Data mappings are critical for correct behavior; tests define the expected mappings before implementation ensures no typos or missing entries.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * All 6 agents have persona mappings
  * All 6 agents have icon mappings
  * Mappings match spec (pm→blue, ba→cyan, etc.)
* Edge Cases:
  * Verify builder-1 and builder-2 share same persona

**Testing Sequence (TDD):**
1. Write `test_all_agents_have_personas` - fails
2. Add `AGENT_PERSONAS` dict - passes
3. Write `test_all_agents_have_icons` - fails
4. Add `AGENT_ICONS` dict - passes
5. Refactor: ensure constants are co-located

---

### 2. `get_agent_style()` Helper Function - **TDD**

**Approach**: TDD  
**Rationale**: Pure function with clear inputs/outputs; perfect TDD candidate. Tests define the contract before implementation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Returns correct (color, icon) tuple for each agent
  * PM returns ("blue", "📋")
  * BA returns ("cyan", "📊")
  * All 6 agents verified
* Edge Cases:
  * Unknown agent returns default ("white", "●")
  * Empty string agent returns default

**Testing Sequence (TDD):**
1. Write `test_get_agent_style_pm_returns_blue_and_clipboard` - fails (function doesn't exist)
2. Implement minimal `get_agent_style()` returning hardcoded values - passes
3. Write `test_get_agent_style_all_agents` - fails for non-PM agents
4. Implement full lookup logic - passes
5. Write `test_get_agent_style_unknown_agent_returns_default` - fails
6. Add fallback handling - passes
7. Refactor for clarity

---

### 3. `OutputPane.__init__()` with `wrap=True` - **Code-First**

**Approach**: Code-First  
**Rationale**: Single-line change to existing working code; test verifies the configuration after change.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * New OutputPane has wrap enabled
* Edge Cases:
  * Explicit wrap=False override still works

**Testing Sequence (Code-First):**
1. Modify `__init__` to set `wrap=True`
2. Write `test_outputpane_wrap_enabled_by_default`
3. Verify existing tests still pass

---

### 4. `_check_handoff()` Method - **TDD**

**Approach**: TDD  
**Rationale**: New logic for state transition detection; well-defined behavior benefits from test-first.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Returns True when previous agent differs from current
  * Returns False when same agent continues
  * Returns False when no previous agent (first message)
* Edge Cases:
  * None → "pm" = False (first message)
  * "pm" → "pm" = False (same agent)
  * "pm" → "builder-1" = True (handoff)

**Testing Sequence (TDD):**
1. Write `test_check_handoff_first_message_returns_false` - fails
2. Implement `_check_handoff` returning False for None - passes
3. Write `test_check_handoff_same_agent_returns_false` - should pass
4. Write `test_check_handoff_different_agent_returns_true` - fails
5. Implement comparison logic - passes

---

### 5. `_write_handoff_separator()` Method - **Code-First**

**Approach**: Code-First  
**Rationale**: Simple string formatting; easier to implement and then verify output format.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Separator contains horizontal line
  * Separator contains new agent icon and ID
  * Separator uses new agent's color
* Edge Cases:
  * Very long agent ID doesn't break formatting

**Testing Sequence (Code-First):**
1. Implement `_write_handoff_separator(from_agent, to_agent)`
2. Write `test_handoff_separator_contains_divider_line`
3. Write `test_handoff_separator_shows_new_agent`
4. Write `test_handoff_separator_uses_agent_color`

---

### 6. Enhanced `write_task_complete()` - **Code-First**

**Approach**: Code-First  
**Rationale**: Modifying existing working method; existing tests verify baseline behavior.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Output includes persona color for agent ID
  * Output includes persona icon
  * Handoff separator appears on agent change
  * Existing tests continue to pass (timestamp, checkmark, content)
* Edge Cases:
  * Unknown agent gets default styling
  * Empty result still works

**Testing Sequence (Code-First):**
1. Modify method to use `get_agent_style()`
2. Run existing tests - should still pass
3. Write `test_write_task_complete_uses_persona_color`
4. Write `test_write_task_complete_includes_icon`
5. Write `test_write_task_complete_triggers_handoff_separator`

---

### 7. Enhanced `write_task_error()` - **Code-First**

**Approach**: Code-First  
**Rationale**: Same pattern as write_task_complete; parallel implementation.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Output includes persona color for agent ID
  * Output includes persona icon
  * Error indicator (✗) still present
* Edge Cases:
  * Long error message with persona styling

**Testing Sequence (Code-First):**
1. Modify method to use `get_agent_style()`
2. Run existing tests
3. Write `test_write_task_error_uses_persona_color`
4. Write `test_write_task_error_includes_icon`

---

### 8. Enhanced `write_streaming_start()` - **Code-First**

**Approach**: Code-First  
**Rationale**: Same pattern as other write methods.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Streaming indicator uses persona color
  * Agent ID uses persona color
  * Icon appears before agent ID
* Edge Cases:
  * Multiple agents streaming simultaneously

**Testing Sequence (Code-First):**
1. Modify method to use `get_agent_style()`
2. Run existing streaming tests
3. Write `test_streaming_start_uses_persona_color`
4. Write `test_streaming_start_includes_icon`

---

### 9. Enhanced `finish_streaming()` - **Code-First**

**Approach**: Code-First  
**Rationale**: Same pattern as other write methods.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Final output uses persona color
  * Icon appears in final output
  * Both success and error cases styled
* Edge Cases:
  * Agent not in streaming buffers (early return)

**Testing Sequence (Code-First):**
1. Modify method to use `get_agent_style()`
2. Run existing streaming tests
3. Write `test_finish_streaming_uses_persona_color`
4. Write `test_finish_streaming_success_includes_icon`
5. Write `test_finish_streaming_error_includes_icon`

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Per pyproject.toml requirements
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock.patch` - For mocking `write()` and `scroll_end()` methods
* **Assertions**: pytest built-in assertions with string matching
* **Coverage**: pytest-cov - Target: 85%+
* **Test Data**: Hardcoded expected values in tests (agent IDs, colors, icons)

### Test Organization
* **Test Location**: `tests/test_ui/test_output_pane.py` (extend existing file)
* **Additional Location**: `tests/test_visualization/test_console.py` (for constants and helper)
* **Naming Convention**: `test_<method_name>_<scenario>`
* **Fixture Strategy**: Direct instantiation of OutputPane (no fixtures needed)
* **Setup/Teardown**: Per-test fresh OutputPane instances

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 85% (minimum)
* **Integration Coverage**: 70%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 80%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `AGENT_PERSONAS` | 100% | N/A | CRITICAL | All 6 agents mapped |
| `AGENT_ICONS` | 100% | N/A | CRITICAL | All 6 agents mapped |
| `get_agent_style()` | 100% | N/A | CRITICAL | Pure function, easy to cover |
| `_check_handoff()` | 100% | N/A | HIGH | State transition logic |
| `_write_handoff_separator()` | 90% | N/A | MEDIUM | String formatting |
| `write_task_complete()` | 90% | 80% | CRITICAL | Core user-facing output |
| `write_task_error()` | 90% | 80% | CRITICAL | Error visibility |
| `write_streaming_start()` | 90% | 80% | HIGH | Streaming UX |
| `finish_streaming()` | 90% | 80% | HIGH | Streaming completion |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Agent Color Mapping** (Priority: CRITICAL)
   * **Description**: Each agent ID maps to correct persona color
   * **Test Type**: Unit
   * **Success Criteria**: PM→blue, BA→cyan, Writer→green, Builder→yellow, Reviewer→magenta
   * **Test Approach**: TDD

2. **Agent Icon Display** (Priority: CRITICAL)
   * **Description**: Each agent ID displays correct icon
   * **Test Type**: Unit
   * **Success Criteria**: PM→📋, BA→📊, Writer→📝, Builder→🔨, Reviewer→🔍
   * **Test Approach**: TDD

3. **Word Wrap Enabled** (Priority: CRITICAL)
   * **Description**: OutputPane has word wrap enabled by default
   * **Test Type**: Unit
   * **Success Criteria**: `wrap=True` in RichLog configuration
   * **Test Approach**: Code-First

4. **Handoff Detection** (Priority: HIGH)
   * **Description**: Agent change triggers handoff separator
   * **Test Type**: Unit
   * **Success Criteria**: Separator appears when `_last_agent_id != agent_id`
   * **Test Approach**: TDD

5. **Multi-Agent Styling** (Priority: HIGH)
   * **Description**: Multiple agents streaming show distinct colors
   * **Test Type**: Unit
   * **Success Criteria**: PM output has blue, Builder output has yellow
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Unknown Agent ID**: Returns default styling (white color, ● icon)
* **Same Agent Continues**: No handoff separator between consecutive messages from same agent
* **First Message**: No handoff separator (no previous agent)
* **Empty Agent ID**: Graceful handling with default styling
* **Builder-1 vs Builder-2**: Both use same color (yellow) but are tracked independently

### Error Scenarios

* **Agent not in streaming buffers**: `finish_streaming()` returns early gracefully
* **Missing persona mapping**: Falls back to "builder" persona
* **Missing icon mapping**: Falls back to "●" icon

---

## Test Data Strategy

### Test Data Requirements
* **Agent IDs**: ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
* **Colors**: {"blue", "cyan", "green", "yellow", "magenta"}
* **Icons**: {"📋", "📊", "📝", "🔨", "🔍"}
* **Sample Messages**: Short strings like "Plan created", "Error occurred"

### Test Data Management
* **Storage**: Hardcoded in test files (simple, static data)
* **Generation**: Manual - known expected values
* **Isolation**: Each test creates fresh OutputPane instance
* **Cleanup**: Automatic - no external state to clean

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_ui/test_output_pane.py` (Lines 24-38)  
**Pattern**: Mock-based output verification

```python
def test_write_task_complete_format(self):
    """write_task_complete has correct format with checkmark."""
    from teambot.ui.widgets.output_pane import OutputPane

    pane = OutputPane()

    with patch.object(pane, "write") as mock_write:
        with patch.object(pane, "scroll_end"):
            pane.write_task_complete("pm", "Plan created")

            mock_write.assert_called_once()
            call_arg = mock_write.call_args[0][0]
            assert "✓" in call_arg
            assert "@pm" in call_arg
            assert "Plan created" in call_arg
```

**Key Conventions:**
* Import inside test method for isolation
* Mock both `write()` and `scroll_end()` methods
* Assert on call arguments for Rich markup verification
* Use `in` assertions for substring matching

### Recommended Test Structure for New Tests

```python
class TestAgentStyling:
    """Tests for agent-specific styling in OutputPane."""

    def test_get_agent_style_returns_correct_color_for_pm(self):
        """get_agent_style returns blue color and clipboard icon for PM."""
        from teambot.visualization.console import get_agent_style

        color, icon = get_agent_style("pm")

        assert color == "blue"
        assert icon == "📋"

    def test_write_task_complete_uses_persona_color(self):
        """write_task_complete applies persona color to agent ID."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("pm", "Plan created")

                call_arg = mock_write.call_args[0][0]
                # Verify Rich markup contains blue color for PM
                assert "[blue]" in call_arg
                assert "📋" in call_arg


class TestHandoffDetection:
    """Tests for agent handoff separator functionality."""

    def test_check_handoff_returns_false_for_first_message(self):
        """First message has no previous agent, so no handoff."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = None

        result = pane._check_handoff("pm")

        assert result is False

    def test_check_handoff_returns_true_for_different_agent(self):
        """Different agent triggers handoff."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = "pm"

        result = pane._check_handoff("builder-1")

        assert result is True
```

---

## Success Criteria

### Test Implementation Complete When:
- [ ] All critical scenarios have tests (agent colors, icons, wrap, handoff)
- [ ] Coverage targets met: 85% unit, 70% integration
- [ ] All 6 agents verified in styling tests
- [ ] Edge cases tested (unknown agent, same agent, first message)
- [ ] Error paths validated (missing mappings, early returns)
- [ ] Tests follow existing codebase conventions (mock pattern)
- [ ] CI/CD integration working (all tests pass in `uv run pytest`)

### Test Quality Indicators:
* ✅ Tests are readable and self-documenting (descriptive names and docstrings)
* ✅ Tests are fast (<1 second each, no external dependencies)
* ✅ Tests are reliable (no flakiness, deterministic)
* ✅ Tests are independent (no test order dependencies)
* ✅ Failures clearly indicate the problem (specific assertions)
* ✅ Mock/stub usage is minimal and appropriate

---

## Implementation Guidance

### For TDD Components (`get_agent_style`, `_check_handoff`, constants):

1. Write failing test for simplest case (e.g., PM color)
2. Implement minimal code to pass (hardcode if needed)
3. Write next test case (e.g., BA color)
4. Generalize implementation to pass all cases
5. Refactor for clarity while keeping tests green
6. Focus on **behavior**, not implementation details

### For Code-First Components (`write_*` method enhancements):

1. Implement the styling enhancement
2. Run existing tests first - ensure no regressions
3. Add new tests for color and icon presence
4. Identify edge cases from implementation
5. Add edge case tests
6. Verify coverage meets target

### For Hybrid Approach Overall:

1. **Phase 1**: TDD for constants and `get_agent_style()` (foundation)
2. **Phase 2**: TDD for `_check_handoff()` (handoff logic)
3. **Phase 3**: Code-First for `__init__` wrap change (simple)
4. **Phase 4**: Code-First for all `write_*` enhancements (bulk of work)
5. **Phase 5**: Add integration tests covering full flows
6. Validate overall feature behavior with manual visual testing

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for pure functions ensures correct color/icon mappings from start
* Code-First for UI methods allows faster iteration on visual output
* Existing test suite provides regression safety during modifications
* Hybrid approach balances thoroughness with development speed

### Accepted Trade-offs:
* Visual verification still needed for actual terminal rendering
* Some integration aspects (Rich markup rendering) tested indirectly via string assertions
* Code-First components may have slightly lower initial coverage (addressed by adding tests after)

### Risk Mitigation:
* Existing 17 tests provide baseline; any regression is caught immediately
* TDD for core logic prevents critical mapping errors
* Mock-based testing allows fast feedback without full Textual app context
* Manual visual QA planned as final validation step

---

## References

* **Feature Spec**: [.teambot/output-pane-enhancement/artifacts/feature_spec.md](../../.teambot/output-pane-enhancement/artifacts/feature_spec.md)
* **Research Doc**: [.agent-tracking/research/20260205-output-pane-enhancement-research.md](./../research/20260205-output-pane-enhancement-research.md)
* **Test Examples**: `tests/test_ui/test_output_pane.py`, `tests/test_visualization/test_console.py`
* **Test Standards**: pytest conventions per pyproject.toml

---

## Next Steps

1. ✅ Test strategy documented and ready for approval
2. ➡️ Upon approval, proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD for core, Code-First for enhancements

---

**Strategy Status**: DRAFT  
**Approved By**: PENDING  
**Ready for Planning**: YES (upon approval)

---

## Validation

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD=4, CF=1 → HYBRID)
- Approach: HYBRID (TDD for core, Code-First for modifications)
- Coverage Targets: SPECIFIED (85% unit, 70% integration)
- Components Covered: 9/9
```
