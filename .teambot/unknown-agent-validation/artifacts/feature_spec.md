<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Unknown Agent ID Validation - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Build

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-09 |
| Problem & Users | ✅ | None | 2026-02-09 |
| Scope | ✅ | None | 2026-02-09 |
| Requirements | ✅ | None | 2026-02-09 |
| Metrics & Risks | ✅ | None | 2026-02-09 |
| Operationalization | ✅ | None | 2026-02-09 |
| Finalization | ✅ | None | 2026-02-09 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary
### Context
TeamBot is a CLI tool that orchestrates a team of 6 specialized AI agent personas (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`). Users direct commands to agents using the `@agent-id` syntax in the REPL. The set of agents is fixed and well-defined; users expect that only these 6 agents exist.

### Core Opportunity
Close a validation gap that allows unknown agent IDs to be silently accepted and executed, causing confusing behaviour. This is a targeted bug fix that improves reliability and user trust.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Reject unknown agent IDs with a clear error message before any task is dispatched | Reliability | Unknown agents silently accepted on advanced paths | 100% rejection with error message | Immediate | P0 |
| G-002 | Prevent ghost agent entries in the status window | UX Quality | AgentStatusManager auto-creates entries for any ID | No entries created for invalid IDs | Immediate | P1 |
| G-003 | Ensure consistent validation across all command shapes | Consistency | Only simple-path commands validated | All paths validated (simple, multi-agent, pipeline, background, $ref) | Immediate | P0 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Fail fast on bad input | Zero tasks dispatched for unknown agents | P0 | Builder |
| Single source of truth | All validation reads from `VALID_AGENTS` in `router.py` | P0 | Builder |

## 2. Problem Definition
### Current Situation
The REPL has two command routing paths:

1. **Simple path** — single-agent, synchronous, no `$ref` commands — routes through `AgentRouter._route_agent()` which validates against `VALID_AGENTS`. This path **correctly rejects** unknown agents.
2. **Advanced path** — multi-agent, pipeline, background, or `$ref` commands — routes directly to `TaskExecutor.execute()` which performs **no agent ID validation**. Unknown agents are silently accepted.

When an unknown agent reaches the execution layer, `AgentRunner` catches the `ValueError` from persona resolution and silently falls back to the **builder** persona. Meanwhile, `AgentStatusManager` auto-creates status entries for any agent ID it receives.

### Problem Statement
Users who mistype an agent ID (e.g., `@buidler-1` instead of `@builder-1`) or invent a non-existent agent (e.g., `@architect`) receive no error. Instead, the command is silently executed by the builder persona under the wrong name, and the ghost agent appears in the status window. This is confusing, misleading, and inconsistent with the simple-path behaviour which correctly rejects the same input.

### Root Causes
* **TaskExecutor bypass** (`loop.py:323-336`): The REPL loop routes advanced commands directly to `TaskExecutor.execute()`, skipping the router's `VALID_AGENTS` check entirely. None of `_execute_simple()`, `_execute_multiagent()`, or `_execute_pipeline()` validate agent IDs.
* **AgentStatusManager auto-creation** (`agent_state.py:153-210`): The `_update()`, `set_idle()`, and `set_model()` methods all auto-create status entries for any agent ID without checking validity.
* **Silent persona fallback** (`agent_runner.py:55-59`): The `AgentRunner` catches persona resolution failures and falls back to the builder persona without surfacing the error.

### Impact of Inaction
* Users will continue to experience silent failures when mistyping agent IDs, leading to wasted time and confusion.
* Ghost agents will accumulate in the status window, eroding trust in the tool's accuracy.
* The inconsistency between simple and advanced paths will continue to surprise users with unpredictable behaviour.

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| TeamBot End User | Direct tasks to the correct specialist agent | Typos in agent IDs are silently accepted; wrong persona runs the task; ghost agents appear in status | High — directly affected by the bug |
| TeamBot Developer | Maintain predictable, consistent REPL behaviour | Two code paths with different validation rules; debugging ghost agent entries | Medium — increased support burden |

### Journeys (Optional)
**Current (broken) journey:**
1. User types `@buidler-1 implement the login page` (typo)
2. Command is parsed → `agent_ids = ["buidler-1"]` → no syntax error
3. REPL loop routes to simple path → router validates → **rejects** ✅

**But if background:**
1. User types `@buidler-1 implement the login page &` (typo + background flag)
2. Command is parsed → `agent_ids = ["buidler-1"]`, `background = True`
3. REPL loop routes to **advanced path** → TaskExecutor → **no validation** ❌
4. AgentRunner falls back to builder persona → executes under wrong name
5. AgentStatusManager creates "buidler-1" entry in status window

**Desired journey (all paths):**
1. User types `@buidler-1 implement the login page &`
2. Validation rejects immediately: `Unknown agent: 'buidler-1'. Valid agents: pm, ba, writer, builder-1, builder-2, reviewer`
3. No task dispatched, no status entry created
4. User corrects typo and re-submits

## 4. Scope
### In Scope
* Add agent ID validation to `TaskExecutor.execute()` before any task dispatch
* Add agent ID validation guard to `AgentStatusManager` auto-creation methods
* Validate all agent IDs in multi-agent, pipeline, background, and `$ref` command paths
* Resolve agent aliases before validation (using existing `AGENT_ALIASES`)
* Return user-friendly error messages listing valid agents
* New tests covering unknown agent rejection for all command shapes

### Out of Scope (justify if empty)
* Dynamic agent registration or user-defined agents (future feature, not needed for this fix)
* Changes to the parser's syntactic regex (parser validates syntax, not semantics)
* Refactoring the dual routing architecture (this is a targeted fix, not an architectural change)
* Changes to the simple-path router validation (already works correctly)
* UI/UX changes to the status window beyond preventing ghost entries

### Assumptions
* The 6-agent set (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`) is static for the current release
* Agent aliases (`project_manager` → `pm`, `business_analyst` → `ba`, `technical_writer` → `writer`) must also be accepted as valid
* The `VALID_AGENTS` set in `router.py` is the single source of truth and must not be duplicated
* The error message format is for human consumption, not machine parsing

