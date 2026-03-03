<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Operation Cost Visibility - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-03 |
| Problem & Users | ✅ | None | 2026-03-03 |
| Scope | ✅ | None | 2026-03-03 |
| Requirements | ✅ | None | 2026-03-03 |
| Metrics & Risks | ✅ | None | 2026-03-03 |
| Operationalization | ✅ | None | 2026-03-03 |
| Finalization | ✅ | None | 2026-03-03 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot orchestrates multi-agent AI workflows using the GitHub Copilot CLI/SDK. Each agent interaction consumes tokens from the underlying LLM, but users currently have no visibility into this consumption. As AI costs scale with usage, understanding operational costs becomes critical for budget management, optimization, and adoption decisions.

### Core Opportunity
Add comprehensive token tracking and cost visibility to TeamBot, enabling users to understand resource consumption per agent, per stage, and per session—supporting informed decisions about model selection and workflow optimization.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Capture token usage from Copilot CLI/SDK responses | Feature | 0 tokens tracked | All available token data captured | v0.2.0 | High |
| G-002 | Display total token consumption at end of orchestration runs | Feature | No display | Summary shown on every run | v0.2.0 | High |
| G-003 | Track and display usage broken down by agent | Feature | No breakdown | Per-agent totals visible | v0.2.0 | Medium |
| G-004 | Track and display usage broken down by workflow stage | Feature | No breakdown | Per-stage totals visible | v0.2.0 | Medium |
| G-005 | Persist token data with documented schema | Feature | No persistence | Data saved to workflow_state.json | v0.2.0 | Medium |
| G-006 | Display session token usage in interactive mode | Feature | No display | End-of-session summary | v0.2.0 | Medium |
| G-007 | Degrade gracefully when token data unavailable | Robustness | Undefined | Display `n/a`, log warning once | v0.2.0 | High |
| G-008 | Capture input/output token breakdown | Feature | No breakdown | prompt_tokens/completion_tokens separated | v0.2.0 | Low |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Enable cost transparency | 100% of orchestration runs show token summary | High | Builder |
| Support optimization decisions | Per-agent and per-stage breakdown available | Medium | Builder |
| Maintain system reliability | Zero workflow failures due to token tracking | High | Builder |

## 2. Problem Definition

### Current Situation
TeamBot provides powerful multi-agent orchestration via `teambot run` and interactive sessions via REPL mode. However:
- **CopilotResult** (client.py) returns only: `success`, `output`, `error`, `exit_code`, `prompt`
- **SDK client** (sdk_client.py) returns only text content from responses
- **TaskResult** stores only: `task_id`, `output`, `success`, `error`, `completed_at`
- **WorkflowState** has a `metadata` dict that could store additional data but is unused for costs

Users have zero visibility into how many tokens are consumed during any operation.

### Problem Statement
**TeamBot users cannot understand, track, or optimize the operational costs of their AI-assisted workflows because token usage data is neither captured nor displayed.**

### Root Causes
* Copilot client implementations do not extract or return token usage from responses
* Data models (CopilotResult, TaskResult) lack fields for usage metrics
* No aggregation logic exists to accumulate usage across agents/stages
* No display components exist to show usage summaries

### Impact of Inaction
1. **Budget uncertainty** — Organizations cannot forecast or control AI costs
2. **Optimization blindness** — Cannot identify inefficient agents, prompts, or stages
3. **Adoption friction** — Teams hesitant to adopt tool without cost visibility
4. **Accountability gaps** — Cannot attribute costs to specific workflows

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **Individual Developer** | Understand personal usage, optimize prompts | No visibility into consumption, surprise costs | Primary user—needs immediate feedback |
| **Team Lead** | Budget forecasting, resource allocation, team oversight | Cannot plan or allocate AI budget | Decision support—needs aggregate data |
| **Finance/Operations** | Cost tracking, chargeback, compliance | No data for accounting or allocation | Secondary—needs exportable data |
| **Workflow Designer** | Optimize agent/stage efficiency | Cannot compare agent costs, no metrics | Power user—needs detailed breakdown |

