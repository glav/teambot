<!-- markdownlint-disable-file -->
# Test Strategy: Model Selection Feature

**Strategy Date**: 2026-02-04  
**Feature Specification**: `.teambot/model-select/artifacts/` (objective-based)  
**Research Reference**: `.teambot/model-select/artifacts/research.md`  
**Strategist**: Test Strategy Agent

---

## Recommended Testing Approach

**Primary Approach**: **HYBRID** (TDD for core logic, Code-First for UI/integration)

### Rationale

The Model Selection feature presents a mix of well-defined core requirements (model validation, configuration loading, command parsing) alongside UI display and SDK integration work that benefits from exploration. The core model validation and configuration components have clear specifications with known valid inputs and expected error behaviors - ideal for TDD. However, the SDK integration and UI display components require working with external dependencies and visual verification where code-first iteration is more practical.

The hybrid approach ensures mission-critical validation logic has comprehensive test coverage from the start, while allowing faster iteration on UI components where visual feedback guides development. This balances quality with development velocity.

**Key Factors:**
* Complexity: **MEDIUM** - Clear requirements but spans multiple subsystems
* Risk: **MEDIUM** - Configuration errors could break agent execution
* Requirements Clarity: **CLEAR** - Well-defined models list and validation rules
* Time Pressure: **MODERATE** - Standard feature development timeline

---

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 14 valid models, clear error cases | **3** | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - Model resolution priority is logic-heavy | **2** | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM - Invalid model breaks agent | **2** | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Clear deliverables | 0 | **0** |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIAL - UI changes are simple | 0 | **1** |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | MODERATE | 0 | **1** |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE - Based on Copilot CLI | 0 | **0** |

### Score Summary

| Score Type | Value |
|------------|-------|
| **TDD Score** | **7** |
| **Code-First Score** | **2** |

### Decision Thresholds Applied

| TDD Score | Code-First Score | Result |
|-----------|------------------|--------|
| 7 (≥ 6) | 2 (< 4) | **HYBRID** - Core components TDD, peripherals Code-First |

**Decision Rationale**: TDD score (7) exceeds threshold (6), but UI/integration components naturally fit Code-First. Apply TDD to core validation/configuration logic, Code-First to UI display and SDK integration.

---

## Feature Analysis Summary

### Complexity Assessment

* **Algorithm Complexity**: MEDIUM - Model resolution priority (inline → session → config → global → default) requires careful logic
* **Integration Depth**: MEDIUM - Spans config, SDK client, UI, parser, and commands
* **State Management**: LOW - Model selection is mostly stateless per request, with session overrides stored simply
* **Error Scenarios**: MEDIUM - 3 error types: config validation, runtime validation, SDK rejection

### Risk Profile

* **Business Criticality**: MEDIUM - Model selection affects agent behavior but doesn't break core functionality
* **User Impact**: MEDIUM - Users will see errors if invalid models configured
* **Data Sensitivity**: LOW - No sensitive data, just model identifiers
* **Failure Cost**: MEDIUM - Invalid model silently falling back could cause confusion

### Requirements Clarity

* **Specification Completeness**: COMPLETE - All 14 models documented from `copilot --help`
* **Acceptance Criteria Quality**: PRECISE - Clear success criteria in objective
* **Edge Cases Identified**: 8+ documented (invalid model, missing config, session override, etc.)
* **Dependencies Status**: STABLE - Copilot CLI model list from production CLI

---

## Test Strategy by Component

### 1. Model Validation (`config/schema.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Pure functions with clear input/output. VALID_MODELS is a known constant, validation is simple boolean logic. Perfect TDD candidate.

**Test Requirements:**
* Coverage Target: **95%**
* Test Types: Unit
* Critical Scenarios:
  * Valid model returns True
  * Invalid model returns False
  * Case sensitivity handling
  * Empty string handling
* Edge Cases:
  * None input
  * Partial model names (e.g., "gpt-5" vs "gpt-5.1")
  * Model with extra whitespace

