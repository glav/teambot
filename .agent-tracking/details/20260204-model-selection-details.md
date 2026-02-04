<!-- markdownlint-disable-file -->
# Implementation Details: Model Selection Support

**Date**: 2026-02-04  
**Plan Reference**: `.agent-tracking/plans/20260204-model-selection-plan.instructions.md`  
**Research Reference**: `.teambot/model-select/artifacts/research.md`  
**Test Strategy Reference**: `.teambot/model-select/artifacts/test_strategy.md`

---

## Phase 1: Core Model Infrastructure

### T1.1T: TDD Tests for Model Validation (Lines 30-65)

**File**: `tests/test_config/test_schema.py` (create or extend)

**Research Reference**: research.md Lines 91-108 (VALID_MODELS list)

```python
"""Tests for model validation in config schema."""

import pytest


class TestModelValidation:
    """Tests for validate_model function."""

    def test_validate_model_valid_claude(self):
        """Valid Claude models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("claude-sonnet-4.5") is True
        assert validate_model("claude-haiku-4.5") is True
        assert validate_model("claude-opus-4.5") is True
        assert validate_model("claude-sonnet-4") is True

    def test_validate_model_valid_gpt(self):
        """Valid GPT models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("gpt-5.2-codex") is True
        assert validate_model("gpt-5.2") is True
        assert validate_model("gpt-5.1-codex-max") is True
        assert validate_model("gpt-5.1-codex") is True
        assert validate_model("gpt-5.1") is True
        assert validate_model("gpt-5") is True
        assert validate_model("gpt-5.1-codex-mini") is True
        assert validate_model("gpt-5-mini") is True
        assert validate_model("gpt-4.1") is True

    def test_validate_model_valid_gemini(self):
        """Valid Gemini models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("gemini-3-pro-preview") is True

    def test_validate_model_invalid(self):
        """Invalid model names return False."""
        from teambot.config.schema import validate_model

        assert validate_model("invalid-model") is False
        assert validate_model("gpt-4") is False  # old model
        assert validate_model("claude-3") is False  # old model

    def test_validate_model_none(self):
        """None returns False."""
        from teambot.config.schema import validate_model

        assert validate_model(None) is False

    def test_validate_model_empty_string(self):
        """Empty string returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("") is False

    def test_validate_model_whitespace(self):
        """Whitespace-only returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("  ") is False
        assert validate_model("\t") is False


class TestGetAvailableModels:
    """Tests for get_available_models function."""

    def test_returns_all_models(self):
        """Returns complete list of 14 models."""
        from teambot.config.schema import get_available_models

        models = get_available_models()
        assert len(models) == 14
        assert "gpt-5" in models
        assert "claude-opus-4.5" in models
```

**Success Criteria**:
- All test methods pass
- Tests cover valid, invalid, edge cases

---

### T1.1: Create VALID_MODELS Constant (Lines 67-95)

**File**: `src/teambot/config/schema.py`

**Research Reference**: research.md Lines 91-108

**Implementation**:

```python
"""Configuration schema definitions for TeamBot."""

# Valid models supported by GitHub Copilot CLI
# Source: copilot --help output, verified 2026-02-04
VALID_MODELS: set[str] = {
    # Claude models
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "claude-opus-4.5",
    "claude-sonnet-4",
    # Gemini models
    "gemini-3-pro-preview",
    # GPT models
    "gpt-5.2-codex",
    "gpt-5.2",
    "gpt-5.1-codex-max",
    "gpt-5.1-codex",
    "gpt-5.1",
    "gpt-5",
    "gpt-5.1-codex-mini",
    "gpt-5-mini",
    "gpt-4.1",
}

# Model display information
MODEL_INFO: dict[str, dict[str, str]] = {
    "claude-sonnet-4.5": {"display": "Claude Sonnet 4.5", "category": "standard"},
    "claude-haiku-4.5": {"display": "Claude Haiku 4.5", "category": "fast"},
    "claude-opus-4.5": {"display": "Claude Opus 4.5", "category": "premium"},
    "claude-sonnet-4": {"display": "Claude Sonnet 4", "category": "standard"},
    "gemini-3-pro-preview": {"display": "Gemini 3 Pro (Preview)", "category": "standard"},
    "gpt-5.2-codex": {"display": "GPT-5.2-Codex", "category": "standard"},
    "gpt-5.2": {"display": "GPT-5.2", "category": "standard"},
    "gpt-5.1-codex-max": {"display": "GPT-5.1-Codex-Max", "category": "standard"},
    "gpt-5.1-codex": {"display": "GPT-5.1-Codex", "category": "standard"},
    "gpt-5.1": {"display": "GPT-5.1", "category": "standard"},
    "gpt-5": {"display": "GPT-5", "category": "standard"},
    "gpt-5.1-codex-mini": {"display": "GPT-5.1-Codex-Mini", "category": "fast"},
    "gpt-5-mini": {"display": "GPT-5 mini", "category": "fast"},
    "gpt-4.1": {"display": "GPT-4.1", "category": "fast"},
}
```

