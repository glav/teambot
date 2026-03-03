# Operation Cost Visibility

## Objective

**Goal**: Add comprehensive token usage and cost visibility to TeamBot interactions

**Problem Statement**: Currently, users have no visibility into how many tokens are consumed during TeamBot interactions. This makes it difficult to understand the "cost" of running orchestrations or interactive sessions, plan resource usage, and identify potentially expensive operations. Token visibility is needed for both file-based orchestration and interactive mode.

**Success Criteria**:
- [ ] Total tokens consumed are recorded and displayed for file-based orchestration runs
- [ ] Token usage is tracked per-agent during orchestration
- [ ] Token usage is tracked per-stage during orchestration
- [ ] End-of-run summary displays token costs for file-based orchestration
- [ ] Token usage data is persisted with a documented schema (JSON format, integrated with workflow state)
- [ ] Interactive mode displays session token usage via end-of-session summary (MVP)
- [ ] Token tracking degrades gracefully when data is unavailable (displays warning, continues operation)
- [ ] Input/output token breakdown is captured (if available from source)
- [ ] Token tracking does not negatively impact performance or user experience

---

## Pre-Requisite: Feasibility Research (BLOCKING)

> ⚠️ **This research must be completed before progressing to SPEC phase**

The current Copilot client implementation (`src/teambot/copilot/client.py` and `sdk_client.py`) does not capture token usage data. The `CopilotResult` dataclass only includes: `success`, `output`, `error`, `exit_code`, `prompt` — no token fields.

**Research Tasks**:
1. [ ] Examine Copilot CLI output (`copilot --help`, verbose modes) to determine if token/usage data is exposed
2. [ ] Review SDK streaming events for usage metadata fields beyond `delta_content`
3. [ ] Determine if token data is available in response headers or final event payloads
4. [ ] Document findings and update this objective with confirmed data source

**Behavior if Token Data Unavailable**:
- **No estimation** — Do not use `tiktoken` or character counts as fallback
- Display `n/a` or equivalent when token data is not available from the source
- Log a warning on first occurrence, then continue silently
- The `data_source` field should indicate `unavailable`

**Resolved Questions**:
1. ✅ **Estimation acceptable?** No — display `n/a` if native token data is unavailable
2. ✅ **Default behavior?** Token tracking is **enabled by default** (opt-out via config)
3. ✅ **Per-call tracking required?** No — session-level is sufficient for MVP, but must be **easily visible**

---

## Technical Context

**Target Codebase**: /workspaces/teambot/src/teambot/

**Primary Language/Framework**: Python / CLI (Click)

**Testing Preference**: TDD

**Key Constraints**:
- Token data must be obtained from Copilot CLI/SDK responses (pending feasibility research)
- Must not introduce new external dependencies (pure Python only)
- No estimation fallback — display `n/a` if token data unavailable
- Must work with both CLI wrapper (`client.py`) and SDK client (`sdk_client.py`)
- Must not slow down or disrupt the existing workflow
- Should gracefully handle cases where token data is unavailable (display `n/a`, log warning once)
- Data persistence should integrate with existing `workflow_state.json` structure
- Token tracking is **enabled by default** (opt-out via configuration)

---

## Additional Context

### Feature Requirements by Mode

**File-Based Orchestration:**
1. Track total tokens consumed across the entire run
2. Break down token usage by agent (pm, ba, writer, builder-1, builder-2, reviewer)
3. Break down token usage by workflow stage
4. Optionally track token usage per task within a stage
5. Display a summary at the end of the run showing all cost metrics
6. Persist the data in `workflow_state.json` with documented schema

**Interactive Mode (MVP):**
1. Show session-level token accumulation via **end-of-session summary** (primary display mechanism)
2. Session-level tracking is sufficient for MVP
3. Summary must be **easily visible** — displayed automatically when session ends (not hidden in logs)

**Interactive Mode (Future Enhancements):**
- Per-call token usage display
- Subtle status bar element showing running total
- On-demand display via a `/tokens` or `/cost` command
- Periodic summary after N calls

### Implementation Considerations

- Research what token/usage data the Copilot CLI provides in its responses (see Feasibility Research section)
- Consider a `TokenTracker` component that can be injected into the orchestrator and agent runners
- Ensure the approach is extensible for future cost metrics (e.g., actual monetary cost estimates)
- Consider configuration options to enable/disable cost tracking or adjust display verbosity
- **Integrate with existing multiplier infrastructure**: `sdk_client.py` already has `_extract_multiplier` and `_get_tier_from_multiplier` for model tiers — token tracker should be designed to work with this
- **Handle multi-model runs**: Different models may have different token counting (GPT vs Claude) — document approach for normalization or use raw counts with model annotation

### Data Schema (Proposed)

Token usage data will be persisted in `workflow_state.json` under a new `token_usage` key:

```json
{
  "token_usage": {
    "total": {
      "input_tokens": 12500,
      "output_tokens": 8200,
      "total_tokens": 20700
    },
    "by_agent": {
      "pm": { "input_tokens": 2000, "output_tokens": 1500, "total_tokens": 3500 },
      "builder-1": { "input_tokens": 5000, "output_tokens": 3000, "total_tokens": 8000 }
    },
    "by_stage": {
      "PLAN": { "input_tokens": 3000, "output_tokens": 2000, "total_tokens": 5000 },
      "IMPLEMENTATION": { "input_tokens": 8000, "output_tokens": 5000, "total_tokens": 13000 }
    },
    "model_info": {
      "primary_model": "gpt-4",
      "multiplier": 1.0
    },
    "data_source": "sdk_response | estimated | unavailable"
  }
}
```

### Related Components

- `src/teambot/orchestrator.py` - Agent lifecycle and workflow management
- `src/teambot/agent_runner.py` - Individual agent process execution
- `src/teambot/copilot/client.py` - Copilot CLI wrapper (`CopilotResult` dataclass needs extension)
- `src/teambot/copilot/sdk_client.py` - SDK client (has `_extract_multiplier`, `_get_tier_from_multiplier`)
- `src/teambot/workflow/` - Workflow state machine (state persistence location)
- `src/teambot/visualization/` - Rich console display (for output formatting)

---

## Out of Scope (Future Enhancements)

The following are explicitly **not** part of this objective but may be addressed in future work:

- **Monetary cost calculation** — Requires pricing API or hardcoded rate tables
- **Real-time cost alerts/limits** — "Stop if cost exceeds X" functionality
- **Historical cost dashboards** — Aggregated reporting across multiple runs
- **Per-call display in interactive mode** — MVP uses session summary only
- **Status bar token indicator** — Complex UI change deferred to future

---

## Notes

- Token tracking should be designed as an extensible system that could later support monetary cost calculations if pricing data becomes available
- Consider making the level of detail configurable (minimal, standard, verbose)
- The `data_source` field in the schema indicates whether tokens are from actual API response, estimated, or unavailable — important for transparency
