<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->

# Feature Specification: Agent Output Reference Syntax (`$agent`)

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Business Analyst Agent |
| **Target Release** | Next Minor Release |
| **Primary Language** | Python |
| **Testing Approach** | Hybrid (TDD for parser, code-first for integration) |

---

## Progress Tracker

| Phase | Status |
|-------|--------|
| ✅ Context & Background | Complete |
| ✅ Problem Definition | Complete |
| ✅ Scope | Complete |
| ✅ Requirements | Complete |
| ✅ Metrics & Success Criteria | Complete |
| ✅ Operationalization | Complete |
| ⏳ Review & Approval | Pending |

---

## Executive Summary

### Context
TeamBot enables multi-agent AI workflows where specialized personas collaborate on development tasks. Users currently chain agent tasks using the pipeline operator (`->`), which passes output sequentially between stages.

### Opportunity
Users need a more flexible way to reference any agent's output within their prompts—not just the immediately preceding stage. This enables complex workflows where agents can selectively incorporate results from any prior agent.

### Goals & Objectives

| ID | Goal | Objective | Success Metric |
|----|------|-----------|----------------|
| G-001 | Enable explicit output references | Implement `$<agent-id>` syntax for referencing agent outputs | Users can reference any agent's output inline |
| G-002 | Automatic dependency handling | System waits for referenced agents to complete | Zero race conditions in output injection |
| G-003 | Clear status visibility | Display which agents are waiting vs. executing | Status UI shows `waiting`, `executing`, `idle` |
| G-004 | Intuitive documentation | Document both `->` and `$agent` syntaxes | README includes comparison table with examples |

---

## Problem Definition

### Current Situation
TeamBot supports the pipeline operator (`->`) for chaining tasks:
```bash
@pm Create a plan -> @builder-1 Implement based on this plan
```

Output from each stage automatically flows to the next. This works well for linear workflows but has limitations.

### Problem Statement
> Users cannot easily reference a specific agent's output within their prompt in a way that is intuitive, explicit, and creates an automatic wait-for-completion dependency.

### Root Causes
1. **Implicit-only output passing**: The `->` operator passes all output to the next stage automatically
2. **Sequential coupling**: Users must restructure entire pipelines to change output routing
3. **No named references**: Cannot reference non-adjacent stage outputs
4. **Single-source limitation**: Each stage receives output only from its immediate predecessor

### Impact

| Stakeholder | Pain Point | Business Impact |
|-------------|------------|-----------------|
| End Users | Must copy/paste outputs manually | Reduced productivity |
| Power Users | Cannot build complex dependency graphs | Limited workflow expressiveness |
| Workflow Designers | Constrained to linear patterns | Suboptimal agent collaboration |

---

## Users & Personas

| Persona | Description | Goals | Pain Points | Feature Impact |
|---------|-------------|-------|-------------|----------------|
| **CLI User** | Developer using TeamBot interactively | Quick task execution | Repetitive copy/paste between agents | High - eliminates manual output transfer |
| **Workflow Designer** | Creates complex multi-agent workflows | Express complex dependencies | Linear-only pipeline structure | High - enables flexible DAGs |
| **Automation Engineer** | Scripts TeamBot for CI/CD | Reliable automated workflows | Race conditions, timing issues | Medium - automatic wait behavior |

---

## Scope

### In Scope
- `$<agent-id>` syntax for inline output references (e.g., `$pm`, `$builder-1`, `$ba`)
- Parser extension to detect and extract `$agent` tokens
- Dependency resolution: wait for referenced agents before execution
- New agent status: `waiting` (in addition to `idle`, `executing`)
- Output injection at reference points
- README documentation with syntax comparison
- Unit tests for parser and dependency resolution
- Integration tests for end-to-end workflows

### Out of Scope
- Field-level references (e.g., `$pm.plan`, `$pm.summary`) — future enhancement
- Cross-session output persistence
- Visual dependency graph UI
- Circular dependency auto-resolution (will error instead)
- Output filtering or transformation