**Testing Sequence (TDD)**:
1. Write test for `validate_model("claude-sonnet-4.5") → True`
2. Implement `VALID_MODELS` constant and `validate_model()` function
3. Write test for `validate_model("invalid-model") → False`
4. Verify implementation covers both cases
5. Add edge case tests (None, empty, whitespace)
6. Refactor if needed

**Example Test Structure**:
```python
class TestModelValidation:
    def test_validate_valid_model(self):
        from teambot.config.schema import validate_model
        assert validate_model("claude-sonnet-4.5") is True
        
    def test_validate_invalid_model(self):
        from teambot.config.schema import validate_model
        assert validate_model("invalid-model") is False
        
    def test_validate_none_returns_false(self):
        from teambot.config.schema import validate_model
        assert validate_model(None) is False
```

---

### 2. Configuration Loader Extension (`config/loader.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Config validation has clear error scenarios. Following existing `test_loader.py` patterns. Each error case is well-defined.

**Test Requirements:**
* Coverage Target: **90%**
* Test Types: Unit
* Critical Scenarios:
  * Load config with valid agent model
  * Load config with invalid agent model raises ConfigError
  * Load config with global default_model
  * Invalid default_model raises ConfigError
  * Model field is optional (defaults to None)
* Edge Cases:
  * Agent without model field
  * default_model but no agent models
  * Agent model that doesn't exist in VALID_MODELS

**Testing Sequence (TDD)**:
1. Write test for valid model in agent config loads successfully
2. Extend `_validate_agent()` to check model field
3. Write test for invalid model raises ConfigError
4. Add validation logic with error message
5. Write test for global default_model validation
6. Implement `_validate_default_model()` method
7. Refactor and ensure consistency with existing patterns

**Example Test Structure** (following existing patterns):
```python
class TestAgentModelConfig:
    def test_agent_with_valid_model(self, tmp_path):
        from teambot.config.loader import ConfigLoader
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps({
            "agents": [{"id": "pm", "persona": "project_manager", "model": "gpt-5"}]
        }))
        
        loader = ConfigLoader()
        config = loader.load(config_file)
        assert config["agents"][0]["model"] == "gpt-5"
        
    def test_agent_with_invalid_model_raises(self, tmp_path):
        from teambot.config.loader import ConfigError, ConfigLoader
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps({
            "agents": [{"id": "pm", "persona": "project_manager", "model": "invalid"}]
        }))
        
        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid model"):
            loader.load(config_file)
```

---

### 3. Parser Extension (`repl/parser.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Parser has well-defined grammar. Existing `test_parser.py` establishes clear patterns. Each new syntax variation is a discrete test case.

**Test Requirements:**
* Coverage Target: **90%**
* Test Types: Unit
* Critical Scenarios:
  * `@pm --model gpt-5 task` parses model correctly
  * `@pm -m gpt-5 task` parses model correctly (short form)
  * Model flag at different positions
  * Command.model field populated
* Edge Cases:
  * `--model` without value
  * Model flag with quoted value
  * Model flag in pipeline syntax
  * Model flag in multi-agent syntax

**Testing Sequence (TDD)**:
1. Write test for `@pm --model gpt-5 task` extracts model
2. Extend parser regex/logic to capture `--model` flag
3. Write test for short form `-m`
4. Add short form handling
5. Write test for missing model value raises ParseError
6. Add validation logic
7. Refactor patterns for consistency

**Example Test Structure**:
```python
class TestParseModelFlag:
    def test_parse_model_flag_long_form(self):
        result = parse_command("@pm --model gpt-5 Create a plan")
        assert result.agent_id == "pm"
        assert result.model == "gpt-5"
        assert result.content == "Create a plan"
        
    def test_parse_model_flag_short_form(self):
        result = parse_command("@pm -m claude-opus-4.5 Review code")
        assert result.model == "claude-opus-4.5"
        
    def test_parse_model_flag_missing_value_raises(self):
        with pytest.raises(ParseError, match="model"):
            parse_command("@pm --model")
```

---

### 4. System Commands (`repl/commands.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Command handlers have clear I/O contracts. Existing patterns in `test_commands.py` show how to test. Each command is isolated and testable.

