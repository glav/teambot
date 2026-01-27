---
title: TeamBot Interactive Mode - Test Strategy
date: 2026-01-23
author: AI Test Strategist
feature: Interactive Mode + Copilot SDK Integration
status: RECOMMENDED
---

# Test Strategy: Interactive Mode

## 1. Strategy Summary

### Recommended Approach: **HYBRID (TDD + Code-First)**

| Component | Strategy | Rationale |
|-----------|----------|-----------|
| Command Parser | **TDD** | Pure logic, easily testable |
| SDK Client Wrapper | **TDD** | Critical integration, mockable |
| REPL Loop | **Code-First** | I/O heavy, async complexity |
| System Commands | **TDD** | Discrete functions, clear inputs/outputs |
| Agent Routing | **TDD** | Core logic, must be reliable |
| Streaming Handler | **Code-First** | Event-driven, hard to unit test |
| Signal Handling | **Code-First** | OS integration, manual testing |

---

## 2. Component Analysis

### TDD Components (Write Tests First)

#### 2.1 Command Parser (`src/teambot/repl/parser.py`)

**Why TDD:**
- Pure function with clear input/output
- Many edge cases to cover
- Critical for user experience

**Test Cases:**
```python
# test_parser.py
def test_parse_agent_command():
    assert parse("@pm create plan") == ("agent", "pm", "create plan")

def test_parse_system_command():
    assert parse("/help") == ("system", "help", "")

def test_parse_system_command_with_arg():
    assert parse("/history pm") == ("system", "history", "pm")

def test_parse_unknown_command():
    assert parse("hello") == ("unknown", "", "hello")

def test_parse_empty_input():
    assert parse("") == ("unknown", "", "")

def test_parse_agent_with_spaces():
    assert parse("@builder-1 implement the login feature") == (
        "agent", "builder-1", "implement the login feature"
    )

def test_parse_invalid_agent():
    assert parse("@") == ("unknown", "", "@")
```

#### 2.2 SDK Client Wrapper (`src/teambot/copilot/sdk_client.py`)

**Why TDD:**
- Critical path for all agent execution
- Must handle errors gracefully
- Mockable SDK dependency

**Test Cases:**
```python
# test_sdk_client.py
@pytest.mark.asyncio
async def test_client_start(mock_sdk):
    client = CopilotSDKClient()
    await client.start()
    mock_sdk.start.assert_called_once()

@pytest.mark.asyncio
async def test_create_session_for_agent(mock_sdk):
    client = CopilotSDKClient()
    await client.start()
    session = await client.get_or_create_session("pm")
    assert session is not None
    mock_sdk.create_session.assert_called_with({
        "session_id": "teambot-pm",
        "model": "gpt-4.1",
        "streaming": True,
    })

@pytest.mark.asyncio
async def test_session_reuse(mock_sdk):
    client = CopilotSDKClient()
    await client.start()
    session1 = await client.get_or_create_session("pm")
    session2 = await client.get_or_create_session("pm")
    assert session1 is session2  # Same session reused

@pytest.mark.asyncio
async def test_execute_returns_response(mock_sdk, mock_session):
    mock_session.send_and_wait.return_value = MockResponse("Hello!")
    client = CopilotSDKClient()
    await client.start()
    result = await client.execute("pm", "Say hello")
    assert result == "Hello!"

@pytest.mark.asyncio
async def test_stop_destroys_sessions(mock_sdk, mock_session):
    client = CopilotSDKClient()
    await client.start()
    await client.get_or_create_session("pm")
    await client.stop()
    mock_session.destroy.assert_called_once()
```

#### 2.3 System Commands (`src/teambot/repl/commands.py`)

**Why TDD:**
- Discrete functions with clear behavior
- Each command is independently testable
- Output format matters

**Test Cases:**
```python
# test_commands.py
def test_help_command_returns_help_text():
    result = cmd_help()
    assert "@<agent>" in result
    assert "/quit" in result

def test_status_command_shows_agents(mock_display):
    cmd_status(mock_display)
    mock_display.print_status.assert_called_once()

def test_history_command_all_agents(mock_history_manager):
    mock_history_manager.list_files.return_value = ["file1.md", "file2.md"]
    result = cmd_history(None, mock_history_manager)
    assert len(result) == 2

def test_history_command_specific_agent(mock_history_manager):
    result = cmd_history("pm", mock_history_manager)
    mock_history_manager.list_files.assert_called_with(agent_id="pm")

def test_quit_command_returns_exit_signal():
    result = cmd_quit()
    assert result.should_exit is True
```

