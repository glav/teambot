<!-- markdownlint-disable-file -->
# Implementation Details: Output Pane Enhancement

**Date**: 2026-02-05  
**Feature**: Output Pane Enhancement for Multi-Agent Identification  
**Plan Reference**: `.agent-tracking/plans/20260205-output-pane-enhancement-plan.instructions.md`  
**Research Reference**: `.agent-tracking/research/20260205-output-pane-enhancement-research.md` (Lines 1-571)

---

## Phase 1: Foundation (TDD Approach)

### T-001: Add AGENT_PERSONAS Constant

**File**: `src/teambot/visualization/console.py`  
**Location**: After `PERSONA_COLORS` (Lines 24-31)  
**Research Reference**: Lines 206-217

**Implementation**:

Add the following constant after `PERSONA_COLORS`:

```python
# Agent ID to persona mapping (Lines 24-31 for PERSONA_COLORS reference)
AGENT_PERSONAS = {
    "pm": "project_manager",
    "ba": "business_analyst",
    "writer": "technical_writer",
    "builder-1": "builder",
    "builder-2": "builder",
    "reviewer": "reviewer",
}
```

**Success Criteria**:
- All 6 agent IDs mapped
- Mappings align with existing PERSONA_COLORS keys
- builder-1 and builder-2 share same persona

---

### T-002: Add AGENT_ICONS Constant

**File**: `src/teambot/visualization/console.py`  
**Location**: After `AGENT_PERSONAS`  
**Research Reference**: Lines 219-237

**Implementation**:

```python
# Agent-specific icons for visual identification
AGENT_ICONS = {
    "pm": "📋",
    "ba": "📊",
    "writer": "📝",
    "builder-1": "🔨",
    "builder-2": "🔨",
    "reviewer": "🔍",
}
```

**Success Criteria**:
- All 6 agent IDs have icons
- Icons are visually distinct
- builder-1 and builder-2 share same icon

---

### T-003: Create get_agent_style() Helper Function

**File**: `src/teambot/visualization/console.py`  
**Location**: After constants  
**Research Reference**: Lines 243-255

**Implementation**:

```python
def get_agent_style(agent_id: str) -> tuple[str, str]:
    """Get color and icon for an agent.
    
    Args:
        agent_id: The agent identifier (e.g., 'pm', 'builder-1').
        
    Returns:
        Tuple of (color, icon) for the agent.
        
    Example:
        >>> color, icon = get_agent_style("pm")
        >>> color
        'blue'
        >>> icon
        '📋'
    """
    persona = AGENT_PERSONAS.get(agent_id, "builder")
    color = PERSONA_COLORS.get(persona, "white")
    icon = AGENT_ICONS.get(agent_id, "●")
    return color, icon
```

**Success Criteria**:
- Returns (color, icon) tuple
- Falls back to ("white", "●") for unknown agents
- Uses existing PERSONA_COLORS for color lookup

---

### T-004: Add Unit Tests for Constants and Helper

**File**: `tests/test_visualization/test_console.py`  
**Research Reference**: Lines 449-455 (test pattern)  
**Test Strategy Reference**: Lines 84-134

**Tests to Add**:

```python
class TestAgentStyling:
    """Tests for agent styling constants and helper."""

    def test_all_agents_have_personas(self):
        """All 6 agent IDs have persona mappings."""
        from teambot.visualization.console import AGENT_PERSONAS
        
        expected_agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
        for agent_id in expected_agents:
            assert agent_id in AGENT_PERSONAS

    def test_all_agents_have_icons(self):
        """All 6 agent IDs have icon mappings."""
        from teambot.visualization.console import AGENT_ICONS
        
        expected_agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
        for agent_id in expected_agents:
            assert agent_id in AGENT_ICONS

    def test_get_agent_style_pm_returns_blue_and_clipboard(self):
        """get_agent_style returns blue color and clipboard icon for PM."""
        from teambot.visualization.console import get_agent_style
        
        color, icon = get_agent_style("pm")
        assert color == "blue"
        assert icon == "📋"

    def test_get_agent_style_all_agents(self):
        """All agents return correct color and icon."""
        from teambot.visualization.console import get_agent_style
        
        expected = {
            "pm": ("blue", "📋"),
            "ba": ("cyan", "📊"),
            "writer": ("green", "📝"),
            "builder-1": ("yellow", "🔨"),
            "builder-2": ("yellow", "🔨"),
            "reviewer": ("magenta", "🔍"),
        }
        for agent_id, (expected_color, expected_icon) in expected.items():
            color, icon = get_agent_style(agent_id)
            assert color == expected_color, f"{agent_id} color mismatch"
            assert icon == expected_icon, f"{agent_id} icon mismatch"

    def test_get_agent_style_unknown_agent_returns_default(self):
        """Unknown agent returns default styling."""
        from teambot.visualization.console import get_agent_style
        
        color, icon = get_agent_style("unknown-agent")
        assert color == "white"
        assert icon == "●"
```