### Journeys

**Developer Journey (Orchestration)**:
1. Run `teambot run objectives/my-task.md`
2. Workflow executes across 6 agents and 14 stages
3. **Current**: Workflow completes with no cost info
4. **Target**: Summary shows total tokens, per-agent breakdown, per-stage breakdown

**Developer Journey (Interactive)**:
1. Start `teambot chat` or REPL session
2. Execute multiple agent commands (`@pm`, `@builder-1`, etc.)
3. End session with `/exit` or Ctrl+C
4. **Current**: Session ends silently
5. **Target**: Summary shows session token usage

## 4. Scope

### In Scope
* Token data capture from Copilot SDK responses (if available)
* Token data capture from Copilot CLI responses (if available)
* TokenUsage dataclass with prompt_tokens, completion_tokens, total_tokens
* Per-task token tracking in TaskResult
* Per-agent token aggregation
* Per-stage token aggregation
* Total token aggregation for orchestration runs
* End-of-run token summary display (Rich console)
* End-of-session token summary display (interactive mode)
* Token data persistence in workflow_state.json metadata
* Graceful degradation when token data unavailable
* Configuration option to disable token tracking (opt-out)

### Out of Scope (justified)
* **Dollar cost estimation** — Requires external pricing data that changes frequently; keep feature focused on tokens
* **Historical trend analysis** — Future enhancement; MVP focuses on single-run visibility
* **Budget enforcement/limits** — Future enhancement; MVP is informational only
* **Real-time streaming display** — Complex UX; summary-only is sufficient for MVP
* **Token prediction** — Future enhancement; requires training data
* **Third-party integration** — Future enhancement; focus on local display first

### Assumptions
| Assumption | Risk if Invalid | Mitigation |
|------------|-----------------|------------|
| Copilot SDK responses include token usage data | Feature shows `n/a` for all runs | Graceful degradation; document limitation |
| Token data structure is consistent across models | May need model-specific parsing | Abstract parser interface |
| workflow_state.json metadata can accommodate data | Schema migration needed | Versioned schema design |
| Performance overhead is negligible | May slow workflows | Lazy aggregation; benchmark testing |

### Constraints
| Constraint | Rationale |
|------------|-----------|
| Token data from Copilot CLI/SDK only | Source of truth; no fabrication |
| No new external dependencies | Pure Python; lightweight footprint |
| No estimation fallback | Display `n/a` if unavailable; honesty |
| Works with both client.py and sdk_client.py | Full coverage |
| No workflow disruption | Must not break existing functionality |
| Integrate with workflow_state.json | Use existing persistence |
| Enabled by default | Opt-out configuration only |

## 5. Product Overview

### Value Proposition
**For** TeamBot users **who** need to understand and optimize AI operational costs, **Operation Cost Visibility** provides token usage tracking and display **that** surfaces consumption data per agent, per stage, and per session. **Unlike** the current opaque experience, **this feature** enables informed budget management and workflow optimization.

### Differentiators
* Integrated into existing workflow—no separate tools needed
* Per-agent and per-stage granularity for optimization insights
* Graceful degradation ensures no workflow disruption
* Persisted data enables future analysis capabilities

