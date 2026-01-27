<!-- markdownlint-disable-file -->
# TeamBot Interactive Mode - Feature Specification Document
Version 0.1 | Status Draft | Owner TBD | Target TBD | Lifecycle Discovery

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-22 |
| Problem & Users | 100% | None | 2026-01-22 |
| Scope | 100% | None | 2026-01-22 |
| Requirements | 100% | None | 2026-01-22 |
| Metrics & Risks | 80% | Performance targets TBD | 2026-01-22 |
| Finalization | 100% | None | 2026-01-22 |
Unresolved Critical Questions: 0 | TBDs: 1

---

## 1. Executive Summary

### Context
TeamBot currently supports objective-file-driven execution only. Users cannot interact with agents in real-time or issue ad-hoc commands. This feature adds a unified interactive mode that supports both file-based objectives and REPL-style interaction with agents.

### Core Opportunity
Enable real-time, conversational interaction with TeamBot agents while maintaining support for file-based objectives. This allows developers to:
- Issue commands to specific agents using `@agent` prefix
- Monitor agent status and progress in real-time
- Control agent execution (pause, resume, stop)
- Work iteratively without pre-planning entire objectives

### Key Change: Copilot SDK Integration
This feature also pivots from wrapping the Copilot CLI to using the **GitHub Copilot SDK** (`github-copilot-sdk`) for Python. This provides:
- Programmatic access to Copilot's agent runtime
- JSON-RPC communication with CLI server
- Better control over tool invocation and streaming
- Direct access to agent capabilities without subprocess overhead

### Goals
| Goal ID | Statement | Type | Priority |
|---------|-----------|------|----------|
| G-001 | Enable real-time interaction with agents via REPL interface | Product | P0 |
| G-002 | Integrate Copilot SDK for programmatic agent control | Technical | P0 |
| G-003 | Support parallel agent execution with dependency awareness | Performance | P1 |
| G-004 | Provide rich status visualization during execution | UX | P1 |

---

## 2. Problem Statement

### Current State
- `teambot run` displays status and exits immediately
- No way to issue commands to agents interactively
- Uses subprocess wrapper around Copilot CLI (limited control)
- Cannot monitor or control running agents

### Desired State
- `teambot run` enters interactive mode (with or without objective file)
- Users can direct commands to specific agents via `@agent` syntax
- Real-time streaming output from agent execution
- System commands for status, help, history, stop/pause/resume
- Copilot SDK provides direct programmatic control

### User Personas
| Persona | Need | Priority |
|---------|------|----------|
| Solo Developer | Issue quick tasks without writing objective files | P0 |
| Team Lead | Monitor multiple agents working in parallel | P1 |
| Power User | Fine-grained control over agent execution | P1 |

---

## 3. Scope

### In Scope (MVP - Phase 1)
| Feature | Description | Priority |
|---------|-------------|----------|
| Copilot SDK Integration | Replace CLI wrapper with SDK client | P0 |
| Basic REPL | Command prompt with input loop | P0 |
| `@agent` Commands | Direct commands to specific agents | P0 |
| System Commands | `/help`, `/status`, `/history`, `/quit` | P0 |
| Single Agent Execution | One agent processes at a time | P0 |
| Status Display | Show agent table with current status | P0 |
| Unified Mode | Support both file + interactive in same session | P0 |

### In Scope (Phase 2)
| Feature | Description | Priority |
|---------|-------------|----------|
| Parallel Agent Execution | Multiple agents work simultaneously | P1 |
| Real-time Streaming | Stream agent output as it executes | P1 |
| Rich TUI | Split view with status panel + input | P1 |
| Background Execution | Run tasks in background with notifications | P1 |
| Agent Dependencies | Sequential execution when output needed | P1 |
| Context Isolation | Per-agent state, explicit sharing only | P1 |

### Out of Scope
| Feature | Reason |
|---------|--------|
| Web UI | CLI-focused tool |
| Multi-user collaboration | Single-user tool |
| Custom agent definitions | Use existing 6 personas |
| Voice input | Text-based interface |