**Success Criteria**:
- `VALID_MODELS` contains exactly 14 model strings
- `MODEL_INFO` has display name and category for each model

---

### T1.2: Implement validate_model() Function (Lines 97-125)

**File**: `src/teambot/config/schema.py` (add to above)

**Implementation**:

```python
def validate_model(model: str | None) -> bool:
    """Validate that a model name is supported by Copilot CLI.

    Args:
        model: Model name to validate.

    Returns:
        True if model is valid, False otherwise.
    """
    if model is None:
        return False
    if not isinstance(model, str):
        return False
    model = model.strip()
    if not model:
        return False
    return model in VALID_MODELS


def get_available_models() -> list[str]:
    """Get list of all available model names.

    Returns:
        Sorted list of valid model names.
    """
    return sorted(VALID_MODELS)


def get_model_info(model: str) -> dict[str, str] | None:
    """Get display information for a model.

    Args:
        model: Model name.

    Returns:
        Dict with 'display' and 'category' keys, or None if invalid.
    """
    return MODEL_INFO.get(model)
```

**Success Criteria**:
- `validate_model("gpt-5")` returns `True`
- `validate_model("invalid")` returns `False`
- `validate_model(None)` returns `False`

---

## Phase 2: Configuration Extension

### T2.1T: TDD Tests for Config Model Loading (Lines 130-175)

**File**: `tests/test_config/test_loader.py` (extend existing)

**Research Reference**: research.md Lines 152-195

```python
class TestAgentModelConfig:
    """Tests for agent model field in config loader."""

    def test_agent_with_valid_model(self, tmp_path):
        """Agent with valid model loads successfully."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                    "model": "gpt-5",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0]["model"] == "gpt-5"

    def test_agent_with_invalid_model_raises(self, tmp_path):
        """Agent with invalid model raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                    "model": "invalid-model",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="Invalid model"):
            loader.load(config_file)

    def test_agent_without_model_is_valid(self, tmp_path):
        """Agent without model field is valid (optional)."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0].get("model") is None


class TestGlobalDefaultModel:
    """Tests for global default_model in config."""

    def test_valid_default_model(self, tmp_path):
        """Valid global default_model loads successfully."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "default_model": "claude-sonnet-4",
            "agents": [
                {"id": "pm", "persona": "project_manager", "display_name": "PM"}
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["default_model"] == "claude-sonnet-4"

    def test_invalid_default_model_raises(self, tmp_path):
        """Invalid global default_model raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "default_model": "invalid-model",
            "agents": [
                {"id": "pm", "persona": "project_manager", "display_name": "PM"}
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="Invalid default_model"):
            loader.load(config_file)
```

**Success Criteria**:
- Valid model in agent config loads successfully
- Invalid model raises `ConfigError` with helpful message
- Missing model field is allowed (optional)

---

### T2.1: Extend ConfigLoader for Model Validation (Lines 177-220)

**File**: `src/teambot/config/loader.py`

**Research Reference**: research.md Lines 152-172

**Changes Required**:

1. Import `validate_model` from schema
2. Add model validation in `_validate_agent()` method
3. Add `_validate_default_model()` method
4. Call validation in `load()` method

```python
# At top of file, add import:
from teambot.config.schema import validate_model

# In _validate_agent() method, add after persona validation:
def _validate_agent(self, agent: dict[str, Any], index: int) -> None:
    """Validate a single agent configuration."""
    # ... existing validation ...
    
    # Validate model if present
    model = agent.get("model")
    if model is not None and not validate_model(model):
        raise ConfigError(
            f"Invalid model '{model}' for agent '{agent.get('id', index)}'. "
            f"Use 'teambot models' to see available models."
        )

# Add new method:
def _validate_default_model(self, config: dict[str, Any]) -> None:
    """Validate global default_model if present."""
    default_model = config.get("default_model")
    if default_model is not None and not validate_model(default_model):
        raise ConfigError(
            f"Invalid default_model '{default_model}'. "
            f"Use 'teambot models' to see available models."
        )

# In load() method, call after loading:
def load(self, config_path: Path) -> dict[str, Any]:
    """Load configuration from JSON file."""
    # ... existing load logic ...
    
    # Validate default_model
    self._validate_default_model(config)
    
    # ... rest of method ...
```

**Success Criteria**:
- `ConfigError` raised for invalid agent model
- `ConfigError` raised for invalid default_model
- Error messages include the invalid model name

---

### T2.2: Add Model to Default Config (Lines 222-250)

**File**: `src/teambot/config/loader.py`

**Changes to `create_default_config()`**:

```python
def create_default_config() -> dict[str, Any]:
    """Create default configuration with MVP agents."""
    return {
        "teambot_dir": ".teambot",
        "default_model": None,  # Use SDK default
        "agents": [
            {
                "id": "pm",
                "persona": "project_manager",
                "display_name": "Project Manager",
                "parallel_capable": False,
                "workflow_stages": ["setup", "planning", "coordination"],
                "model": None,  # Uses default_model or SDK default
            },
            # ... other agents with model: None ...
        ],
    }
```

**Note**: Default to `None` to maintain backward compatibility. Users can add model per agent in their config.

**Success Criteria**:
- Default config includes `model` field (set to None)
- Existing configs without model field continue to work

---

## Phase 3: Data Model Updates

### T3.1T: TDD Tests for AgentStatus.model (Lines 255-295)

**File**: `tests/test_ui/test_agent_state.py` (extend existing)

```python
class TestAgentStatusModel:
    """Tests for model field in AgentStatus."""

    def test_agent_status_with_model(self):
        """AgentStatus can be created with model."""
        from teambot.ui.agent_state import AgentStatus

        status = AgentStatus(agent_id="pm", model="gpt-5")
        assert status.model == "gpt-5"

    def test_agent_status_model_defaults_to_none(self):
        """AgentStatus.model defaults to None."""
        from teambot.ui.agent_state import AgentStatus

        status = AgentStatus(agent_id="pm")
        assert status.model is None

    def test_with_state_preserves_model(self):
        """with_state() preserves model field."""
        from teambot.ui.agent_state import AgentState, AgentStatus

        status = AgentStatus(agent_id="pm", model="gpt-5")
        new_status = status.with_state(AgentState.RUNNING, task="test")
        assert new_status.model == "gpt-5"

    def test_with_model_creates_new_status(self):
        """with_model() creates new status with different model."""
        from teambot.ui.agent_state import AgentStatus

        status = AgentStatus(agent_id="pm", model="gpt-5")
        new_status = status.with_model("claude-opus-4.5")
        assert new_status.model == "claude-opus-4.5"
        assert status.model == "gpt-5"  # Original unchanged


class TestAgentStatusManagerModel:
    """Tests for model in AgentStatusManager."""

    def test_set_model_updates_agent(self):
        """set_model() updates agent's model."""
        from teambot.ui.agent_state import AgentStatusManager

        manager = AgentStatusManager()
        manager.set_model("pm", "claude-opus-4.5")
        assert manager.get("pm").model == "claude-opus-4.5"

    def test_set_model_notifies_listeners(self):
        """set_model() triggers listener notification."""
        from teambot.ui.agent_state import AgentStatusManager

        manager = AgentStatusManager()
        notified = []
        manager.add_listener(lambda: notified.append(True))

        manager.set_model("pm", "gpt-5")
        assert len(notified) == 1
```

**Success Criteria**:
- AgentStatus has model field
- with_state() preserves model
- Manager can set/get model

---

### T3.1: Add Model Field to AgentStatus (Lines 297-335)

**File**: `src/teambot/ui/agent_state.py`

**Changes**:

```python
@dataclass
class AgentStatus:
    """Status information for a single agent."""

    agent_id: str
    state: AgentState = AgentState.IDLE
    task: str | None = None
    model: str | None = None  # Add this field

    def with_state(self, state: AgentState, task: str | None = None) -> "AgentStatus":
        """Create a new AgentStatus with updated state."""
        return AgentStatus(
            agent_id=self.agent_id,
            state=state,
            task=task if task is not None else self.task,
            model=self.model,  # Preserve model
        )

    def with_model(self, model: str | None) -> "AgentStatus":
        """Create a new AgentStatus with updated model.
        
        Args:
            model: New model for the agent.
            
        Returns:
            New AgentStatus with updated model.
        """
        return AgentStatus(
            agent_id=self.agent_id,
            state=self.state,
            task=self.task,
            model=model,
        )


# In AgentStatusManager class, add:
def set_model(self, agent_id: str, model: str | None) -> None:
    """Set model for an agent.
    
    Args:
        agent_id: Agent identifier.
        model: Model to set (or None to clear).
    """
    if agent_id in self._statuses:
        self._statuses[agent_id] = self._statuses[agent_id].with_model(model)
        self._notify_listeners()
```

**Success Criteria**:
- AgentStatus dataclass has `model` field
- `with_state()` preserves model
- `with_model()` method works
- Manager has `set_model()` method

---

### T3.2: Add Model Field to Task Dataclass (Lines 337-375)

**File**: `src/teambot/tasks/models.py`

**Changes**:

```python
@dataclass
class Task:
    """A task to be executed by an agent."""

    id: str
    agent_id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    timeout: float = 120.0
    background: bool = False
    result: TaskResult | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model: str | None = None  # Add this field
```

**Test** (add to `tests/test_tasks/test_models.py`):