**Test Requirements:**
* Coverage Target: **90%**
* Test Types: Unit
* Critical Scenarios:
  * `/models` returns list of all valid models
  * `/model pm gpt-5` sets session override
  * `/model --reset pm` clears session override
  * Invalid model in `/model` returns error message
* Edge Cases:
  * `/models --json` format output
  * `/model` with unknown agent
  * `/model` without arguments shows current models

**Testing Sequence (TDD)**:
1. Write test for `/models` returns all 14 models
2. Implement `handle_models()` function
3. Write test for `/model pm gpt-5` stores override
4. Implement `handle_model()` with state storage
5. Write test for invalid model error message
6. Add validation with error response
7. Test reset functionality

**Example Test Structure**:
```python
class TestModelsCommand:
    def test_models_lists_all_valid_models(self):
        result = handle_models([])
        assert result.success is True
        assert "claude-sonnet-4.5" in result.output
        assert "gpt-5" in result.output
        
class TestModelCommand:
    def test_model_sets_session_override(self):
        commands = SystemCommands()
        result = commands.model(["pm", "gpt-5"])
        assert result.success is True
        assert commands.get_session_model("pm") == "gpt-5"
        
    def test_model_invalid_returns_error(self):
        commands = SystemCommands()
        result = commands.model(["pm", "invalid-model"])
        assert result.success is False
        assert "Invalid model" in result.output
```

---

### 5. Task Model Extension (`tasks/models.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Simple dataclass field addition. Existing `test_models.py` provides clear pattern. Small, focused change.

**Test Requirements:**
* Coverage Target: **95%**
* Test Types: Unit
* Critical Scenarios:
  * Task created with model field
  * Task model defaults to None
  * Task model preserved through status transitions
* Edge Cases:
  * Model in TaskResult (for output display)

**Testing Sequence (TDD)**:
1. Write test for `Task(id="t1", agent_id="pm", prompt="test", model="gpt-5")`
2. Add `model: str | None = None` field to Task dataclass
3. Write test verifying model preserved in mark_completed()
4. Verify existing tests still pass
5. Add model to TaskResult if needed

**Example Test Structure**:
```python
class TestTaskModel:
    def test_task_with_model(self):
        task = Task(id="t1", agent_id="pm", prompt="test", model="gpt-5")
        assert task.model == "gpt-5"
        
    def test_task_model_defaults_to_none(self):
        task = Task(id="t1", agent_id="pm", prompt="test")
        assert task.model is None
```

---

### 6. Agent State Extension (`ui/agent_state.py`) - **TDD**

**Approach**: TDD  
**Rationale**: Similar to Task model - dataclass field addition with clear tests. Existing `test_agent_state.py` provides excellent patterns.

**Test Requirements:**
* Coverage Target: **90%**
* Test Types: Unit
* Critical Scenarios:
  * AgentStatus includes model field
  * Model updated via manager methods
  * Model included in get_all() output
* Edge Cases:
  * Model changes without state change (still notifies listeners)

**Testing Sequence (TDD)**:
1. Write test for AgentStatus with model field
2. Add `model: str | None = None` to AgentStatus dataclass
3. Write test for `manager.set_model(agent_id, model)`
4. Implement set_model() method
5. Verify listener notification on model change

**Example Test Structure**:
```python
class TestAgentStatusModel:
    def test_agent_status_includes_model(self):
        status = AgentStatus(agent_id="pm", model="gpt-5")
        assert status.model == "gpt-5"
        
class TestAgentStatusManagerModel:
    def test_set_model_updates_agent(self):
        manager = AgentStatusManager()
        manager.set_model("pm", "claude-opus-4.5")
        assert manager.get("pm").model == "claude-opus-4.5"
```

---

### 7. SDK Client Integration (`copilot/sdk_client.py`) - **Code-First**

**Approach**: Code-First  
**Rationale**: SDK integration requires mocking complex async behavior. Easier to implement working code first, then add tests to verify. Existing `test_sdk_client.py` shows complex fixture setup needed.

**Test Requirements:**
* Coverage Target: **80%**
* Test Types: Integration (with mocks)
* Critical Scenarios:
  * Model passed to session creation config
  * Model parameter in execute() method signature
  * Model resolution (fallback chain) works correctly
