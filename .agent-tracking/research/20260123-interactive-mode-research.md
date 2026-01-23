---
title: TeamBot Interactive Mode - Technical Research
date: 2026-01-23
researcher: AI Research Agent
feature: Interactive Mode + Copilot SDK Integration
status: COMPLETE
---

# Technical Research: Interactive Mode + Copilot SDK

## 1. Research Summary

### Key Findings

| Topic | Finding | Impact |
|-------|---------|--------|
| SDK API Style | **Async** (asyncio) for Python | Must use async/await throughout |
| Package Name | `github-copilot-sdk` (import as `copilot`) | Update pyproject.toml |
| Session Management | Built-in persistence with custom IDs | Perfect for per-agent sessions |
| Streaming | Native support via event callbacks | Real-time output available |
| Multiple Sessions | Fully supported in parallel | Enables multi-agent execution |
| Error Handling | Context manager + try/except | Standard patterns work |
| Tool Definition | `@define_tool` decorator | Can extend agent capabilities |

### SDK Availability
- **Status:** Technical Preview
- **Python Version:** 3.8+
- **Installation:** `uv add github-copilot-sdk`
- **Prerequisite:** Copilot CLI must be installed

---

## 2. SDK Architecture

### Communication Flow
```
TeamBot Application
       ↓
  SDK Client (CopilotClient)
       ↓ JSON-RPC
  Copilot CLI (server mode)
       ↓
  GitHub Copilot API
```

### Key Classes

| Class | Purpose | Notes |
|-------|---------|-------|
| `CopilotClient` | Main entry point | Manages CLI server lifecycle |
| `Session` | Conversation context | One per agent recommended |
| `SessionEvent` | Event types | For streaming callbacks |

---

## 3. Python SDK API Reference

### Installation
```bash
uv add github-copilot-sdk
```

### Basic Usage (Async)
```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()  # Starts CLI server

    session = await client.create_session({
        "model": "gpt-4.1",
        "streaming": True,
    })

    response = await session.send_and_wait({"prompt": "Hello"})
    print(response.data.content)

    await client.stop()

asyncio.run(main())
```

### Streaming Responses
```python
from copilot.generated.session_events import SessionEventType

def handle_event(event):
    if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
        sys.stdout.write(event.data.delta_content)
        sys.stdout.flush()
    if event.type == SessionEventType.SESSION_IDLE:
        print()  # Done

session.on(handle_event)
await session.send_and_wait({"prompt": "Tell me a story"})
```

### Session Persistence
```python
# Create with custom ID (per agent)
session = await client.create_session({
    "session_id": "pm-agent-session",
    "model": "gpt-4.1",
})

# Resume later
session = await client.resume_session("pm-agent-session")

# List all sessions
sessions = client.list_sessions()

# Delete session
client.delete_session("pm-agent-session")
```

### Multiple Sessions (Parallel Agents)
```python
# Create independent sessions for each agent
pm_session = await client.create_session({"session_id": "pm", "model": "gpt-4.1"})
builder_session = await client.create_session({"session_id": "builder-1", "model": "gpt-4.1"})
reviewer_session = await client.create_session({"session_id": "reviewer", "model": "gpt-4.1"})

# Each maintains its own context
await pm_session.send_and_wait({"prompt": "You are a project manager..."})
await builder_session.send_and_wait({"prompt": "You are a builder..."})
```

### Custom Tools
```python
from copilot.tools import define_tool

@define_tool(description="Read a file from the project")
async def read_file(params: dict) -> dict:
    path = params["path"]
    content = Path(path).read_text()
    return {"path": path, "content": content}

session = await client.create_session({
    "model": "gpt-4.1",
    "tools": [read_file],
})
```

### Error Handling
```python
from copilot import CopilotClient

try:
    client = CopilotClient()
    await client.start()
    # ... use client ...
except FileNotFoundError:
    print("Copilot CLI not found")
except ConnectionError:
    print("Could not connect to CLI server")
finally:
    await client.stop()

# Or use context manager
async with CopilotClient() as client:
    await client.start()
    # ... use client ...
    # auto-cleanup on exit
```

### Graceful Shutdown
```python
import signal

def signal_handler(sig, frame):
    print("Shutting down...")
    asyncio.create_task(client.stop())
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

---

## 4. Event Types

| Event Type | Description | Use Case |
|------------|-------------|----------|
| `ASSISTANT_MESSAGE_DELTA` | Streaming chunk | Real-time output |
| `ASSISTANT_MESSAGE` | Complete message | Final response |
| `SESSION_IDLE` | Session ready | Prompt for next input |
| `TOOL_CALL` | Tool invocation | Custom tool handling |
| `ERROR` | Error occurred | Error handling |

---

## 5. Implementation Recommendations

### For TeamBot MVP

#### 1. Replace CopilotClient
```python
# OLD: src/teambot/copilot/client.py
class CopilotClient:
    def execute(self, prompt: str) -> CopilotResult:
        result = subprocess.run(["copilot", "-p", prompt], ...)
        return CopilotResult(...)

# NEW: src/teambot/copilot/sdk_client.py
from copilot import CopilotClient as SDKClient

class CopilotSDKClient:
    def __init__(self):
        self._client = SDKClient()
        self._sessions: dict[str, Session] = {}

    async def start(self):
        await self._client.start()

    async def get_or_create_session(self, agent_id: str) -> Session:
        if agent_id not in self._sessions:
            self._sessions[agent_id] = await self._client.create_session({
                "session_id": f"teambot-{agent_id}",
                "model": "gpt-4.1",
                "streaming": True,
            })
        return self._sessions[agent_id]

    async def execute(self, agent_id: str, prompt: str) -> str:
        session = await self.get_or_create_session(agent_id)
        response = await session.send_and_wait({"prompt": prompt})
        return response.data.content

    async def stop(self):
        for session in self._sessions.values():
            session.destroy()
        await self._client.stop()
