<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# TeamBot - Feature Specification Document
Version 0.2 | Status Complete | Owner TBD | Team TBD | Target TBD | Lifecycle Production

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-22 |
| Problem & Users | 100% | None | 2026-01-22 |
| Scope | 100% | None | 2026-01-22 |
| Requirements | 100% | None | 2026-01-22 |
| Metrics & Risks | 100% | None | 2026-01-22 |
| Operationalization | 100% | Deployment automation pending | 2026-01-22 |
| Finalization | 100% | None | 2026-01-22 |
| **Implementation** | **100%** | **None** | **2026-01-22** |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary
### Context
TeamBot is a CLI wrapper for GitHub Copilot CLI designed to enable autonomous, collaborative AI agent teams for software development. The tool addresses the limitation of single-threaded, sequential AI interactions by providing a prescriptive, team-based approach where multiple AI agent personas work in parallel or sequentially on defined objectives.

### Core Opportunity
Enable solo developers and development teams to achieve autonomous development workflows by providing a "team" of AI agents that can plan, act, review, iterate, modify, test, and implement solutions with quality and determinism based on simple natural language instructions.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Enable autonomous multi-agent development workflows | Product Goal | Manual, single-threaded AI interactions | Autonomous team-based AI execution | TBD | P0 |
| G-002 | Improve development velocity through parallel agent execution | Performance Goal | TBD | TBD | TBD | P0 |
| G-003 | Provide prescriptive, deterministic development workflows | Quality Goal | Ad-hoc Copilot CLI usage | Known, repeatable team-based flows | TBD | P0 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| TBD | TBD | TBD | TBD |

## 2. Problem Definition
### Current Situation
GitHub Copilot CLI currently operates in a single-threaded, synchronous manner where users provide one line of input, the system executes instructions, and waits for the next input. This model limits:
- Parallel execution of independent development tasks
- Autonomous operation without constant user intervention
- Visualization of multiple concurrent work streams
- Context sharing between different development concerns

### Problem Statement
Developers need a way to orchestrate multiple AI agents working autonomously and collaboratively on complex development objectives, with clear visualization of parallel work streams, prescriptive workflows, and deterministic outcomes - capabilities not provided by the current single-threaded Copilot CLI interaction model.

### Root Causes
* GitHub Copilot CLI is designed for interactive, single-session use cases
* No native support for parallel agent execution or multi-agent collaboration
* Lack of shared workspace and history management for autonomous agents
* No prescriptive workflow patterns to ensure consistent, quality outcomes

### Impact of Inaction
Without TeamBot, developers must:
- Manually orchestrate multiple Copilot CLI sessions
- Sequentially handle tasks that could run in parallel
- Lack visibility into concurrent development activities
- Spend significant time on coordination rather than high-value work
- Experience inconsistent outcomes due to ad-hoc workflows

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Solo Developer | Rapidly prototype and build features autonomously with AI assistance | Manual coordination of AI interactions; slow sequential workflows; context switching overhead | High - Primary user |
| Development Team Member | Leverage AI team for parallel development tasks while maintaining quality | Lack of visibility into AI-generated work; inconsistent patterns; difficulty coordinating AI outputs | High - Secondary user |
| Engineering Lead | Ensure consistent, quality outcomes from AI-assisted development | Ad-hoc AI usage leads to variable quality; hard to establish best practices | Medium - Influencer |

### Journeys (Optional)
**Solo Developer Daily Workflow:**
1. Morning: Provide high-level objective via file/script
2. TeamBot orchestrates agent personas to plan, implement, test
3. Developer reviews progress throughout day via visualizations
4. Agents iterate autonomously, creating history files for transparency
5. End of day: Review completed work and agent history

## 4. Scope
### In Scope
* CLI wrapper interface for GitHub Copilot CLI
* Multi-agent orchestration with distinct personas
* Parallel and sequential agent execution patterns
* Shared `.teambot` working directory for all agents
* History file management with frontmatter metadata
* Automatic context loading based on frontmatter
* Visualization of agent work streams
* Prescriptive workflow patterns for deterministic outcomes
* Date/time stamped history files for traceability
* Simple natural language objective specification

### Out of Scope (justify if empty)
* Direct modification of GitHub Copilot CLI itself
* GUI-based interface (CLI only for initial version)
* Real-time collaboration between human developers (focus is on AI agent collaboration)
* Integration with non-GitHub version control systems

