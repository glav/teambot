<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Agent Output Color Indent - Feature Specification Document
Version 0.1 | Status Draft | Owner TBD | Team TeamBot | Target TBD | Lifecycle Proposal

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-05 |
| Problem & Users | 100% | None | 2026-02-05 |
| Scope | 80% | Technical research | 2026-02-05 |
| Requirements | 100% | None | 2026-02-05 |
| Metrics & Risks | 50% | Performance benchmarks | 2026-02-05 |
| Research | 0% | Rich library capabilities | - |
| Test Strategy | 0% | TBD | - |
| Task Planning | 0% | TBD | - |
Unresolved Critical Questions: 1 | TBDs: 3

---

## 1. Executive Summary

### Context
TeamBot displays output from multiple agents (pm, ba, writer, builder-1, builder-2, reviewer) in a shared output pane. Each agent has a colored header line (e.g., `[blue]━━━ 📋 @pm ━━━[/blue]`), but subsequent output lacks visual grouping. When multiple agents produce interleaved output, users struggle to quickly identify which output belongs to which agent.

### Core Opportunity
Add a **vertical colored indent line** to the left of each agent's output block. The indent line would:
- Match the agent's header color
- Visually group all output from that agent
- Create clear visual separation between agents
- Improve scannability in multi-agent workflows

**Before:**
```
[blue]━━━ 📋 @pm (task abc123) ━━━[/blue]
Here is my analysis of the problem...
The key considerations are:
- Item one
- Item two

[green]━━━ 🔨 @builder-1 (task def456) ━━━[/green]
I'll implement the solution...
```

**After:**
```
[blue]━━━ 📋 @pm (task abc123) ━━━[/blue]
[blue]│[/blue] Here is my analysis of the problem...
[blue]│[/blue] The key considerations are:
[blue]│[/blue] - Item one
[blue]│[/blue] - Item two

[green]━━━ 🔨 @builder-1 (task def456) ━━━[/green]
[green]│[/green] I'll implement the solution...
```

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Visually group agent output | UX | No grouping | Colored indent bars | MVP | P0 |
| G-002 | Match agent header colors | UX | Headers only | Headers + indent lines | MVP | P0 |
| G-003 | Maintain readability | UX | Current readability | Equal or better | MVP | P0 |
| G-004 | Support streaming output | Compatibility | Streaming works | Streaming with indent | MVP | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement indent line rendering | All agent output has colored left border | P0 | TBD |
| Color consistency | Indent matches header for all 6 agents | P0 | TBD |
| Streaming support | Indent appears on streamed content | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Visual ambiguity**: When agents output sequentially, it's unclear where one agent's output ends and another begins
- **Scanning difficulty**: Users must read headers to identify agent ownership of content
- **Interleaved confusion**: Multi-agent parallel output can be hard to attribute
- **Headers scroll away**: Once the header scrolls up, there's no visual cue for attribution

### Problem Statement
Agent output lacks persistent visual attribution. Users must rely on colored headers that scroll away, making it difficult to scan long outputs or track ownership when multiple agents contribute. This reduces efficiency in understanding multi-agent workflows.

### Root Causes
* Original output design treated each line independently
* No concept of "output blocks" associated with agents
* Header was the only visual attribution mechanism

### Impact of Inaction
* Reduced comprehension speed for multi-agent output
* User frustration when reviewing logs
* Difficulty in debugging which agent produced what
* Suboptimal UX compared to modern chat interfaces

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer | Quickly scan agent output | Can't tell which agent said what | High |
| PM/Lead | Review multi-agent session logs | Lost context when scrolling | Medium |
| Debugger | Trace output to specific agent | Headers scroll away | High |

---

## 4. Scope

### In Scope
- Vertical indent line (│) to the left of agent output
- Color matching between header and indent line
- Support for all 6 agent personas
- Support for Rich console rendering
- Streaming output compatibility

### Out of Scope
- Collapsible/expandable output sections (future enhancement)
- Agent output filtering by color (future enhancement)
- Custom color schemes (use existing agent color mappings)
- Nested indentation for sub-tasks

### Assumptions
- Rich library supports inline styling for indent characters
- Agent output is already processed through a central renderer
- Each agent has a defined color in the existing color scheme

### Dependencies
- Existing agent color definitions
- Rich console rendering pipeline
- Output streaming mechanism

---

## 5. Requirements

### Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | Display colored indent line for all agent output | P0 | Every line of agent output prefixed with colored `│ ` |
| FR-002 | Match indent color to agent header color | P0 | PM=blue, BA=cyan, Writer=magenta, Builder-1=green, Builder-2=yellow, Reviewer=red |
| FR-003 | Apply indent to streaming output | P1 | Streamed characters appear after indent |
| FR-004 | Preserve content formatting | P0 | Code blocks, markdown, tables render correctly with indent |
| FR-005 | Handle multi-line content | P0 | Indent applies to wrapped lines |

### Non-Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-001 | No visible rendering delay | P0 | Indent appears synchronously with content |
| NFR-002 | Minimal memory overhead | P1 | <1% increase in memory usage |
| NFR-003 | Terminal compatibility | P0 | Works in standard terminals (256-color minimum) |

---

## 6. Agent Color Mapping

| Agent ID | Persona | Header Color | Indent Color |
|----------|---------|--------------|--------------|
| `pm` | Project Manager | Blue | Blue |
| `ba` | Business Analyst | Cyan | Cyan |
| `writer` | Technical Writer | Magenta | Magenta |
| `builder-1` | Builder (Primary) | Green | Green |
| `builder-2` | Builder (Secondary) | Yellow | Yellow |
| `reviewer` | Reviewer | Red | Red |

---

## 7. Visual Design

### Indent Character Options

| Option | Character | Pros | Cons |
|--------|-----------|------|------|
| A (Recommended) | `│` (U+2502) | Clean, standard box drawing | Requires Unicode support |
| B | `┃` (U+2503) | Heavier weight, more visible | May be too bold |
| C | `▎` (U+258E) | Thick block style | Different aesthetic |
| D | `\|` (pipe) | ASCII compatible | Less elegant |

**Recommendation**: Option A (`│`) for clean appearance with Unicode fallback to Option D (`|`) for limited terminals.

### Spacing
- Indent line followed by single space: `│ `
- Total indent width: 2 characters
- Preserves content alignment

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Rich library limitations | Low | High | Research Rich Panel/padding capabilities early |
| Terminal Unicode issues | Medium | Medium | Provide ASCII fallback option |
| Performance on long output | Low | Medium | Buffer and batch rendering |
| Breaking existing tests | Medium | Low | Update test fixtures |

---

## 9. Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-001 | Does Rich support per-line prefix styling efficiently? | Open | Requires research |
| Q-002 | Should indent apply to error/warning output? | Proposed: Yes | TBD |
| Q-003 | How to handle code blocks with existing indentation? | Proposed: Add to existing indent | TBD |

---

## 10. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Output attribution accuracy | Manual scanning | Instant visual | User feedback |
| Time to identify agent source | ~2 seconds | <0.5 seconds | Observation |
| User satisfaction | N/A | Positive feedback | Survey |

---

## 11. Implementation Notes

*For @builder-1 or @builder-2:*

Key areas to investigate:
1. `src/teambot/visualization/` - Likely location for rendering logic
2. Rich library `Panel`, `Padding`, or custom `Console.print()` styling
3. Agent output pipeline - where text is formatted before display

This spec is ready for technical research and task breakdown.