```

#### 2. REPL Loop Structure
```python
async def repl_loop(client: CopilotSDKClient, display: ConsoleDisplay):
    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "teambot> "
            )
        except EOFError:
            break

        if user_input.startswith("/"):
            await handle_system_command(user_input, display)
        elif user_input.startswith("@"):
            await handle_agent_command(user_input, client, display)
        else:
            display.print_warning("Use @agent or /command")
```

#### 3. Command Parsing
```python
import re

def parse_command(input: str) -> tuple[str, str]:
    """Parse @agent or /command from input."""
    if input.startswith("@"):
        match = re.match(r"@(\S+)\s+(.*)", input)
        if match:
            return ("agent", match.group(1), match.group(2))
    elif input.startswith("/"):
        parts = input[1:].split(maxsplit=1)
        return ("system", parts[0], parts[1] if len(parts) > 1 else "")
    return ("unknown", "", input)
```

#### 4. Async CLI Entry Point
```python
# src/teambot/cli.py
import asyncio

def cmd_run(args, display):
    """Run TeamBot interactively."""
    asyncio.run(async_run(args, display))

async def async_run(args, display):
    client = CopilotSDKClient()
    await client.start()

    try:
        if args.objective:
            await load_objective(args.objective, client)
        await repl_loop(client, display)
    finally:
        await client.stop()
```

---

## 6. Session Management for Agents

### Recommended Approach

Each agent gets its own persistent session:

```python
SESSION_IDS = {
    "pm": "teambot-pm",
    "ba": "teambot-ba",
    "writer": "teambot-writer",
    "builder-1": "teambot-builder-1",
    "builder-2": "teambot-builder-2",
    "reviewer": "teambot-reviewer",
}
```

### Benefits
- ✅ Isolated context per agent
- ✅ Persistence across restarts
- ✅ Explicit sharing via `/share` command
- ✅ Independent parallel execution

### Context Sharing Implementation
```python
async def share_context(from_agent: str, to_agent: str, client: CopilotSDKClient):
    from_session = await client.get_or_create_session(from_agent)
    to_session = await client.get_or_create_session(to_agent)

    # Get history from source
    messages = from_session.get_messages()
    context = "\n".join([m["data"]["content"] for m in messages[-5:]])

    # Inject into target
    await to_session.send_and_wait({
        "prompt": f"Context from {from_agent}:\n{context}\n\nPlease acknowledge."
    })
```

---

## 7. Dependency Updates

### pyproject.toml Changes
```toml
[project]
dependencies = [
    "python-frontmatter>=1.0.0",
    "rich>=13.0.0",
    "github-copilot-sdk>=0.1.0",  # NEW
]
```

### Remove Old Dependency
- Remove subprocess-based `CopilotClient` (keep for fallback)
- Add `CopilotSDKClient` as primary

---

## 8. Testing Strategy

### Unit Tests (Mock SDK)
```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_sdk_client():
    client = MagicMock()
    client.start = AsyncMock()
    client.stop = AsyncMock()
    client.create_session = AsyncMock(return_value=mock_session())
    return client

def mock_session():
    session = MagicMock()
    session.send_and_wait = AsyncMock(return_value=mock_response())
    return session
```

### Integration Tests (Requires Copilot)
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_sdk_connection():
    client = CopilotClient()
    await client.start()
    session = await client.create_session({"model": "gpt-4.1"})
    response = await session.send_and_wait({"prompt": "Say hello"})
    assert response.data.content
    await client.stop()
```

---

## 9. Risk Mitigations

| Risk | Mitigation |
|------|------------|
| SDK API changes | Pin version, abstract behind interface |
| CLI not installed | Graceful error message, check on startup |
| Connection failures | Retry logic, timeout handling |
| Session state corruption | Catch exceptions, recreate session |

---

## 10. Open Questions Resolved

| Question | Answer |
|----------|--------|
| SDK async or sync? | **Async** - uses asyncio |
| Package import name? | `from copilot import CopilotClient` |
| Streaming support? | Yes - via `session.on()` callbacks |
| Multiple sessions? | Yes - fully independent |
| Session persistence? | Yes - custom session IDs |

---

## 11. Appendix: Full Example

```python
import asyncio
import sys
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType

async def main():
    client = CopilotClient()
    await client.start()

    # Create session for PM agent
    pm_session = await client.create_session({
        "session_id": "teambot-pm",
        "model": "gpt-4.1",
        "streaming": True,
    })

    # Set up streaming handler
    def handle_event(event):
        if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
            sys.stdout.write(event.data.delta_content)
            sys.stdout.flush()
        if event.type == SessionEventType.SESSION_IDLE:
            print()

    pm_session.on(handle_event)

    # REPL loop
    print("TeamBot Interactive Mode (type /quit to exit)")
    while True:
        try:
            user_input = input("teambot> ")
        except EOFError:
            break

        if user_input == "/quit":
            break

        if user_input.startswith("@pm "):
            task = user_input[4:]
            print("[PM] ", end="")
            await pm_session.send_and_wait({"prompt": task})
        else:
            print("Use @pm <task> or /quit")

    await client.stop()

asyncio.run(main())
```