```python
class TestTaskModel:
    """Tests for model field in Task."""

    def test_task_with_model(self):
        """Task can be created with model."""
        from teambot.tasks.models import Task

        task = Task(id="t1", agent_id="pm", prompt="test", model="gpt-5")
        assert task.model == "gpt-5"

    def test_task_model_defaults_to_none(self):
        """Task.model defaults to None."""
        from teambot.tasks.models import Task

        task = Task(id="t1", agent_id="pm", prompt="test")
        assert task.model is None
```

**Success Criteria**:
- Task dataclass has `model` field
- Defaults to None for backward compatibility

---

## Phase 4: SDK Integration

### T4.1: Modify SDK Client for Model (Lines 380-430)

**File**: `src/teambot/copilot/sdk_client.py`

**Research Reference**: research.md Lines 136-161

**Changes to `get_or_create_session()`**:

```python
async def get_or_create_session(
    self, agent_id: str, model: str | None = None
) -> Any:
    """Get existing session or create new one for an agent.
    
    Args:
        agent_id: Agent identifier.
        model: Optional model override for this session.
        
    Returns:
        Session object for the agent.
    """
    session_id = f"teambot-{agent_id}"

    # Return cached session if exists AND model matches
    if session_id in self._sessions:
        existing = self._sessions[session_id]
        # If model changed, need new session
        if model and getattr(existing, '_model', None) != model:
            del self._sessions[session_id]
        else:
            return existing

    # Load agent definition
    loader = get_agent_loader()
    agent_def = loader.get_agent(agent_id)

    # Build session config
    session_config: dict[str, Any] = {
        "session_id": session_id,
        "streaming": True,
    }
    
    # Add model if specified
    if model:
        session_config["model"] = model

    # Add custom agent definition if available
    if agent_def:
        session_config["customAgents"] = [
            {
                "name": agent_id,
                "displayName": agent_def.display_name,
                "description": agent_def.description,
                "prompt": agent_def.prompt,
            }
        ]

    session = await self._client.create_session(session_config)
    session._model = model  # Track model for cache invalidation
    
    self._sessions[session_id] = session
    return session
```

**Success Criteria**:
- `session_config` includes `model` key when specified
- Session is recreated if model changes

---

### T4.2: Model Resolution Logic (Lines 432-485)

**File**: `src/teambot/copilot/sdk_client.py` (add helper function)

```python
def resolve_model(
    inline_model: str | None,
    session_overrides: dict[str, str],
    agent_id: str,
    config: dict[str, Any],
) -> str | None:
    """Resolve which model to use for an agent task.
    
    Priority (highest to lowest):
    1. Inline override (--model flag)
    2. Session override (/model command)
    3. Agent config (teambot.json agent.model)
    4. Global default (teambot.json default_model)
    5. None (use SDK default)
    
    Args:
        inline_model: Model specified in command (--model).
        session_overrides: Dict of agent_id -> model for session.
        agent_id: Agent identifier.
        config: TeamBot configuration dict.
        
    Returns:
        Resolved model name, or None to use SDK default.
    """
    # Priority 1: Inline override
    if inline_model:
        return inline_model
    
    # Priority 2: Session override
    if agent_id in session_overrides:
        return session_overrides[agent_id]
    
    # Priority 3: Agent config
    for agent in config.get("agents", []):
        if agent.get("id") == agent_id:
            if agent.get("model"):
                return agent["model"]
            break
    
    # Priority 4: Global default
    if config.get("default_model"):
        return config["default_model"]
    
    # Priority 5: SDK default
    return None
```

**Success Criteria**:
- Priority order is correct
- Returns None when no model specified

---

### T4.1T: Integration Tests for SDK Model (Lines 487-530)

**File**: `tests/test_copilot/test_sdk_client.py` (extend)

```python
class TestCopilotSDKClientModel:
    """Tests for model support in SDK client."""

    @pytest.mark.asyncio
    async def test_session_config_includes_model(self, mock_sdk):
        """Session config includes model when specified."""
        captured_config = None

        async def capture_create(config):
            nonlocal captured_config
            captured_config = config
            return MagicMock()

        mock_sdk.create_session = AsyncMock(side_effect=capture_create)

        client = CopilotSDKClient()
        client._client = mock_sdk
        await client.get_or_create_session("pm", model="gpt-5")

        assert captured_config is not None
        assert captured_config.get("model") == "gpt-5"

    @pytest.mark.asyncio
    async def test_session_without_model(self, mock_sdk):
        """Session config omits model when not specified."""
        captured_config = None

        async def capture_create(config):
            nonlocal captured_config
            captured_config = config
            return MagicMock()

        mock_sdk.create_session = AsyncMock(side_effect=capture_create)

        client = CopilotSDKClient()
        client._client = mock_sdk
        await client.get_or_create_session("pm")

        assert "model" not in captured_config
```

**Success Criteria**:
- Model is included in session config when specified
- Model is omitted when not specified

