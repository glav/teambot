<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Split-Pane Terminal Interface - Feature Specification Document
Version 0.1 | Status Draft | Owner TBD | Team TeamBot | Target TBD | Lifecycle Discovery

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-28 |
| Problem & Users | 100% | None | 2026-01-28 |
| Scope | 100% | None | 2026-01-28 |
| Requirements | 100% | None | 2026-01-28 |
| Metrics & Risks | 80% | Performance benchmarks TBD | 2026-01-28 |
| Operationalization | 0% | Not started | - |
| Finalization | 0% | Pending review | - |
Unresolved Critical Questions: 0 | TBDs: 2

---

## 1. Executive Summary

### Context
TeamBot's current interactive mode uses a single-pane terminal interface where user input and agent output share the same display area. This creates visual conflicts when agents are processing tasks - the prompt can be disrupted by incoming output, and users must either wait for agents to finish or use the `&` suffix for background execution. The current overlay solution addresses some issues but doesn't fully solve the fundamental problem of input/output interference.

### Core Opportunity
Replace the single-pane interface with a split-pane design that separates user input (left pane) from agent output (right pane). This creates a stable, predictable user experience where:
- The input prompt remains stable and always accessible
- Agent responses appear asynchronously without interrupting input
- All agent tasks effectively become background tasks (no `&` suffix needed)
- Commands like `/status` display in the output pane without affecting the input area

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Provide stable, uninterrupted input experience | UX | Prompt disrupted by output | Prompt always stable | MVP | P0 |
| G-002 | Display agent output asynchronously without blocking | UX | Wait or use `&` for background | All output async | MVP | P0 |
| G-003 | Simplify interaction model by removing `&` suffix | UX | `&` required for background | No special syntax | MVP | P1 |
| G-004 | Ensure reliable, artifact-free display rendering | Technical | Occasional visual glitches | Zero visual artifacts | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement split-pane layout | Left input, right output panes functional | P0 | TBD |
| Remove background task syntax | `&` suffix deprecated, all tasks async | P1 | TBD |
| Achieve display stability | No flicker or artifacts during operation | P0 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Single output area**: User input and agent responses share the same terminal space
- **Output interference**: When agents respond, the output can disrupt or scroll past the user's input line
- **Background workaround**: Users must append `&` to commands to run tasks in background
- **Overlay limitations**: Current persistent overlay only shows summary status, not full agent responses
- **Input instability**: The prompt can "disappear" when output is written, requiring user to re-orient

### Problem Statement
The current single-pane terminal interface creates a poor user experience because input and output compete for the same visual space. Users cannot type commands while viewing agent output without interference, and the `&` suffix for background execution is a UX workaround that adds cognitive load.

### Root Causes
* Terminal UIs traditionally use a single scrolling output area with input at the bottom
* No separation between where user types and where output appears
* Synchronous display model - output writes block input readability

### Impact of Inaction
* Users experience frustration when output disrupts their command typing
* Cognitive overhead of remembering `&` syntax for background tasks
* Reduced productivity due to waiting for output before typing next command
* Perception of unreliable or "jumpy" interface

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer using TeamBot | Issue commands quickly, monitor multiple agent tasks | Prompt instability, waiting for output | High - primary user |
| Power User | Run multiple parallel agent tasks, monitor progress | `&` syntax overhead, output flooding | High - advanced workflows |

### Journeys
1. **Command Entry Flow**: User types command → submits → continues typing next command while agent works → sees response in right pane when ready
2. **Status Check Flow**: User types `/status` → output appears in right pane → prompt remains stable for next command

---

## 4. Scope

### In Scope
* Split-pane terminal layout with input (left) and output (right) panes
* Stable, always-visible input prompt in left pane
* Asynchronous output display in right pane
* Removal of `&` background task syntax (all tasks are async)
* `/status` and similar commands output to right pane
* Basic terminal resize handling