### Assumptions
1. Agent IDs are unique within a session
2. Agent output is stored in memory during session lifetime
3. Only the most recent output per agent is referenced (no history access)
4. Valid agent IDs follow pattern: lowercase alphanumeric with hyphens (e.g., `pm`, `builder-1`)

### Constraints
- Must maintain backward compatibility with existing `->` syntax
- Must not break existing scripts or workflows
- Parser changes must not impact performance significantly
- Status updates must be real-time for UI responsiveness

---

## Product Overview

### Value Proposition
Enable users to build flexible, expressive multi-agent workflows by referencing any agent's output anywhere in their prompt, with automatic dependency handling.

### Key Differentiators from Pipeline (`->`)

| Aspect | Pipeline (`->`) | Reference (`$agent`) |
|--------|-----------------|---------------------|
| **Use Case** | Sequential task chaining | Explicit output injection |
| **Dependency Type** | Implicit (previous stage) | Explicit (named agent) |
| **Output Passing** | Automatic to next stage | On-demand at reference |
| **Multiple Sources** | One source per stage | Multiple agents in one prompt |
| **Flexibility** | Linear flow only | Arbitrary dependency graphs |
| **Example** | `@pm Plan -> @builder Build` | `@builder Build using $pm` |

### Combined Usage Examples

```bash
# Simple reference
@pm Create a project plan
@builder-1 Implement the features from $pm

# Multiple references in one prompt
@builder-1 Implement based on $pm requirements and $ba specifications

# Combined with pipeline
@pm Create plan -> @builder-1 Implement $pm -> @reviewer Review $builder-1

# Parallel agents, then merge
@pm Create plan
@ba Write requirements
@builder-1 Implement using $pm and $ba
```

---

## Functional Requirements

| ID | Requirement | Linked Goal | Priority | Acceptance Criteria |
|----|-------------|-------------|----------|---------------------|
| FR-001 | System SHALL parse `$<agent-id>` tokens in user prompts | G-001 | P0 | Parser extracts all `$agent` references from prompt text |
| FR-002 | System SHALL validate that referenced agent IDs exist | G-001 | P0 | Error displayed for invalid agent ID references |
| FR-003 | System SHALL wait for referenced agents to complete before executing | G-002 | P0 | Execution blocked until all `$agent` dependencies complete |
| FR-004 | System SHALL inject referenced agent's output at the reference point | G-001 | P0 | Output appears in context where `$agent` was referenced |
| FR-005 | System SHALL display `waiting` status for agents blocked on dependencies | G-003 | P0 | UI shows "waiting for @pm" when blocked |
| FR-006 | System SHALL support multiple `$agent` references in a single prompt | G-001 | P1 | `$pm and $ba` both resolved in one prompt |
| FR-007 | System SHALL detect circular dependencies and display error | G-002 | P1 | Clear error message for `$a` refs `$b` refs `$a` |
| FR-008 | System SHALL support `$agent` within pipeline stages | G-001 | P1 | `@pm Plan -> @builder Impl $pm` works correctly |
| FR-009 | System SHALL return error when referencing agent with no output | G-002 | P2 | "Agent @pm has no output to reference" message |
| FR-010 | System SHALL support escaping with `\$` for literal dollar signs | G-001 | P2 | `\$pm` renders as literal `$pm` in prompt |

### Functional Requirement Details

#### FR-001: Parse `$<agent-id>` Tokens
**Description**: The parser must identify and extract all `$agent-id` patterns from user input.

**Pattern**: `\$([a-z][a-z0-9-]*)`
- Must start with `$`
- Agent ID starts with lowercase letter
- Followed by lowercase letters, digits, or hyphens
- Examples: `$pm`, `$builder-1`, `$ba`

**Acceptance Criteria**:
- [x] Pattern matches: `$pm`, `$builder-1`, `$builder-2`, `$ba`, `$reviewer`, `$writer`
- [x] Pattern rejects: `$1agent` (starts with number), `$PM` (uppercase), `$$pm` (double dollar)
- [x] Multiple references extracted: `$pm and $ba` → `['pm', 'ba']`