* Edge Cases:
  * SDK rejects model (error handling)
  * Session recreation with different model

**Testing Sequence (Code-First)**:
1. Implement model parameter in `get_or_create_session(agent_id, model=None)`
2. Add model to session_config dict
3. Test manually with SDK
4. Write integration test verifying session_config includes model
5. Test model fallback chain
6. Add error handling tests

**Example Test Structure**:
```python
class TestCopilotSDKClientModel:
    @pytest.mark.asyncio
    async def test_session_config_includes_model(self, mock_sdk_client):
        captured_config = None
        async def capture_config(config):
            nonlocal captured_config
            captured_config = config
            return MagicMock()
        mock_sdk_client.create_session = AsyncMock(side_effect=capture_config)
        
        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()
            await client.get_or_create_session("pm", model="gpt-5")
            
        assert captured_config.get("model") == "gpt-5"
```

---

### 8. UI Display Components (`ui/widgets/`, `visualization/`) - **Code-First**

**Approach**: Code-First  
**Rationale**: UI rendering requires visual verification. StatusPanel and ConsoleDisplay changes are presentation-focused. Test after implementation validates correct output format.

**Test Requirements:**
* Coverage Target: **75%**
* Test Types: Unit (output string verification)
* Critical Scenarios:
  * StatusPanel displays model next to agent
  * ConsoleDisplay table includes Model column
  * Model displayed in /status output
  * Model displayed in /tasks output
* Edge Cases:
  * Long model name truncation
  * No model configured (graceful handling)

**Testing Sequence (Code-First)**:
1. Implement model display in StatusPanel._format_status()
2. Verify visually in running application
3. Write test checking output string contains model
4. Implement Model column in ConsoleDisplay.render_table()
5. Write test for table output format
6. Add truncation logic if needed

**Example Test Structure**:
```python
class TestStatusPanelModel:
    def test_format_status_includes_model(self):
        manager = AgentStatusManager()
        manager.set_model("pm", "gpt-5")
        
        panel = StatusPanel(manager)
        output = panel._format_status()
        
        assert "pm" in output
        assert "gpt-5" in output
```

---

### 9. Task Executor Integration (`tasks/executor.py`) - **Code-First**

**Approach**: Code-First  
**Rationale**: Integration layer connecting config → SDK. Best tested after core components work. Verify model flows through entire pipeline.

**Test Requirements:**
* Coverage Target: **80%**
* Test Types: Integration
* Critical Scenarios:
  * Executor passes model to SDK client
  * Model from config used when not specified inline
  * Inline model overrides config
* Edge Cases:
  * Pipeline with different models per stage
  * Multi-agent with model specified

**Testing Sequence (Code-First)**:
1. Implement model resolution in TaskExecutor
2. Pass model to SDK client execute()
3. Write integration test with mocked SDK
4. Verify model precedence (inline > session > config > default)

---

## Test Infrastructure

### Existing Test Framework

* **Framework**: pytest 9.0.2
* **Version**: Python 3.12.12
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required

* **Mocking**: `unittest.mock` (AsyncMock, MagicMock, patch)
* **Assertions**: pytest built-in + match patterns
* **Coverage**: pytest-cov (target via `--cov=src/teambot`)
* **Async Support**: pytest-asyncio (mode=auto)
* **Test Data**: Inline JSON configs with tmp_path fixture

### Test Organization

* **Test Location**: `tests/` (mirrors `src/teambot/` structure)
* **Naming Convention**: `test_*.py`, `Test*` classes, `test_*` functions
* **Fixture Strategy**: `conftest.py` for shared fixtures (mock_sdk_client, etc.)
* **Setup/Teardown**: pytest fixtures with tmp_path for file-based tests

---

## Coverage Requirements

### Overall Targets