#### 2.4 Agent Router (`src/teambot/repl/router.py`)

**Why TDD:**
- Maps agent IDs to sessions
- Validates agent names
- Critical for correct routing

**Test Cases:**
```python
# test_router.py
def test_valid_agent_ids():
    router = AgentRouter(AGENT_CONFIG)
    assert router.is_valid_agent("pm") is True
    assert router.is_valid_agent("builder-1") is True
    assert router.is_valid_agent("invalid") is False

def test_get_agent_persona():
    router = AgentRouter(AGENT_CONFIG)
    assert router.get_persona("pm") == "project_manager"
    assert router.get_persona("builder-1") == "builder"

def test_route_to_agent(mock_sdk_client):
    router = AgentRouter(AGENT_CONFIG, mock_sdk_client)
    await router.route("pm", "create a plan")
    mock_sdk_client.execute.assert_called_with("pm", ANY)
```

---

### Code-First Components (Implement Then Test)

#### 2.5 REPL Loop (`src/teambot/repl/loop.py`)

**Why Code-First:**
- Heavy I/O (stdin/stdout)
- Async event loop complexity
- Integration of multiple components

**Implementation First, Then:**
```python
# test_repl_loop.py (integration style)
@pytest.mark.asyncio
async def test_repl_processes_agent_command(mock_input, mock_sdk):
    mock_input.side_effect = ["@pm hello", "/quit"]
    await repl_loop(mock_sdk, mock_display)
    mock_sdk.execute.assert_called_with("pm", "hello")

@pytest.mark.asyncio
async def test_repl_handles_quit(mock_input):
    mock_input.return_value = "/quit"
    result = await repl_loop(mock_sdk, mock_display)
    assert result == 0  # Clean exit
```

#### 2.6 Streaming Handler (`src/teambot/repl/streaming.py`)

**Why Code-First:**
- Event-driven callbacks
- SDK integration details
- Visual output testing

**Implementation First, Then:**
```python
# test_streaming.py
def test_handler_writes_delta_content(capsys):
    handler = StreamingHandler()
    event = MockEvent(type="ASSISTANT_MESSAGE_DELTA", delta_content="Hello")
    handler.handle(event)
    captured = capsys.readouterr()
    assert "Hello" in captured.out

def test_handler_newline_on_idle(capsys):
    handler = StreamingHandler()
    event = MockEvent(type="SESSION_IDLE")
    handler.handle(event)
    captured = capsys.readouterr()
    assert captured.out == "\n"
```

#### 2.7 Signal Handling (`src/teambot/repl/signals.py`)

**Why Code-First:**
- OS-level integration
- Hard to unit test signals
- Manual verification needed

**Implementation First, Then:**
```python
# test_signals.py
def test_sigint_handler_sets_flag():
    handler = SignalHandler()
    handler.setup()
    # Simulate SIGINT
    os.kill(os.getpid(), signal.SIGINT)
    assert handler.should_exit is True
```

---

## 3. Test Coverage Targets

| Component | Target Coverage | Priority |
|-----------|-----------------|----------|
| Command Parser | 95% | P0 |
| SDK Client Wrapper | 90% | P0 |
| System Commands | 90% | P0 |
| Agent Router | 90% | P0 |
| REPL Loop | 75% | P1 |
| Streaming Handler | 70% | P1 |
| Signal Handling | 60% | P2 |
| **Overall** | **80%** | - |

---

## 4. Mock Strategy

### SDK Mocking

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_sdk():
    """Mock the Copilot SDK client."""
    sdk = MagicMock()
    sdk.start = AsyncMock()
    sdk.stop = AsyncMock()
    sdk.create_session = AsyncMock(return_value=mock_session())
    return sdk

@pytest.fixture
def mock_session():
    """Mock a Copilot SDK session."""
    session = MagicMock()
    session.send_and_wait = AsyncMock(return_value=MockResponse("OK"))
    session.destroy = MagicMock()
    session.on = MagicMock()
    return session

