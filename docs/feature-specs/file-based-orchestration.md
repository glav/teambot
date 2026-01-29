<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# File-Based Orchestration - Feature Specification Document
Version 1.0 | Status **Complete** | Owner TBD | Team TeamBot | Completed 2026-01-29 | Lifecycle Production

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-29 |
| Problem & Users | 100% | None | 2026-01-29 |
| Scope | 100% | None | 2026-01-29 |
| Requirements | 100% | None | 2026-01-29 |
| Metrics & Risks | 100% | None | 2026-01-29 |
| Research | 100% | None | 2026-01-29 |
| Test Strategy | 100% | None | 2026-01-29 |
| Task Planning | 100% | None | 2026-01-29 |
| Implementation | 100% | None | 2026-01-29 |
| Finalization | 100% | None | 2026-01-29 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot has the foundational infrastructure for multi-agent orchestration (orchestrator, workflow state machine, agent runner, message routing) but lacks an **execution loop** that drives agents through the 13-stage workflow autonomously. Currently, `teambot run objectives/file.md` reads the file but exits with "File-based orchestration not yet implemented."

### Core Opportunity
Implement the autonomous execution loop that:
1. Parses an objective file containing goals and success criteria
2. Drives the 6-agent team (pm, ba, writer, builder-1, builder-2, reviewer) through workflow stages
3. Implements review-action iteration loops (max 4 iterations)
4. Runs for up to 8 hours or until objectives are achieved
5. Provides live status updates with cancellation support

This transforms TeamBot from an interactive tool into an **autonomous development assistant** capable of completing complex multi-day objectives.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-FBO-001 | Enable autonomous objective completion | Core | Manual agent calls only | Fully autonomous workflow | MVP | P0 |
| G-FBO-002 | Support iterative review cycles | Quality | No review loops | 4-iteration review cycles | MVP | P0 |
| G-FBO-003 | Provide live progress visibility | UX | No progress tracking | Real-time status updates | MVP | P0 |
| G-FBO-004 | Support graceful cancellation | Control | No cancellation | Safe interrupt with state save | MVP | P1 |
| G-FBO-005 | Enforce time limits | Safety | Unlimited execution | 8-hour maximum runtime | MVP | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement execution loop | Objective file drives autonomous workflow | P0 | TBD |
| Parse objective files | Goals, success criteria, constraints extracted | P0 | TBD |
| Implement review iterations | Max 4 cycles per review stage | P0 | TBD |
| Add progress display | Real-time status in terminal | P0 | TBD |
| Support cancellation | Ctrl+C saves state and exits cleanly | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Infrastructure exists**: Orchestrator, AgentRunner, WorkflowStateMachine, MessageRouter all implemented
- **No execution driver**: Nothing connects these components into an autonomous loop
- **No objective parsing**: Files are read but not parsed for structure
- **No review iteration**: Workflow advances linearly without feedback loops
- **No progress display**: Users have no visibility into autonomous execution

### Problem Statement
TeamBot cannot autonomously execute multi-agent workflows. Users must manually invoke individual agents and manage workflow progression. There is no mechanism to define objectives, track progress, iterate on reviews, or enforce time limits. This makes TeamBot unsuitable for its core use case: autonomous development task completion.

### Root Causes
* Execution loop intentionally deferred to prioritize foundation infrastructure
* Review iteration logic requires task-result-feedback cycle not yet designed
* Objective file format not defined
* Progress display requires integration with existing UI components

### Impact of Inaction
* TeamBot cannot fulfill its primary value proposition
* Users cannot delegate multi-step development tasks
* Infrastructure investments remain unrealized
* No path to "daily objectives" workflow

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Solo Developer | Delegate routine tasks overnight | Manual multi-step processes | High - primary user |
| Team Lead | Assign daily objectives to AI team | Can't batch work for AI agents | High - efficiency |
| DevOps Engineer | Automate repetitive setup tasks | Manual intervention required | Medium - automation |

### Journeys
1. **Daily Objective Flow**: User writes objectives.md → runs `teambot run objectives.md` → checks progress occasionally → finds completed work next morning
2. **Supervised Flow**: User starts orchestration → monitors live status → intervenes if needed → cancels or lets complete
3. **Review Iteration Flow**: Agent submits work → reviewer finds issues → agent addresses → reviewer approves (or repeats up to 4x)