### UX / UI
**Orchestration Run Summary** (Rich console output):
```
╭─────────────────────────────────────────────────────────────╮
│                    Token Usage Summary                       │
├─────────────────────────────────────────────────────────────┤
│  Total Tokens:     45,230 (prompt: 32,100 | completion: 13,130)
│                                                              │
│  By Agent:                                                   │
│    pm           │ ████████░░ │   8,450 (18.7%)              │
│    ba           │ ██████░░░░ │   6,120 (13.5%)              │
│    builder-1    │ ████████████ │  15,890 (35.1%)            │
│    builder-2    │ ████████░░ │   9,240 (20.4%)              │
│    reviewer     │ ████░░░░░░ │   4,030 (8.9%)               │
│    writer       │ ██░░░░░░░░ │   1,500 (3.3%)               │
│                                                              │
│  By Stage:                                                   │
│    SPEC         │ ████░░░░░░ │   4,200                      │
│    IMPLEMENTATION│ ████████████ │  28,500                   │
│    TEST         │ ████████░░ │   8,130                      │
│    REVIEW       │ ████░░░░░░ │   4,400                      │
╰─────────────────────────────────────────────────────────────╯
```

**Interactive Mode Summary** (on session exit):
```
Session Token Usage: 12,450 tokens (prompt: 9,200 | completion: 3,250)
```

**Unavailable Data Display**:
```
Token Usage Summary: n/a (token data unavailable from Copilot)
```

| UX Status: Wireframe |

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-001 | TokenUsage data model | Create `TokenUsage` dataclass with `prompt_tokens: int`, `completion_tokens: int`, `total_tokens: int` fields. All fields optional (None = unavailable). | G-001, G-008 | All | High | Dataclass exists, can be instantiated with partial data | Pure Python, no deps |
| FR-002 | SDK token extraction | Extend SDK client to extract token usage from response objects (inspect `response.data` beyond `.content`). | G-001 | All | High | Token data captured when available; None when not | Research SDK response structure |
| FR-003 | CLI token extraction | Extend CLI client to parse token usage from stdout/stderr if available. | G-001 | All | Medium | Token data captured if present; None otherwise | May not be available |
| FR-004 | TaskResult token field | Add optional `token_usage: TokenUsage | None` field to TaskResult dataclass. | G-001 | All | High | Field exists, serializes correctly | Backward compatible |
| FR-005 | Per-task tracking | Store token usage in TaskResult after each agent execution. | G-001, G-003 | All | High | Each task has token_usage populated or None | Thread through executor |
| FR-006 | Per-agent aggregation | Aggregate token usage by agent_id across all tasks. | G-003 | Workflow Designer | Medium | Accurate per-agent totals | Sum in orchestrator |
| FR-007 | Per-stage aggregation | Aggregate token usage by workflow stage. | G-004 | Workflow Designer | Medium | Accurate per-stage totals | Map tasks to stages |
| FR-008 | Total aggregation | Calculate total token usage for entire orchestration run. | G-002 | All | High | Accurate grand total | Sum of all tasks |
| FR-009 | Orchestration summary display | Display token usage summary at end of `teambot run`. Rich console format with breakdown. | G-002, G-003, G-004 | All | High | Summary appears before exit, shows totals and breakdowns | Use Rich library |
| FR-010 | Interactive session tracking | Track token usage across interactive session commands. | G-006 | Individual Developer | Medium | Accumulated session total | REPL loop integration |
| FR-011 | Interactive summary display | Display token usage summary when exiting interactive mode. | G-006 | Individual Developer | Medium | Summary on /exit or Ctrl+C | Graceful shutdown hook |
| FR-012 | Workflow state persistence | Store token tracking data in `workflow_state.json` metadata section. | G-005 | All | Medium | Data persists and loads correctly | Schema documented |
| FR-013 | Graceful degradation | When token data unavailable, display `n/a` and log warning once (not per-task). | G-007 | All | High | No crashes, clear feedback | Single warning log |
| FR-014 | Configuration option | Add `token_tracking.enabled` config option (default: true). | G-007 | All | Low | Can disable via config | teambot.json |