### Assumptions
* GitHub Copilot CLI is installed and properly configured
* Users have appropriate GitHub Copilot licenses
* Agents operate on local development environment
* Users can provide objectives in markdown format
* Python 3.x environment is available for execution
* Operating system supports independent window/process management

### Constraints
* Must work within GitHub Copilot CLI's existing capabilities and limitations
* History files and working directory must be managed locally
* Agent sessions must be isolated unless explicitly shared
* All agents share the same working directory (`.teambot`)
* **Cannot use tmux** for window management - must use independent windows/processes
* Must implement reliable inter-agent messaging/synchronization without tmux
* Built in Python (primary implementation language)

## 5. Product Overview
### Value Proposition
TeamBot transforms GitHub Copilot CLI from a single-threaded assistant into an autonomous development team, enabling developers to specify high-level objectives and let multiple AI agent personas collaboratively plan, execute, and iterate on solutions with transparency, quality, and determinism.

### Differentiators (Optional)
* **Multi-agent autonomy**: First tool to orchestrate multiple Copilot CLI agent personas autonomously
* **Prescriptive workflows**: Enforces known engineering patterns rather than open-ended possibilities
* **Parallel execution visualization**: Clear visibility into concurrent agent work streams
* **History-based transparency**: Every action logged with metadata for full traceability
* **Context-aware agents**: Automatic history loading based on relevance (frontmatter metadata)

### UX / UI (Conditional)
CLI-based interface with console output using colors, positioning, and simple informative displays. Each agent persona operates in independent window (not tmux) with distinct identity. TeamBot automatically creates windows/panes based on configurable default setup. | UX Status: Specified

## 6. Functional Requirements

### MVP Agent Personas
TeamBot shall include the following agent personas in the initial release:
1. **Project Manager/Planner/Coordinator**: Orchestrates workflow, assigns tasks, tracks progress
2. **Business Analyst**: Analyzes business problems, defines requirements, validates solutions
3. **Technical Writer/Documentor**: Creates and maintains documentation
4. **Builder/Implementer (x2)**: Implements code changes, can work in parallel on independent tasks
5. **Reviewer**: Reviews all artifacts (specs, code, docs, tests) for quality and consistency

