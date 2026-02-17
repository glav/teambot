<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Default Agent Context Reference Extraction - Feature Specification
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot Core | Target v0.2.x | Lifecycle Active

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-17 |
| Problem & Users | ✅ | None | 2026-02-17 |
| Scope | ✅ | None | 2026-02-17 |
| Requirements | ✅ | None | 2026-02-17 |
| Metrics & Risks | ✅ | None | 2026-02-17 |
| Operationalization | ✅ | None | 2026-02-17 |
| Finalization | ✅ | None | 2026-02-17 |

Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot's REPL and UI allow users to configure a "default agent" (e.g., `pm`) so that raw input is automatically routed to that agent without requiring an explicit `@agent` prefix. Additionally, TeamBot supports context references using `$agent` syntax (e.g., `$reviewer`, `$ba`) to inject another agent's previous output into the current prompt.

### Core Opportunity
Fix a bug where context references (`$reviewer`, `$ba`, etc.) are not extracted when relying on default agent routing. This ensures consistent behavior whether users explicitly type `@pm task $reviewer` or rely on the default agent with just `task $reviewer`.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Context references work identically with and without explicit @agent prefix | Functional | Broken for default routing | Fully functional | This release | P0 |
| G-002 | No regression in existing functionality | Quality | All tests pass | All tests pass | This release | P0 |
| G-003 | Consistent behavior between REPL and UI code paths | Consistency | Different behaviors | Identical behaviors | This release | P1 |

---

## 2. Problem Definition

### Current Situation
When a user types `@pm Incorporate the feedback from $reviewer`, the system correctly:
1. Parses the command via `parse_command()`
2. Extracts `$reviewer` using `REFERENCE_PATTERN`
3. Populates `command.references = ["reviewer"]`
4. Injects the reviewer's output into the prompt

However, when a user types `Incorporate the feedback from $reviewer` (relying on default agent routing), the system:
1. Creates a `Command` object manually (bypassing `parse_command()`)
2. **Does NOT extract references** — `command.references` remains empty
3. The `$reviewer` text is passed literally, not resolved

### Problem Statement
Manual `Command` instantiation in `loop.py` and `app.py` bypasses the reference extraction logic, causing context references to fail silently when using default agent routing.

### Root Causes
* **Inconsistent code path**: Default agent routing creates `Command` objects manually instead of using `parse_command()`
* **No helper function**: Reference extraction logic is embedded in `_parse_agent_command()` rather than being a reusable helper
* **Duplicated code**: Both `loop.py` and `app.py` contain identical manual instantiation logic

### Impact of Inaction
* Users cannot rely on the default agent feature for commands with context references
* Inconsistent behavior erodes user trust
* Users must always type `@agent` prefix, negating the productivity benefit of default agent configuration

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Power User | Use default agent for faster workflows | Must remember to add @prefix for reference commands | High |
| New User | Learn TeamBot with minimal syntax | Confused by inconsistent behavior | Medium |
| Team Lead | Configure default agents for team | Feature appears broken | High |

---

## 4. Scope

### In Scope
* Fix reference extraction in `src/teambot/repl/loop.py` (lines ~308-314)
* Fix reference extraction in `src/teambot/ui/app.py` (lines ~140-146)
* Create helper function `extract_references()` in `src/teambot/repl/parser.py`
* Add unit tests for default agent + reference extraction scenario
* Verify existing tests continue to pass

### Out of Scope
* Changes to `REFERENCE_PATTERN` syntax
* Changes to how references are resolved or injected (working correctly)
* Performance optimizations
* Refactoring beyond the minimal fix
* UI/UX changes

### Assumptions
* `REFERENCE_PATTERN` in `parser.py` is the canonical pattern for reference extraction
* The reference resolution/injection logic is working correctly (only extraction is broken)
* The `Command` dataclass supports a `references` field (confirmed)

### Constraints
* **Minimal changes**: Bug fix only, not a refactor
* **Reuse existing logic**: Use `REFERENCE_PATTERN`, avoid duplication
* **No breaking changes**: Existing explicit `@agent` parsing and pipelines must continue working
* **Testing**: Follow existing pytest + pytest-mock patterns

---

## 5. Product Overview

### Value Proposition
Consistent, predictable context reference behavior regardless of whether users explicitly specify an agent or rely on default agent routing.