### Out of Scope (justified)
* Mouse interaction with panes - CLI-focused, keyboard-driven interface
* Resizable pane divider by user - fixed split is simpler and more reliable
* Multiple output panes - complexity outweighs benefit for MVP
* Custom pane positioning (top/bottom split) - vertical split is most natural for terminal
* Rich text formatting beyond current Rich library capabilities - maintain compatibility

### Assumptions
* Terminal supports ANSI escape codes (xterm-256color compatible)
* Terminal width is at least 80 columns (minimum for meaningful split)
* Python curses or similar library can be used for pane management
* Users have terminals that support alternate screen buffer

### Constraints
* Must work in VS Code integrated terminal, iTerm2, Windows Terminal, standard xterm
* Cannot require additional OS-level dependencies beyond Python packages
* Must maintain backward compatibility with existing commands
* Performance: render updates must not exceed 50ms

---

## 5. Product Overview

### Value Proposition
TeamBot with split-pane interface provides a stable, professional terminal experience where users can continuously issue commands without interruption, while agent responses appear asynchronously in a dedicated output area - similar to IDE debug consoles or chat applications.

### Differentiators
* Eliminates `&` syntax - every task is inherently asynchronous
* Stable input that never scrolls away
* Real-time output without blocking user interaction
* Clean separation of concerns (input vs. output)

### UX / UI
**Layout:**
```
┌─────────────────────────┬───────────────────────────────────────┐
│                         │                                       │
│  INPUT PANE (Left)      │  OUTPUT PANE (Right)                  │
│                         │                                       │
│  teambot: @pm plan auth │  [2026-01-28 10:30:15] @pm            │
│  teambot: _             │  Starting task: plan authentication   │
│                         │  ...                                  │
│                         │  ✓ Task completed                     │
│                         │                                       │
│                         │  [2026-01-28 10:30:45] /status        │
│                         │  Agent    Status   Task               │
│                         │  pm       idle     -                  │
│                         │  builder  working  implementing...    │
│                         │                                       │
└─────────────────────────┴───────────────────────────────────────┘
```

**Pane Proportions:**
- Input pane: ~30% of terminal width (minimum 25 columns)
- Output pane: ~70% of terminal width (remaining space)
- Vertical divider: single character `│`

| UX Status: Mockup Complete |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-SPI-001 | Split Pane Layout | Terminal shall be divided into left (input) and right (output) vertical panes | G-001, G-002 | All | P0 | Panes visible, divider drawn | Use curses or ANSI regions |
| FR-SPI-002 | Stable Input Pane | Left pane displays prompt and accepts input; content never disrupted by output pane | G-001 | All | P0 | Input persists across output events | Core requirement |
| FR-SPI-003 | Async Output Display | Right pane displays agent output as it arrives, without waiting for input | G-002 | All | P0 | Output appears within 100ms of receipt | Event-driven updates |
| FR-SPI-004 | Output Scrolling | Right pane scrolls independently when content exceeds visible area | G-002 | All | P0 | New output scrolls up older content | Auto-scroll to bottom |
| FR-SPI-005 | Command History in Input | Input pane supports up/down arrow for command history | G-001 | All | P1 | Arrow keys navigate history | Same as current REPL |
| FR-SPI-006 | Remove & Background Syntax | The `&` suffix for background tasks shall be deprecated; all tasks run async | G-003 | All | P1 | `&` ignored or warns, tasks always async | Breaking change - document |
| FR-SPI-007 | Status Command Output | `/status` command displays in right pane | G-002 | All | P0 | Status table renders in output pane | Same content, new location |
| FR-SPI-008 | Help Command Output | `/help` command displays in right pane | G-002 | All | P0 | Help text renders in output pane | |
| FR-SPI-009 | Task Output Attribution | Output includes timestamp and agent ID for each message | G-002 | All | P1 | Format: `[timestamp] @agent: message` | Traceability |
| FR-SPI-010 | Terminal Resize Handling | Layout adjusts when terminal is resized | G-004 | All | P1 | Panes resize proportionally | SIGWINCH handler |
| FR-SPI-011 | Minimum Terminal Width | If terminal < 80 columns, display warning and fall back to single-pane mode | G-004 | All | P1 | Warning shown, graceful fallback | Backward compat |
| FR-SPI-012 | Pane Divider | Visual divider between panes using `│` character | G-001 | All | P0 | Divider visible full height | Simple box drawing |
| FR-SPI-013 | Input Continuation | Multi-line input supported in left pane (if applicable) | G-001 | All | P2 | Line wrap within input pane | Optional enhancement |
| FR-SPI-014 | Clear Output Command | `/clear` command clears right pane content | G-002 | All | P2 | Output pane cleared, input unaffected | New command |
| FR-SPI-015 | Output Timestamps | Each output entry prefixed with timestamp | G-002 | All | P1 | HH:MM:SS format | Configurable format |