---

## Phase 5: Parser Extension

### T5.1T: TDD Tests for --model Parsing (Lines 535-585)

**File**: `tests/test_repl/test_parser.py` (extend)

```python
class TestParseModelFlag:
    """Tests for --model flag parsing."""

    def test_parse_model_flag_long_form(self):
        """Parse --model flag extracts model."""
        from teambot.repl.parser import parse_command

        result = parse_command("@pm --model gpt-5 Create a plan")
        assert result.agent_id == "pm"
        assert result.model == "gpt-5"
        assert result.content == "Create a plan"

    def test_parse_model_flag_short_form(self):
        """Parse -m flag extracts model."""
        from teambot.repl.parser import parse_command

        result = parse_command("@pm -m claude-opus-4.5 Review code")
        assert result.model == "claude-opus-4.5"
        assert result.content == "Review code"

    def test_parse_model_flag_no_task_sets_session(self):
        """Parse --model without task sets session override."""
        from teambot.repl.parser import parse_command

        result = parse_command("@pm --model gpt-5")
        assert result.model == "gpt-5"
        assert result.content == ""  # Empty content signals session set
        assert result.is_session_model_set is True

    def test_parse_model_flag_in_multi_agent(self):
        """Parse --model in multi-agent command."""
        from teambot.repl.parser import parse_command

        result = parse_command("@pm,ba --model gpt-5 analyze requirements")
        assert result.model == "gpt-5"
        assert "pm" in result.agent_ids
        assert "ba" in result.agent_ids

    def test_parse_model_flag_missing_value_raises(self):
        """Parse --model without value raises ParseError."""
        from teambot.repl.parser import ParseError, parse_command

        with pytest.raises(ParseError, match="model"):
            parse_command("@pm --model")

    def test_parse_no_model_flag(self):
        """Command without --model has model as None."""
        from teambot.repl.parser import parse_command

        result = parse_command("@pm Create a plan")
        assert result.model is None
```

**Success Criteria**:
- `--model` and `-m` both work
- Model extracted correctly
- Missing value raises ParseError

---

### T5.1: Add --model Flag Parsing (Lines 587-640)

**File**: `src/teambot/repl/parser.py`

**Changes**:

```python
# Add pattern for model flag
MODEL_FLAG_PATTERN = re.compile(r'(?:--model|-m)\s+([^\s]+)')

# Modify parse_command() to extract model:
def parse_command(text: str) -> Command:
    """Parse user input into Command."""
    text = text.strip()
    
    # Check for system command
    if text.startswith("/"):
        # ... existing system command handling ...
        pass
    
    # Check for agent command
    agent_match = AGENT_PATTERN.match(text)
    if agent_match:
        agents_str = agent_match.group(1)
        rest = agent_match.group(2).strip()
        
        # Extract model flag if present
        model = None
        is_session_model_set = False
        model_match = MODEL_FLAG_PATTERN.search(rest)
        if model_match:
            model = model_match.group(1)
            # Remove model flag from rest
            rest = MODEL_FLAG_PATTERN.sub('', rest).strip()
            
            # If nothing left, this is a session model set
            if not rest:
                is_session_model_set = True
        
        # Check for missing model value
        if '--model' in text or '-m ' in text:
            if not model:
                raise ParseError("--model flag requires a model name")
        
        # Parse agent IDs
        agent_ids = [a.strip() for a in agents_str.split(',') if a.strip()]
        
        # ... rest of existing parsing ...
        
        return Command(
            type=CommandType.AGENT,
            agent_id=agent_ids[0] if agent_ids else None,
            agent_ids=agent_ids,
            content=rest,
            model=model,
            is_session_model_set=is_session_model_set,
            # ... other fields ...
        )
```

**Success Criteria**:
- `@pm --model gpt-5 task` extracts model="gpt-5"
- `@pm -m gpt-5 task` also works
- `@pm --model gpt-5` (no task) sets is_session_model_set=True

---

### T5.2: Add Model Field to Command Dataclass (Lines 642-670)

**File**: `src/teambot/repl/parser.py`

**Changes to Command dataclass**:

```python
@dataclass
class Command:
    """Parsed command from user input."""

    type: CommandType
    agent_id: str | None = None
    agent_ids: list[str] = field(default_factory=list)
    content: str | None = None
    command: str | None = None
    args: list[str] | None = None
    background: bool = False
    is_pipeline: bool = False
    pipeline: list[PipelineStage] | None = None
    references: list[str] = field(default_factory=list)
    model: str | None = None  # Add this field
    is_session_model_set: bool = False  # Add this field
```

**Success Criteria**:
- Command has `model` field
- Command has `is_session_model_set` field

---

## Phase 6: System Commands

### T6.1T: TDD Tests for /models Command (Lines 675-715)

**File**: `tests/test_repl/test_commands.py` (extend)