### Constraints
* Minimal changes — this is a targeted bug fix
* Must not break the existing simple-path router validation
* Must not introduce circular import issues (follow existing local-import pattern in executor.py)
* All existing tests must continue to pass

## 5. Product Overview
### Value Proposition
TeamBot users get immediate, clear feedback when they mistype or invent an agent ID, regardless of which command syntax they use. This eliminates a class of silent failures that waste time and erode trust.

### Differentiators (Optional)
* Consistent validation across all command shapes (simple, multi-agent, pipeline, background)
* Actionable error messages that list valid agents for quick self-correction
* Fail-fast design that prevents wasted compute on invalid commands

### UX / UI (Conditional)
Error message format: `Unknown agent: '{agent_id}'. Valid agents: pm, ba, writer, builder-1, builder-2, reviewer` | UX Status: Defined

For multi-agent commands with mixed valid/invalid IDs: `Unknown agent: '{invalid_id}'. Valid agents: pm, ba, writer, builder-1, builder-2, reviewer` (reject the entire command, do not partially execute)

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | TaskExecutor agent ID validation | `TaskExecutor.execute()` validates all agent IDs in `command.agent_ids` against `VALID_AGENTS` (after alias resolution) before dispatching any task. Returns error result for unknown agents. | G-001, G-003 | End User | P0 | `@unknown query` via advanced path returns error with valid agent list; no task created | Must use `VALID_AGENTS` from `router.py` and `AGENT_ALIASES` for resolution |
| FR-002 | Multi-agent validation | When a command targets multiple agents (e.g., `@builder-1,unknown query`), all agent IDs are validated before any task is dispatched. If any ID is invalid, the entire command is rejected. | G-001, G-003 | End User | P0 | `@pm,unknown query` returns error; no tasks created for any agent | No partial execution |
| FR-003 | Pipeline validation | Pipeline commands (e.g., `@unknown -> @pm query`) validate all agent IDs across all pipeline stages before execution begins. | G-001, G-003 | End User | P0 | `@unknown -> @pm query` returns error; no pipeline stages execute | Validation before first stage |
| FR-004 | Background command validation | Background commands (e.g., `@unknown query &`) validate agent IDs before spawning background tasks. | G-001, G-003 | End User | P0 | `@unknown query &` returns error; no background task created | Same validation as foreground |
| FR-005 | AgentStatusManager guard | `AgentStatusManager` methods (`_update`, `set_idle`, `set_model`) do not auto-create status entries for agent IDs not in `VALID_AGENTS`. | G-002 | End User, Developer | P1 | Calling `set_idle("fake-agent")` does not create a status entry | Defence-in-depth; primary validation is in FR-001 |
| FR-006 | Alias resolution in validation | Agent aliases (`project_manager`, `business_analyst`, `technical_writer`) are resolved to canonical IDs before validation, so aliased commands continue to work. | G-003 | End User | P0 | `@project_manager query` succeeds; `@proj_mgr query` is rejected | Uses existing `AGENT_ALIASES` dict |
| FR-007 | Error message format | Error messages include the invalid agent ID and a sorted list of valid agent IDs: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer` | G-001 | End User | P1 | Error message matches expected format string | Sorted for consistency |

### Feature Hierarchy (Optional)
```plain
Unknown Agent Validation
├── TaskExecutor Validation (FR-001)
│   ├── Simple execute path
│   ├── Multi-agent path (FR-002)
│   ├── Pipeline path (FR-003)
│   └── Background path (FR-004)
├── Alias Resolution (FR-006)
├── Error Messaging (FR-007)
└── AgentStatusManager Guard (FR-005)
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Validation must add negligible latency | < 1ms per command | P1 | Set membership check is O(1) | VALID_AGENTS is a Python set |
| NFR-002 | Maintainability | Valid agent list must be defined in exactly one place | Zero duplication of VALID_AGENTS | P0 | Code review; grep for hardcoded agent lists | Import from `router.py` |
| NFR-003 | Reliability | No false rejections of valid agent IDs or aliases | 0 false rejections | P0 | Test all 6 agents + 3 aliases | Regression tests required |
| NFR-004 | Maintainability | No new circular import issues | Zero import errors at startup | P0 | Application starts cleanly | Follow existing local-import pattern |
| NFR-005 | Testability | All validation paths covered by automated tests | 100% path coverage for new code | P1 | pytest coverage report | New tests for each FR |