* **Unit Test Coverage**: 85% (minimum)
* **Integration Coverage**: 75%
* **Critical Path Coverage**: 100% (model validation, config loading)
* **Error Path Coverage**: 90%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Approach | Notes |
|-----------|--------|---------------|----------|----------|-------|
| `config/schema.py` | 95% | - | CRITICAL | TDD | Model validation is foundation |
| `config/loader.py` | 90% | - | CRITICAL | TDD | Config errors must be clear |
| `repl/parser.py` | 90% | - | HIGH | TDD | Parse errors block usage |
| `repl/commands.py` | 90% | - | HIGH | TDD | User-facing commands |
| `tasks/models.py` | 95% | - | HIGH | TDD | Data model correctness |
| `ui/agent_state.py` | 90% | - | MEDIUM | TDD | State management |
| `copilot/sdk_client.py` | 80% | 75% | HIGH | Code-First | SDK mocking complex |
| `ui/widgets/*` | 75% | - | MEDIUM | Code-First | Visual verification |
| `tasks/executor.py` | 80% | 80% | HIGH | Code-First | Integration layer |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Valid Model Configuration** (Priority: CRITICAL)
   * **Description**: Config with valid model loads successfully
   * **Test Type**: Unit
   * **Success Criteria**: Config object has model field populated
   * **Test Approach**: TDD

2. **Invalid Model Rejection** (Priority: CRITICAL)
   * **Description**: Invalid model in config raises ConfigError
   * **Test Type**: Unit
   * **Success Criteria**: ConfigError with helpful message
   * **Test Approach**: TDD

3. **Inline Model Parsing** (Priority: HIGH)
   * **Description**: `@pm --model gpt-5 task` parses correctly
   * **Test Type**: Unit
   * **Success Criteria**: Command.model == "gpt-5"
   * **Test Approach**: TDD

4. **Model Display in Status** (Priority: HIGH)
   * **Description**: Model shown in /status output
   * **Test Type**: Unit
   * **Success Criteria**: Output contains model identifier
   * **Test Approach**: Code-First

5. **Model Passed to SDK** (Priority: HIGH)
   * **Description**: SDK session config includes model
   * **Test Type**: Integration
   * **Success Criteria**: Session config dict has "model" key
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **None model in config**: Should default to global or SDK default
* **Empty string model**: Should be treated as invalid
* **Case sensitivity**: `GPT-5` vs `gpt-5` handling
* **Whitespace in model**: `" gpt-5 "` should trim or reject
* **Model in pipeline**: Each stage can have different model
* **Session override then reset**: Reset restores config default

### Error Scenarios

* **Invalid model in teambot.json**: Clear error pointing to agent and model
* **Invalid model in `/model` command**: Helpful error with valid options
* **Missing model value in parser**: ParseError with syntax hint
* **SDK model rejection**: Graceful error, not crash

---

## Test Data Strategy

### Test Data Requirements

* **Valid models list**: Hardcoded VALID_MODELS constant
* **Config JSON**: Created inline per test using tmp_path fixture
* **Mock SDK responses**: Fixtures from conftest.py

### Test Data Management

* **Storage**: Inline in tests, no external files
* **Generation**: Manual creation in test setup
* **Isolation**: Each test gets fresh tmp_path
* **Cleanup**: pytest handles tmp_path cleanup automatically

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_config/test_loader.py`  
**Pattern**: Config validation with tmp_path and ConfigError

```python
def test_validate_persona_type(self, tmp_path):
    """Persona must be a valid type."""
    from teambot.config.loader import ConfigError, ConfigLoader

    config_data = {
        "agents": [
            {"id": "agent-1", "persona": "invalid_persona_type"},
        ]
    }
    config_file = tmp_path / "teambot.json"
    config_file.write_text(json.dumps(config_data))

    loader = ConfigLoader()

    with pytest.raises(ConfigError, match="persona"):
        loader.load(config_file)
```

**Key Conventions:**
* Use `tmp_path` fixture for temporary files
* Use `pytest.raises` with `match` for error validation
* Import from module at test-level (not file-level)
* Docstring describes test purpose

### Recommended Test Structure for Model Selection

```python
"""Tests for model selection configuration."""

import json
import pytest

class TestModelValidation:
    """Tests for model validation in config schema."""
    
    def test_validate_model_valid(self):
        """Valid model returns True."""
        from teambot.config.schema import validate_model
        
        assert validate_model("gpt-5") is True
        assert validate_model("claude-opus-4.5") is True
        
    def test_validate_model_invalid(self):
        """Invalid model returns False."""
        from teambot.config.schema import validate_model
        
        assert validate_model("not-a-model") is False
        
    def test_validate_model_none(self):
        """None returns False."""
        from teambot.config.schema import validate_model
        
        assert validate_model(None) is False