### Feature Hierarchy
```
Split-Pane Interface
├── Input Pane (Left)
│   ├── Prompt Display
│   ├── User Input Capture
│   ├── Command History (up/down)
│   └── Input Line Editing
├── Output Pane (Right)
│   ├── Async Message Display
│   ├── Auto-Scroll
│   ├── Timestamp + Attribution
│   └── Independent Scrolling
├── Pane Management
│   ├── Layout Calculation
│   ├── Divider Rendering
│   ├── Resize Handling
│   └── Fallback Mode
└── Integration
    ├── Command Routing to Output
    ├── Agent Response Routing
    └── Background Task Removal
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-SPI-001 | Performance | Output display latency | < 100ms from receipt to render | P0 | Benchmark test | Critical for responsiveness |
| NFR-SPI-002 | Performance | Input responsiveness | < 10ms keystroke to display | P0 | Manual testing | Must feel instant |
| NFR-SPI-003 | Reliability | No visual artifacts | 0 flicker/glitch per session | P0 | Visual inspection testing | Core requirement |
| NFR-SPI-004 | Compatibility | Terminal support | VS Code, iTerm2, Windows Terminal, xterm | P0 | Test on each platform | Key terminals |
| NFR-SPI-005 | Usability | Learning curve | Existing users productive in < 1 minute | P1 | User testing | Commands unchanged |
| NFR-SPI-006 | Maintainability | Code complexity | Single-responsibility pane classes | P1 | Code review | Clean architecture |
| NFR-SPI-007 | Performance | Memory usage | < 50MB overhead for pane management | P1 | Memory profiling | Reasonable limit |
| NFR-SPI-008 | Graceful Degradation | Fallback mode | Works on terminals < 80 cols | P1 | Test with narrow terminal | Current behavior |

---

## 8. Data & Analytics

### Inputs
- User keyboard input (stdin)
- Agent response events from SDK
- Terminal size (rows, columns)
- SIGWINCH resize signals

### Outputs / Events
- Rendered output to terminal (stdout)
- Command history updates
- Pane content buffers

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| pane_render | Output displayed | timestamp, agent_id, render_time_ms | Performance monitoring | TBD |
| input_submitted | User submits command | command_type, length | Usage analytics | TBD |
| resize_event | Terminal resized | old_size, new_size | Compatibility data | TBD |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Output latency | Performance | N/A (new) | < 100ms p95 | Per session | Instrumentation |
| Visual artifacts | Quality | Occasional | Zero | Per session | User reports |
| User satisfaction | UX | 3/5 (estimated) | 4.5/5 | Post-release | Feedback |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Python curses or urwid library | External | High | TBD | Cross-platform issues | Use blessed library as alternative |
| Rich library | External | Medium | TBD | Compatibility with curses | May need custom renderer |
| Terminal ANSI support | Environment | High | N/A | Some terminals lack support | Fallback mode |
| Existing REPL architecture | Internal | Medium | TBD | Refactoring complexity | Incremental migration |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | curses/Windows compatibility issues | High | Medium | Use blessed library (cross-platform) | TBD | Open |
| R-002 | Rich library conflict with curses rendering | Medium | Medium | Custom renderer or raw ANSI | TBD | Open |
| R-003 | Performance degradation from dual-buffer management | Medium | Low | Optimize render batching | TBD | Open |
| R-004 | Complex refactoring of existing REPL | Medium | Medium | Incremental migration, feature flag | TBD | Open |
| R-005 | Terminal resize edge cases | Low | Medium | Comprehensive resize testing | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
- User commands: Internal/User-generated
- Agent output: Internal/System-generated
- No PII expected in standard usage

### PII Handling
N/A - No PII collected or stored by this feature

### Threat Considerations
- Terminal escape sequence injection: Sanitize all output before display
- Buffer overflow: Limit output pane buffer size (e.g., 10,000 lines)

### Regulatory / Compliance
N/A - No regulatory requirements for this feature

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Feature flag to disable split-pane | Falls back to current behavior |
| Monitoring | Log render errors if any | Debug logging only |
| Alerting | N/A | Client-side feature |
| Support | Document fallback mode | For incompatible terminals |
| Capacity Planning | N/A | Local execution only |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Description | Gate Criteria | Owner |
|-------|-------------|---------------|-------|
| Phase 1 | Core split-pane layout | Panes render, divider visible | TBD |
| Phase 2 | Input pane stability | Input never disrupted by output | TBD |
| Phase 3 | Async output routing | All output to right pane | TBD |
| Phase 4 | Remove & syntax | Background mode deprecated | TBD |
| Phase 5 | Polish & fallback | Resize, graceful degradation | TBD |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| `TEAMBOT_SPLIT_PANE` | Enable split-pane interface | false (until stable) | Remove after 2 releases |
| `TEAMBOT_LEGACY_MODE` | Force single-pane mode | false | Keep for compatibility |

### Communication Plan
- Update README with new interface description
- Add migration notes for `&` syntax deprecation
- Screenshot/GIF in documentation

---

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Use curses, blessed, or raw ANSI for pane management? | TBD | Research phase | Open |
| Q-002 | Should output pane support manual scrollback (keyboard navigation)? | TBD | Design phase | Open |

---

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 0.1 | 2026-01-28 | AI Assistant | Initial specification draft | New |

---

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Existing Spec | docs/feature-specs/persistent-status-overlay.md | Current overlay implementation | This feature supersedes overlay approach |
| REF-002 | Existing Spec | docs/feature-specs/teambot-interactive-mode.md | Interactive mode architecture | Build upon existing REPL foundation |
| REF-003 | Code | src/teambot/visualization/overlay.py | Current ANSI rendering approach | Reuse terminal detection logic |
| REF-004 | Code | src/teambot/repl/loop.py | Current input/output handling | Refactor to route output to right pane |

### Citation Usage Notes
This specification builds upon existing interactive mode and overlay specifications. The split-pane approach is a more comprehensive solution that may supersede the persistent status overlay feature.

---

## 17. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Split-pane | Terminal divided into two vertical sections |
| Input pane | Left section where user types commands |
| Output pane | Right section where agent responses appear |
| ANSI escape codes | Terminal control sequences for cursor positioning, colors |
| curses | Python library for terminal UI (Unix) |
| blessed | Cross-platform Python terminal library |

### Technical Approach Options

**Option A: Python curses/blessed**
- Pros: Full terminal control, well-tested
- Cons: Rich library integration challenges, Windows curses limited

**Option B: Raw ANSI with scroll regions**
- Pros: Lightweight, builds on existing overlay code
- Cons: Complex to implement reliably, terminal variance

**Option C: Textual library (Rich ecosystem)**
- Pros: Modern, Rich-compatible, reactive
- Cons: Learning curve, may be overkill

**Recommendation**: Start with blessed library (cross-platform curses) for reliability. Evaluate Textual if blessed proves insufficient.

### Additional Notes
- The `&` syntax removal is a breaking change that should be clearly documented
- Consider keeping `&` as a no-op with deprecation warning for one release cycle
- Output pane buffer should be capped to prevent memory issues (suggest 10,000 lines max)

Generated 2026-01-28T00:59:20Z by sdd.1-create-feature-spec (mode: collaborative)
<!-- markdown-table-prettify-ignore-end -->