### Feature Hierarchy
```plain
Operation Cost Visibility
├── Data Capture Layer
│   ├── TokenUsage dataclass (FR-001)
│   ├── SDK token extraction (FR-002)
│   └── CLI token extraction (FR-003)
├── Tracking Layer
│   ├── TaskResult integration (FR-004, FR-005)
│   ├── Per-agent aggregation (FR-006)
│   ├── Per-stage aggregation (FR-007)
│   └── Total aggregation (FR-008)
├── Display Layer
│   ├── Orchestration summary (FR-009)
│   ├── Interactive tracking (FR-010)
│   └── Interactive summary (FR-011)
├── Persistence Layer
│   └── Workflow state storage (FR-012)
└── Configuration Layer
    ├── Graceful degradation (FR-013)
    └── Config option (FR-014)
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Token tracking must not significantly impact workflow execution time | <1% overhead | High | Benchmark before/after | Lazy aggregation if needed |
| NFR-002 | Reliability | Token tracking failures must not crash workflows | Zero crashes due to tracking | High | Error injection testing | Try/except all extraction |
| NFR-003 | Maintainability | Token tracking code isolated in dedicated module | Single responsibility | Medium | Code review | src/teambot/tokens/ module |
| NFR-004 | Observability | Token tracking operations logged at DEBUG level | All operations traceable | Low | Log inspection | Standard logging |
| NFR-005 | Compatibility | Must work with existing workflow_state.json files | Backward compatible | High | Load old state files | Default empty token data |
| NFR-006 | Usability | Summary display readable within 5 seconds | Clear visual hierarchy | Medium | User testing | Rich formatting |

## 8. Data & Analytics

### Inputs
| Input | Source | Format | Notes |
|-------|--------|--------|-------|
| Token usage | Copilot SDK response | SDK-specific object | Extract from response.data |
| Token usage | Copilot CLI stdout | Text (if available) | Parse structured output |
| Agent ID | Task execution context | String | From TaskResult |
| Stage | Workflow state machine | WorkflowStage enum | Current stage at execution |

### Outputs / Events
| Output | Destination | Format | Notes |
|--------|-------------|--------|-------|
| Token summary | Console (Rich) | Formatted table/panel | End of run/session |
| Token data | workflow_state.json | JSON | Persisted for analysis |
| Warning log | stderr/log file | Text | When data unavailable |

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| token_captured | After task execution | task_id, agent_id, tokens | Track capture success | Builder |
| token_unavailable | When extraction fails | task_id, agent_id, reason | Track gaps | Builder |
| summary_displayed | End of run/session | total_tokens, run_id | Confirm display | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Token capture rate | Percentage | 0% | >90% of SDK calls | Per release | Logs |
| Display reliability | Percentage | N/A | 100% runs show summary | Per release | Testing |
| Performance overhead | Milliseconds | 0ms | <50ms per run | Per release | Benchmarks |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Copilot SDK response structure | External | High | GitHub | Token data may not exist | Graceful degradation |
| WorkflowStateMachine | Internal | Medium | TeamBot | Schema changes | Metadata dict is extensible |
| TaskResult dataclass | Internal | Medium | TeamBot | Field additions | Optional field, backward compat |
| Rich library | Internal | Low | TeamBot | Already a dependency | No change needed |
| Configuration loader | Internal | Low | TeamBot | Config schema | Add optional section |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Copilot SDK does not expose token usage | High | Medium | Graceful degradation; display `n/a`; document limitation | Builder | Open |
| R-002 | Token data format varies by model | Medium | Medium | Abstract parser interface; model-specific handlers | Builder | Open |
| R-003 | Performance overhead exceeds target | Medium | Low | Lazy aggregation; batch processing; benchmark early | Builder | Open |
| R-004 | Schema changes break existing state files | Medium | Low | Versioned schema; migration logic; default empty data | Builder | Open |
| R-005 | Interactive mode exit hooks unreliable | Low | Low | Multiple hook points (signal, /exit, exception) | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
**Internal/Low Sensitivity** — Token counts are numerical aggregates with no PII or sensitive content.

### PII Handling
**None** — Token usage data contains no personally identifiable information.

### Threat Considerations
**Minimal** — Feature adds read-only metrics display; no new attack surface. Logging should avoid embedding prompts or responses (already handled).

### Regulatory / Compliance
| Regulation | Applicability | Action | Owner | Status |
|------------|---------------|--------|-------|--------|
| N/A | No regulatory requirements for token counting | None | - | Complete |

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Disable via config `token_tracking.enabled: false` | Feature flag behavior |
| Monitoring | DEBUG-level logging for all operations | Standard log aggregation |
| Alerting | N/A for MVP | Future: alert on tracking failures |
| Support | Document `n/a` display meaning | FAQ entry |
| Capacity Planning | N/A | Negligible storage/compute |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Research | TBD | SDK response structure documented | Builder |
| Implementation | TBD | All FRs implemented, tests pass | Builder |
| Review | TBD | Code review complete | Reviewer |
| Release | TBD | Merged to main, docs updated | PM |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| token_tracking.enabled | Disable token tracking if issues | true | Never (permanent config) |

### Communication Plan
- Release notes entry describing new token visibility feature
- AGENTS.md update with usage instructions
- README mention of cost visibility capability

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Does Copilot SDK response.data contain usage/token fields? | Builder | Research phase | Open |
| Q-002 | Does Copilot CLI output token info in any mode? | Builder | Research phase | Open |
| Q-003 | What is the exact structure of SDK usage data (if exists)? | Builder | Research phase | Open |

## 15. Acceptance Test Scenarios

### AT-001: Basic Orchestration Run Token Display
**Description**: User runs a complete orchestration and sees token summary at end
**Preconditions**: Copilot CLI authenticated, objective file exists
**Steps**:
1. User runs `teambot run docs/objectives/sample-task.md`
2. Workflow executes through multiple agents and stages
3. Workflow completes successfully
**Expected Result**: Token usage summary panel displayed before exit showing total tokens, per-agent breakdown, per-stage breakdown
**Verification**: Visual inspection of console output; verify panel contains numerical data or `n/a`

### AT-002: Interactive Session Token Summary
**Description**: User runs interactive session and sees token summary on exit
**Preconditions**: Copilot SDK authenticated, REPL functional
**Steps**:
1. User starts `teambot` (REPL mode)
2. User executes `@pm create a simple plan`
3. User executes `@builder-1 implement the first item`
4. User types `/exit` to end session
**Expected Result**: Token usage summary displayed showing session totals
**Verification**: Summary line appears with token count or `n/a`

### AT-003: Graceful Degradation When Data Unavailable
**Description**: System handles missing token data without crashing
**Preconditions**: Token extraction returns None (simulated or actual)
**Steps**:
1. User runs orchestration or interactive session
2. Token data is unavailable from Copilot response
3. Workflow/session continues normally
**Expected Result**: Display shows `n/a` for token values; warning logged once (not per-task); no crashes or errors
**Verification**: Check console shows `n/a`; check logs for single warning; confirm workflow completed

### AT-004: Token Data Persistence
**Description**: Token usage data is persisted in workflow state
**Preconditions**: Orchestration run completed with token data available
**Steps**:
1. User runs `teambot run docs/objectives/sample-task.md`
2. Workflow completes successfully
3. User inspects `.teambot/workflow_state.json`
**Expected Result**: Token tracking data present in `metadata.token_tracking` with documented schema
**Verification**: JSON inspection shows `total_tokens`, `by_agent`, `by_stage` fields

### AT-005: Configuration Opt-Out
**Description**: User can disable token tracking via configuration
**Preconditions**: `teambot.json` exists
**Steps**:
1. User adds `"token_tracking": {"enabled": false}` to `teambot.json`
2. User runs orchestration
3. Workflow completes
**Expected Result**: No token tracking occurs; no summary displayed; no tracking data persisted
**Verification**: Console output has no token panel; workflow_state.json has no token_tracking in metadata

### AT-006: Per-Agent Token Breakdown Accuracy
**Description**: Token counts accurately attributed to each agent
**Preconditions**: Multiple agents execute during orchestration
**Steps**:
1. User runs orchestration with multiple agent tasks
2. Workflow completes
3. User reviews token summary
**Expected Result**: Each agent (pm, ba, builder-1, builder-2, reviewer, writer) shows individual token count that sums to total
**Verification**: Sum of per-agent tokens equals total tokens displayed

## 16. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-03-03 | BA Agent | Initial specification | New |

## 17. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Problem Statement | .teambot/operation-cost-visibility/artifacts/problem_statement.md | Business problem and goals definition | N/A |
| REF-002 | Codebase | src/teambot/copilot/client.py | CopilotResult dataclass structure | N/A |
| REF-003 | Codebase | src/teambot/copilot/sdk_client.py | SDK client response handling | N/A |
| REF-004 | Codebase | src/teambot/workflow/state_machine.py | WorkflowState and metadata structure | N/A |
| REF-005 | Codebase | src/teambot/tasks/models.py | TaskResult dataclass structure | N/A |

### Citation Usage
All requirements derived from problem statement (REF-001) and constrained by existing codebase structures (REF-002 through REF-005).

## 18. Appendices

### Appendix A: Token Tracking Schema (workflow_state.json)

```json
{
  "current_stage": "COMPLETE",
  "started_at": "2026-03-03T10:00:00Z",
  "objective": "sample-task",
  "metadata": {
    "token_tracking": {
      "schema_version": "1.0",
      "total": {
        "prompt_tokens": 32100,
        "completion_tokens": 13130,
        "total_tokens": 45230
      },
      "by_agent": {
        "pm": {"prompt_tokens": 6200, "completion_tokens": 2250, "total_tokens": 8450},
        "ba": {"prompt_tokens": 4500, "completion_tokens": 1620, "total_tokens": 6120},
        "builder-1": {"prompt_tokens": 11500, "completion_tokens": 4390, "total_tokens": 15890},
        "builder-2": {"prompt_tokens": 6700, "completion_tokens": 2540, "total_tokens": 9240},
        "reviewer": {"prompt_tokens": 2500, "completion_tokens": 1530, "total_tokens": 4030},
        "writer": {"prompt_tokens": 700, "completion_tokens": 800, "total_tokens": 1500}
      },
      "by_stage": {
        "SPEC": {"prompt_tokens": 3000, "completion_tokens": 1200, "total_tokens": 4200},
        "IMPLEMENTATION": {"prompt_tokens": 20500, "completion_tokens": 8000, "total_tokens": 28500},
        "TEST": {"prompt_tokens": 5800, "completion_tokens": 2330, "total_tokens": 8130},
        "REVIEW": {"prompt_tokens": 2800, "completion_tokens": 1600, "total_tokens": 4400}
      },
      "data_availability": "full",
      "warning_logged": false
    }
  },
  "history": [...]
}
```

### Appendix B: Glossary
| Term | Definition |
|------|------------|
| Token | Unit of text processing in LLMs; approximately 4 characters or 0.75 words |
| Prompt tokens | Tokens in the input sent to the model (input_tokens) |
| Completion tokens | Tokens in the model's response (output_tokens) |
| Orchestration run | File-based execution of a multi-agent workflow via `teambot run` |
| Interactive mode | Single-agent session via `teambot` REPL |
| Workflow state | Persisted state in `.teambot/workflow_state.json` tracking execution progress |
| Graceful degradation | System continues functioning with reduced capability when data unavailable |

### Appendix C: Configuration Schema

```json
{
  "token_tracking": {
    "enabled": true
  }
}
```

Default: `{"token_tracking": {"enabled": true}}`

When disabled, no token extraction, tracking, or display occurs.

Generated 2026-03-03T00:56:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