---

## 4. Technical Approach

### Architecture Change: Copilot SDK

**Before (CLI Wrapper):**
```
AgentRunner → subprocess.run("copilot -p ...") → Parse output
```

**After (SDK Integration):**
```
AgentRunner → CopilotSDK.Client → JSON-RPC → Copilot CLI Server
```

### SDK Installation
```bash
pip install github-copilot-sdk
```

### SDK Usage Pattern
```python
from github_copilot_sdk import CopilotClient

client = CopilotClient()
response = await client.prompt(
    message="Create a Python function to...",
    tools=["write", "shell"],
    stream=True
)
async for chunk in response:
    print(chunk.content)
```

### Interactive Mode Flow
```
┌─────────────────────────────────────────────────────┐
│                   TeamBot REPL                       │
├─────────────────────────────────────────────────────┤
│ Agent          │ Status    │ Task                   │
│ PM             │ idle      │ -                      │
│ Builder-1      │ working   │ Implementing auth...   │
│ Reviewer       │ idle      │ -                      │
├─────────────────────────────────────────────────────┤
│ > @builder-1 implement user authentication          │
│                                                     │
│ [Builder-1] Starting task...                        │
│ [Builder-1] Creating src/auth/login.py...           │
│ [Builder-1] ✓ Task complete                         │
│                                                     │
│ > /status                                           │
│ > @reviewer review the auth implementation          │
│ > /quit                                             │
└─────────────────────────────────────────────────────┘
```

### Command Syntax
| Command | Description | Example |
|---------|-------------|---------|
| `@<agent> <task>` | Direct task to agent | `@pm create a plan for login feature` |
| `/help` | Show available commands | `/help` |
| `/status` | Show agent status table | `/status` |
| `/history` | Show recent actions | `/history` |
| `/history <agent>` | Show agent-specific history | `/history builder-1` |
| `/stop` | Stop current execution | `/stop` |
| `/stop <agent>` | Stop specific agent | `/stop builder-1` |
| `/pause` | Pause all agents | `/pause` |
| `/resume` | Resume paused agents | `/resume` |
| `/quit` or `/exit` | Exit TeamBot | `/quit` |
| `/share <from> <to>` | Share context between agents | `/share builder-1 reviewer` |

---

## 5. Functional Requirements

### MVP (Phase 1)

| FR ID | Title | Description | Priority | Acceptance Criteria |
|-------|-------|-------------|----------|---------------------|
| FR-IM-001 | Copilot SDK Client | Replace CopilotClient with SDK-based implementation | P0 | SDK client connects to Copilot CLI server |
| FR-IM-002 | REPL Loop | Interactive command loop that doesn't exit | P0 | `teambot run` stays running until `/quit` |
| FR-IM-003 | Agent Commands | Parse and route `@agent` commands | P0 | `@pm <task>` routes to PM agent |
| FR-IM-004 | System Commands | Implement `/help`, `/status`, `/history`, `/quit` | P0 | All commands work as documented |
| FR-IM-005 | Status Display | Show agent table with status updates | P0 | Table updates after each command |
| FR-IM-006 | Task Execution | Execute task via SDK and display result | P0 | Agent receives task, executes, returns result |
| FR-IM-007 | Unified Mode | Load objective file if provided, then enter REPL | P0 | `teambot run obj.md` loads then prompts |
| FR-IM-008 | Graceful Exit | Handle Ctrl+C and `/quit` cleanly | P0 | No orphan processes, state saved |

### Phase 2