### Core Prescriptive Workflow
TeamBot shall implement the following standard workflow pattern:
```
Setup → Business Problem (for major features/products) → 
Spec → Review → Research → Test Strategy → 
Plan → Review → Task Implementation → Review → 
Test → Post Implementation Review
```

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Multi-Agent Orchestration | System shall support multiple AI agent personas operating simultaneously | G-001, G-002 | Solo Developer, Dev Team Member | P0 | Can launch and manage 6+ agents concurrently (per MVP personas) | Core capability |
| FR-002 | Agent Persona Definition | Each agent shall have a distinct persona/identity per MVP persona list | G-001, G-003 | Solo Developer, Dev Team Member | P0 | MVP personas: PM/Coordinator, BA, Tech Writer, Builder x2, Reviewer | Required for team metaphor |
| FR-003 | Shared Working Directory | All agents shall use `.teambot` directory for shared workspace | G-001, G-003 | Solo Developer, Dev Team Member | P0 | All agents can read/write to `.teambot` directory | Enables collaboration |
| FR-004 | History File Management | Agents shall create history files for all modify/create/delete actions | G-003 | All Personas | P0 | Every agent action generates history file with frontmatter | Traceability requirement |
| FR-005 | Frontmatter Metadata | History files shall include structured metadata in frontmatter | G-003 | All Personas | P0 | Frontmatter includes: title, description, timestamp, agent-id, action-type (verbose but concise) | Enables smart loading |
| FR-006 | Context-Aware History Loading | Agents shall automatically load relevant history files based on frontmatter | G-003 | All Personas | P0 | Agent loads only relevant history (not all files) | Performance optimization |
| FR-007 | Date/Time Stamped Files | History files shall be named with date/time format | G-003 | All Personas | P0 | Files named like `YYYY-MM-DD-HHMMSS-<descriptor>.md` | Enables chronological sorting |
| FR-008 | Parallel Execution Support | System shall support parallel agent execution when tasks are independent | G-002 | Solo Developer, Dev Team Member | P0 | Can run 2+ agents simultaneously without blocking | Performance requirement |
| FR-009 | Sequential Execution Support | System shall support sequential agent execution when tasks have dependencies | G-003 | Solo Developer, Dev Team Member | P0 | Can define task dependencies and execution order | Workflow control |
| FR-010 | Objective Specification | Users shall provide objectives via markdown file | G-001 | Solo Developer | P0 | Can specify day's work in markdown format | Ease of use |
| FR-011 | Prescriptive Workflow Patterns | System shall enforce standard workflow: Setup → Business Problem → Spec → review → research → test strategy → plan → review → task implementation → review → test → post implementation review | G-003 | Engineering Lead | P0 | Workflow automatically enforced based on objective type | Quality assurance |
| FR-012 | Session Isolation | Each agent operates in separate session unless context sharing requested | G-001 | Solo Developer, Dev Team Member | P0 | Agents have isolated contexts by default | Prevents interference |
| FR-013 | Explicit Context Sharing | Users can explicitly request context sharing between agents | G-001 | Dev Team Member | P1 | Can configure agents to share specific context | Advanced use case |
| FR-014 | Work Stream Visualization | System shall provide console-based visualization with colors and positioning | G-002, G-003 | All Personas | P0 | Simple, informative display of agent status and activities | User visibility |
| FR-015 | Independent Window Management | System shall create independent windows using Python subprocess with OS-native console | G-001, G-002 | Solo Developer, Dev Team Member | P0 | Windows created via subprocess.CREATE_NEW_CONSOLE (Windows), start_new_session (Linux/Unix), osascript (macOS) | Critical constraint |
| FR-016 | Automatic Window Creation | System shall automatically spawn agent windows based on configuration | G-001, G-003 | Solo Developer | P0 | Windows created from default or user-specified configuration file | Ease of use |
| FR-020 | Parent Orchestrator Process | System shall maintain parent TeamBot process to manage agent queues and lifecycle | G-001, G-002 | Solo Developer | P0 | Orchestrator coordinates all agents via multiprocessing queues | Architecture requirement |
| FR-017 | Inter-Agent Messaging | System shall use Python multiprocessing queues for real-time messaging with file-based persistence | G-001, G-003 | All Personas | P0 | Agents communicate via queues managed by orchestrator; durable state in .teambot files | Coordination requirement |
| FR-018 | Configurable Agent Setup | Users shall be able to modify agent configuration via JSON file | G-003 | Engineering Lead, Dev Team Member | P1 | JSON configuration defines agent personas, windows, workflows | Flexibility |
| FR-019 | Parallel Builder Support | System shall support 2 Builder agents working in parallel | G-002 | Solo Developer, Dev Team Member | P0 | Independent tasks assigned to separate Builders simultaneously | Performance optimization |
| FR-021 | Dynamic Agent Prompts | System shall generate agent prompts dynamically based on current task context | G-001, G-003 | All Personas | P0 | Agent instructions tailored to specific task requirements | Flexibility and relevance |
| FR-022 | History File Context Management | System shall warn when history files approach context limits with compaction options | G-003 | All Personas | P1 | Offers little/medium/high compaction when context boundaries approached | Prevents context overflow |
| FR-023 | Objective Schema | Objective markdown files shall include: description, definition of done, success criteria, implementation specifics | G-001, G-003 | Solo Developer | P0 | Example: "Build chatbot SPA with FastAPI backend" + DoD + criteria + specs | Clarity requirement |