#### FR-003: Wait for Referenced Agents
**Description**: When a prompt contains `$agent` references, execution must wait until all referenced agents have completed their current task.

**Behavior**:
1. Parse prompt to extract all `$agent` references
2. Check status of each referenced agent
3. If any referenced agent is `RUNNING` or `STREAMING`, set current agent to `WAITING`
4. When all referenced agents reach `COMPLETED` or `IDLE` with output, proceed
5. If referenced agent is `FAILED`, propagate error or proceed with error context

**Acceptance Criteria**:
- [x] Agent waits when reference is running
- [x] Agent proceeds when reference completes
- [x] Timeout handling after configurable duration (default: 5 minutes)

#### FR-005: Display Waiting Status
**Description**: The UI must clearly show when an agent is waiting for dependencies.

**Status Format**:
```
@builder-1: waiting for @pm, @ba
@pm: executing
@ba: executing
@reviewer: idle
```

**Acceptance Criteria**:
- [x] Status includes which agents are being waited on
- [x] Status updates in real-time as dependencies complete
- [x] Status changes to `executing` once all dependencies satisfied

---

## Non-Functional Requirements

| ID | Category | Requirement | Target | Measurement |
|----|----------|-------------|--------|-------------|
| NFR-001 | Performance | Reference parsing overhead | < 10ms per prompt | Benchmark parser with 10 references |
| NFR-002 | Performance | Status update latency | < 100ms | Time from state change to UI update |
| NFR-003 | Reliability | No race conditions in output injection | 100% | Integration tests with concurrent agents |
| NFR-004 | Usability | Clear error messages | All errors actionable | User can fix issue from error text |
| NFR-005 | Maintainability | Code follows existing patterns | Consistent with codebase | Code review checklist |
| NFR-006 | Compatibility | Backward compatible with `->` | 100% existing workflows work | Regression test suite |

---

## Data & Analytics

### Inputs
| Data | Source | Format |
|------|--------|--------|
| User prompt | REPL input | String with potential `$agent` references |
| Agent outputs | Task completion | String (agent response text) |
| Agent status | AgentStatusManager | Enum: IDLE, RUNNING, STREAMING, WAITING, COMPLETED, FAILED |

### Outputs
| Data | Destination | Format |
|------|-------------|--------|
| Parsed references | Task executor | List of agent IDs |
| Injected prompt | Agent runner | String with outputs inserted |
| Status updates | UI | AgentStatus objects |

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Feature adoption | 50% of multi-agent sessions use `$agent` | Usage telemetry |
| Error rate | < 5% of `$agent` uses result in error | Error logging |
| User satisfaction | Positive feedback on syntax intuitiveness | User surveys |

---

## Dependencies

| Dependency | Component | Criticality | Owner | Risk | Mitigation |
|------------|-----------|-------------|-------|------|------------|
| Parser infrastructure | `src/teambot/repl/parser.py` | High | Builder | Breaking changes | Extend, don't replace |
| Status management | `src/teambot/ui/agent_state.py` | High | Builder | New state enum value | Add `WAITING` to existing enum |
| Output injection | `src/teambot/tasks/output_injector.py` | High | Builder | Interface changes | Maintain backward compatibility |
| Task manager | `src/teambot/tasks/manager.py` | Medium | Builder | Dependency resolution | Leverage existing TaskGraph |
| README | `README.md` | Low | Writer | Documentation drift | Update in same PR |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular dependencies cause infinite wait | Medium | High | Implement cycle detection in parser; error immediately |
| Race condition between status check and execution | Low | Medium | Use locks or atomic status transitions |
| User confusion between `->` and `$agent` | Medium | Medium | Clear documentation with comparison table |
| Performance degradation with many references | Low | Low | Cache parsed references; limit to 10 per prompt |
| Shell variable conflicts (`$PATH`, etc.) | Low | Low | Document escaping; only match known agent IDs |

---

## Privacy, Security & Compliance

### Data Classification
- **Agent outputs**: Internal/session-scoped, not persisted beyond session
- **User prompts**: May contain sensitive data; handled per existing policies