| FR ID | Title | Description | Priority | Acceptance Criteria |
|-------|-------|-------------|----------|---------------------|
| FR-IM-009 | Parallel Execution | Multiple agents work simultaneously | P1 | 2+ agents can process tasks concurrently |
| FR-IM-010 | Streaming Output | Real-time output as agent works | P1 | See incremental output, not just final |
| FR-IM-011 | Rich TUI | Split view with status + input | P1 | Status panel updates independently |
| FR-IM-012 | Background Mode | Execute in background with notification | P1 | `@pm & <task>` runs in background |
| FR-IM-013 | Dependency Awareness | Sequential when agent needs another's output | P1 | Automatic wait for dependent tasks |
| FR-IM-014 | Context Sharing | Explicit `/share` command for context | P1 | `/share builder-1 reviewer` works |
| FR-IM-015 | Stop/Pause/Resume | Control running agents | P1 | `/stop builder-1` cancels execution |

---

## 6. Non-Functional Requirements

| NFR ID | Category | Requirement | Target |
|--------|----------|-------------|--------|
| NFR-IM-001 | Latency | Command response time | < 100ms for system commands |
| NFR-IM-002 | Reliability | REPL stability | No crashes during normal use |
| NFR-IM-003 | Usability | Command discoverability | `/help` shows all commands |
| NFR-IM-004 | Compatibility | SDK version | github-copilot-sdk >= 0.1.0 |
| NFR-IM-005 | State | Session persistence | Agent state persists on exit |

---

## 7. Dependencies

### External
| Dependency | Version | Purpose |
|------------|---------|---------|
| `github-copilot-sdk` | >= 0.1.0 | Programmatic Copilot access |
| Copilot CLI | Latest | SDK backend (server mode) |
| GitHub Copilot subscription | Active | Required for SDK usage |

### Internal
| Dependency | Impact |
|------------|--------|
| Existing orchestrator | Needs SDK integration |
| AgentRunner | Replace CopilotClient with SDK |
| CLI module | Add REPL loop |
| Visualization | Add dynamic updates |

---

## 8. Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SDK API changes (Technical Preview) | High | Medium | Pin version, monitor releases |
| SDK not available in all regions | Medium | Low | Fall back to CLI wrapper |
| Streaming complexity | Medium | Medium | Phase 2, start with sync |
| Terminal compatibility | Low | Medium | Test common terminals |

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| REPL responsiveness | < 100ms | Time from input to prompt return |
| Task completion rate | > 95% | Tasks that complete without error |
| User commands supported | 10+ | Count of working commands |
| Test coverage | > 80% | pytest-cov report |

---

## 10. Implementation Phases

### Phase 1: MVP (This Spec)
- Copilot SDK integration
- Basic REPL with `@agent` and system commands
- Single agent execution
- Status display

**Estimated Effort:** 8-12 hours

### Phase 2: Enhanced (Future Spec)
- Parallel agent execution
- Real-time streaming
- Rich TUI
- Background execution
- Context sharing

**Estimated Effort:** 12-16 hours

---

## 11. Open Questions

| # | Question | Status | Answer |
|---|----------|--------|--------|
| 1 | SDK Python package exact name? | Resolved | `github-copilot-sdk` |
| 2 | SDK async or sync API? | TBD | Research during implementation |

---

## Appendix A: Command Reference

### Agent Commands
```
@pm <task>           - Assign task to Project Manager
@ba <task>           - Assign task to Business Analyst
@writer <task>       - Assign task to Technical Writer
@builder-1 <task>    - Assign task to Builder (Primary)
@builder-2 <task>    - Assign task to Builder (Secondary)
@reviewer <task>     - Assign task to Reviewer
```

### System Commands
```
/help                - Show this help
/status              - Show agent status table
/history             - Show recent actions (all agents)
/history <agent>     - Show history for specific agent
/stop                - Stop all running tasks
/stop <agent>        - Stop specific agent's task
/pause               - Pause all agents
/resume              - Resume paused agents
/share <from> <to>   - Share context from one agent to another
/quit or /exit       - Exit TeamBot
```

### Examples
```
> @pm create a plan for implementing user authentication
> @builder-1 implement the login endpoint based on PM's plan
> /share builder-1 reviewer
> @reviewer review the authentication implementation
> /status
> /quit
```