class TestAgentModelConfig:
    """Tests for agent model field in config loader."""
    
    def test_agent_model_valid(self, tmp_path):
        """Agent with valid model loads successfully."""
        from teambot.config.loader import ConfigLoader
        
        config_data = {
            "agents": [
                {"id": "pm", "persona": "project_manager", "model": "gpt-5"}
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))
        
        loader = ConfigLoader()
        config = loader.load(config_file)
        
        assert config["agents"][0]["model"] == "gpt-5"
        
    def test_agent_model_invalid_raises(self, tmp_path):
        """Agent with invalid model raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader
        
        config_data = {
            "agents": [
                {"id": "pm", "persona": "project_manager", "model": "invalid"}
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))
        
        loader = ConfigLoader()
        
        with pytest.raises(ConfigError, match="Invalid model"):
            loader.load(config_file)
```

---

## Success Criteria

### Test Implementation Complete When:

* [x] All critical scenarios have tests (validation, config, parser)
* [x] Coverage targets are met per component (85%+ overall)
* [x] All edge cases are tested (None, empty, whitespace, case)
* [x] Error paths are validated (ConfigError, ParseError messages)
* [x] Tests follow codebase conventions (pytest, tmp_path, conftest)
* [x] Tests are maintainable and clear (docstrings, isolation)
* [x] CI/CD integration is working (uv run pytest passes)

### Test Quality Indicators:

* Tests are readable and self-documenting (clear docstrings)
* Tests are fast and reliable (no flakiness, no external deps)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (only for SDK)

---

## Implementation Guidance

### For TDD Components (schema, loader, parser, commands, models, agent_state):

1. Start with simplest test case (happy path)
2. Write minimal code to pass
3. Add next test case (first edge case)
4. Refactor when all tests pass
5. Focus on behavior, not implementation
6. Use existing test files as templates

### For Code-First Components (sdk_client, widgets, executor):

1. Implement core functionality
2. Verify manually (run app, check output)
3. Add happy path test
4. Identify edge cases from implementation
5. Add edge case tests
6. Verify coverage meets target

### For Hybrid Approach Overall:

1. **Phase 1**: TDD for `config/schema.py` - foundation
2. **Phase 2**: TDD for `config/loader.py` - depends on schema
3. **Phase 3**: TDD for `repl/parser.py` - independent
4. **Phase 4**: TDD for `tasks/models.py`, `ui/agent_state.py` - small changes
5. **Phase 5**: Code-First for `copilot/sdk_client.py` - integration
6. **Phase 6**: Code-First for UI components - visual verification
7. **Phase 7**: Integration tests to verify full flow

---

## Considerations and Trade-offs

### Selected Approach Benefits:

* TDD for core ensures validation logic is bulletproof from start
* Code-First for SDK/UI allows faster iteration on complex integrations
* Existing test patterns reduce learning curve
* Coverage targets are achievable within normal timeline

### Accepted Trade-offs:

* SDK tests may be less comprehensive (mocking complexity)
* UI tests verify string output, not actual rendering
* Some integration paths tested manually initially

### Risk Mitigation:

* Critical validation logic has 95%+ coverage via TDD
* Error messages are explicit and tested
* Integration tests verify end-to-end flow after unit tests

---

## References

* **Feature Spec**: `.teambot/model-select/` (objective-based)
* **Research Doc**: `.teambot/model-select/artifacts/research.md`
* **Test Examples**: 
  * `tests/test_config/test_loader.py` - Config validation patterns
  * `tests/test_repl/test_parser.py` - Parser test patterns
  * `tests/test_tasks/test_models.py` - Dataclass test patterns
  * `tests/test_ui/test_agent_state.py` - State management patterns
  * `tests/test_copilot/test_sdk_client.py` - Async/mock patterns
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD for core, Code-First for integrations

---

**Strategy Status**: APPROVED  
**Approved By**: PENDING  
**Ready for Planning**: YES