**Success Criteria**:
- All tests pass
- Coverage for constants: 100%
- Coverage for helper: 100%

---

## Phase 2: Word Wrap (Code-First Approach)

### T-005: Enable wrap=True in OutputPane __init__

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Location**: `__init__` method  
**Research Reference**: Lines 260-270

**Current Code** (approximate):
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._streaming_buffers: dict[str, list[str]] = {}
    self._streaming_starts: dict[str, str] = {}
```

**Modified Code**:
```python
def __init__(self, *args, **kwargs):
    # Enable word wrap to prevent horizontal scrolling
    kwargs.setdefault('wrap', True)
    super().__init__(*args, **kwargs)
    self._streaming_buffers: dict[str, list[str]] = {}
    self._streaming_starts: dict[str, str] = {}
```

**Success Criteria**:
- `wrap=True` is set by default
- Can be overridden with explicit `wrap=False`
- Existing tests still pass

---

### T-006: Add Wrap Test

**File**: `tests/test_ui/test_output_pane.py`  
**Test Strategy Reference**: Lines 136-153

**Test to Add**:

```python
def test_outputpane_wrap_enabled_by_default(self):
    """OutputPane has wrap enabled by default."""
    from teambot.ui.widgets.output_pane import OutputPane
    
    pane = OutputPane()
    # RichLog stores wrap setting internally
    assert pane.wrap is True
```

**Success Criteria**:
- Test passes
- Verifies wrap configuration

---

## Phase 3: Handoff Logic (TDD Approach)

### T-007: Add _last_agent_id State Variable

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Location**: `__init__` method  
**Research Reference**: Lines 269, 277-278

**Modified Code**:
```python
def __init__(self, *args, **kwargs):
    kwargs.setdefault('wrap', True)
    super().__init__(*args, **kwargs)
    self._streaming_buffers: dict[str, list[str]] = {}
    self._streaming_starts: dict[str, str] = {}
    self._last_agent_id: str | None = None  # For handoff detection
```

**Success Criteria**:
- State variable initialized to None
- Type hint included

---

### T-008: Implement _check_handoff() Method

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 279-286

**Implementation**:

```python
def _check_handoff(self, agent_id: str) -> bool:
    """Check if this is a handoff from another agent.
    
    Args:
        agent_id: The current agent identifier.
        
    Returns:
        True if previous agent was different (and not None).
    """
    if self._last_agent_id and self._last_agent_id != agent_id:
        return True
    return False
```

**Success Criteria**:
- Returns False for first message (None → agent)
- Returns False for same agent continues
- Returns True for different agent

---

### T-009: Implement _write_handoff_separator() Method

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 288-294

**Implementation**:

```python
def _write_handoff_separator(self, from_agent: str, to_agent: str) -> None:
    """Write a visual separator for agent handoff.
    
    Args:
        from_agent: The agent that was previously active.
        to_agent: The agent that is now active.
    """
    from teambot.visualization.console import get_agent_style
    
    to_color, to_icon = get_agent_style(to_agent)
    separator = f"[dim]{'─' * 40}[/dim]"
    label = f"[{to_color}]→ {to_icon} @{to_agent}[/{to_color}]"
    self.write(f"{separator} {label}")
