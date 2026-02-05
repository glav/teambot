<!-- markdownlint-disable-file -->
# Research Document: Output Pane Enhancement

**Date:** 2026-02-05  
**Feature:** Output Pane Enhancement for Multi-Agent Identification  
**Status:** ✅ Research Complete  
**Spec Reference:** `.teambot/output-pane-enhancement/artifacts/feature_spec.md`

---

## 📋 Table of Contents

1. [Research Scope](#1-research-scope)
2. [Current Implementation Analysis](#2-current-implementation-analysis)
3. [Entry Point Analysis](#3-entry-point-analysis)
4. [Technical Approach](#4-technical-approach)
5. [Implementation Patterns](#5-implementation-patterns)
6. [Testing Strategy Research](#6-testing-strategy-research)
7. [Task Implementation Requests](#7-task-implementation-requests)
8. [Potential Next Research](#8-potential-next-research)

---

## 1. Research Scope

### 1.1 Objectives

| Objective | Description |
|-----------|-------------|
| **Agent Identification** | Ensure each agent's output is visually distinguishable with persona-specific colors and icons |
| **Eliminate Horizontal Scroll** | Configure word wrapping to prevent horizontal scrolling in output pane |
| **Agent Handoff Indicators** | Visual separator when processing switches between agents |
| **Terminal Compatibility** | Maintain existing terminal experience without degradation |

### 1.2 Success Criteria from Feature Spec

- ✅ FR-001: Agent Color Coding (P0)
- ✅ FR-002: Agent Persona Icons (P0)
- ✅ FR-003: Text Word Wrap (P0)
- ✅ FR-004: Agent Handoff Indicator (P1)
- ✅ FR-005: Colored Output Block Border (P2)
- ✅ FR-006: Agent ID Color in All Message Types (P0)
- ✅ FR-007: Streaming Indicator Colored (P1)
- ✅ FR-008: Preserve Code Block Formatting (P0)

### 1.3 Assumptions

- Rich (>=13.0.0) and Textual (>=0.47.0) are already dependencies
- Terminal supports 256-color or truecolor
- 6 agent personas with distinct visual identities are sufficient

---

## 2. Current Implementation Analysis

### 2.1 OutputPane Class (`src/teambot/ui/widgets/output_pane.py`)

**Current Location:** Lines 1-136

```python
class OutputPane(RichLog):
    """Output pane for displaying agent responses with timestamps."""
```

**Current Features:**
- Extends Textual's `RichLog` widget
- Timestamps in dim gray: `[dim]{timestamp}[/dim]`
- Status icons: ✓ (green), ✗ (red), ⟳ (yellow), ℹ (blue)
- Small `@agent_id` prefix (no persona color)
- Streaming state tracking via `_streaming_buffers` dict

**Current Write Methods:**

| Method | Format | Persona Color? |
|--------|--------|----------------|
| `write_command()` | `[dim]HH:MM:SS[/dim] [bold]>[/bold] {command}` | ❌ |
| `write_task_complete()` | `[dim]HH:MM:SS[/dim] [green]✓[/green] @{agent_id}: {result}` | ❌ |
| `write_task_error()` | `[dim]HH:MM:SS[/dim] [red]✗[/red] @{agent_id}: {error}` | ❌ |
| `write_info()` | `[dim]HH:MM:SS[/dim] [blue]ℹ[/blue] {message}` | N/A |
| `write_streaming_start()` | `[dim]HH:MM:SS[/dim] [yellow]⟳[/yellow] @{agent_id}: [dim]streaming...[/dim]` | ❌ |
| `finish_streaming()` | `[dim]HH:MM:SS[/dim] [green/red]✓/✗[/] @{agent_id}: {content}` | ❌ |

### 2.2 Existing PERSONA_COLORS (`src/teambot/visualization/console.py`)

**Location:** Lines 24-31

```python
PERSONA_COLORS = {
    "project_manager": "blue",
    "business_analyst": "cyan",
    "technical_writer": "green",
    "builder": "yellow",
    "reviewer": "magenta",
}
```

**Problem:** These colors are defined but NOT used in `OutputPane`. They use persona names (e.g., `project_manager`), not agent IDs (e.g., `pm`).

### 2.3 RichLog Widget Configuration

**Discovery:** RichLog has a `wrap` parameter!

```python
RichLog.__init__ signature:
(self, *, max_lines: 'int | None' = None, min_width: 'int' = 78, 
 wrap: 'bool' = False, highlight: 'bool' = False, markup: 'bool' = False,
 auto_scroll: 'bool' = True, ...)
```

**Current Usage in app.py (Line 95):**
```python
yield OutputPane(id="output", highlight=True, markup=True)
```

**Missing:** `wrap=True` parameter! This is why horizontal scrolling occurs.

### 2.4 Styles CSS (`src/teambot/ui/styles.css`)

**Current Output Pane Style (Lines 36-40):**
```css
#output {
    width: 70%;
    border: solid $secondary;
    padding: 0 1;
}
```

**Note:** No explicit wrap or overflow settings for output pane.

---

## 3. Entry Point Analysis

### 3.1 User Input Entry Points

| Entry Point | Code Path | Reaches OutputPane? | Implementation Required? |
|-------------|-----------|---------------------|-------------------------|
| `@agent task` (simple) | `app.py:handle_input()` → `_handle_agent_command()` → `OutputPane.write_*()` | ✅ YES | ✅ YES |
| `@agent task &` (background) | `app.py:handle_input()` → `_handle_agent_command()` → `OutputPane.write_*()` | ✅ YES | ✅ YES |
| `@agent1,@agent2 task` (multi-agent) | `app.py:handle_input()` → `_handle_multiagent_streaming()` → `OutputPane.write_*()` | ✅ YES | ✅ YES |
| `/command` (system) | `app.py:_handle_system_command()` → `OutputPane.write_system()` | ✅ YES | ❌ No agent ID |
| Raw input (default agent) | `app.py:handle_input()` → `_handle_agent_command()` → `OutputPane.write_*()` | ✅ YES | ✅ YES |

### 3.2 Code Path Trace

#### Entry Point 1: Simple Agent Command (`@pm create a plan`)

1. User enters: `@pm create a plan`
2. Handled by: `app.py:handle_input()` (Lines 97-138)
3. Parsed by: `parse_command()` → CommandType.AGENT
4. Routes to: `app.py:_handle_agent_command()` (Lines 140-234)
5. Output calls:
   - `output.write_streaming_start(agent_id)` (Line 166)
   - `output.write_streaming_chunk(agent_id, chunk)` (Line 192)
   - `output.finish_streaming(agent_id, success=True)` (Line 202)
   - `output.write_task_complete(agent_id, result.output)` (Line 221) OR
   - `output.write_task_error(agent_id, str(e))` (Line 209)

#### Entry Point 2: Multi-Agent Command (`@pm,@ba analyze requirements`)

1. User enters: `@pm,@ba analyze requirements`
2. Handled by: `app.py:handle_input()` (Lines 97-138)
3. Routes to: `app.py:_handle_multiagent_streaming()` (Lines 236-284)
4. Output calls (per agent in parallel):
   - `output.write_streaming_start(agent_id)` (Line 250)
   - `output.write_streaming_chunk(agent_id, chunk)` (Line 264)
   - `output.finish_streaming(agent_id, success=True)` (Line 270)

### 3.3 Coverage Verification

| Method in OutputPane | Called From | Agent ID Available? | Needs Enhancement? |
|---------------------|-------------|--------------------|--------------------|
| `write_command()` | `handle_input()` Line 108 | ❌ (command text) | ❌ No |
| `write_task_complete()` | `_handle_agent_command()` Line 221 | ✅ | ✅ YES |
| `write_task_error()` | `_handle_agent_command()` Lines 209, 225, 229 | ✅ | ✅ YES |
| `write_info()` | Various system messages | ❌ | ❌ No |
| `write_system()` | `_handle_system_command()` Line 308 | ❌ | ❌ No |
| `write_streaming_start()` | `_handle_agent_command()` Line 166, `_handle_multiagent_streaming()` Line 250 | ✅ | ✅ YES |
| `write_streaming_chunk()` | `_handle_agent_command()` Line 192, `_handle_multiagent_streaming()` Line 264 | ✅ | ⚠️ (internal) |
| `finish_streaming()` | Multiple locations | ✅ | ✅ YES |

### 3.4 Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| Agent ID to persona mapping missing | Cannot lookup persona color from agent_id | Create `AGENT_ID_TO_PERSONA` mapping |
| No handoff tracking | Cannot detect when agent changes | Add `_last_agent_id` state variable |
| `wrap=False` default | Horizontal scrolling | Set `wrap=True` in OutputPane init |

---

## 4. Technical Approach

### 4.1 Recommended Approach: Rich Markup Enhancement

**Rationale:** Leverage existing Rich markup support in RichLog without complex widget restructuring.

**Benefits:**
- ✅ Minimal code changes
- ✅ Uses existing Rich markup parsing (`markup=True` already set)
- ✅ Persona colors already defined
- ✅ RichLog supports `wrap=True` parameter

### 4.2 Agent ID to Persona Mapping

**Proposed Constant (add to `console.py` or new `output_pane.py` section):**

```python
# Agent ID to persona mapping
AGENT_PERSONAS = {
    "pm": "project_manager",
    "ba": "business_analyst", 
    "writer": "technical_writer",
    "builder-1": "builder",
    "builder-2": "builder",
    "reviewer": "reviewer",
}

# Agent-specific icons for visual identification
AGENT_ICONS = {
    "pm": "📋",
    "ba": "📊",
    "writer": "📝",
    "builder-1": "🔨",
    "builder-2": "🔨",
    "reviewer": "🔍",
}

# ASCII fallback icons for limited terminals
AGENT_ICONS_ASCII = {
    "pm": "[PM]",
    "ba": "[BA]",
    "writer": "[WR]",
    "builder-1": "[B1]",
    "builder-2": "[B2]",
    "reviewer": "[RV]",
}
```

### 4.3 Helper Function Design

```python
def get_agent_style(agent_id: str) -> tuple[str, str]:
    """Get color and icon for an agent.
    
    Args:
        agent_id: The agent identifier (e.g., 'pm', 'builder-1').
        
    Returns:
        Tuple of (color, icon) for the agent.
    """
    persona = AGENT_PERSONAS.get(agent_id, "builder")
    color = PERSONA_COLORS.get(persona, "white")
    icon = AGENT_ICONS.get(agent_id, "●")
    return color, icon
```

### 4.4 Word Wrap Implementation

**Simple Fix:** Modify `OutputPane.__init__()` to pass `wrap=True`:

```python
def __init__(self, *args, **kwargs):
    # Enable word wrap to prevent horizontal scrolling
    kwargs.setdefault('wrap', True)
    super().__init__(*args, **kwargs)
    self._streaming_buffers: dict[str, list[str]] = {}
    self._streaming_starts: dict[str, str] = {}
    self._last_agent_id: str | None = None  # For handoff detection
```

### 4.5 Handoff Indicator Implementation

**State Tracking:**
```python
# In OutputPane class
self._last_agent_id: str | None = None

def _check_handoff(self, agent_id: str) -> bool:
    """Check if this is a handoff from another agent.
    
    Returns True if previous agent was different (and not None).
    """
    if self._last_agent_id and self._last_agent_id != agent_id:
        return True
    return False

def _write_handoff_separator(self, from_agent: str, to_agent: str) -> None:
    """Write a visual separator for agent handoff."""
    _, to_icon = get_agent_style(to_agent)
    to_color, _ = get_agent_style(to_agent)
    separator = f"[dim]{'─' * 40}[/dim]"
    label = f"[{to_color}]→ {to_icon} @{to_agent}[/{to_color}]"
    self.write(f"{separator} {label}")
```

### 4.6 Code Block Preservation Strategy

**Challenge:** Text wrapping should NOT apply inside code blocks (```) to preserve formatting.

**Research Finding:** RichLog's `wrap=True` applies to all content. For code blocks, we need to either:

1. **Option A: Pre-process content** - Detect code blocks and wrap them in Rich `Syntax` objects
2. **Option B: Use `no_wrap` Text objects** - Wrap code blocks in `Text(content, no_wrap=True)`
3. **Option C: Rich Markdown rendering** - Use Rich's Markdown class for full content

**Recommended: Option B** - Simplest, preserves existing behavior for non-code content.

```python
from rich.text import Text

def _format_content_with_code_blocks(self, content: str) -> list:
    """Split content into wrapped text and preserved code blocks."""
    # Split on code block markers
    parts = []
    in_code_block = False
    current_block = []
    
    for line in content.split('\n'):
        if line.startswith('```'):
            if in_code_block:
                # End of code block - emit as no_wrap
                parts.append(Text('\n'.join(current_block), no_wrap=True))
                current_block = []
            in_code_block = not in_code_block
        else:
            current_block.append(line)
    
    # Remaining content
    if current_block:
        parts.append('\n'.join(current_block))
    
    return parts
```

---

## 5. Implementation Patterns

### 5.1 Enhanced write_task_complete Example

**Before (Lines 24-28):**
```python
def write_task_complete(self, agent_id: str, result: str) -> None:
    """Write task completion message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    self.write(f"[dim]{timestamp}[/dim] [green]✓[/green] @{agent_id}: {result}")
    self.scroll_end()
```

**After:**
```python
def write_task_complete(self, agent_id: str, result: str) -> None:
    """Write task completion message with persona styling."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    color, icon = get_agent_style(agent_id)
    
    # Check for handoff
    if self._check_handoff(agent_id):
        self._write_handoff_separator(self._last_agent_id, agent_id)
    self._last_agent_id = agent_id
    
    # Format with persona color
    self.write(
        f"[dim]{timestamp}[/dim] [green]✓[/green] "
        f"[{color}]{icon} @{agent_id}[/{color}]: {result}"
    )
    self.scroll_end()
```

### 5.2 Enhanced finish_streaming Example

**After:**
```python
def finish_streaming(self, agent_id: str, success: bool = True) -> None:
    """Mark streaming complete with persona styling."""
    if agent_id not in self._streaming_buffers:
        return

    content = "".join(self._streaming_buffers[agent_id])
    timestamp = self._streaming_starts.get(agent_id, datetime.now().strftime("%H:%M:%S"))

    del self._streaming_buffers[agent_id]
    if agent_id in self._streaming_starts:
        del self._streaming_starts[agent_id]

    color, icon = get_agent_style(agent_id)
    
    # Check for handoff
    if self._check_handoff(agent_id):
        self._write_handoff_separator(self._last_agent_id, agent_id)
    self._last_agent_id = agent_id
    
    status_icon = "[green]✓[/green]" if success else "[red]✗[/red]"
    self.write(
        f"[dim]{timestamp}[/dim] {status_icon} "
        f"[{color}]{icon} @{agent_id}[/{color}]: {content}"
    )
    self.scroll_end()
```

### 5.3 CSS Enhancement (Optional)

For additional styling, update `styles.css`:

```css
#output {
    width: 70%;
    border: solid $secondary;
    padding: 0 1;
    /* Word wrap is handled by RichLog wrap=True */
}
```

---

## 6. Testing Strategy Research

### 6.1 Existing Test Infrastructure

**Framework:** pytest 7.4.0+ with pytest-asyncio  
**Location:** `tests/test_ui/test_output_pane.py`  
**Current Tests:** 17 tests, all passing  
**Coverage Tool:** pytest-cov  
**Test Runner:** `uv run pytest`

### 6.2 Test Patterns Found

**File:** `tests/test_ui/test_output_pane.py` (Lines 1-297)

**Key Patterns:**
- Uses `unittest.mock.patch` for mocking `write()` and `scroll_end()` methods
- Direct instantiation of `OutputPane()` without full Textual app context
- Assertions on call arguments to verify Rich markup format
- Two test classes: `TestOutputPane` (basic methods) and `TestOutputPaneStreaming` (streaming)

**Example Test Pattern:**
```python
def test_write_task_complete_format(self):
    from teambot.ui.widgets.output_pane import OutputPane
    pane = OutputPane()
    
    with patch.object(pane, "write") as mock_write:
        with patch.object(pane, "scroll_end"):
            pane.write_task_complete("pm", "Plan created")
            
            call_arg = mock_write.call_args[0][0]
            assert "✓" in call_arg
            assert "@pm" in call_arg
            assert "Plan created" in call_arg
```

### 6.3 New Tests Required

| Test Category | Test Name | Purpose |
|---------------|-----------|---------|
| **Agent Colors** | `test_write_task_complete_uses_persona_color` | Verify PM output uses blue color |
| **Agent Colors** | `test_all_agents_have_distinct_colors` | Verify each agent ID maps to correct color |
| **Agent Icons** | `test_write_task_complete_includes_icon` | Verify 📋 icon appears for PM |
| **Agent Icons** | `test_all_agents_have_icons` | Verify all 6 agents have icons |
| **Handoff** | `test_handoff_separator_on_agent_change` | Verify separator appears when agent changes |
| **Handoff** | `test_no_handoff_for_same_agent` | Verify no separator when same agent continues |
| **Wrap** | `test_wrap_enabled_by_default` | Verify `wrap=True` is set |
| **Streaming** | `test_streaming_uses_persona_color` | Verify streaming indicator uses agent color |

### 6.4 Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `get_agent_style()` | TDD | Pure function, easy to test first |
| `AGENT_PERSONAS` mapping | TDD | Data mapping, test coverage critical |
| `write_*` methods | Code-First | Modifying existing working code |
| `_check_handoff()` | TDD | New logic, benefits from test-first |
| `_write_handoff_separator()` | Code-First | Simple string formatting |
| Integration tests | Code-First | Requires working implementation |

---

## 7. Task Implementation Requests

### 7.1 Core Implementation Tasks

| Task ID | Description | Priority | Files Affected | Est. Complexity |
|---------|-------------|----------|----------------|-----------------|
| **T-001** | Add `AGENT_PERSONAS` and `AGENT_ICONS` constants | P0 | `visualization/console.py` | Low |
| **T-002** | Create `get_agent_style()` helper function | P0 | `visualization/console.py` | Low |
| **T-003** | Enable `wrap=True` in OutputPane init | P0 | `ui/widgets/output_pane.py` | Low |
| **T-004** | Add `_last_agent_id` state tracking | P1 | `ui/widgets/output_pane.py` | Low |
| **T-005** | Implement `_check_handoff()` method | P1 | `ui/widgets/output_pane.py` | Low |
| **T-006** | Implement `_write_handoff_separator()` | P1 | `ui/widgets/output_pane.py` | Medium |
| **T-007** | Update `write_task_complete()` with persona styling | P0 | `ui/widgets/output_pane.py` | Medium |
| **T-008** | Update `write_task_error()` with persona styling | P0 | `ui/widgets/output_pane.py` | Medium |
| **T-009** | Update `write_streaming_start()` with persona styling | P0 | `ui/widgets/output_pane.py` | Medium |
| **T-010** | Update `finish_streaming()` with persona styling | P0 | `ui/widgets/output_pane.py` | Medium |
| **T-011** | Add unit tests for new functionality | P0 | `tests/test_ui/test_output_pane.py` | Medium |
| **T-012** | Add tests for console.py additions | P0 | `tests/test_visualization/test_console.py` | Low |

### 7.2 Optional Enhancement Tasks (P2)

| Task ID | Description | Priority | Notes |
|---------|-------------|----------|-------|
| **T-013** | Implement colored left border using Rich Panel | P2 | May require custom rendering |
| **T-014** | Code block preservation logic | P2 | Only if word wrap breaks code |
| **T-015** | ASCII icon fallback for limited terminals | P2 | Detect terminal capabilities |

### 7.3 Implementation Order Recommendation

```
Phase 1 (P0 - Core):
T-001 → T-002 → T-003 → T-007 → T-008 → T-009 → T-010 → T-011 → T-012

Phase 2 (P1 - Handoff):
T-004 → T-005 → T-006 → Update T-007/T-008/T-009/T-010 to use handoff

Phase 3 (P2 - Optional):
T-013 → T-014 → T-015
```

---

## 8. Potential Next Research

### 8.1 Completed Research Areas ✅

- [x] RichLog wrap parameter discovery
- [x] PERSONA_COLORS location and format
- [x] Entry point analysis for all agent command paths
- [x] Testing infrastructure and patterns
- [x] Rich markup syntax for styling

### 8.2 Future Research (Not Required for MVP)

| Topic | When to Research | Impact |
|-------|------------------|--------|
| Rich Panel for left border | If FR-005 becomes P0/P1 | Medium |
| Terminal capability detection | If icon rendering issues reported | Low |
| Rich Syntax for code blocks | If code formatting issues reported | Medium |
| Performance benchmarking | After implementation | Low |

---

## 📎 References

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Code | `src/teambot/ui/widgets/output_pane.py` | Current OutputPane implementation (136 lines) |
| REF-002 | Code | `src/teambot/visualization/console.py` (Lines 24-31) | PERSONA_COLORS definition |
| REF-003 | Code | `src/teambot/ui/app.py` (Lines 140-284) | Agent command handling entry points |
| REF-004 | Test | `tests/test_ui/test_output_pane.py` | 17 existing tests for OutputPane |
| REF-005 | External | Rich Markup Docs | https://rich.readthedocs.io/en/stable/markup.html |
| REF-006 | External | Rich Style Docs | https://rich.readthedocs.io/en/stable/style.html |
| REF-007 | Spec | `.teambot/output-pane-enhancement/artifacts/feature_spec.md` | Feature specification |
| REF-008 | Code | `pyproject.toml` | Dependencies: rich>=13.0.0, textual>=0.47.0 |

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED
- Placeholders: 0 remaining
- Technical Approach: DOCUMENTED (Rich markup enhancement)
- Entry Points: 5 traced, 5 covered
- Test Infrastructure: RESEARCHED (pytest, 17 existing tests)
- Implementation Ready: YES
```

---

*Research completed 2026-02-05 by Builder-1 Agent*