## 8. Data & Analytics (Conditional)
### Inputs
* `command.agent_ids`: List of agent ID strings from the parsed command
* `VALID_AGENTS`: Set of valid canonical agent IDs from `router.py`
* `AGENT_ALIASES`: Dict mapping aliases to canonical IDs from `router.py`

### Outputs / Events
* `ExecutionResult` with `success=False` and error message for invalid agents
* No status events emitted for invalid agents (FR-005)

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| N/A | N/A | N/A | No telemetry needed for a validation fix | N/A |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Unknown agent commands rejected | Functional | 0% (advanced path) | 100% (all paths) | Immediate | Test suite |
| Ghost agent status entries | Functional | Created for any ID | Never created for invalid IDs | Immediate | Test suite |
| Existing test suite passing | Regression | All pass | All pass | Immediate | CI |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `VALID_AGENTS` set in `router.py` | Internal | High | Existing code | None — already exists | N/A |
| `AGENT_ALIASES` dict in `router.py` | Internal | Medium | Existing code | None — already exists | N/A |
| Existing test infrastructure (pytest) | Internal | Medium | Existing | None | N/A |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Circular import when TaskExecutor imports from router.py | Medium | Low | Follow existing pattern: use local imports inside methods (already done for `$ref` validation at executor.py:199) | Builder | Mitigated |
| R-002 | Future agent additions require updating VALID_AGENTS | Low | Medium | VALID_AGENTS is already the single source of truth; no new maintenance burden introduced | N/A | Accepted |
| R-003 | AgentStatusManager guard could mask legitimate status updates during startup | Low | Low | Only guard auto-creation in `_update`/`set_idle`/`set_model`; explicit `initialize()` or constructor-based setup is unaffected | Builder | Mitigated |

## 11. Privacy, Security & Compliance
### Data Classification
No user data involved. Agent IDs are system-internal identifiers.

### PII Handling
N/A — no PII is processed, stored, or transmitted by this feature.

### Threat Considerations
N/A — this is an input validation fix that reduces the attack surface by rejecting unexpected input.

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| N/A | Not applicable | None | N/A | N/A |

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard release — no special deployment steps | Part of next version |
| Rollback | Standard rollback — revert commit | No data migration |
| Monitoring | No new monitoring needed | Validation is synchronous and local |
| Alerting | No new alerting needed | Errors are surfaced to user directly |
| Support | No new support procedures | Error message is self-explanatory |
| Capacity Planning | No impact | Validation is O(1) set lookup |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|--------------|-------|
| Implementation | All FRs implemented, all tests pass | Builder |
| Review | Code review approved, no regressions | Reviewer |
| Merge | CI green, all acceptance tests pass | PM |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| N/A | No feature flag needed — this is a bug fix that should always be active | N/A | N/A |

