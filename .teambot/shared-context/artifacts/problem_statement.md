# Problem Statement: Agent Output Reference Syntax

## Executive Summary

TeamBot users need an intuitive way to reference another agent's output within prompts, enabling flexible cross-agent dependencies without requiring strict pipeline ordering.

---

## Business Problem

### Current State

TeamBot currently supports the **pipeline operator (`->`)** for chaining agent tasks:
```bash
@pm Create a plan -> @builder-1 Implement based on this plan
```

While powerful for sequential workflows, this syntax has limitations:
1. **Sequential dependency only** — Each stage must complete before the next begins
2. **Implicit output passing** — Output flows automatically; users cannot selectively reference specific agent results
3. **No named references** — Users cannot reference an earlier agent's output from a non-adjacent stage
4. **Limited flexibility** — Cannot express "wait for agent X's output" without restructuring the entire pipeline

### Problem Statement

> **Users cannot easily reference a specific agent's output within their prompt in a way that is intuitive, explicit, and creates an automatic wait-for-completion dependency.**

### Impact

| Stakeholder | Impact |
|-------------|--------|
| **End Users** | Must manually copy/paste agent outputs or restructure pipelines to pass context |
| **Power Users** | Cannot build complex dependency graphs between agents |
| **Workflow Designers** | Limited to linear or parallel-then-merge patterns |

---

## Goals

### Primary Goal
Enable users to reference another agent's latest output using a simple, intuitive syntax (e.g., `$pm`) that:
1. Creates an implicit dependency (the referencing agent waits for the referenced agent to complete)
2. Injects the referenced output into the prompt context at execution time

### Secondary Goals
- Maintain backward compatibility with existing `->` pipeline syntax
- Provide clear status visibility showing which agents are waiting, executing, or idle
- Document both syntaxes clearly with comparison of use cases

---

## Success Criteria

| ID | Criterion | Measurable Outcome |
|----|-----------|-------------------|
| **SC-1** | Easy-to-use reference syntax | Users can reference agent output with `$<agent-id>` (e.g., `$pm`, `$builder-1`) |
| **SC-2** | Automatic wait behavior | When a prompt contains `$agent`, execution waits for that agent to complete before proceeding |
| **SC-3** | Documentation clarity | README.md explains both `$agent` and `->` syntax with clear comparison table |
| **SC-4** | Status accuracy | Agent status correctly reflects: `waiting` (blocked on dependency), `executing`, or `idle` |

---

## Scope

### In Scope
- New `$<agent-id>` syntax for referencing agent outputs
- Parser updates to detect and resolve `$agent` references
- Dependency resolution to wait for referenced agents
- Agent status states: `idle`, `executing`, `waiting`
- README documentation updates
- Unit and integration tests

### Out of Scope
- Referencing specific fields within agent output (e.g., `$pm.plan`) — future enhancement
- Persisting agent outputs across sessions
- Circular dependency detection beyond basic validation
- GUI/visual dependency graph

---

## Syntax Comparison

| Feature | Pipeline (`->`) | Reference (`$agent`) |
|---------|-----------------|---------------------|
| **Use Case** | Sequential task chaining | Explicit output injection |
| **Dependency** | Implicit (previous stage) | Explicit (named agent) |
| **Output Passing** | Automatic to next stage | On-demand via reference |
| **Multiple Sources** | One previous stage | Multiple agents possible |
| **Example** | `@pm Plan -> @builder Build` | `@builder Build using $pm` |

### Combined Usage Example
```bash
# Pipeline with explicit reference
@pm Create plan -> @builder-1 Implement $pm -> @reviewer Review $builder-1

# Non-adjacent reference
@ba Write requirements
@pm Create plan based on $ba
@builder-1 Implement using $pm and referencing $ba
```

---

## Assumptions

1. Agent IDs are unique and known at prompt-entry time
2. Agent output is stored in memory during the session and accessible for reference
3. A referenced agent must have completed at least one task to have output available
4. If a referenced agent has no output, the system will either wait or return an error (TBD in spec)

---

## Dependencies

| Dependency | Component | Impact |
|------------|-----------|--------|
| Existing pipeline parser | `src/teambot/repl/parser.py` | Must extend, not replace |
| Message protocol | `src/teambot/messaging/protocol.py` | May need new message types for status |
| Agent status tracking | `src/teambot/orchestrator.py` | Must add `waiting` state |
| Output storage | `src/teambot/tasks/output_injector.py` | Must support named retrieval |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular dependencies (`$a` refs `$b`, `$b` refs `$a`) | Medium | High | Add cycle detection in parser |
| Race condition (ref before completion) | Low | Medium | Wait mechanism handles this |
| Syntax conflicts with shell variables | Low | Low | Document escaping (`\$` for literal) |
| User confusion between `->` and `$` | Medium | Medium | Clear documentation with examples |

---

## Stakeholder Sign-off

| Role | Name | Approval |
|------|------|----------|
| Product Owner | — | ☐ Pending |
| Technical Lead | — | ☐ Pending |
| End User Representative | — | ☐ Pending |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | Business Analyst Agent | Initial problem statement |