### Feature Hierarchy (Optional)
```plain
TeamBot CLI
├── Agent Orchestration
│   ├── Multi-agent management (6 personas: PM, BA, Writer, Builder x2, Reviewer)
│   ├── Session isolation (independent windows)
│   ├── Context sharing (explicit via .teambot)
│   └── Inter-agent messaging (reliable, non-tmux mechanism)
├── Workflow Engine
│   ├── Parallel execution (2 Builders)
│   ├── Sequential execution (workflow stages)
│   └── Prescriptive pattern (Setup → Problem → Spec → ... → Post Review)
├── History Management
│   ├── File creation (with frontmatter: title, desc, timestamp, agent-id, action-type)
│   ├── Smart loading (frontmatter-based relevance)
│   └── Date/time stamping (YYYY-MM-DD-HHMMSS format)
├── Shared Workspace
│   ├── .teambot directory
│   └── Cross-agent file access
├── User Interface
│   ├── Objective specification (markdown)
│   ├── Console visualization (colors, positioning)
│   ├── Automatic window creation (configurable)
│   └── Work stream display
└── Configuration
    ├── Agent persona definitions
    ├── Window layout settings
    └── Workflow customization
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Agent startup time shall be minimal | <5 seconds to launch agent | P0 | Measure from command to agent ready | User experience |
| NFR-002 | Performance | History file loading shall be efficient | <2 seconds for frontmatter scan of 1000 files | P1 | Benchmark with large history | Scalability concern |
| NFR-003 | Reliability | System shall handle agent failures gracefully | No cascading failures; isolated agent errors | P0 | Fault injection testing | Robustness |
| NFR-004 | Scalability | System shall support up to 10 concurrent agents | 10 agents without performance degradation | P1 | Load testing | Future-proofing |
| NFR-005 | Maintainability | History files shall be human-readable markdown | 100% markdown format | P0 | Manual review | Debugging and transparency |
| NFR-006 | Observability | All agent actions shall be logged | 100% action coverage in history | P0 | Log analysis | Auditability |
| NFR-007 | Usability | Objective specification shall use natural language | No code/syntax required | P0 | User testing | Accessibility |
| NFR-008 | Compatibility | Must work with existing GitHub Copilot CLI | Compatible with current version | P0 | Integration testing | Core dependency |
| NFR-009 | Maintainability | Code-first development with TDD where appropriate | TDD used for critical components | P1 | Test coverage reports | Development approach |
| NFR-010 | Portability | Must work across major operating systems (Linux, macOS, Windows) | All window management mechanisms cross-platform | P0 | Multi-OS testing | Platform support |
| NFR-011 | Reliability | Inter-agent messaging must be reliable | <1% message loss rate | P0 | Stress testing | Critical for coordination |
| NFR-012 | Performance | Multiprocessing queue message latency shall be minimal | <100ms average latency | P1 | Performance testing | Real-time coordination |
| NFR-013 | Maintainability | No external dependencies for window management | 100% Python stdlib for window creation | P0 | Dependency audit | Minimize overhead |
| NFR-014 | Reliability | Deliverables must work reliably without human intervention | 100% autonomous completion when DoD met | P0 | End-to-end testing | Core success metric |
| NFR-015 | Usability | History file context warnings shall alert before model limits | Warning at 80% of context capacity | P1 | Context size monitoring | Prevents failures |

## 8. Data & Analytics (Conditional)
### Inputs
* User-provided objectives (markdown file with: description, definition of done, success criteria, implementation specifics)
* Agent persona configurations (JSON)
* Workflow pattern definitions
* Existing history files from `.teambot` directory

### Outputs / Events
* History files with frontmatter metadata
* Agent activity logs
* Workflow execution reports
* Work stream visualizations

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| agent_started | Agent session begins | agent_id, persona, timestamp | Track agent lifecycle | TBD |
| agent_completed | Agent session ends | agent_id, status, duration | Measure agent performance | TBD |
| history_created | History file written | file_name, agent_id, action_type | Track development activities | TBD |
| workflow_started | Objective processing begins | workflow_id, objective_summary | Track workflow execution | TBD |
| workflow_completed | Objective processing ends | workflow_id, status, duration | Measure workflow efficiency | TBD |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Autonomous completion rate | Quality | 0% (manual development) | 100% | Per objective | Workflow completion logs |
| Definition of Done adherence | Quality | Manual validation | Automated validation | Per objective | Post-implementation review |
| Human intervention rate | Efficiency | 100% (fully manual) | 0% (fully autonomous) | Per objective | User interaction logs |
| Success criteria met | Quality | Manual assessment | Automated assessment | Per deliverable | Review agent validation |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| GitHub Copilot CLI | External | Critical | GitHub | API changes, deprecation | Monitor releases, version pinning |
| Python runtime (3.x) | External | Critical | Python.org | Version compatibility | Specify minimum version (3.8+) |
| Python multiprocessing | Internal | Critical | Python stdlib | Cross-platform differences | Test on Windows, Linux, macOS |
| OS console/terminal | External | Critical | OS vendor | Platform differences | Platform-specific subprocess code |
| Python subprocess | Internal | Critical | Python stdlib | Platform differences | Test window creation per OS |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | GitHub Copilot CLI API changes break TeamBot | High | Medium | Version pinning, compatibility layer | TBD | Open |
| R-002 | Agent context conflicts when accessing shared files | Medium | High | File locking, conflict detection | TBD | Open |
| R-003 | Performance degradation with large history files | Medium | Medium | Efficient frontmatter parsing, pagination | TBD | Open |
| R-004 | Users find multi-agent visualization confusing | Medium | Medium | User testing, iterative UX refinement | TBD | Open |
| R-005 | Autonomous agents produce low-quality code | High | Medium | Prescriptive patterns, review workflows | TBD | Open |

## 11. Privacy, Security & Compliance
### Data Classification
* History files may contain source code and development context (confidential)
* Objective specifications may contain business logic descriptions (confidential)
* Agent logs contain development activities (internal use)

### PII Handling
TeamBot does not directly process PII. However, user-generated objectives and code may inadvertently contain PII - users must follow existing data handling practices.

### Threat Considerations
* **File system access**: All agents have read/write access to `.teambot` directory - ensure proper permissions
* **Command injection**: Natural language objectives are translated to Copilot CLI commands - validate/sanitize inputs
* **Secret exposure**: History files may capture sensitive data - implement secret detection

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| TBD | TBD | TBD | TBD | TBD |

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Installable via pip/uv as Python package | Standard Python distribution |
| Rollback | Users can downgrade to previous version | Version management via package manager |
| Monitoring | History files provide built-in audit trail | Local logging only initially |
| Alerting | Agent failures logged to console/file | No external alerting initially |
| Support | Community support via GitHub issues | Open source model |
| Capacity Planning | Local execution only, scales with user machine | No server-side infrastructure |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|------|--------------|-------|
| MVP Development | TBD | Core agent orchestration + history management | TBD |
| Alpha Release | TBD | Internal testing with 2-3 agent personas | TBD |
| Beta Release | TBD | Community feedback, 5+ agent personas | TBD |
| GA Release | TBD | Production-ready, documentation complete | TBD |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| parallel_execution | Enable/disable parallel agent execution | On | After GA |
| history_visualization | Enable/disable work stream visualization | On | After GA |

### Communication Plan (Optional)
TBD - Will include developer community announcements, documentation, and tutorials

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| Q-001 | ~~What specific agent personas should be included in MVP?~~ | TBD | TBD | Resolved: PM/Coordinator, BA, Writer, Builder x2, Reviewer |
| Q-002 | ~~How should work stream visualization be implemented?~~ | TBD | TBD | Resolved: Console with colors/positioning, no tmux |
| Q-003 | ~~What is the exact frontmatter schema for history files?~~ | TBD | TBD | Resolved: title, description, timestamp, agent-id, action-type |
| Q-004 | How should agent dependencies be specified in objective files? | TBD | TBD | Open |
| Q-005 | ~~What are the prescriptive workflow patterns to implement?~~ | TBD | TBD | Resolved: Setup → Problem → Spec → review → ... → Post Review |
| Q-006 | Should TeamBot support remote execution or local only? | TBD | TBD | Open |
| Q-007 | ~~What specific inter-agent messaging mechanism should be used?~~ | TBD | TBD | Resolved: Python multiprocessing queues + file-based persistence |
| Q-008 | ~~What is the exact configuration file format and schema?~~ | TBD | TBD | Resolved: JSON format |
| Q-009 | ~~What format should objective markdown files follow?~~ | TBD | TBD | Resolved: Markdown with description, DoD, success criteria, implementation specifics |
| Q-010 | ~~What are the key success metrics?~~ | TBD | TBD | Resolved: Autonomous completion without human intervention based on DoD |
| Q-011 | What is the detailed JSON schema for configuration files? | TBD | TBD | Open - needs definition |
| Q-012 | What is the message protocol structure for multiprocessing queues? | TBD | TBD | Open - needs definition |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 0.1 | 2026-01-22 | TeamBot Spec Builder | Initial specification creation | Creation |
| 0.2 | 2026-01-22 | TeamBot Spec Builder | Added technical stack, agent personas, workflow details, windowing constraints | Major Update |
| 0.3 | 2026-01-22 | TeamBot Spec Builder | Specified inter-agent messaging (multiprocessing queues + files) and window creation mechanism (subprocess with OS-native console) | Technical Update |
| 0.4 | 2026-01-22 | TeamBot Spec Builder | Added configuration format (JSON), objective structure with DoD/success criteria, success metrics (autonomous completion), dynamic prompts, context management with compaction | Completion Update |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | User Input | Initial specification conversation | Core concept: multi-agent autonomous development wrapper for Copilot CLI | N/A - Primary source |

### Citation Usage
All information derived from initial user conversation during specification creation.

## 17. Appendices (Optional)
### Glossary
| Term | Definition |
|------|-----------|
| Agent Persona | An AI agent with a specific role within TeamBot. MVP personas: PM/Coordinator, Business Analyst, Technical Writer, Builder (x2), Reviewer |
| History File | Markdown file created by agents to log actions, stored in `.teambot` directory with date/time stamped filename |
| Frontmatter | YAML metadata at the top of history files containing: title, description, timestamp, agent-id, action-type (verbose descriptor) |
| Objective | High-level development goal specified by user in markdown format containing: description, definition of done, success criteria, and implementation specifics |
| Definition of Done (DoD) | Specific criteria that must be met for objective to be considered complete (e.g., "API responds with 200 status", "All tests pass") |
| Success Criteria | Measurable indicators of successful completion (e.g., "Chatbot responds to user input", "FastAPI endpoints functional") |
| Work Stream | Sequence of activities performed by one or more agents following the prescriptive workflow |
| Prescriptive Workflow | Standard workflow pattern: Setup → Business Problem → Spec → review → research → test strategy → plan → review → task implementation → review → test → post implementation review |
| Independent Window | Separate OS window/process for each agent created via Python subprocess with OS-native console APIs |
| Inter-Agent Messaging | Communication via Python multiprocessing queues (real-time) with file-based persistence in .teambot (durable state) |
| Orchestrator | Parent TeamBot process that manages all agent child processes and coordinates via multiprocessing queues |
| Context Compaction | Process of summarizing history files when approaching model context limits (options: little/medium/high compression) |
| Dynamic Prompts | Agent instructions generated on-the-fly based on current task context rather than static templates |

### Additional Notes

**Example Objective Structure:**
```markdown
# Objective: Build Chatbot SPA with FastAPI Backend