---

## 4. Scope

### In Scope
* **Objective file parsing**: Extract goals, success criteria, constraints from markdown
* **Execution loop**: Drive workflow through all 13 stages autonomously
* **Agent task routing**: Assign tasks to appropriate agents per stage
* **Review iteration**: Loop task→review→action up to 4 times per review stage
* **Progress display**: Live status updates during execution
* **Cancellation**: Ctrl+C graceful shutdown with state persistence
* **Time limits**: 8-hour maximum execution time
* **State persistence**: Resume interrupted runs
* **History logging**: All agent outputs saved to `.teambot/history/`

### Out of Scope
* Multi-repository orchestration
* Cloud/remote agent execution
* Custom workflow stage definitions
* Real-time collaboration (multiple users)
* Cost estimation/budgeting for LLM calls
* Parallel stage execution (stages remain sequential)

### Assumptions
* Copilot CLI is available and authenticated
* Single Git repository context
* Sufficient local resources for 6 concurrent agent processes
* User has write access to working directory

### Constraints
* Maximum 8 hours execution time (configurable)
* Maximum 4 iterations per review cycle
* Sequential workflow stages (no parallel stages)
* Single objective file per run

---

## 5. Product Overview

### Value Proposition
File-based orchestration transforms TeamBot from an interactive tool into an **autonomous development agent** that can work on complex objectives over extended periods. Users can define a day's worth of goals and let TeamBot work through them systematically, with built-in quality gates through review iterations.

### Differentiators
* **Multi-agent collaboration**: 6 specialized personas working together
* **Review iteration loops**: Quality enforcement through reviewer feedback
* **Prescriptive workflow**: Proven 13-stage software development process
* **Time-bounded execution**: Safe 8-hour limits prevent runaway costs
* **Stateful execution**: Can resume interrupted runs

### UX / UI

**Objective File Format:**
```markdown
# Objective: Implement User Authentication

## Goals
1. Add login/logout functionality to the web app
2. Implement JWT token-based session management
3. Create user registration flow

## Success Criteria
- [ ] Login form validates credentials against database
- [ ] JWT tokens expire after 24 hours
- [ ] Registration requires email verification
- [ ] All auth endpoints have >80% test coverage

## Constraints
- Must use existing PostgreSQL database
- Must integrate with current session middleware
- No third-party auth providers (in-house only)

## Context
- Existing codebase uses Express.js
- User table already exists with email/password_hash columns
- See docs/architecture.md for system overview
```

