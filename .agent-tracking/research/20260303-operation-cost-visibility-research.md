<!-- markdownlint-disable-file -->
# Operation Cost Visibility - Deep Research Document

**Version**: 1.0  
**Date**: 2026-03-03  
**Feature Spec**: `.teambot/operation-cost-visibility/artifacts/feature_spec.md`  
**Status**: ✅ Complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Research Scope](#research-scope)
3. [Entry Point Analysis](#entry-point-analysis)
4. [Technical Findings](#technical-findings)
5. [Implementation Approach](#implementation-approach)
6. [Testing Strategy Research](#testing-strategy-research)
7. [Task Implementation Requests](#task-implementation-requests)
8. [Potential Next Research](#potential-next-research)

---

## Executive Summary

This research document provides deep technical analysis for implementing token usage tracking and cost visibility in TeamBot. The research confirms that the **Copilot SDK does expose token usage data** via streaming events, making this feature feasible.

### Key Discoveries

| Finding | Status | Impact |
|---------|--------|--------|
| SDK provides `ASSISTANT_USAGE` events with token data | ✅ Confirmed | High - Feature is feasible |
| `Usage` dataclass has `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens` | ✅ Confirmed | High - Full breakdown available |
| `SESSION_IDLE` events contain `model_metrics` with aggregated usage | ✅ Confirmed | Medium - Alternative capture point |
| CLI client (`client.py`) does NOT provide token data | ❌ Confirmed | Low - SDK path covers most use cases |
| WorkflowState.metadata dict is extensible | ✅ Confirmed | High - Persistence ready |

### Recommended Approach

**Selected**: Event-based token capture during SDK streaming with aggregation in a new `tokens` module.

---

## Research Scope

### Questions Answered

1. ✅ **Does Copilot SDK expose token usage?** - Yes, via `ASSISTANT_USAGE` events
2. ✅ **What is the data structure?** - `Usage` dataclass with 4 token fields
3. ✅ **Does CLI client expose tokens?** - No, subprocess stdout/stderr only
4. ✅ **Where to store aggregated data?** - WorkflowState.metadata and dedicated tracking
5. ✅ **How to display summaries?** - Rich library (already a dependency)

### Assumptions Validated

| Assumption | Validation |
|------------|------------|
| SDK response includes token usage | ✅ `session_events.py` defines `Usage` class (Lines 322-344) |
| Token data format is consistent | ✅ Single `Usage` dataclass for all models |
| WorkflowState.metadata can store data | ✅ Dict field, no schema restrictions (Lines 42, 62) |

---

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run <obj.md>` (orchestration) | cli.py:run_cmd → execution_loop.py → sdk_client.py | ✅ YES | YES - Primary path |
| `teambot` (REPL simple) | cli.py:main → loop.py → router.py → sdk_client.py | ✅ YES | YES - Direct SDK |
| `@agent task` (REPL advanced) | loop.py → executor.py → manager.py → sdk_client.py | ✅ YES | YES - Via executor |
| `@agent -> @agent2` (pipeline) | loop.py → executor.py → manager.py → sdk_client.py | ✅ YES | YES - Via executor |
| `@agent,@agent2 task` (multi-agent) | loop.py → executor.py → manager.py → sdk_client.py | ✅ YES | YES - Via executor |
| `@agent task &` (background) | loop.py → executor.py → manager.py → sdk_client.py | ✅ YES | YES - Via executor |

### Code Path Trace

#### Entry Point 1: Orchestration Run (`teambot run`)

1. User runs: `teambot run docs/objectives/my-task.md`
2. Handled by: `cli.py:run_cmd()` (Lines 798-960)
3. Creates: `ExecutionLoop` instance (`execution_loop.py:88-143`)
4. Executes stages via: `sdk_client.py:execute_streaming()` (Lines 399-434)
5. **Token capture point**: SDK events during streaming ✅

#### Entry Point 2: Interactive REPL (Simple)

1. User enters: `@pm create a plan`
2. Handled by: `loop.py:_handle_agent_command()` (Lines 82-108)
3. Routes to: `sdk_client.py:execute()` (Lines 351-397)
4. Uses streaming internally: `sdk_client.py:execute_streaming()` (Lines 399-434)
5. **Token capture point**: SDK events during streaming ✅

#### Entry Point 3: Interactive REPL (Advanced - Pipelines/Multi-agent)

1. User enters: `@pm -> @builder-1 create and implement`
2. Parsed by: `loop.py` detects `is_pipeline` or `len(agent_ids) > 1`
3. Handled by: `loop.py:_handle_advanced_command()` (Lines 110-136)
4. Executes via: `executor.py:execute()` → `manager.py` → SDK
5. **Token capture point**: SDK events during each task execution ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| CLI client (`client.py`) | Low - Used only for non-interactive mode | Display `n/a` for CLI-based runs |
| None critical | - | All major paths go through SDK |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## Technical Findings

### 1. SDK Token Data Structure ✅

**Source**: `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py`

```python
# Lines 322-344
@dataclass
class Usage:
    cache_read_tokens: float   # Tokens read from cache
    cache_write_tokens: float  # Tokens written to cache
    input_tokens: float        # Prompt tokens (input)
    output_tokens: float       # Completion tokens (output)

    @staticmethod
    def from_dict(obj: Any) -> 'Usage':
        cache_read_tokens = from_float(obj.get("cacheReadTokens"))
        cache_write_tokens = from_float(obj.get("cacheWriteTokens"))
        input_tokens = from_float(obj.get("inputTokens"))
        output_tokens = from_float(obj.get("outputTokens"))
        return Usage(cache_read_tokens, cache_write_tokens, input_tokens, output_tokens)
```

**Key Insight**: The SDK uses `float` for token counts (likely for future fractional tokens or precision), but we should cast to `int` for display.

### 2. SDK Event Types for Token Capture ✅

**Source**: `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py`

```python
# Lines 915-955 (SessionEventType enum)
class SessionEventType(Enum):
    ASSISTANT_USAGE = "assistant.usage"        # Per-request usage
    SESSION_IDLE = "session.idle"              # Contains model_metrics
    SESSION_USAGE_INFO = "session.usage_info"  # Session-level usage
    # ...
```

**Token Capture Points**:

| Event Type | Contains | When Fired | Recommended Use |
|------------|----------|------------|-----------------|
| `ASSISTANT_USAGE` | `input_tokens`, `output_tokens`, `cache_*_tokens` | After each API call | ✅ Primary capture |
| `SESSION_IDLE` | `model_metrics` with aggregated `Usage` | When session becomes idle | Backup/validation |

### 3. SDK Event Data Structure ✅

**Source**: `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py`

```python
# Lines 565-572 (Data fields relevant to token tracking)
@dataclass
class Data:
    # ... many fields ...
    cache_read_tokens: Optional[float] = None
    cache_write_tokens: Optional[float] = None
    input_tokens: Optional[float] = None
    output_tokens: Optional[float] = None
    model_metrics: Optional[Dict[str, ModelMetric]] = None  # Aggregated usage
    # ...
```

**Key Pattern**: Token data is available both per-event (`input_tokens`, etc.) and aggregated (`model_metrics`).

### 4. Current SDK Client Implementation

**Source**: `src/teambot/copilot/sdk_client.py` (Lines 435-531)

```python
async def _execute_streaming_once(self, agent_id, prompt, on_chunk=None):
    # Current event handler (Lines 451-499)
    def on_event(event):
        event_type_upper = event_type_str.upper()
        
        # Currently only handles:
        if "ASSISTANT_MESSAGE_DELTA" in event_type_upper:
            # Text streaming
            ...
        elif "SESSION_IDLE" in event_type_upper:
            # Completion marker
            done.set()
        elif "SESSION_ERROR" in event_type_upper:
            # Error handling
            ...
```

**Gap**: No handling for `ASSISTANT_USAGE` events currently.

**Required Change**: Add token capture in the `on_event` callback.

### 5. WorkflowState Metadata Structure ✅

**Source**: `src/teambot/workflow/state_machine.py` (Lines 35-86)

```python
@dataclass
class WorkflowState:
    current_stage: WorkflowStage
    started_at: datetime
    history: list[StageHistory] = field(default_factory=list)
    objective: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)  # ← Extension point

    def to_dict(self) -> dict[str, Any]:
        return {
            # ...
            "metadata": self.metadata,  # Directly serialized
        }
```

**Key Insight**: `metadata` is a free-form dict that serializes directly to JSON. Perfect for token tracking data.

### 6. TaskResult Current Structure

**Source**: `src/teambot/tasks/models.py` (Lines 33-50)

```python
@dataclass
class TaskResult:
    task_id: str
    output: str
    success: bool
    error: str | None = None
    completed_at: datetime = field(default_factory=datetime.now)
    # ⚠️ No token_usage field currently
```

**Required Change**: Add optional `token_usage: TokenUsage | None` field.

### 7. CLI Client Analysis (No Token Data) ❌

**Source**: `src/teambot/copilot/client.py` (Lines 85-101)

```python
result = subprocess.run(cmd, capture_output=True, text=True, ...)
return CopilotResult(
    success=result.returncode == 0,
    output=result.stdout,
    error=result.stderr if result.stderr else None,
    # ⚠️ No token data available from subprocess
)
```

**Conclusion**: CLI client cannot provide token data. Graceful degradation required.

### 8. Display Infrastructure (Rich Library) ✅

**Source**: `src/teambot/visualization/console.py`

The codebase already uses Rich for display:
- `Panel` for boxed content (Line 293)
- `Table` for structured data (Line 254-271)
- Color support via markup (Lines 24-52)

**No new dependencies needed.**

### 9. Configuration Pattern ✅

**Source**: `src/teambot/config/loader.py` (Lines 217-327)

Pattern for adding new config section:

```python
# Validation (add to _validate method)
if "token_tracking" in config:
    self._validate_token_tracking(config["token_tracking"])

def _validate_token_tracking(self, token_tracking: dict[str, Any]) -> None:
    if not isinstance(token_tracking, dict):
        raise ConfigError("'token_tracking' must be an object")
    if "enabled" in token_tracking:
        if not isinstance(token_tracking["enabled"], bool):
            raise ConfigError("'token_tracking.enabled' must be a boolean")

# Defaults (add to _apply_defaults method)
if "token_tracking" not in config:
    config["token_tracking"] = {}
token_cfg = config["token_tracking"]
if "enabled" not in token_cfg:
    token_cfg["enabled"] = True  # Default: enabled
```

---

## Implementation Approach

### Selected Architecture

```
src/teambot/
├── tokens/                          # NEW MODULE
│   ├── __init__.py                  # Exports
│   ├── models.py                    # TokenUsage dataclass
│   ├── tracker.py                   # TokenTracker class
│   ├── aggregator.py                # Per-agent/stage aggregation
│   └── display.py                   # Rich-based summary rendering
├── copilot/
│   └── sdk_client.py                # MODIFY: Add token capture
├── tasks/
│   └── models.py                    # MODIFY: Add token_usage to TaskResult
├── workflow/
│   └── state_machine.py             # MODIFY: Token data in metadata
├── repl/
│   └── loop.py                      # MODIFY: Session summary on exit
├── orchestration/
│   └── execution_loop.py            # MODIFY: Run summary display
└── config/
    └── loader.py                    # MODIFY: token_tracking config
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        SDK Client                                │
│  on_event() captures ASSISTANT_USAGE events                      │
│  Returns TokenUsage with response                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TaskResult + TokenUsage                      │
│  Each task stores its token usage                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TokenTracker                                │
│  Aggregates by agent_id and stage                                │
│  Maintains running totals                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Display / Persistence                       │
│  Rich panel for console output                                   │
│  JSON serialization for workflow_state.json                      │
└─────────────────────────────────────────────────────────────────┘
```

### TokenUsage Dataclass Design

```python
# src/teambot/tokens/models.py
from dataclasses import dataclass
from typing import Any

@dataclass
class TokenUsage:
    """Token usage from a single API call.
    
    All fields are optional (None = unavailable).
    Uses int for display simplicity despite SDK using float.
    """
    input_tokens: int | None = None      # prompt_tokens equivalent
    output_tokens: int | None = None     # completion_tokens equivalent
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    
    @property
    def total_tokens(self) -> int | None:
        """Calculate total tokens if data available."""
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON storage."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "total_tokens": self.total_tokens,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenUsage":
        """Deserialize from JSON."""
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            cache_read_tokens=data.get("cache_read_tokens"),
            cache_write_tokens=data.get("cache_write_tokens"),
        )
    
    @classmethod
    def from_sdk_usage(cls, sdk_usage: Any) -> "TokenUsage":
        """Create from SDK Usage dataclass."""
        return cls(
            input_tokens=int(sdk_usage.input_tokens) if sdk_usage.input_tokens else None,
            output_tokens=int(sdk_usage.output_tokens) if sdk_usage.output_tokens else None,
            cache_read_tokens=int(sdk_usage.cache_read_tokens) if sdk_usage.cache_read_tokens else None,
            cache_write_tokens=int(sdk_usage.cache_write_tokens) if sdk_usage.cache_write_tokens else None,
        )
    
    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage instances for aggregation."""
        def add_optional(a: int | None, b: int | None) -> int | None:
            if a is None and b is None:
                return None
            return (a or 0) + (b or 0)
        
        return TokenUsage(
            input_tokens=add_optional(self.input_tokens, other.input_tokens),
            output_tokens=add_optional(self.output_tokens, other.output_tokens),
            cache_read_tokens=add_optional(self.cache_read_tokens, other.cache_read_tokens),
            cache_write_tokens=add_optional(self.cache_write_tokens, other.cache_write_tokens),
        )
```

### SDK Client Modification

```python
# In sdk_client.py:_execute_streaming_once() - modify on_event handler

async def _execute_streaming_once(
    self,
    agent_id: str,
    prompt: str,
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[str, TokenUsage | None]:  # Return type change
    """Execute a single streaming attempt (no retry).
    
    Returns:
        Tuple of (response_text, token_usage).
    """
    # ... existing setup ...
    
    # Add token tracking
    usage_holder: list[TokenUsage | None] = [None]
    
    def on_event(event):
        event_type_str = str(event.type.value if hasattr(event.type, "value") else event.type)
        event_type_upper = event_type_str.upper()
        
        # Existing handlers...
        if "ASSISTANT_MESSAGE_DELTA" in event_type_upper:
            # ... existing text streaming ...
            pass
        
        # NEW: Token usage capture
        elif "ASSISTANT_USAGE" in event_type_upper:
            # Capture token data from event.data
            if hasattr(event.data, "input_tokens") and event.data.input_tokens is not None:
                from teambot.tokens.models import TokenUsage
                usage_holder[0] = TokenUsage(
                    input_tokens=int(event.data.input_tokens) if event.data.input_tokens else None,
                    output_tokens=int(event.data.output_tokens) if event.data.output_tokens else None,
                    cache_read_tokens=int(event.data.cache_read_tokens) if event.data.cache_read_tokens else None,
                    cache_write_tokens=int(event.data.cache_write_tokens) if event.data.cache_write_tokens else None,
                )
                logger.debug(f"Token usage captured: {usage_holder[0]}")
        
        elif "SESSION_IDLE" in event_type_upper:
            # ... existing completion handling ...
            done.set()
        
        # ... rest of existing handlers ...
    
    # ... rest of method ...
    
    return "".join(accumulated), usage_holder[0]
```

### Display Component Design

```python
# src/teambot/tokens/display.py
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from teambot.tokens.models import TokenUsage

def render_token_summary(
    total: TokenUsage,
    by_agent: dict[str, TokenUsage],
    by_stage: dict[str, TokenUsage] | None = None,
) -> Panel:
    """Render token usage summary as Rich Panel.
    
    Args:
        total: Total aggregated usage.
        by_agent: Usage per agent.
        by_stage: Optional usage per workflow stage.
    
    Returns:
        Rich Panel ready for console.print().
    """
    if total.total_tokens is None:
        return Panel(
            "[yellow]Token Usage Summary: n/a (token data unavailable from Copilot)[/yellow]",
            title="📊 Token Usage",
        )
    
    lines = []
    
    # Total line
    total_str = f"[bold]Total Tokens:[/bold] {total.total_tokens:,}"
    if total.input_tokens and total.output_tokens:
        total_str += f" (prompt: {total.input_tokens:,} | completion: {total.output_tokens:,})"
    lines.append(total_str)
    lines.append("")
    
    # By agent breakdown
    if by_agent:
        lines.append("[bold]By Agent:[/bold]")
        max_tokens = max((u.total_tokens or 0) for u in by_agent.values()) or 1
        for agent_id, usage in sorted(by_agent.items(), key=lambda x: -(x[1].total_tokens or 0)):
            tokens = usage.total_tokens or 0
            bar_width = int((tokens / max_tokens) * 10)
            bar = "█" * bar_width + "░" * (10 - bar_width)
            pct = (tokens / (total.total_tokens or 1)) * 100
            lines.append(f"  {agent_id:12} │ {bar} │ {tokens:>8,} ({pct:.1f}%)")
    
    # By stage breakdown (if provided)
    if by_stage:
        lines.append("")
        lines.append("[bold]By Stage:[/bold]")
        for stage_name, usage in by_stage.items():
            tokens = usage.total_tokens or 0
            lines.append(f"  {stage_name:20} │ {tokens:>8,}")
    
    return Panel("\n".join(lines), title="📊 Token Usage Summary")


def render_session_summary(total: TokenUsage) -> str:
    """Render brief session summary line.
    
    Args:
        total: Session total usage.
    
    Returns:
        Formatted string for console output.
    """
    if total.total_tokens is None:
        return "Session Token Usage: n/a"
    
    result = f"Session Token Usage: {total.total_tokens:,} tokens"
    if total.input_tokens and total.output_tokens:
        result += f" (prompt: {total.input_tokens:,} | completion: {total.output_tokens:,})"
    return result
```

---

## Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Details | Source |
|--------|---------|--------|
| **Framework** | pytest 7.4.0 | `pyproject.toml:26` |
| **Location** | `tests/` directory | `pyproject.toml:54` |
| **Naming** | `test_*.py` files | `pyproject.toml:55` |
| **Runner** | `uv run pytest` | AGENTS.md |
| **Coverage** | pytest-cov, 80% target | pyproject.toml:27 |
| **Async** | pytest-asyncio (auto mode) | pyproject.toml:58 |
| **Mocking** | pytest-mock | pyproject.toml:28 |
| **Markers** | `acceptance` (slow tests) | pyproject.toml:59-62 |

### Test Patterns Found

**File**: `tests/test_tasks/test_models.py` (Lines 1-182)

- Uses dataclass instantiation testing
- Tests default values
- Tests method behaviors
- Clear arrange-act-assert pattern

```python
# Example pattern (Lines 33-47)
def test_task_creation_minimal(self):
    task = Task(
        id="task-1",
        agent_id="pm",
        prompt="Create a plan",
    )
    assert task.id == "task-1"
    assert task.agent_id == "pm"
```

**File**: `tests/test_copilot/` directory

- Mocks SDK responses
- Tests error handling
- Tests async methods with `pytest.mark.asyncio`

### Coverage Standards

- **Unit Tests**: 80% minimum (current project standard)
- **Acceptance Tests**: Marked with `@pytest.mark.acceptance`
- **Critical Paths**: 100% for token capture logic

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `TokenUsage` dataclass | TDD | Critical data model, well-defined requirements |
| `TokenTracker` aggregation | TDD | Complex logic, multiple edge cases |
| SDK event capture | Code-First | Requires SDK mocking, integration focus |
| Display rendering | Code-First | UI/formatting, easier to iterate |
| Config validation | TDD | Clear validation rules |
| Integration (REPL exit) | Code-First then acceptance | End-to-end validation |

---

## Task Implementation Requests

### High Priority (Core Functionality)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **T1: Create tokens module** | New `src/teambot/tokens/` with `models.py`, `tracker.py`, `aggregator.py` | Medium |
| **T2: TokenUsage dataclass** | Implement dataclass with SDK conversion, serialization, addition | Small |
| **T3: SDK token capture** | Modify `sdk_client.py` to capture `ASSISTANT_USAGE` events | Medium |
| **T4: TaskResult extension** | Add `token_usage: TokenUsage | None` field | Small |
| **T5: TokenTracker class** | Aggregate by agent, stage; maintain session totals | Medium |

### Medium Priority (Display & Persistence)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **T6: Display rendering** | Rich Panel for orchestration summary | Small |
| **T7: Session summary** | Brief line for interactive mode exit | Small |
| **T8: Workflow state persistence** | Store token tracking in `metadata.token_tracking` | Small |
| **T9: Orchestration integration** | Call display at end of `ExecutionLoop.run()` | Small |
| **T10: REPL integration** | Display on `/exit` or Ctrl+C in `loop.py:_cleanup()` | Small |

### Lower Priority (Configuration & Polish)

| Task | Description | Estimated Effort |
|------|-------------|------------------|
| **T11: Config validation** | Add `token_tracking.enabled` to loader | Small |
| **T12: Graceful degradation** | Handle missing data, single warning log | Small |
| **T13: Unit tests** | TokenUsage, TokenTracker, aggregation logic | Medium |
| **T14: Acceptance tests** | AT-001 through AT-006 from spec | Medium |

### Implementation Order

1. **Phase 1**: T2 → T1 → T5 (Data models and aggregation)
2. **Phase 2**: T3 → T4 (SDK integration)
3. **Phase 3**: T6 → T7 → T9 → T10 (Display and integration)
4. **Phase 4**: T8 → T11 → T12 (Persistence and config)
5. **Phase 5**: T13 → T14 (Tests)

---

## Potential Next Research

| Topic | Reason | Priority |
|-------|--------|----------|
| None | Research complete | - |

All open questions from the feature spec have been answered:

- **Q-001**: ✅ SDK response.data DOES contain usage/token fields
- **Q-002**: ❌ CLI output does NOT include token info (subprocess only)
- **Q-003**: ✅ Exact structure documented (`Usage` dataclass with 4 fields)

---

## References

| Ref | Type | Location | Description |
|-----|------|----------|-------------|
| SDK Usage class | External | `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py:322-344` | Token usage dataclass |
| SDK Event types | External | `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py:915-955` | Session event enum |
| SDK Data fields | External | `/home/vscode/.local/lib/python3.12/site-packages/copilot/generated/session_events.py:565-572` | Event data with token fields |
| SDK Client | Internal | `src/teambot/copilot/sdk_client.py:435-531` | Streaming event handler |
| WorkflowState | Internal | `src/teambot/workflow/state_machine.py:35-86` | State with metadata dict |
| TaskResult | Internal | `src/teambot/tasks/models.py:33-50` | Task result dataclass |
| ConfigLoader | Internal | `src/teambot/config/loader.py:217-327` | Config validation pattern |
| ConsoleDisplay | Internal | `src/teambot/visualization/console.py` | Rich library patterns |
| Feature Spec | Internal | `.teambot/operation-cost-visibility/artifacts/feature_spec.md` | Requirements |