## Description
Today we are building a basic chatbot single-page application (SPA) that integrates with a FastAPI backend.

## Definition of Done
- [ ] FastAPI backend running with chat endpoint
- [ ] SPA UI responds to user input
- [ ] Messages sent to backend and responses displayed
- [ ] All tests passing
- [ ] Code follows project standards

## Success Criteria
- API endpoint returns responses within 200ms
- UI is responsive and user-friendly
- No console errors in browser
- Backend handles at least 10 concurrent connections

## Implementation Specifics
- Use React for SPA frontend
- FastAPI with async endpoints
- WebSocket or REST API for communication
- Store conversation history in memory (no persistence required for MVP)
- Include basic error handling
```

**Technical Stack Decisions:**
- Primary language: Python 3.x (minimum 3.8+)
- Configuration format: JSON
- Testing approach: Code-first with TDD where it improves quality
- Window management: Python subprocess with OS-native console (subprocess.CREATE_NEW_CONSOLE/start_new_session/osascript)
- Inter-agent communication: Python multiprocessing queues for real-time messaging + file-based persistence in .teambot
- Architecture: Parent orchestrator process manages child agent processes via queues
- Agent prompts: Dynamically generated based on task context
- Visualization: Console-based with colors and positioning

**Critical Design Constraints:**
- No tmux dependency for window/pane management
- Must support 2 parallel Builder agents
- All agents share `.teambot` directory for collaboration
- History files with structured frontmatter for smart context loading
- All agents are child processes of main TeamBot orchestrator
- No external dependencies for window creation (Python stdlib only)
- No hard limits on history file sizes, but smart warnings with compaction options
- Success measured by autonomous completion without human intervention

**Example Objective Structure:**
```markdown
# Objective: Build Chatbot SPA with FastAPI Backend