```

**Success Criteria**:
- Separator contains horizontal line
- Shows new agent icon and ID
- Uses new agent's color

---

### T-010: Add Handoff Detection Tests

**File**: `tests/test_ui/test_output_pane.py`  
**Test Strategy Reference**: Lines 159-200

**Tests to Add**:

```python
class TestHandoffDetection:
    """Tests for agent handoff separator functionality."""

    def test_check_handoff_returns_false_for_first_message(self):
        """First message has no previous agent, so no handoff."""
        from teambot.ui.widgets.output_pane import OutputPane
        
        pane = OutputPane()
        pane._last_agent_id = None
        
        result = pane._check_handoff("pm")
        
        assert result is False

    def test_check_handoff_returns_false_for_same_agent(self):
        """Same agent continuing does not trigger handoff."""
        from teambot.ui.widgets.output_pane import OutputPane
        
        pane = OutputPane()
        pane._last_agent_id = "pm"
        
        result = pane._check_handoff("pm")
        
        assert result is False

    def test_check_handoff_returns_true_for_different_agent(self):
        """Different agent triggers handoff."""
        from teambot.ui.widgets.output_pane import OutputPane
        
        pane = OutputPane()
        pane._last_agent_id = "pm"
        
        result = pane._check_handoff("builder-1")
        
        assert result is True

    def test_handoff_separator_contains_divider_line(self):
        """Handoff separator contains horizontal divider."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            pane._write_handoff_separator("pm", "builder-1")
            
            call_arg = mock_write.call_args[0][0]
            assert "─" in call_arg

    def test_handoff_separator_shows_new_agent(self):
        """Handoff separator shows new agent icon and ID."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            pane._write_handoff_separator("pm", "builder-1")
            
            call_arg = mock_write.call_args[0][0]
            assert "@builder-1" in call_arg
            assert "🔨" in call_arg
```

**Success Criteria**:
- All handoff tests pass
- 100% coverage for _check_handoff
- 90% coverage for _write_handoff_separator

---

## Phase 4: Write Method Enhancement (Code-First Approach)

### T-011: Enhance write_task_complete() with Persona Styling

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 343-368

**Current Code** (approximate):
```python
def write_task_complete(self, agent_id: str, result: str) -> None:
    """Write task completion message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    self.write(f"[dim]{timestamp}[/dim] [green]✓[/green] @{agent_id}: {result}")
    self.scroll_end()
```

**Modified Code**:
```python
def write_task_complete(self, agent_id: str, result: str) -> None:
    """Write task completion message with persona styling."""
    from teambot.visualization.console import get_agent_style
    
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

**Success Criteria**:
- Output includes persona color for agent ID
- Output includes persona icon
- Handoff separator appears on agent change
- Existing tests still pass

---

### T-012: Enhance write_task_error() with Persona Styling

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 343-368 (same pattern)

**Modified Code**:
```python
def write_task_error(self, agent_id: str, error: str) -> None:
    """Write task error message with persona styling."""
    from teambot.visualization.console import get_agent_style
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    color, icon = get_agent_style(agent_id)
    
    # Check for handoff
    if self._check_handoff(agent_id):
        self._write_handoff_separator(self._last_agent_id, agent_id)
    self._last_agent_id = agent_id
    
    # Format with persona color
    self.write(
        f"[dim]{timestamp}[/dim] [red]✗[/red] "
        f"[{color}]{icon} @{agent_id}[/{color}]: {error}"
    )
    self.scroll_end()
```

**Success Criteria**:
- Error indicator (✗) still present
- Output includes persona color
- Output includes persona icon

---

### T-013: Enhance write_streaming_start() with Persona Styling

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 343-368 (same pattern)

**Modified Code**:
```python
def write_streaming_start(self, agent_id: str) -> None:
    """Write streaming start message with persona styling."""
    from teambot.visualization.console import get_agent_style
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    color, icon = get_agent_style(agent_id)
    
    # Check for handoff
    if self._check_handoff(agent_id):
        self._write_handoff_separator(self._last_agent_id, agent_id)
    self._last_agent_id = agent_id
    
    self._streaming_buffers[agent_id] = []
    self._streaming_starts[agent_id] = timestamp
    
    self.write(
        f"[dim]{timestamp}[/dim] [{color}]⟳ {icon} @{agent_id}[/{color}]: "
        f"[dim]streaming...[/dim]"
    )
    self.scroll_end()
```

**Success Criteria**:
- Streaming indicator uses persona color
- Agent ID uses persona color
- Icon appears before agent ID

---

### T-014: Enhance finish_streaming() with Persona Styling

**File**: `src/teambot/ui/widgets/output_pane.py`  
**Research Reference**: Lines 374-399

**Modified Code**:
```python
def finish_streaming(self, agent_id: str, success: bool = True) -> None:
    """Mark streaming complete with persona styling."""
    from teambot.visualization.console import get_agent_style
    
    if agent_id not in self._streaming_buffers:
        return

    content = "".join(self._streaming_buffers[agent_id])
    timestamp = self._streaming_starts.get(agent_id, datetime.now().strftime("%H:%M:%S"))

    del self._streaming_buffers[agent_id]
    if agent_id in self._streaming_starts:
        del self._streaming_starts[agent_id]

    color, icon = get_agent_style(agent_id)
    
    # Check for handoff (streaming may have interleaved)
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

**Success Criteria**:
- Final output uses persona color
- Icon appears in final output
- Both success and error cases styled

---

### T-015: Add Tests for Enhanced Methods

**File**: `tests/test_ui/test_output_pane.py`  
**Test Strategy Reference**: Lines 205-298

**Tests to Add**:

```python
class TestAgentStyledOutput:
    """Tests for persona-styled output methods."""

    def test_write_task_complete_uses_persona_color(self):
        """write_task_complete applies persona color to agent ID."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("pm", "Plan created")
                
                # Find the main output call (not handoff separator)
                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "Plan created" in c][0]
                assert "[blue]" in main_call
                assert "📋" in main_call

    def test_write_task_complete_includes_icon(self):
        """write_task_complete includes agent icon."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("builder-1", "Code complete")
                
                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "Code complete" in c][0]
                assert "🔨" in main_call

    def test_write_task_complete_triggers_handoff_separator(self):
        """write_task_complete shows separator on agent change."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        pane._last_agent_id = "pm"
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("builder-1", "Code complete")
                
                # Should have 2 write calls: separator + message
                assert mock_write.call_count == 2
                separator_call = mock_write.call_args_list[0][0][0]
                assert "─" in separator_call

    def test_write_task_error_uses_persona_color(self):
        """write_task_error applies persona color to agent ID."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_error("reviewer", "Review failed")
                
                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "Review failed" in c][0]
                assert "[magenta]" in main_call
                assert "🔍" in main_call

    def test_streaming_start_uses_persona_color(self):
        """write_streaming_start applies persona color."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("ba")
                
                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "streaming" in c][0]
                assert "[cyan]" in main_call
                assert "📊" in main_call

    def test_finish_streaming_uses_persona_color(self):
        """finish_streaming applies persona color."""
        from teambot.ui.widgets.output_pane import OutputPane
        from unittest.mock import patch
        
        pane = OutputPane()
        pane._streaming_buffers["writer"] = ["Documentation complete"]
        pane._streaming_starts["writer"] = "12:00:00"
        
        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.finish_streaming("writer", success=True)
                
                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "Documentation" in c][0]
                assert "[green]" in main_call  # Writer color
                assert "📝" in main_call