```python
class TestModelsCommand:
    """Tests for /models command."""

    def test_models_lists_all_valid_models(self):
        """'/models' returns all 14 valid models."""
        from teambot.repl.commands import handle_models

        result = handle_models([])
        assert result.success is True
        assert "claude-sonnet-4.5" in result.output
        assert "gpt-5" in result.output
        assert "gemini-3-pro-preview" in result.output

    def test_models_shows_categories(self):
        """'/models' shows model categories."""
        from teambot.repl.commands import handle_models

        result = handle_models([])
        assert "standard" in result.output or "fast" in result.output

    def test_models_count(self):
        """'/models' lists exactly 14 models."""
        from teambot.repl.commands import handle_models

        result = handle_models([])
        # Count model entries (each model on its own line)
        model_lines = [l for l in result.output.split('\n') if 'gpt-' in l or 'claude-' in l or 'gemini-' in l]
        assert len(model_lines) == 14
```

**Success Criteria**:
- All 14 models listed
- Categories shown
- Formatted nicely

---

### T6.1: Implement handle_models() Function (Lines 717-760)

**File**: `src/teambot/repl/commands.py`

```python
from teambot.config.schema import get_available_models, get_model_info


def handle_models(args: list[str]) -> CommandResult:
    """Handle /models command - list available models.
    
    Args:
        args: Command arguments (unused).
        
    Returns:
        CommandResult with model list.
    """
    lines = ["Available Models", "=" * 50, ""]
    
    models = get_available_models()
    for model in models:
        info = get_model_info(model)
        if info:
            display = info["display"]
            category = info["category"]
            lines.append(f"  {model:<24} {display} ({category})")
        else:
            lines.append(f"  {model}")
    
    lines.append("")
    lines.append("Usage: @agent --model <model-name> <task>")
    lines.append("       @agent --model <model-name>  (set for session)")
    
    return CommandResult(output="\n".join(lines), success=True)
```

**Success Criteria**:
- Lists all models with display names
- Shows usage hint

---

### T6.2: Implement handle_model() Function (Lines 762-820)

**File**: `src/teambot/repl/commands.py`

```python
from teambot.config.schema import validate_model


# Module-level session overrides storage
_session_model_overrides: dict[str, str] = {}


def get_session_model(agent_id: str) -> str | None:
    """Get session model override for an agent."""
    return _session_model_overrides.get(agent_id)


def set_session_model(agent_id: str, model: str) -> None:
    """Set session model override for an agent."""
    _session_model_overrides[agent_id] = model


def clear_session_model(agent_id: str) -> None:
    """Clear session model override for an agent."""
    _session_model_overrides.pop(agent_id, None)


def handle_model(args: list[str]) -> CommandResult:
    """Handle /model command - set/view session model overrides.
    
    Usage:
        /model                     - Show current session overrides
        /model <agent> <model>     - Set model for agent
        /model --reset <agent>     - Clear override for agent
        /model --reset-all         - Clear all overrides
    
    Args:
        args: Command arguments.
        
    Returns:
        CommandResult with status.
    """
    # No args: show current overrides
    if not args:
        if not _session_model_overrides:
            return CommandResult(
                output="No session model overrides set.\n"
                       "Use: /model <agent> <model>",
                success=True
            )
        lines = ["Session Model Overrides:", ""]
        for agent_id, model in sorted(_session_model_overrides.items()):
            lines.append(f"  {agent_id}: {model}")
        return CommandResult(output="\n".join(lines), success=True)
    
    # --reset-all: clear all
    if args[0] == "--reset-all":
        _session_model_overrides.clear()
        return CommandResult(output="All session model overrides cleared.", success=True)
    
    # --reset <agent>: clear one
    if args[0] == "--reset":
        if len(args) < 2:
            return CommandResult(output="Usage: /model --reset <agent>", success=False)
        agent_id = args[1]
        clear_session_model(agent_id)
        return CommandResult(output=f"Session model override cleared for {agent_id}.", success=True)
    
    # <agent> <model>: set override
    if len(args) < 2:
        return CommandResult(
            output="Usage: /model <agent> <model>\n"
                   "       /model --reset <agent>",
            success=False
        )
    
    agent_id = args[0]
    model = args[1]
    
    # Validate model
    if not validate_model(model):
        return CommandResult(
            output=f"Invalid model: {model}\n"
                   f"Use /models to see available models.",
            success=False
        )
    
    set_session_model(agent_id, model)
    return CommandResult(
        output=f"Session model for {agent_id} set to: {model}",
        success=True
    )
```

**Success Criteria**:
- `/model` shows current overrides
- `/model pm gpt-5` sets override
- `/model --reset pm` clears override
- Invalid model shows error

---

## Phase 7: UI Display

### T7.1: Update StatusPanel Display (Lines 825-870)

**File**: `src/teambot/ui/widgets/status_panel.py`

**Changes to `_format_status()`**:

```python
def _format_status(self) -> str:
    """Format the status panel content."""
    lines = []

    # Git branch header
    if self._git_branch:
        branch_display = self._git_branch[:12] + "..." if len(self._git_branch) > 15 else self._git_branch
        lines.append(f"[dim]Branch:[/dim] [white]{branch_display}[/white]")
        lines.append("")

    lines.append("[bold]Agents[/bold]")
    for agent_id, status in self._status_manager.get_all().items():
        indicator = self._get_indicator(status.state)
        
        # Format model display (truncate if needed)
        model_display = ""
        if status.model:
            model_short = status.model
            if len(model_short) > 12:
                model_short = model_short[:10] + ".."
            model_display = f" [dim]({model_short})[/dim]"
        
        line = f"{indicator} {agent_id}{model_display}"

        if status.state in (AgentState.RUNNING, AgentState.STREAMING):
            lines.append(line)
            if status.task:
                task_display = status.task[:17] + "..." if len(status.task) > 20 else status.task
                lines.append(f"  [dim]→ {task_display}[/dim]")
        elif status.state == AgentState.IDLE:
            lines.append(f"{line} [dim]idle[/dim]")
        else:
            lines.append(line)

    return "\n".join(lines)
```

**Success Criteria**:
- Model shown in parentheses after agent name
- Long model names truncated
- Doesn't break existing layout

---

### T7.2: Update /status Command Output (Lines 872-910)

**File**: `src/teambot/repl/commands.py`

**Changes to handle_status()**:

```python
def handle_status(args: list[str], executor: "TaskExecutor" = None) -> CommandResult:
    """Handle /status command."""
    lines = ["TeamBot Status", "=" * 50, ""]
    
    # ... existing stage/runtime info ...
    
    lines.append("Agents:")
    for agent_id, status in status_manager.get_all().items():
        state_str = status.state.value
        model_str = f"model: {status.model}" if status.model else "model: (default)"
        
        if status.task:
            lines.append(f"  {agent_id:<12} {state_str:<12} {model_str}")
            lines.append(f"               └─ {status.task[:40]}")
        else:
            lines.append(f"  {agent_id:<12} {state_str:<12} {model_str}")
    
    return CommandResult(output="\n".join(lines), success=True)
```

**Success Criteria**:
- Model shown for each agent
- "(default)" shown when no specific model

---

### T7.3: Update /tasks Command Output (Lines 912-950)

**File**: `src/teambot/repl/commands.py`

**Changes to handle_tasks()**:

```python
def handle_tasks(args: list[str], executor: "TaskExecutor" = None) -> CommandResult:
    """Handle /tasks command."""
    if not executor:
        return CommandResult(output="No task executor available.", success=False)
    
    tasks = executor.get_active_tasks()
    if not tasks:
        return CommandResult(output="No active tasks.", success=True)
    
    lines = ["Active Tasks", "=" * 50, ""]
    
    for task in tasks:
        model_str = f"({task.model})" if task.model else "(default)"
        lines.append(f"Task #{task.id}: @{task.agent_id} {model_str}")
        lines.append(f"  Prompt: {task.prompt[:50]}...")
        lines.append(f"  Status: {task.status.value}")
        if task.started_at:
            lines.append(f"  Started: {task.started_at.strftime('%H:%M:%S')}")
        lines.append("")
    
    return CommandResult(output="\n".join(lines), success=True)
```

**Success Criteria**:
- Model shown after agent in task list
- "(default)" when no model specified

---

### T7.1T: Tests for UI Display (Lines 952-995)

**File**: `tests/test_ui/test_status_panel.py` (create or extend)

```python
class TestStatusPanelModel:
    """Tests for model display in StatusPanel."""

    def test_format_status_includes_model(self):
        """Model shown in status output."""
        from teambot.ui.agent_state import AgentStatusManager
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_model("pm", "gpt-5")

        panel = StatusPanel(manager)
        output = panel._format_status()

        assert "pm" in output
        assert "gpt-5" in output

    def test_format_status_truncates_long_model(self):
        """Long model names are truncated."""
        from teambot.ui.agent_state import AgentStatusManager
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_model("pm", "gpt-5.1-codex-max")

        panel = StatusPanel(manager)
        output = panel._format_status()

        # Should be truncated with ..
        assert ".." in output or "gpt-5.1-cod" in output
```

**Success Criteria**:
- Model appears in formatted output
- Long names truncated appropriately

---

## Phase 8: Integration

### T8.1: Integrate in TaskExecutor (Lines 1000-1055)

**File**: `src/teambot/tasks/executor.py`

**Changes**:

```python
from teambot.copilot.sdk_client import resolve_model
from teambot.repl.commands import get_session_model


class TaskExecutor:
    """Executes tasks with model support."""
    
    async def execute_task(
        self,
        task: Task,
        inline_model: str | None = None,
    ) -> TaskResult:
        """Execute a task with model resolution.
        
        Args:
            task: Task to execute.
            inline_model: Optional inline model override.
            
        Returns:
            TaskResult from execution.
        """
        # Resolve model
        model = resolve_model(
            inline_model=inline_model or task.model,
            session_overrides={
                aid: get_session_model(aid)
                for aid in [task.agent_id]
                if get_session_model(aid)
            },
            agent_id=task.agent_id,
            config=self._config,
        )
        
        # Update task model for tracking
        task.model = model
        
        # Update agent status with model
        self._status_manager.set_model(task.agent_id, model)
        
        # Execute with model
        result = await self._sdk_client.execute(
            agent_id=task.agent_id,
            prompt=task.prompt,
            model=model,
        )
        
        return result
```

**Success Criteria**:
- Model resolved using priority chain
- Task.model updated for tracking
- Agent status updated with model
- Model passed to SDK client

---

### T8.2: Update File Orchestration (Lines 1057-1110)

**File**: `src/teambot/orchestration/execution_loop.py`

**Changes**:

```python
async def execute_agent_task(
    self,
    agent_id: str,
    task_content: str,
) -> str:
    """Execute a task for an agent in file-based orchestration.
    
    Uses agent's configured default model.
    """
    # Get agent's configured model from config
    agent_model = None
    for agent in self._config.get("agents", []):
        if agent.get("id") == agent_id:
            agent_model = agent.get("model")
            break
    
    # Fall back to global default
    if not agent_model:
        agent_model = self._config.get("default_model")
    
    # Execute with resolved model
    result = await self._sdk_client.execute(
        agent_id=agent_id,
        prompt=task_content,
        model=agent_model,
    )
    
    return result
```

**Success Criteria**:
- File orchestration uses agent config model
- Falls back to global default
- Model passed to SDK

---

### T8.1T: Integration Tests (Lines 1112-1160)

**File**: `tests/test_integration/test_model_selection.py` (create)

```python
"""Integration tests for model selection feature."""

import pytest


class TestModelSelectionIntegration:
    """End-to-end tests for model selection."""

    @pytest.mark.asyncio
    async def test_inline_model_override(self, mock_sdk_client, config):
        """Inline --model flag overrides all other settings."""
        # Setup config with agent model
        config["agents"][0]["model"] = "gpt-5"
        
        # Execute with inline override
        executor = TaskExecutor(config=config, sdk_client=mock_sdk_client)
        task = Task(id="t1", agent_id="pm", prompt="test")
        
        await executor.execute_task(task, inline_model="claude-opus-4.5")
        
        # Verify SDK called with override model
        assert mock_sdk_client.execute.call_args.kwargs["model"] == "claude-opus-4.5"

    @pytest.mark.asyncio
    async def test_session_override_priority(self, mock_sdk_client, config):
        """Session override takes priority over config."""
        from teambot.repl.commands import set_session_model
        
        config["agents"][0]["model"] = "gpt-5"
        set_session_model("pm", "claude-sonnet-4")
        
        executor = TaskExecutor(config=config, sdk_client=mock_sdk_client)
        task = Task(id="t1", agent_id="pm", prompt="test")
        
        await executor.execute_task(task)
        
        assert mock_sdk_client.execute.call_args.kwargs["model"] == "claude-sonnet-4"

    @pytest.mark.asyncio
    async def test_config_default_used(self, mock_sdk_client, config):
        """Agent config model used when no overrides."""
        config["agents"][0]["model"] = "gpt-5"
        
        executor = TaskExecutor(config=config, sdk_client=mock_sdk_client)
        task = Task(id="t1", agent_id="pm", prompt="test")
        
        await executor.execute_task(task)
        
        assert mock_sdk_client.execute.call_args.kwargs["model"] == "gpt-5"
```

**Success Criteria**:
- Inline override works
- Session override works
- Config default works
- Priority order respected

---

## References

| Document | Path | Lines |
|----------|------|-------|
| Research | `.teambot/model-select/artifacts/research.md` | Full doc |
| Test Strategy | `.teambot/model-select/artifacts/test_strategy.md` | Full doc |
| Feature Spec | `.teambot/model-select/artifacts/feature_spec.md` | Full doc |
| CopilotConfig | `src/teambot/copilot/client.py` | 26-34 |
| CopilotSDKClient | `src/teambot/copilot/sdk_client.py` | 130-161 |
| ConfigLoader | `src/teambot/config/loader.py` | 32-94 |
| AgentStatus | `src/teambot/ui/agent_state.py` | 22-51 |
| Task | `src/teambot/tasks/models.py` | 52-79 |
| StatusPanel | `src/teambot/ui/widgets/status_panel.py` | 101-137 |
| Command parser | `src/teambot/repl/parser.py` | 46-72 |
| Commands | `src/teambot/repl/commands.py` | 1-60 |