## Description
Today we are building a basic chatbot single-page application (SPA) that integrates with a FastAPI backend.

## Definition of Done
- [ ] FastAPI backend running with chat endpoint
- [ ] SPA UI responds to user input
- [ ] Messages sent to backend and responses displayed
- [ ] All tests passing
- [ ] Code follows project standards

## Success Criteria
- API endpoint returns responses within 200ms
- UI is responsive and user-friendly
- No console errors in browser
- Backend handles at least 10 concurrent connections

## Implementation Specifics
- Use React for SPA frontend
- FastAPI with async endpoints
- WebSocket or REST API for communication
- Store conversation history in memory (no persistence required for MVP)
- Include basic error handling
```
1. Define detailed JSON configuration schema (agent setup, window layout, personas)
2. Create example objective markdown template with DoD, success criteria, implementation specs
3. Design dynamic prompt generation system for agent personas
4. Implement parent orchestrator with multiprocessing queue management
5. Implement OS-specific window creation (Windows/Linux/macOS)
6. Implement file-based persistence layer for durable state
7. Design inter-agent message protocol and queue routing
8. Implement history file context monitoring and compaction system (little/medium/high options)
9. Create agent persona behavior definitions for PM/Coordinator, BA, Tech Writer, Builder x2, Reviewer

Generated 2026-01-22T02:42:47Z by Feature Spec Builder (mode: interactive)
<!-- markdown-table-prettify-ignore-end -->
