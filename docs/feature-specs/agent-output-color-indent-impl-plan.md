# Agent Output Color Indent - Implementation Plan

**Feature Spec**: `agent-output-color-indent.md`  
**Owner**: @builder-1  
**Status**: Ready for Implementation  
**Created**: 2025-02-05

---

## 1. Research Summary

### Rich Library Capabilities ✓

**Q-001 Resolved**: Rich library **does** support efficient per-line prefix styling.

Three viable approaches tested:

| Approach | Method | Performance | Recommended |
|----------|--------|-------------|-------------|
| A | String manipulation with Rich markup | Excellent | ✓ Yes |
| B | `rich.text.Text` object with styled appends | Excellent | Alternative |
| C | Custom `rich.box.Box` for Panel | Good | Not needed |

**Chosen approach**: String manipulation (Approach A) - simplest, works with streaming:
```python
def prefix_output(content: str, color: str) -> str:
    prefix = f"[{color}]│[/{color}] "
    lines = content.split('\n')
    return '\n'.join(prefix + line for line in lines)
```

---

## 2. Current Architecture Analysis

### Output Flow

```
User Command → App._handle_agent_command()
                    ↓
             OutputPane methods:
               - write_streaming_start()
               - write_streaming_chunk()
               - finish_streaming()
               - write_task_complete()
               - write_task_error()
                    ↓
             RichLog.write() → Terminal
```

### Key Files

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `src/teambot/visualization/console.py` | Color/icon mappings, `get_agent_style()` | Update color mapping |
| `src/teambot/ui/widgets/output_pane.py` | Output rendering methods | Add indent prefix logic |
| `src/teambot/tasks/formatting.py` | Agent header formatting | No changes needed |

### Color Mapping Discrepancy

**Spec defines**:
- builder-1 = green
- builder-2 = yellow
- writer = magenta
- reviewer = red

**Current code** (`console.py`):
- builder (shared) = yellow
- technical_writer = green
- reviewer = magenta

**Decision**: Update code to match spec (spec takes precedence). This requires:
1. Separate colors for builder-1 vs builder-2
2. Swap writer ↔ builder-1 colors
3. Change reviewer from magenta → red

---

## 3. Implementation Tasks

### Phase 1: Core Infrastructure

- [ ] **Task 1.1**: Update `PERSONA_COLORS` mapping in `console.py`
  - Add `builder_primary` and `builder_secondary` personas (or use direct agent ID mapping)
  - Change writer to magenta, reviewer to red
  - Estimated: 15 min

- [ ] **Task 1.2**: Create `get_agent_color()` helper (simpler than `get_agent_style()`)
  - Direct agent_id → color mapping for indent use
  - Falls back to white for unknown agents
  - Estimated: 10 min

- [ ] **Task 1.3**: Create `format_indented_line()` utility
  - Location: `src/teambot/tasks/formatting.py` or new `src/teambot/ui/utils/indent.py`
  - Handles single line with colored prefix
  - Unicode indent char (│) with ASCII fallback (|)
  - Estimated: 15 min

- [ ] **Task 1.4**: Create `format_indented_content()` utility
  - Multi-line content wrapper
  - Preserves empty lines
  - Estimated: 10 min

### Phase 2: OutputPane Integration

- [ ] **Task 2.1**: Update `write_task_complete()` to apply indent
  - Add indent to result content
  - Estimated: 10 min

- [ ] **Task 2.2**: Update `write_task_error()` to apply indent
  - Add indent to error content
  - Estimated: 10 min

- [ ] **Task 2.3**: Update `finish_streaming()` to apply indent
  - Add indent to accumulated content
  - Estimated: 10 min

- [ ] **Task 2.4**: Update `write_streaming_chunk()` for real-time indent
  - Apply indent as chunks arrive (per-line basis)
  - Handle partial lines at chunk boundaries
  - Estimated: 30 min (most complex)

- [ ] **Task 2.5**: Update `write_info()` / `write_system()` (optional)
  - Decide: Should system output have indent? (Spec says Q-002: Yes)
  - Estimated: 10 min

### Phase 3: Testing

- [ ] **Task 3.1**: Unit tests for indent formatting utilities
  - Test single line, multi-line, empty lines
  - Test color application
  - Test Unicode/ASCII fallback
  - Estimated: 20 min