### Differentiators
* Single source of truth for reference extraction (`extract_references()` helper)
* Eliminates code duplication between REPL and UI paths

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Create extract_references helper | Add `extract_references(content: str) -> list[str]` function in `parser.py` that uses `REFERENCE_PATTERN` to extract and deduplicate references | G-001, G-003 | All | P0 | Function exists, uses REFERENCE_PATTERN, returns deduplicated list preserving order | Reuse existing extraction logic from `_parse_agent_command()` |
| FR-002 | Fix REPL default agent routing | In `loop.py`, call `extract_references()` when creating manual `Command` for default agent and populate `references` field | G-001 | Power User | P0 | `command.references` populated correctly for default agent commands | Lines ~308-314 |
| FR-003 | Fix UI default agent routing | In `app.py`, call `extract_references()` when creating manual `Command` for default agent and populate `references` field | G-001, G-003 | All | P0 | `command.references` populated correctly for default agent commands | Lines ~140-146 |
| FR-004 | Refactor _parse_agent_command | Update `_parse_agent_command()` to call `extract_references()` instead of inline logic | G-003 | Developers | P1 | No code duplication, single source of truth | Optional but recommended |

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Maintainability | Single source of truth for reference extraction | 1 function location | P1 | Code review | Helper function in parser.py |
| NFR-002 | Reliability | No regression in existing functionality | 100% existing tests pass | P0 | Test suite | Run full test suite |
| NFR-003 | Performance | No measurable performance impact | < 1ms overhead | P2 | Manual verification | Regex already compiled |

---

## 8. Data & Analytics

### Inputs
* User input string containing potential `$agent` references

### Outputs
* List of extracted agent reference names (deduplicated, order preserved)

### Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Default agent + reference commands work | Functional | 0% | 100% | Post-fix | Manual + automated tests |
| Existing tests pass | Quality | 100% | 100% | Post-fix | CI pipeline |
| New test coverage | Quality | 0 tests | ≥4 tests | Post-fix | Test suite |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `REFERENCE_PATTERN` in parser.py | Internal | High | TeamBot | Low | Verified exists at line 93 |
| `Command` dataclass | Internal | High | TeamBot | Low | Verified supports `references` field |
| Existing test infrastructure | Internal | Medium | TeamBot | Low | pytest + pytest-mock in place |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Regex change breaks edge cases | Medium | Low | Reuse existing REFERENCE_PATTERN exactly | Builder | Open |
| R-002 | UI and REPL diverge again | Medium | Medium | Create shared helper function | Builder | Open |
| R-003 | Breaking existing pipeline handling | High | Low | Comprehensive test coverage | Builder | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
* No PII involved
* Agent references are identifier strings only

### PII Handling
* N/A — no personal data processed

### Threat Considerations
* None — internal reference extraction only

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard release process | Bug fix in patch release |
| Rollback | Standard rollback if needed | No migrations or state changes |
| Monitoring | Existing logging sufficient | No new instrumentation needed |
| Support | No support changes needed | Bug fix improves support burden |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|---------------|-------|
| Implementation | Code complete, tests pass | Builder |
| Review | Code review approved | Reviewer |
| Merge | CI passes, no conflicts | Builder |
| Release | Included in next patch release | PM |

---

## 14. Acceptance Test Scenarios

### AT-001: Single Reference with Default Agent
**Description**: User types command with single `$agent` reference using default agent routing
**Preconditions**: Default agent configured to `pm`, `reviewer` agent has previous output
**Steps**:
1. Configure default agent: `/default pm`
2. Run reviewer agent: `@reviewer analyze the code`
3. Wait for reviewer to complete
4. User enters: `Incorporate the feedback from $reviewer` (no @pm prefix)
**Expected Result**: 
- `$reviewer` is extracted as a reference
- PM agent receives reviewer's output injected into the prompt
- PM responds with content that references the reviewer's feedback
**Verification**: PM's response demonstrates awareness of reviewer's prior output

### AT-002: Multiple References with Default Agent
**Description**: User types command with multiple `$agent` references using default agent routing
**Preconditions**: Default agent configured, multiple agents have previous output
**Steps**:
1. Configure default agent: `/default pm`
2. Run `@reviewer review the code` and wait for completion
3. Run `@ba analyze requirements` and wait for completion
4. User enters: `Combine insights from $reviewer and $ba`
**Expected Result**:
- Both `$reviewer` and `$ba` are extracted as references
- PM agent receives both outputs injected into the prompt
**Verification**: PM's response synthesizes content from both agents

### AT-003: Escaped Reference Not Extracted
**Description**: Escaped `\$agent` syntax should not be extracted as reference
**Preconditions**: Default agent configured
**Steps**:
1. Configure default agent: `/default pm`
2. User enters: `Explain what \$reviewer syntax means` (escaped)
**Expected Result**:
- No references extracted
- `\$reviewer` passed literally to PM
**Verification**: PM explains the syntax rather than waiting for reviewer output