class MockResponse:
    def __init__(self, content: str):
        self.data = MagicMock()
        self.data.content = content
```

### Input Mocking

```python
@pytest.fixture
def mock_input(monkeypatch):
    """Mock user input for REPL testing."""
    inputs = []
    def mock_fn(prompt=""):
        if not inputs:
            raise EOFError
        return inputs.pop(0)
    monkeypatch.setattr("builtins.input", mock_fn)
    return inputs
```

---

## 5. Integration Tests

### SDK Integration (Requires Real Copilot)

```python
# tests/integration/test_sdk_integration.py
@pytest.mark.integration
@pytest.mark.skipif(not COPILOT_AVAILABLE, reason="Copilot CLI not installed")
@pytest.mark.asyncio
async def test_real_sdk_connection():
    """Test actual SDK connection to Copilot CLI."""
    from copilot import CopilotClient
    
    client = CopilotClient()
    await client.start()
    
    session = await client.create_session({"model": "gpt-4.1"})
    response = await session.send_and_wait({"prompt": "Say 'test'"})
    
    assert response.data.content
    await client.stop()
```

### End-to-End REPL Test

```python
# tests/integration/test_repl_e2e.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_repl_session(mock_sdk):
    """Test complete REPL session flow."""
    inputs = [
        "@pm create a simple plan",
        "/status",
        "/quit"
    ]
    
    with patch_input(inputs):
        exit_code = await run_interactive_mode(mock_sdk)
    
    assert exit_code == 0
    assert mock_sdk.execute.call_count == 1
```

---

## 6. Test File Structure

```
tests/
├── test_repl/
│   ├── __init__.py
│   ├── test_parser.py        # TDD - command parsing
│   ├── test_commands.py      # TDD - system commands
│   ├── test_router.py        # TDD - agent routing
│   ├── test_loop.py          # Code-First - REPL loop
│   └── test_streaming.py     # Code-First - streaming
├── test_copilot/
│   ├── __init__.py           # Existing
│   ├── test_prompts.py       # Existing
│   └── test_sdk_client.py    # TDD - SDK wrapper
└── integration/
    ├── __init__.py
    ├── test_sdk_integration.py
    └── test_repl_e2e.py
```

---

## 7. Implementation Order

### Phase 1: TDD Components (Tests First)

1. **Command Parser** - Write tests → Implement
2. **Agent Router** - Write tests → Implement  
3. **SDK Client Wrapper** - Write tests → Implement
4. **System Commands** - Write tests → Implement

### Phase 2: Code-First Components

5. **REPL Loop** - Implement → Write tests
6. **Streaming Handler** - Implement → Write tests
7. **Signal Handling** - Implement → Write tests

### Phase 3: Integration

8. **CLI Integration** - Connect to `cmd_run`
9. **End-to-End Tests** - Full workflow validation

---

## 8. Async Testing Setup

### pytest-asyncio Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Async Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

---

## 9. Decision Matrix

| Factor | Weight | TDD Score | Code-First Score |
|--------|--------|-----------|------------------|
| Clear I/O boundaries | 30% | High (parser, commands) | Low (REPL, streaming) |
| Mockability | 25% | High (SDK client) | Medium |
| Complexity | 20% | Low-Medium | High (async, events) |
| Iteration speed | 15% | Medium | High |
| Coverage confidence | 10% | High | Medium |

**Result:** Hybrid approach optimizes for both reliability (TDD for core logic) and velocity (Code-First for I/O integration).

---

## 10. Recommendation

### ✅ APPROVED: Hybrid Strategy

- **TDD (4 components):** Parser, Router, SDK Client, System Commands
- **Code-First (3 components):** REPL Loop, Streaming, Signals
- **Target Coverage:** 80% overall
- **New Test Files:** 7 files
- **Estimated Test Count:** 40-50 new tests

### Dependencies to Add

```toml
# pyproject.toml - dev dependencies
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-asyncio>=0.23.0",  # NEW - async test support
    "ruff>=0.4.0",
]
```

Ready for implementation planning (`/sdd.5.task-planner-for-feature`).