- [ ] **Task 3.2**: Unit tests for OutputPane updates
  - Test that output includes indent prefix
  - Test all 6 agents get correct colors
  - Estimated: 30 min

- [ ] **Task 3.3**: Integration test (manual)
  - Run `uv run teambot` and verify visual output
  - Test with streaming output
  - Test multi-agent output interleaving
  - Estimated: 15 min

### Phase 4: Documentation & Polish

- [ ] **Task 4.1**: Update feature spec with implementation status
  - Mark Q-001 resolved
  - Update Research section
  - Estimated: 10 min

- [ ] **Task 4.2**: Add ASCII fallback detection
  - Check terminal Unicode support
  - Environment variable override: `TEAMBOT_ASCII_INDENT=1`
  - Estimated: 15 min

---

## 4. Detailed Design

### Color Mapping (Updated)

```python
# New mapping - direct agent ID to color
AGENT_COLORS = {
    "pm": "blue",
    "ba": "cyan", 
    "writer": "magenta",
    "builder-1": "green",
    "builder-2": "yellow",
    "reviewer": "red",
}

def get_agent_color(agent_id: str) -> str:
    """Get color for agent's indent bar."""
    return AGENT_COLORS.get(agent_id, "white")
```

### Indent Formatting

```python
INDENT_CHAR = "│"  # U+2502 Box Drawings Light Vertical
INDENT_CHAR_ASCII = "|"

def format_indented_content(content: str, agent_id: str, use_ascii: bool = False) -> str:
    """Apply colored indent prefix to each line of content.
    
    Args:
        content: Multi-line text content.
        agent_id: Agent identifier for color lookup.
        use_ascii: Use ASCII pipe instead of Unicode box drawing.
        
    Returns:
        Content with colored indent prefix on each line.
    """
    color = get_agent_color(agent_id)
    char = INDENT_CHAR_ASCII if use_ascii else INDENT_CHAR
    prefix = f"[{color}]{char}[/{color}] "
    
    lines = content.split('\n')
    return '\n'.join(prefix + line for line in lines)
```

### Streaming Chunk Handling

For streaming, chunks may arrive mid-line. Strategy:

```python
class OutputPane(RichLog):
    def __init__(self, ...):
        ...
        # Track incomplete line per agent
        self._streaming_line_buffers: dict[str, str] = {}
    
    def write_streaming_chunk(self, agent_id: str, chunk: str) -> None:
        """Handle streaming chunk with indent support."""
        # Get or create line buffer
        buffer = self._streaming_line_buffers.get(agent_id, "")
        buffer += chunk
        
        # Split into complete lines and remainder
        if '\n' in buffer:
            lines = buffer.split('\n')
            complete_lines = lines[:-1]  # All except last
            remainder = lines[-1]        # May be partial
            
            # Write complete lines with indent
            for line in complete_lines:
                indented = format_indented_line(line, agent_id)
                self.write(indented)
            
            # Store remainder for next chunk
            self._streaming_line_buffers[agent_id] = remainder
        else:
            # No newline yet, just buffer
            self._streaming_line_buffers[agent_id] = buffer
```

---

## 5. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Run full test suite after each phase |
| Color changes confuse users | Document in changelog; colors match spec |
| Streaming performance | Pre-compute prefix string; reuse per agent |
| Unicode rendering issues | Detect and fallback to ASCII |

---

## 6. Acceptance Criteria

- [ ] All 6 agents display colored indent line matching their header color
- [ ] Indent appears on all output lines (not just headers)
- [ ] Streaming output shows indent in real-time
- [ ] Code blocks and multi-line content render correctly with indent
- [ ] Existing tests pass (with updates for color changes)
- [ ] New tests cover indent formatting logic

---

## 7. Estimated Effort

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | Infrastructure | ~50 min |
| Phase 2 | OutputPane | ~70 min |
| Phase 3 | Testing | ~65 min |
| Phase 4 | Polish | ~25 min |
| **Total** | | **~3.5 hours** |

---

## 8. Open Questions Resolved

| ID | Question | Resolution |
|----|----------|------------|
| Q-001 | Does Rich support per-line prefix styling? | **Yes** - tested, works efficiently |
| Q-002 | Should indent apply to error/warning output? | **Yes** - same agent, same indent |
| Q-003 | How to handle code blocks with existing indentation? | **Add to existing** - indent is additional prefix |