**Progress Display (in terminal):**
```
╭─ TeamBot Orchestration ─────────────────────────────────────────╮
│ Objective: Implement User Authentication                        │
│ Runtime: 02:34:15 / 08:00:00                                    │
│ Stage: IMPLEMENTATION (7/13)                                    │
├─────────────────────────────────────────────────────────────────┤
│ Agents                                                          │
│ ● pm         idle                                               │
│ ● ba         idle                                               │
│ ● writer     idle                                               │
│ ◉ builder-1  running → implementing login endpoint...           │
│ ● builder-2  idle                                               │
│ ● reviewer   idle                                               │
├─────────────────────────────────────────────────────────────────┤
│ Stage Progress                                                  │
│ ✓ Setup           ✓ Spec Review     ○ Impl Review               │
│ ✓ Business Prob   ✓ Research        ○ Test                      │
│ ✓ Spec            ✓ Test Strategy   ○ Post Review               │
│                   ✓ Plan            ○ Complete                  │
│                   ✓ Plan Review                                 │
├─────────────────────────────────────────────────────────────────┤
│ Current Activity                                                │
│ [14:23:45] builder-1: Creating auth middleware...               │
│ [14:24:12] builder-1: Writing JWT token generation...           │
│ [14:25:01] builder-1: Task completed: login endpoint            │
╰─────────────────────────────────────────────────────────────────╯
Press Ctrl+C to cancel (state will be saved)
```

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance |
|-------|-------|-------------|-------|----------|------------|
| FR-FBO-001 | Objective File Parsing | Parse markdown objective files to extract goals, success criteria, constraints, and context | G-FBO-001 | P0 | Goals, criteria, constraints extracted as structured data |
| FR-FBO-002 | Execution Loop | Main loop that drives workflow through stages by assigning tasks to agents | G-FBO-001 | P0 | Workflow advances through all 13 stages without manual intervention |
| FR-FBO-003 | Stage-to-Agent Routing | Route tasks to appropriate agents based on workflow stage persona rules | G-FBO-001 | P0 | Tasks assigned only to allowed personas per stage |
| FR-FBO-004 | Agent Task Execution | Agents execute tasks via Copilot CLI and return results | G-FBO-001 | P0 | Tasks execute with output captured and logged |
| FR-FBO-005 | Review Iteration Loop | For review stages, iterate task→review→action up to 4 times until approved | G-FBO-002 | P0 | Reviews iterate max 4 times, stop on failure |
| FR-FBO-006 | Iteration Counter | Track iteration count per review stage, enforce max 4 limit | G-FBO-002 | P0 | Counter increments, stops at 4 regardless of review outcome |
| FR-FBO-007 | Review Feedback Routing | Route reviewer feedback back to original agent for action | G-FBO-002 | P0 | Feedback message reaches agent, agent addresses issues |
| FR-FBO-008 | Progress Display | Live terminal display showing current stage, agent status, elapsed time | G-FBO-003 | P0 | Display updates in real-time during execution |
| FR-FBO-009 | Activity Log | Scrolling log of recent agent activities in progress display | G-FBO-003 | P1 | Last 5-10 activities visible with timestamps |
| FR-FBO-010 | Cancellation Handler | Ctrl+C triggers graceful shutdown, saves state, exits cleanly | G-FBO-004 | P0 | State persisted, can resume later, no data loss |
| FR-FBO-011 | State Persistence | Save workflow state, current stage, iteration counts to disk | G-FBO-004 | P0 | State file updated after each significant event |
| FR-FBO-012 | Resume Capability | Resume interrupted run from saved state | G-FBO-004 | P1 | `teambot run --resume` continues from last state |
| FR-FBO-013 | Time Limit Enforcement | Stop execution after configurable max time (default 8 hours) | G-FBO-005 | P0 | Execution stops at time limit, state saved |
| FR-FBO-014 | Time Remaining Display | Show elapsed and remaining time in progress display | G-FBO-005 | P1 | Time visible and updates every second |
| FR-FBO-015 | History Logging | Save all agent task executions to `.teambot/history/` with frontmatter | G-FBO-001 | P0 | Each task creates timestamped markdown file |
| FR-FBO-016 | Artifact Collection | Collect stage artifacts (specs, plans, reviews) in workflow state | G-FBO-001 | P1 | Artifacts referenced in state, files in `.teambot/` |
| FR-FBO-017 | Success Criteria Tracking | Track completion status of success criteria from objective file | G-FBO-001 | P2 | Criteria checklist updated as items verified |
| FR-FBO-018 | Error Recovery | Handle agent failures gracefully, retry or skip with logging | G-FBO-001 | P1 | Failures logged, workflow continues where possible |
| FR-FBO-019 | Parallel Agent Execution | builder-1 and builder-2 can execute subtasks concurrently during IMPLEMENTATION stage | G-FBO-001 | P0 | Tasks partitioned, assigned in parallel, results merged |
| FR-FBO-020 | Review Failure Handling | When 4 review iterations fail, stop with error summary and suggestions | G-FBO-002 | P0 | Clear error message, failure summary, reviewer suggestions displayed |
| FR-FBO-021 | Failure Report Generation | Generate detailed failure report with all iteration feedback | G-FBO-002 | P0 | Report saved to `.teambot/failures/` with full context |

