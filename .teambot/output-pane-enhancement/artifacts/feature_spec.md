<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Output Pane Enhancement - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Active

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-05 |
| Problem & Users | ✅ | None | 2026-02-05 |
| Scope | ✅ | None | 2026-02-05 |
| Requirements | ✅ | None | 2026-02-05 |
| Metrics & Risks | ✅ | None | 2026-02-05 |
| Operationalization | ✅ | None | 2026-02-05 |
| Finalization | ✅ | None | 2026-02-05 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot orchestrates 6 specialized AI agent personas working concurrently on software development tasks. The information/agent message output pane (right panel) displays real-time output from all agents, but currently lacks sufficient visual differentiation to help users track which agent produced which output.

### Core Opportunity
Enhance the output pane visual design to provide clear agent attribution, eliminate horizontal scrolling, and improve the multi-agent workflow experience without degrading terminal compatibility.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Users can instantly identify which agent produced each output block | UX | Manual scanning required | <1 second visual recognition | v0.2.0 | P0 |
| G-002 | All output is readable without horizontal scrolling | UX | Horizontal scrollbar appears | No horizontal scrollbar | v0.2.0 | P0 |
| G-003 | Agent handoffs are visually apparent | UX | No indication | Clear visual separator | v0.2.0 | P1 |
| G-004 | Terminal experience quality is maintained | Compatibility | Functional | No degradation | v0.2.0 | P0 |

---

## 2. Problem Definition