### Security Considerations
- No new attack vectors introduced
- Reference syntax validated against known agent IDs only
- No shell expansion or command injection risk

---

## Operational Considerations

### Deployment
- Feature flag: `TEAMBOT_ENABLE_AGENT_REFS` (default: enabled)
- No database migrations required
- No infrastructure changes required

### Monitoring
- Log all `$agent` reference resolutions
- Track wait times for dependency resolution
- Alert on circular dependency detection

### Rollback
- Disable feature flag to revert to `->` only behavior
- No data migration needed for rollback

---

## Implementation Guidance

### Component Changes

#### 1. Parser Extension (`src/teambot/repl/parser.py`)
- Add `AGENT_REF_PATTERN = re.compile(r'\$([a-z][a-z0-9-]*)')`
- Extract references in `parse()` method
- Store in `Command.agent_references: List[str]`

#### 2. Agent Status (`src/teambot/ui/agent_state.py`)
- Add `WAITING = "waiting"` to `AgentState` enum
- Add `waiting_for: List[str]` field to `AgentStatus`
- Update `set_waiting(agent_ids: List[str])` method

#### 3. Result Store (new: `src/teambot/tasks/result_store.py`)
- Store agent outputs by agent ID
- Provide `get_output(agent_id: str) -> Optional[str]`
- Clear on session end

#### 4. Reference Manager (new: `src/teambot/tasks/reference_manager.py`)
- Resolve `$agent` references to outputs
- Handle waiting logic
- Detect circular dependencies

#### 5. Output Injector (`src/teambot/tasks/output_injector.py`)
- Support inline injection at reference points
- Format: `[Output from @{agent_id}]: {output}`

#### 6. Documentation (`README.md`)
- Add "Agent Output References" section
- Include syntax comparison table
- Provide usage examples

### Suggested File Structure
```
src/teambot/
├── repl/
│   └── parser.py          # Extended with AGENT_REF_PATTERN
├── tasks/
│   ├── result_store.py    # NEW: Store agent outputs by ID
│   ├── reference_manager.py # NEW: Resolve references, handle waits
│   └── output_injector.py # Extended for inline injection
└── ui/
    └── agent_state.py     # Extended with WAITING state
```

---

## Acceptance Test Scenarios

### AT-001: Simple Reference After Completion
**Description**: User references an agent's output after that agent has completed
**Preconditions**: REPL running, no prior agent activity
**Steps**:
1. User enters: `@pm Create a simple project plan`
2. Wait for PM to complete (status shows `completed`)
3. User enters: `@builder-1 Implement based on $pm`
**Expected Result**: Builder-1 receives PM's output in its context and references it in response
**Verification**: Builder-1's response demonstrates awareness of PM's plan content

### AT-002: Reference Triggers Wait
**Description**: User references an agent that is still executing
**Preconditions**: REPL running
**Steps**:
1. User enters: `@pm Create a detailed project plan &` (background)
2. While PM is running, user enters: `@builder-1 Implement $pm`
3. Observe status display
**Expected Result**: Builder-1 shows status `waiting for @pm`; once PM completes, Builder-1 executes
**Verification**: 
- Status UI shows: `@builder-1: waiting for @pm`
- After PM completes, Builder-1 starts executing
- Builder-1's response includes PM's output

### AT-003: Multiple References
**Description**: User references multiple agents in one prompt
**Preconditions**: PM and BA have both completed tasks with output
**Steps**:
1. User enters: `@pm Create a plan`
2. Wait for completion
3. User enters: `@ba Write requirements`
4. Wait for completion
5. User enters: `@builder-1 Implement using $pm plan and $ba requirements`
**Expected Result**: Builder-1 receives both PM and BA outputs in context
**Verification**: Builder-1's response references content from both PM and BA

### AT-004: Invalid Agent Reference
**Description**: User references a non-existent agent
**Preconditions**: REPL running
**Steps**:
1. User enters: `@builder-1 Implement based on $nonexistent`
**Expected Result**: Clear error message displayed
**Verification**: Error shows: `Unknown agent reference: $nonexistent. Valid agents: pm, ba, builder-1, builder-2, reviewer, writer`