### AT-004: Pipeline with Default Agent Still Works
**Description**: Pipeline syntax continues to work with default agent
**Preconditions**: Default agent configured
**Steps**:
1. Configure default agent: `/default pm`
2. User enters: `tell a joke -> @notify`
**Expected Result**:
- Pipeline is correctly parsed
- Default agent used for first stage
- @notify receives output from PM
**Verification**: Notification received with PM's joke

### AT-005: Explicit Agent Prefix Still Works
**Description**: Explicit `@agent` prefix continues to extract references
**Preconditions**: Default agent may or may not be configured
**Steps**:
1. Run `@reviewer analyze code` and wait for completion
2. User enters: `@pm Incorporate $reviewer feedback`
**Expected Result**:
- `$reviewer` extracted correctly
- Works identically whether default agent is configured or not
**Verification**: PM's response references reviewer's feedback

---

## 15. Unit Test Scenarios

### UT-001: extract_references returns single reference
```python
def test_extract_references_single():
    result = extract_references("use $reviewer feedback")
    assert result == ["reviewer"]
```

### UT-002: extract_references returns multiple references
```python
def test_extract_references_multiple():
    result = extract_references("combine $reviewer and $ba")
    assert result == ["reviewer", "ba"]
```

### UT-003: extract_references deduplicates preserving order
```python
def test_extract_references_deduplicate():
    result = extract_references("$pm said $ba but $pm again")
    assert result == ["pm", "ba"]
```

### UT-004: extract_references excludes escaped
```python
def test_extract_references_escaped():
    result = extract_references("explain \\$reviewer syntax")
    assert result == []
```

### UT-005: extract_references empty for no references
```python
def test_extract_references_none():
    result = extract_references("no references here")
    assert result == []
```

### UT-006: Default agent command includes references
```python
def test_default_agent_command_has_references():
    # Simulates the fixed loop.py behavior
    content = "use $reviewer feedback"
    references = extract_references(content)
    command = Command(
        type=CommandType.AGENT,
        agent_id="pm",
        agent_ids=["pm"],
        content=content,
        references=references,
    )
    assert command.references == ["reviewer"]
```

---

## 16. Technical Implementation Guidance

### Recommended Helper Function (parser.py)

**Location**: `src/teambot/repl/parser.py` (after REFERENCE_PATTERN definition, ~line 94)

**Signature**:
```python
def extract_references(content: str | None) -> list[str]:
    """Extract agent references from content string.
    
    Finds all $agent patterns (e.g., $pm, $reviewer, $builder-1) and returns
    a deduplicated list preserving the order of first occurrence.
    
    Args:
        content: String that may contain $agent references.
        
    Returns:
        List of agent reference names (without $ prefix), deduplicated.
    """
```

**Logic**: Extract the existing code from `_parse_agent_command()` lines 219-225.

### Fix Locations

**loop.py** (~line 309): Replace manual `Command` instantiation with:
```python
from teambot.repl.parser import extract_references
# ...
command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
    references=extract_references(command.content),  # ADD THIS
)
```

**app.py** (~line 141): Identical fix pattern.

---

## 17. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | No open questions | - | - | - |

---

## 18. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-17 | BA Agent | Initial specification | Create |

---

## 19. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Code | src/teambot/repl/parser.py:93 | REFERENCE_PATTERN definition |
| REF-002 | Code | src/teambot/repl/parser.py:219-225 | Existing extraction logic in _parse_agent_command |
| REF-003 | Code | src/teambot/repl/loop.py:308-314 | REPL manual Command instantiation |
| REF-004 | Code | src/teambot/ui/app.py:140-146 | UI manual Command instantiation |
| REF-005 | Tests | tests/test_repl/test_parser.py:268-346 | Existing reference parsing tests |
| REF-006 | Artifact | .teambot/default-agent-context/artifacts/problem_statement.md | Business problem definition |

---

## VALIDATION_STATUS: PASS

- Placeholders: 0 remaining
- Sections Complete: 19/19
- Technical Stack: DEFINED (Python, pytest)
- Testing Approach: DEFINED (pytest with pytest-mock, following existing patterns)
- Acceptance Tests: 5 scenarios defined (AT-001 through AT-005)
- Unit Tests: 6 scenarios defined (UT-001 through UT-006)

---

*Next Step: Run specification review to validate completeness before proceeding to implementation.*

<!-- markdown-table-prettify-ignore-end -->