### Current Situation
The OutputPane class (extending Textual's RichLog widget) displays agent messages with:
- Timestamps in dim gray
- Status icons (✓, ✗, ⟳, ℹ)
- Small `@agent_id` prefix
- No persona-specific colors (defined in `console.py` but unused in OutputPane)
- Basic automatic word-wrap from RichLog defaults

### Problem Statement
When multiple agents produce output simultaneously, users struggle to:
1. Quickly identify which agent produced specific output
2. Read long lines without horizontal scrolling
3. Recognize when processing transitions between agents

### Root Causes
* Agent persona colors (`PERSONA_COLORS` dict) are defined but not integrated into OutputPane
* No visual boundary or separator exists between different agents' output blocks
* Text wrapping relies on RichLog defaults without explicit configuration
* Agent identification relies solely on small `@agent_id` text prefix

### Impact of Inaction
Users experience cognitive overload during multi-agent workflows, reducing productivity and increasing time to debug issues. New users may find the tool overwhelming and abandon adoption.

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer User | Track agent progress, identify errors quickly | Cannot distinguish agents at-a-glance | High - primary user |
| Debugging User | Find specific agent output during troubleshooting | Scrolling through mixed output wastes time | High - critical workflow |
| New User | Understand multi-agent collaboration | Visual chaos creates cognitive overload | Medium - adoption risk |

---

## 4. Scope

### In Scope
* Agent-specific color coding for output messages
* Unique icons per agent persona
* Text wrapping configuration to eliminate horizontal scrolling
* Visual separator/divider when active agent changes
* Integration with existing `PERSONA_COLORS` definitions
* OutputPane class modifications

### Out of Scope
* Status panel (left panel) redesign
* New agent personas or workflow changes
* Real-time progressive streaming display (chunks still accumulate)
* External logging or file output formatting
* Performance optimization beyond visual changes
* Accessibility features beyond color+icon redundancy

### Assumptions
* Rich and Textual libraries support required styling capabilities
* Terminal supports 256-color or truecolor (fallback to icons provided)
* Six distinct visual identities are sufficient (one per persona)
* Users have terminals with 80+ column width

### Constraints
* Must work in standard terminal environments
* Backward compatibility with existing output formatting
* No perceptible performance lag
* Colors must not be sole differentiator (icons required for accessibility)

---

## 5. Product Overview

### Value Proposition
Clear visual organization of multi-agent output that allows users to instantly identify agent attribution, read complete messages without scrolling, and recognize workflow transitions—improving productivity and reducing cognitive load.

### Differentiators
* Persona-aware color coding integrated with existing color definitions
* Dual-channel identification (color + icon) for accessibility
* Smart handoff indicators that appear only on agent transitions

### UX / UI Considerations
| Element | Current | Enhanced |
|---------|---------|----------|
| Agent ID | `@pm` text only | Colored `@pm` + persona icon |
| Output block | No visual boundary | Color-coded left border or background tint |
| Handoff | No indicator | Horizontal divider with agent transition label |
| Long lines | Horizontal scroll | Word-wrapped within viewport |

UX Status: Design Complete

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Agent Color Coding | Each agent's output uses persona-specific foreground color for the agent ID and message prefix | G-001 | All | P0 | `@pm` displays in blue, `@ba` in cyan, `@writer` in green, `@builder-1` and `@builder-2` in yellow, `@reviewer` in magenta | Integrate existing `PERSONA_COLORS` |
| FR-002 | Agent Persona Icons | Each agent has a unique icon displayed before the agent ID | G-001 | All | P0 | PM: 📋, BA: 📊, Writer: 📝, Builder: 🔨, Reviewer: 🔍 displayed consistently | Icons provide non-color identification |
| FR-003 | Text Word Wrap | Long output lines wrap at viewport width without horizontal scrolling | G-002 | All | P0 | No horizontal scrollbar appears for any output; text wraps at word boundaries | Preserve code block formatting |
| FR-004 | Agent Handoff Indicator | Visual separator appears when the outputting agent changes | G-003 | All | P1 | Horizontal line with "→ @{new_agent}" label appears between last message from previous agent and first message from new agent | Only on agent transitions |
| FR-005 | Colored Output Block Border | Optional left-side colored border or subtle background tint per agent | G-001 | All | P2 | Each agent's output block has a 1-char colored left border matching persona color | May require Rich Panel usage |
| FR-006 | Agent ID Color in All Message Types | Apply persona color to agent ID across all message types (success, error, streaming, info) | G-001 | All | P0 | `write_task_complete`, `write_task_error`, `write_streaming_start`, `finish_streaming` all use persona-colored agent ID | Consistent visual language |
| FR-007 | Streaming Indicator Colored | Streaming indicator (⟳) inherits agent's persona color | G-001 | All | P1 | When agent is streaming, the ⟳ icon and @agent_id use persona color | Visual consistency |
| FR-008 | Preserve Code Block Formatting | Code blocks and pre-formatted content maintain fixed-width formatting | G-002, G-004 | Debugging User | P0 | Markdown code blocks (```) display with preserved spacing; no word-wrap inside code blocks | Detect code block markers |

### Feature Hierarchy
```
Output Pane Enhancement
├── Agent Visual Identity
│   ├── FR-001: Agent Color Coding
│   ├── FR-002: Agent Persona Icons
│   ├── FR-005: Colored Output Block Border
│   ├── FR-006: Agent ID Color in All Message Types
│   └── FR-007: Streaming Indicator Colored
├── Readability
│   ├── FR-003: Text Word Wrap
│   └── FR-008: Preserve Code Block Formatting
└── Workflow Clarity
    └── FR-004: Agent Handoff Indicator
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Output rendering must not introduce perceptible lag | <50ms per message write | P0 | Benchmark timing in test | Current baseline ~10ms |
| NFR-002 | Compatibility | Must work in standard terminal emulators | Support xterm-256color, truecolor, basic 16-color fallback | P0 | Test in iTerm2, Terminal.app, Windows Terminal, VS Code terminal | Icon fallback for no-color terminals |
| NFR-003 | Accessibility | Color must not be sole differentiator | Each agent has unique icon + color | P0 | Visual inspection | FR-002 addresses this |
| NFR-004 | Maintainability | Color definitions centralized | Single source of truth for persona colors | P1 | Code review | Use existing `PERSONA_COLORS` dict |
| NFR-005 | Reliability | No output data loss | 100% of agent output displayed | P0 | Integration test | Streaming completion verified |
| NFR-006 | Usability | Wrap behavior predictable | Word-wrap only; no mid-word breaks except URLs/paths | P1 | Manual test with long content | Rich/Textual default behavior |

---

## 8. Data & Analytics

### Inputs
* Agent output messages (text content, agent_id, message type)
* Terminal viewport width (columns)
* Previous message's agent_id (for handoff detection)

### Outputs / Events
* Formatted Rich markup strings written to RichLog
* Handoff separator lines when agent changes

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| agent_output_written | After each write method | agent_id, message_type, char_count | Debug output issues | Builder |
| handoff_displayed | When handoff separator shown | from_agent, to_agent | Validate handoff detection | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Horizontal scroll occurrences | UX | Unknown (>0) | 0 | Per session | User observation |
| Agent identification time | UX | >3 seconds (estimated) | <1 second | User study | Manual testing |
| Output rendering latency | Performance | ~10ms | <50ms | Per message | Benchmark |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Rich library | External | High | Open source | Low - stable | Pin version in pyproject.toml |
| Textual framework | External | High | Open source | Low - stable | Pin version; test with updates |
| PERSONA_COLORS dict | Internal | Medium | TeamBot | Low | Already exists in console.py |
| OutputPane class | Internal | High | TeamBot | Low | Primary modification target |
| RichLog widget | External | High | Textual | Medium | Limited API; may need workaround for borders |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | User terminal theme conflicts with persona colors | Medium | Medium | Test with popular themes; choose high-contrast colors; icons as fallback | Builder | Open |
| R-002 | Text wrapping breaks code blocks or formatted output | High | Medium | Detect code block markers; preserve pre-formatted content | Builder | Open |
| R-003 | Colored borders not supported by RichLog | Medium | Medium | Fall back to color-coded agent ID without border; investigate Rich Panel | Builder | Open |
| R-004 | Performance degradation with many rapid messages | Medium | Low | Benchmark before/after; optimize if needed | Builder | Open |
| R-005 | Icons not rendering in some terminals | Low | Low | Use ASCII fallback icons (e.g., [PM], [BA]) | Builder | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
Public - No sensitive data involved; output pane displays user-initiated agent output.

### PII Handling
N/A - This feature does not introduce new data collection or PII handling.

### Threat Considerations
N/A - Visual formatting changes only; no new attack surface.

### Regulatory / Compliance
N/A - No regulatory requirements applicable.

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard pip install | No new dependencies |
| Rollback | Git revert | Code changes only |
| Monitoring | N/A | Client-side UI only |
| Alerting | N/A | No server components |
| Support | Documentation update | Update README with new visual features |
| Capacity Planning | N/A | No resource impact |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Implementation | TBD | All FR P0/P1 complete | Builder |
| Testing | TBD | All tests pass; manual visual QA | Reviewer |
| Documentation | TBD | README updated | Writer |
| Release | TBD | v0.2.0 tag created | PM |

### Feature Flags
N/A - No feature flags; visual enhancement applies globally.

---

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | - | - | - | No open questions |

---

## 15. Acceptance Test Scenarios

### AT-001: Multi-Agent Output Identification
**Description**: User runs a workflow where multiple agents produce output; user can identify each agent's output at-a-glance.
**Preconditions**: TeamBot running with enhanced output pane; at least 2 agents active.
**Steps**:
1. User initiates workflow causing PM and Builder agents to produce output
2. PM outputs "Creating project plan..."
3. Builder outputs "Implementing feature X..."
4. User observes the output pane
**Expected Result**: PM output appears in blue with 📋 icon; Builder output appears in yellow with 🔨 icon; each clearly distinguishable without reading text.
**Verification**: Visual inspection confirms distinct colors and icons per agent.

### AT-002: Long Line Word Wrap
**Description**: User observes long output line wrapping correctly without horizontal scroll.
**Preconditions**: TeamBot running; terminal width set to 80 columns.
**Steps**:
1. Agent produces output line exceeding 120 characters
2. User observes the output pane
3. User attempts to scroll horizontally
**Expected Result**: Long line wraps at word boundary within 80-column viewport; no horizontal scrollbar appears; text remains fully readable.
**Verification**: No horizontal scrollbar visible; all text readable within viewport.

### AT-003: Agent Handoff Indicator
**Description**: When output switches from one agent to another, a visual separator appears.
**Preconditions**: TeamBot running; at least 2 agents producing sequential output.
**Steps**:
1. PM agent outputs "Plan complete"
2. Builder agent outputs "Starting implementation"
3. User observes the transition area
**Expected Result**: Horizontal divider with "→ @builder-1" label appears between PM's last message and Builder's first message.
**Verification**: Visual separator clearly visible; label identifies the new agent.

### AT-004: Code Block Formatting Preserved
**Description**: Code blocks within agent output maintain fixed-width formatting without wrapping.
**Preconditions**: TeamBot running; agent producing code block output.
**Steps**:
1. Agent outputs markdown code block with 4-space indentation:
   ```
   def example():
       return True
   ```
2. User observes code block in output pane
**Expected Result**: Code block maintains fixed-width formatting; indentation preserved; no word-wrap inside code block.
**Verification**: Indentation matches original; code block visually distinct.

### AT-005: Color Consistency Across Message Types
**Description**: Agent's persona color applies to success, error, and streaming messages consistently.
**Preconditions**: TeamBot running; single agent producing different message types.
**Steps**:
1. PM agent starts streaming (⟳ indicator)
2. PM agent completes successfully (✓ indicator)
3. PM agent encounters error (✗ indicator)
4. User observes all three message types
**Expected Result**: All three messages show PM's blue color for @pm identifier; icons visible in appropriate status colors (yellow/green/red) but agent ID consistently blue.
**Verification**: Agent ID color consistent across all message types.

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-05 | BA Agent | Initial specification created | Creation |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Internal | problem_statement.md | Business problem definition | Primary source |
| REF-002 | Code | src/teambot/visualization/console.py | PERSONA_COLORS definition | Use existing colors |
| REF-003 | Code | src/teambot/ui/widgets/output_pane.py | Current OutputPane implementation | Modification target |
| REF-004 | External | Rich library docs | Markup and styling reference | Implementation guidance |
| REF-005 | External | Textual docs | RichLog widget API | Implementation guidance |

---

## 18. Technical Implementation Notes

### Agent Color Mapping (from existing PERSONA_COLORS)
| Agent ID | Persona Key | Color | Icon |
|----------|-------------|-------|------|
| pm | project_manager | blue | 📋 |
| ba | business_analyst | cyan | 📊 |
| writer | technical_writer | green | 📝 |
| builder-1 | builder | yellow | 🔨 |
| builder-2 | builder | yellow | 🔨 |
| reviewer | reviewer | magenta | 🔍 |

### Suggested Implementation Approach
1. Create `AGENT_ICONS` constant mapping agent IDs to icons
2. Create `get_agent_style(agent_id)` function returning color and icon
3. Modify `write_*` methods to use `get_agent_style()` for formatting
4. Add `_last_agent_id` state to track handoff detection
5. Create `_write_handoff_separator(from_agent, to_agent)` method
6. Configure RichLog word-wrap settings if available, or wrap text before writing

### Files to Modify
* `src/teambot/ui/widgets/output_pane.py` - Primary implementation
* `src/teambot/visualization/console.py` - Add AGENT_ICONS constant
* `tests/test_ui/` - Add unit tests for new formatting

---

Generated 2026-02-05 by BA Agent (mode: Specification)
<!-- markdown-table-prettify-ignore-end -->