```

**Success Criteria**:
- All styling tests pass
- 90% coverage for enhanced methods
- No regression in existing tests

---

## Phase 5: Validation

### T-016: Run Full Test Suite with Coverage

**Command**:
```bash
uv run pytest --cov=src/teambot --cov-report=term-missing
```

**Expected Output**:
- All tests pass
- Coverage ≥85% overall
- No uncovered lines in modified files

**Success Criteria**:
- 0 failures
- Coverage target met
- No regressions

---

### T-017: Manual Visual Verification

**Verification Steps**:

1. Start teambot: `uv run teambot run`
2. Test single agent: `@pm create a simple plan`
   - ✅ Verify blue color and 📋 icon
3. Test agent switch: `@builder-1 implement it`
   - ✅ Verify handoff separator appears
   - ✅ Verify yellow color and 🔨 icon
4. Test multi-agent: `@pm,@ba analyze this`
   - ✅ Verify distinct colors for each agent
5. Test word wrap: Enter long message
   - ✅ Verify no horizontal scrolling
6. Test error case: Force an error
   - ✅ Verify error styling with icon

**Success Criteria**:
- All visual elements render correctly
- Colors match spec
- Icons display properly
- Word wrap prevents horizontal scroll
- Handoff separator visible on agent change

---

## References

| Ref | Type | Location | Description |
|-----|------|----------|-------------|
| R-001 | Research | Lines 56-98 | Current OutputPane analysis |
| R-002 | Research | Lines 206-237 | Agent ID mapping design |
| R-003 | Research | Lines 260-270 | Word wrap implementation |
| R-004 | Research | Lines 275-294 | Handoff detection design |
| R-005 | Research | Lines 343-399 | Enhanced method patterns |
| T-001 | Test Strategy | Lines 84-134 | TDD for constants and helper |
| T-002 | Test Strategy | Lines 136-153 | Code-First for wrap |
| T-003 | Test Strategy | Lines 159-200 | TDD for handoff logic |
| T-004 | Test Strategy | Lines 205-298 | Code-First for write methods |