### AT-005: Reference Agent With No Output
**Description**: User references an agent that exists but has no output yet
**Preconditions**: REPL running, PM has not executed any tasks
**Steps**:
1. User enters: `@builder-1 Implement $pm`
**Expected Result**: System waits for PM or displays helpful message
**Verification**: Either waits with status `waiting for @pm (no output yet)` or displays: `Agent @pm has no output to reference. Run a task for @pm first.`

### AT-006: Circular Dependency Detection
**Description**: User creates a circular reference
**Preconditions**: REPL running
**Steps**:
1. User enters: `@pm Create plan based on $builder-1 &`
2. User enters: `@builder-1 Implement $pm`
**Expected Result**: Circular dependency error displayed
**Verification**: Error shows: `Circular dependency detected: @builder-1 → @pm → @builder-1`

### AT-007: Combined Pipeline and Reference
**Description**: User combines `->` pipeline with `$agent` reference
**Preconditions**: BA has completed a task
**Steps**:
1. User enters: `@ba Write requirements`
2. Wait for completion
3. User enters: `@pm Create plan for $ba -> @builder-1 Implement`
**Expected Result**: PM receives BA's output, then Builder-1 receives PM's output via pipeline
**Verification**: Builder-1's response shows awareness of original BA requirements through PM's plan

### AT-008: Escape Sequence
**Description**: User wants literal `$pm` in prompt without reference
**Preconditions**: REPL running
**Steps**:
1. User enters: `@pm Explain what \$pm means in shell scripting`
**Expected Result**: PM receives literal `$pm` in prompt, not treated as reference
**Verification**: PM's response discusses shell variable syntax, no output injection occurs

---

## README Documentation Section

The following section should be added to README.md:

```markdown
## Agent Output References

### Overview
Reference any agent's output in your prompt using the `$agent` syntax. This creates an automatic dependency—your task waits for the referenced agent to complete.

### Syntax
```bash
$<agent-id>    # Reference agent's most recent output
```

### Examples

# Reference a single agent
@pm Create a project plan
@builder-1 Implement the features from $pm

# Reference multiple agents
@builder-1 Implement based on $pm plan and $ba requirements

# Combined with pipeline
@pm Plan -> @builder-1 Implement $pm -> @reviewer Review

### Comparison: Pipeline (`->`) vs References (`$agent`)

| Feature | Pipeline (`->`) | Reference (`$agent`) |
|---------|-----------------|---------------------|
| **Use Case** | Sequential chaining | Explicit injection |
| **Dependency** | Implicit (previous) | Explicit (named) |
| **Multiple Sources** | One per stage | Multiple allowed |
| **Flexibility** | Linear only | Any pattern |

### When to Use Which

**Use `->` when:**
- Tasks must run in sequence
- Each task builds directly on the previous
- Simple linear workflows

**Use `$agent` when:**
- Need output from non-adjacent agent
- Combining multiple agent outputs
- Building complex dependency graphs

### Agent Status

When referencing a running agent, your task shows:
```
@builder-1: waiting for @pm
@pm: executing
```

### Escaping
Use `\$` for literal dollar signs:
```bash
@pm Explain what \$PATH means   # Literal $PATH, not a reference
```
```

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| OQ-001 | Should `$agent` reference most recent output only, or allow history access? | Resolved | Most recent only (v1) |
| OQ-002 | What timeout for waiting on referenced agents? | Resolved | 5 minutes default, configurable |
| OQ-003 | Should invalid references error or warn? | Resolved | Error - fail fast |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | Business Analyst Agent | Initial specification |

---

## References & Provenance

| Source | Usage |
|--------|-------|
| Problem Statement | `.teambot/shared-context/artifacts/problem_statement.md` |
| Existing Pipeline Implementation | `src/teambot/repl/parser.py`, `src/teambot/tasks/output_injector.py` |
| Agent Status System | `src/teambot/ui/agent_state.py` |

<!-- markdown-table-prettify-ignore-end -->
