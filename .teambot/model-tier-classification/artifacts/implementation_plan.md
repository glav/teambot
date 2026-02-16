<!-- markdownlint-disable-file -->
# Implementation Plan: Model Tier Classification Fix

**Date**: 2026-02-16  
**Feature**: Model Tier Classification Fix  
**Status**: Ready for Implementation

## Overview

Fix model tier classification to derive tier from `billing.multiplier` instead of the non-existent `capabilities.tier` SDK attribute.

## Objectives

1. Extract tier category from `billing.multiplier` SDK attribute
2. Add `multiplier` field to `TeamBotModelInfo` and cache
3. Update `/models` command to display multiplier
4. Remove warning spam for "missing tier"
5. Achieve 100% test coverage for tier mapping logic

## Tier Mapping Specification

| Multiplier Range | Tier |
|-----------------|------|
| 0.0 - 0.5 | fast |
| 0.51 - 1.5 | standard |
| > 1.5 | premium |
| None/negative | standard (fallback) |

## Phase Summary

| Phase | Tasks | Approach | Effort |
|-------|-------|----------|--------|
| 1. TDD Test Setup | 3 | TDD | 30 min |
| 2. Core Implementation | 3 | Code | 45 min |
| 3. Cache Updates | 4 | Code | 20 min |
| 4. Display Updates | 2 | Code-First | 15 min |
| 5. Validation | 3 | Verification | 15 min |
| **Total** | **15** | Mixed | ~2 hours |

## Task Breakdown

### Phase 1: TDD Test Setup

- [ ] **1.1** Write parametrized boundary value tests for tier mapping
- [ ] **1.2** Write silent fallback test (no warning on missing data)
- [ ] **1.3** Delete obsolete warning tests (2 tests)

### Phase 2: Core Implementation

- [ ] **2.1** Add `multiplier: float | None = None` to `TeamBotModelInfo`
- [ ] **2.2** Add helper functions: `_extract_multiplier()`, `_get_tier_from_multiplier()`
- [ ] **2.3** Rewrite `_adapt_model_info()` to use billing.multiplier

### Phase 3: Cache Updates

- [ ] **3.1** Add `multiplier` field to `CachedModel` dataclass
- [ ] **3.2** Update `load_cache()` to read multiplier
- [ ] **3.3** Update `save_cache()` to write multiplier
- [ ] **3.4** Update `schema.py` to propagate multiplier

### Phase 4: Display Updates

- [ ] **4.1** Update `/models` to show `[{multiplier}x]` suffix
- [ ] **4.2** Add display integration test

### Phase 5: Validation

- [ ] **5.1** Run full test suite: `uv run pytest`
- [ ] **5.2** Verify coverage: `uv run pytest --cov=src/teambot`
- [ ] **5.3** Lint check: `uv run ruff check . && uv run ruff format --check .`

## Files to Modify

| File | Changes |
|------|---------|
| `src/teambot/copilot/sdk_client.py` | Add multiplier field, helper functions, rewrite adapter |
| `src/teambot/config/model_cache.py` | Add multiplier to CachedModel, update load/save |
| `src/teambot/config/schema.py` | Add multiplier to cached model dict |
| `src/teambot/repl/commands.py` | Display multiplier in /models output |
| `tests/test_copilot/test_sdk_client.py` | Delete 2 tests, add 4 new tests, update 3 tests |

## Success Criteria

- [ ] No "missing tier" warnings logged during model refresh
- [ ] Models display correct tier classification (e.g., `claude-opus-4.5` shows as premium)
- [ ] `/models` command shows multiplier: `gpt-5 (GPT-5) [1.0x]`
- [ ] Graceful fallback to "standard" if `billing.multiplier` is unavailable
- [ ] All tests pass
- [ ] Coverage maintained at 80%+

## References

- **Plan Details**: `.agent-tracking/plans/20260216-model-tier-classification-plan.instructions.md`
- **Implementation Details**: `.agent-tracking/details/20260216-model-tier-classification-details.md`
- **Research**: `.teambot/model-tier-classification/artifacts/research.md`
- **Test Strategy**: `.teambot/model-tier-classification/artifacts/test_strategy.md`