### Feature Hierarchy
```
File-Based Orchestration
├── Objective Parsing (FR-001)
├── Execution Engine
│   ├── Main Loop (FR-002)
│   ├── Agent Routing (FR-003)
│   ├── Task Execution (FR-004)
│   ├── Parallel Execution (FR-019)
│   └── Error Recovery (FR-018)
├── Review Iteration System
│   ├── Iteration Loop (FR-005)
│   ├── Counter/Limits (FR-006)
│   ├── Feedback Routing (FR-007)
│   ├── Failure Handling (FR-020)
│   └── Failure Reports (FR-021)
├── Progress & Display
│   ├── Progress Display (FR-008)
│   ├── Activity Log (FR-009)
│   └── Time Display (FR-014)
├── State Management
│   ├── Cancellation (FR-010)
│   ├── Persistence (FR-011)
│   └── Resume (FR-012)
├── Time Management
│   └── Enforcement (FR-013)
└── Logging & Artifacts
    ├── History Logging (FR-015)
    ├── Artifact Collection (FR-016)
    └── Success Tracking (FR-017)
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Target | Priority |
|--------|----------|-------------|--------|----------|
| NFR-FBO-001 | Performance | Workflow stage transitions | < 5 seconds | P0 |
| NFR-FBO-002 | Performance | Progress display refresh | < 1 second | P0 |
| NFR-FBO-003 | Reliability | State save frequency | After every agent task completion | P0 |
| NFR-FBO-004 | Reliability | Crash recovery | Resume from last saved state | P1 |
| NFR-FBO-005 | Resource | Memory usage | < 500MB for orchestrator + 6 agents | P1 |
| NFR-FBO-006 | Resource | CPU usage | < 50% during idle periods | P2 |
| NFR-FBO-007 | Scalability | Concurrent objectives | 1 per directory (single tenant) | P0 |
| NFR-FBO-008 | Observability | Log level support | DEBUG, INFO, WARNING, ERROR | P1 |

---

## 8. Technical Approach

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    Execution Loop (new)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Parse objective file → extract goals, criteria       │   │
│  │ 2. Initialize workflow state (or resume)                │   │
│  │ 3. For each stage in workflow:                          │   │
│  │    a. Determine task from stage + objective             │   │
│  │    b. Select agent(s) for stage                         │   │
│  │    c. Execute task via agent                            │   │
│  │    d. If review stage: iterate until approved (max 4)   │   │
│  │    e. Collect artifacts, advance workflow               │   │
│  │ 4. Until complete or timeout or cancelled               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Orchestrator │    │ AgentRunner  │    │ Progress     │
│ (existing)   │◄──►│ (existing)   │    │ Display (new)│
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │
        ▼                    ▼
┌──────────────┐    ┌──────────────┐
│ Workflow     │    │ History      │
│ StateMachine │    │ Manager      │
│ (existing)   │    │ (existing)   │
└──────────────┘    └──────────────┘
```

### New Components
1. **ObjectiveParser**: Parse markdown objective files into structured data
2. **ExecutionLoop**: Main driver that coordinates workflow execution
3. **ReviewIterator**: Manages review→feedback→action cycles
4. **ProgressDisplay**: Terminal UI for live progress updates
5. **TimeManager**: Tracks elapsed time, enforces limits

### Integration Points
- **Orchestrator**: Use existing `assign_task()`, `advance_workflow()`
- **AgentRunner**: Use existing `_execute_task()` with Copilot CLI
- **WorkflowStateMachine**: Use existing state persistence
- **HistoryManager**: Use existing history file creation

### Review Iteration Algorithm
```python
def execute_review_stage(stage, max_iterations=4):
    for iteration in range(1, max_iterations + 1):
        # 1. Execute the work (implementation, spec, plan)
        work_result = execute_work_task(stage)
        
        # 2. Execute review
        review_result = execute_review_task(work_result)
        
        # 3. Check if approved
        if review_result.approved:
            return StageResult.APPROVED
        
        # 4. Route feedback to worker for next iteration
        feedback = review_result.feedback
        prepare_next_iteration(feedback)
    
    # Max iterations reached - STOP with error
    return StageResult.FAILED_MAX_ITERATIONS

def handle_review_failure(stage, iteration_history):
    """Handle review stage that exhausted all iterations."""
    # 1. Generate failure summary
    summary = generate_failure_summary(iteration_history)
    
    # 2. Collect reviewer suggestions from all iterations
    suggestions = collect_review_suggestions(iteration_history)
    
    # 3. Save failure report to artifacts
    save_failure_report(stage, summary, suggestions)
    
    # 4. Stop workflow execution
    raise ReviewFailureError(
        stage=stage,
        iterations=len(iteration_history),
        summary=summary,
        suggestions=suggestions
    )
```

