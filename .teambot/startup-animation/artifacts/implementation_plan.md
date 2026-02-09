<!-- markdownlint-disable-file -->
# Implementation Plan: Startup Animation

> This is the stage artifact for the Plan stage. Full implementation details are in the SDD tracking files.

**Plan:** `.agent-tracking/plans/20260209-startup-animation-plan.instructions.md`
**Details:** `.agent-tracking/details/20260209-startup-animation-details.md`
**Research:** `.agent-tracking/research/20260209-startup-animation-research.md`
**Test Strategy:** `.agent-tracking/test-strategies/20260209-startup-animation-test-strategy.md`

---

## Summary

Create a branded ASCII/Unicode startup animation for TeamBot that plays during `teambot run` and `teambot init`. The animation uses the existing agent color palette (6 agents × 6 colors) to show a convergence motif — colored dots representing agents assembling into the TeamBot wordmark — rendered via Rich `Live` display over ~3.5 seconds.

## Phases (6 phases, 18 tasks)

| Phase | Tasks | Description |
|-------|-------|-------------|
| **1. Core Animation Module** | T1.1–T1.4 | Create `animation.py` with `StartupAnimation` class, `should_animate()` logic, static banner, ASCII art |
| **2. Animation Rendering** | T2.1–T2.3 | Frame generation (convergence + logo reveal), Rich Live playback, play dispatcher |
| **3. Configuration Integration** | T3.1–T3.3 | Config validation (`show_startup_animation`), CLI flag (`--no-animation`), package exports |
| **4. CLI Integration** | T4.1–T4.3 | Wire animation into `cmd_run`, `cmd_init`, `_run_orchestration_resume` |
| **5. Testing** | T5.1–T5.5 | 22 new tests: should_animate (8), class (6), config (3), CLI flag (2), integration (3) |
| **6. Validation** | T6.1–T6.3 | Full test suite, manual visual verification, lint check |

## Files Changed

| File | Action |
|------|--------|
| `src/teambot/visualization/animation.py` | CREATE |
| `src/teambot/visualization/__init__.py` | MODIFY |
| `src/teambot/config/loader.py` | MODIFY |
| `src/teambot/cli.py` | MODIFY |
| `tests/test_visualization/test_animation.py` | CREATE |
| `tests/test_config/test_loader.py` | MODIFY |
| `tests/test_cli.py` | MODIFY |

## Testing Approach

**Code-First** (per test strategy) — implement code, then write comprehensive tests. TDD-style targeted coverage for `should_animate()` decision logic (100% branch coverage target). Overall animation module target: 80%+ coverage.

## Critical Path

T1.1 → T1.4 → T2.1 → T2.2 → T2.3 → T4.1 → T5.1 → T6.1

## Next Step

Run **Step 6** (`sdd.6-review-plan.prompt.md`) to validate the plan before implementation.