### Communication Plan (Optional)
Mention in release notes: "Fixed: Unknown agent IDs are now rejected with a helpful error message across all command types."

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| None | All questions resolved | N/A | N/A | N/A |

## Acceptance Test Scenarios

### AT-001: Simple Unknown Agent Command (Simple Path)
**Description**: User sends a command to an unknown agent via the simple (single-agent, synchronous) path
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@unknown-agent do something`
2. Observe REPL output
**Expected Result**: Error message: `Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
**Verification**: No task dispatched; no status entry created for "unknown-agent"

### AT-002: Unknown Agent in Background Command (Advanced Path)
**Description**: User sends a background command to an unknown agent, which previously bypassed validation
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@unknown-agent do something &`
2. Observe REPL output
**Expected Result**: Error message listing valid agents; no background task spawned
**Verification**: Status window does not show "unknown-agent"; no task result produced

### AT-003: Multi-Agent Command with One Invalid ID
**Description**: User sends a multi-agent command where one of the agent IDs is invalid
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@builder-1,fake-agent implement the feature`
2. Observe REPL output
**Expected Result**: Error message identifying "fake-agent" as unknown; entire command rejected (builder-1 does not execute)
**Verification**: No task dispatched for either agent; no status entries created

### AT-004: Pipeline Command with Unknown Agent
**Description**: User creates a pipeline where one stage targets an unknown agent
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@fake -> @pm create a plan`
2. Observe REPL output
**Expected Result**: Error message identifying "fake" as unknown; no pipeline stages execute
**Verification**: No tasks dispatched; PM does not receive any input

### AT-005: Valid Alias Continues to Work
**Description**: User uses a valid agent alias that should resolve to a canonical agent ID
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@project_manager create a project plan`
2. Observe REPL output
**Expected Result**: Command is accepted and routed to the `pm` agent; plan is produced
**Verification**: PM agent executes successfully; status shows "pm" as active

### AT-006: All Six Valid Agents Work (Regression)
**Description**: Verify that all 6 valid agents continue to accept commands
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm plan this`
2. User enters: `@ba analyze this`
3. User enters: `@writer document this`
4. User enters: `@builder-1 build this`
5. User enters: `@builder-2 build that`
6. User enters: `@reviewer review this`
**Expected Result**: All 6 commands are accepted and dispatched to the correct agent
**Verification**: Each agent produces output; no validation errors

### AT-007: Typo Near Valid Agent ID
**Description**: User makes a common typo that is close to but not exactly a valid agent ID
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@buidler-1 implement login`
2. Observe REPL output
**Expected Result**: Error message: `Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
**Verification**: No task dispatched; user can correct the typo and re-submit

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-09 | BA Agent | Initial specification | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | `.teambot/unknown-agent-validation/artifacts/problem_statement.md` | Root cause analysis and impact assessment | N/A |
| REF-002 | Source Code | `src/teambot/repl/router.py:19-27` | `VALID_AGENTS` set and `AGENT_ALIASES` dict — single source of truth | N/A |
| REF-003 | Source Code | `src/teambot/repl/loop.py:323-336` | REPL loop routing decision (simple vs advanced path) | N/A |
| REF-004 | Source Code | `src/teambot/tasks/executor.py:162-183` | TaskExecutor.execute() — missing validation point | N/A |
| REF-005 | Source Code | `src/teambot/ui/agent_state.py:153-210` | AgentStatusManager auto-creation methods | N/A |

### Citation Usage
All code references verified against current `main` branch as of 2026-02-09.

## 17. Appendices (Optional)
### Glossary
| Term | Definition |
|------|-----------|
| Simple path | REPL routing for single-agent, synchronous, no-reference commands — goes through `AgentRouter` |
| Advanced path | REPL routing for multi-agent, pipeline, background, or `$ref` commands — goes through `TaskExecutor` |
| Ghost agent | A status entry created for an agent ID that does not correspond to any defined persona |
| Alias | An alternate name for a valid agent (e.g., `project_manager` → `pm`) |

### Technical Stack
* **Language**: Python
* **Testing**: pytest (follow existing patterns)
* **Approach**: Bug fix — test-after (validate fix with new tests)

### Additional Notes
This specification was derived from codebase analysis of the REPL subsystem. The fix is intentionally minimal — it closes the validation gap without refactoring the dual-path routing architecture.

Generated 2026-02-09T22:48:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