### Parallel Agent Execution
```python
def execute_parallel_stage(stage, agents=['builder-1', 'builder-2']):
    """Execute stage with multiple agents in parallel."""
    # 1. Partition work into subtasks
    subtasks = partition_work_for_agents(stage.task, len(agents))
    
    # 2. Assign subtasks to agents concurrently
    futures = []
    for agent, subtask in zip(agents, subtasks):
        future = assign_task_async(agent, subtask)
        futures.append(future)
    
    # 3. Wait for all agents to complete
    results = await asyncio.gather(*futures)
    
    # 4. Merge results
    return merge_agent_results(results)
```

---

## 9. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM costs exceed expectations | Medium | High | Time limits, iteration caps, cost tracking |
| Review loops never approve | Medium | High | Max 4 iterations, stop with failure summary |
| Agent crashes mid-workflow | Medium | High | State persistence, error recovery |
| Copilot CLI unavailable | Low | High | Graceful degradation, skip mode |
| 8-hour limit too short | Low | Medium | Configurable via environment/config |
| Memory leak during long runs | Medium | Medium | Process isolation, periodic cleanup |
| Parallel agent conflicts | Low | Medium | Task partitioning, separate work areas |

---

## 10. Open Questions

| ID | Question | Status | Decision |
|----|----------|--------|----------|
| OQ-1 | Should parallel agent execution be supported (e.g., builder-1 and builder-2 on same stage)? | Resolved | Yes - parallel execution for builder agents |
| OQ-2 | What happens if all 4 review iterations fail? | Resolved | Stop with error message, failure summary, and review suggestions |
| OQ-3 | How to handle multi-file objectives (e.g., objectives/*.md)? | Resolved | Single file per run for MVP |
| OQ-4 | Should success criteria be automatically verified? | Resolved | Track manually for MVP, auto-verify as enhancement |

---

## 11. Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Objective completion rate | 0% | 70%+ | Objectives fully completed / total runs |
| Average time to completion | N/A | < 4 hours | Clock time for typical objective |
| Review iteration efficiency | N/A | < 2.5 avg | Average iterations per review stage |
| Cancellation recovery rate | N/A | 100% | Successful resumes / cancellations |

---

## 12. Milestones

| Milestone | Description | Target |
|-----------|-------------|--------|
| M1: Objective Parsing | Parse files, extract structure | TBD |
| M2: Basic Execution Loop | Drive through stages, no review iteration | TBD |
| M3: Review Iteration | Implement review feedback loops | TBD |
| M4: Progress Display | Live terminal UI | TBD |
| M5: State Management | Cancellation, persistence, resume | TBD |
| M6: Polish & Testing | Error handling, edge cases, tests | TBD |

---

## Appendix A: Objective File Schema

```yaml
# Parsed structure from markdown objective file
objective:
  title: string           # From H1 heading
  goals: list[string]     # From ## Goals section
  success_criteria:       # From ## Success Criteria section
    - description: string
      completed: boolean
  constraints: list[string]  # From ## Constraints section
  context: string         # From ## Context section (optional)
  priority: string        # From ## Priority section (optional)
  deadline: datetime      # From ## Deadline section (optional)
```

---

## Appendix B: State File Schema

```json
{
  "objective_file": "objectives/auth.md",
  "objective_title": "Implement User Authentication",
  "started_at": "2026-01-29T08:00:00Z",
  "elapsed_seconds": 9255,
  "max_seconds": 28800,
  "current_stage": "IMPLEMENTATION",
  "stage_history": [...],
  "review_iterations": {
    "SPEC_REVIEW": 2,
    "PLAN_REVIEW": 1,
    "IMPLEMENTATION_REVIEW": 0
  },
  "success_criteria_status": {
    "Login form validates credentials": false,
    "JWT tokens expire after 24 hours": true
  },
  "artifacts": {
    "problem_statement": ".teambot/artifacts/problem_statement.md",
    "feature_spec": ".teambot/artifacts/feature_spec.md"
  },
  "status": "running"
}
```

---

## Appendix C: Review Stage Mapping

| Review Stage | Work Stage | Worker Personas | Reviewer Personas |
|--------------|------------|-----------------|-------------------|
| SPEC_REVIEW | SPEC | ba, writer | reviewer, pm |
| PLAN_REVIEW | PLAN | pm, builder | reviewer, pm |
| IMPLEMENTATION_REVIEW | IMPLEMENTATION | builder | reviewer |
| POST_REVIEW | (all) | (varies) | pm, reviewer |
