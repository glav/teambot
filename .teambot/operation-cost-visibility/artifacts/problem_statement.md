# Problem Statement: Operation Cost Visibility

## Business Problem

**TeamBot users have no visibility into the operational costs of their AI-assisted workflows.**

When running orchestrated multi-agent workflows or interactive sessions, users cannot:
- Understand how many tokens are being consumed
- See which agents or workflow stages are most resource-intensive
- Track costs across sessions or projects
- Make informed decisions about model selection based on cost/value tradeoffs

This lack of transparency creates several business risks:
1. **Budget management uncertainty** — Organizations cannot forecast or control AI operational costs
2. **Optimization blindness** — No data to identify inefficient prompts, agents, or stages
3. **Accountability gaps** — Cannot attribute costs to specific workflows or team members
4. **Adoption friction** — Users hesitant to adopt tool without cost visibility

---

## Goals

| Goal | Description | Priority |
|------|-------------|----------|
| **G1** | Capture token usage from Copilot CLI/SDK responses | High |
| **G2** | Display total token consumption at end of orchestration runs | High |
| **G3** | Track and display usage broken down by agent | Medium |
| **G4** | Track and display usage broken down by workflow stage | Medium |
| **G5** | Persist token data with documented schema | Medium |
| **G6** | Display session token usage in interactive mode | Medium |
| **G7** | Degrade gracefully when token data unavailable | High |
| **G8** | Capture input/output token breakdown (when available) | Low |

---

## Success Criteria

### Orchestration Mode (File-based runs)

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-1 | Total tokens consumed are recorded and displayed for orchestration runs | Run `teambot run <objective>`, verify token totals appear in summary |
| SC-2 | Per-agent token usage is tracked and visible | Verify breakdown shows tokens per agent (pm, builder-1, etc.) |
| SC-3 | Per-stage token usage is tracked and visible | Verify breakdown shows tokens per stage (SPEC, IMPLEMENTATION, etc.) |
| SC-4 | End-of-run summary displays token costs | Verify summary section appears before exit |
| SC-5 | Token data persisted in workflow state | Inspect `.teambot/workflow_state.json` for token data with documented schema |

### Interactive Mode

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-6 | End-of-session summary displays token usage | Exit interactive mode, verify token summary appears |

### Robustness

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| SC-7 | Graceful degradation when data unavailable | Simulate missing token data, verify `n/a` displayed and warning logged (once) |
| SC-8 | Input/output breakdown captured when available | Verify prompt_tokens and completion_tokens stored separately |
| SC-9 | No negative performance impact | Benchmark before/after, verify no significant degradation |

---

## Stakeholders

| Stakeholder | Interest | Impact |
|-------------|----------|--------|
| **TeamBot Users** | Understand costs, optimize usage | Primary beneficiary |
| **Team Leads** | Budget forecasting, resource allocation | Decision support |
| **Finance/Operations** | Cost tracking, chargeback | Accountability data |
| **Developers** | Optimize prompts, agent efficiency | Performance insights |

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| **Token data from Copilot CLI/SDK only** | Cannot estimate or fabricate data; source of truth is the Copilot response |
| **No new external dependencies** | Must use pure Python; maintain lightweight footprint |
| **No estimation fallback** | Display `n/a` if unavailable; honesty over approximation |
| **Works with both client.py and sdk_client.py** | Full coverage across CLI wrapper and SDK client |
| **No workflow disruption** | Must not slow down or break existing orchestration |
| **Integrate with workflow_state.json** | Use existing persistence mechanisms; no new state files |
| **Enabled by default** | Opt-out via configuration, not opt-in |

---

## Assumptions

| Assumption | Risk if Invalid |
|------------|-----------------|
| Copilot CLI/SDK responses include token usage data | Feature may display `n/a` for all runs; requires feasibility research |
| Token data structure is consistent across models | May need model-specific parsing logic |
| Workflow state file can accommodate additional data | May need schema migration |
| Performance overhead of tracking is negligible | May need lazy/batched aggregation |

---

## Dependencies

| Dependency | Description | Status |
|------------|-------------|--------|
| **Copilot CLI/SDK token response** | Source of token usage data | Pending feasibility research |
| **Workflow state persistence** | Existing mechanism in `workflow/state_machine.py` | Available |
| **Message protocol** | Existing `AgentMessage.payload` structure | Available |
| **Task model** | Existing `Task` dataclass for execution tracking | Available |
| **Configuration system** | Existing `config/` module for settings | Available |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Token data not available from Copilot | Medium | High | Graceful degradation; display `n/a`, log warning |
| Token data format varies by model | Medium | Medium | Abstract parsing layer; model-specific handlers |
| Performance overhead too high | Low | Medium | Lazy aggregation; async tracking |
| Schema changes break existing state files | Low | Medium | Versioned schema; migration support |

---

## Out of Scope

The following are explicitly **not** included in this feature:

- **Cost estimation in dollars** — No price-per-token calculations (requires external rate data)
- **Historical trend analysis** — No dashboards or visualizations across multiple runs
- **Budget enforcement** — No automatic limits or stops based on token consumption
- **Real-time cost display** — Summary only, not streaming updates during execution
- **Token prediction** — No forecasting of expected usage before execution
- **Third-party reporting integration** — No export to external cost management tools

---

## Glossary

| Term | Definition |
|------|------------|
| **Token** | Unit of text processing in LLMs; approximately 4 characters or 0.75 words |
| **Prompt tokens** | Tokens in the input sent to the model (input_tokens) |
| **Completion tokens** | Tokens in the model's response (output_tokens) |
| **Orchestration run** | File-based execution of a multi-agent workflow via `teambot run` |
| **Interactive mode** | Single-agent session via `teambot chat` or similar |
| **Workflow state** | Persisted state in `.teambot/workflow_state.json` tracking execution progress |

---

## Next Steps

1. **Feasibility Research** — Investigate Copilot CLI/SDK response structures for token data availability
2. **Schema Design** — Define JSON schema for token tracking in workflow state
3. **Specification** — Create detailed feature specification with technical approach
4. **Implementation Planning** — Break down into tasks with test strategies

---

*Document created: 2026-03-03*
*Stage: BUSINESS_PROBLEM*
*Author: Business Analyst Agent*
