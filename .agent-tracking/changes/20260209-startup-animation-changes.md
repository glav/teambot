<!-- markdownlint-disable-file -->
# Release Changes: Startup Animation

**Related Plan**: 20260209-startup-animation-plan.instructions.md
**Implementation Date**: 2026-02-09

## Summary

Implemented branded ASCII/Unicode startup animation for TeamBot CLI with team assembly convergence motif, agent color palette, configuration controls (`--no-animation` flag, `show_startup_animation` config), and graceful degradation for non-TTY/dumb/narrow terminals.

## Changes

### Added

* `src/teambot/visualization/animation.py` — New animation module with `StartupAnimation` class, frame generation, Rich Live rendering, `should_animate()` decision logic, static banner fallback, and `play_startup_animation()` convenience function
* `tests/test_visualization/test_animation.py` — 18 tests covering `should_animate()` branches, `StartupAnimation` class dispatch, static banner content, frame generation, ASCII fallback, constants, and convenience function

### Modified

* `src/teambot/visualization/__init__.py` — Added `StartupAnimation` and `play_startup_animation` to package exports
* `src/teambot/config/loader.py` — Added `show_startup_animation` boolean validation in `_validate()` and default `True` in `_apply_defaults()`
* `src/teambot/cli.py` — Added `--no-animation` global CLI flag; replaced `print_header()` calls in `cmd_run()`, `cmd_init()`, and `_run_orchestration_resume()` with `play_startup_animation()` calls; added `no_animation` parameter to `_run_orchestration_resume()`
* `tests/test_config/test_loader.py` — Added `TestAnimationConfig` class with 3 tests for config validation
* `tests/test_cli.py` — Added 2 tests for `--no-animation` flag parsing

### Removed

* None

## Release Summary

**Total Files Affected**: 7

### Files Created (2)

* `src/teambot/visualization/animation.py` — Startup animation module
* `tests/test_visualization/test_animation.py` — Animation test suite

### Files Modified (5)

* `src/teambot/visualization/__init__.py` — Added exports
* `src/teambot/config/loader.py` — Added config validation and defaults
* `src/teambot/cli.py` — Added CLI flag and animation wiring
* `tests/test_config/test_loader.py` — Added config validation tests
* `tests/test_cli.py` — Added CLI flag tests

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None (uses existing Rich >= 13.0.0)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: New optional `show_startup_animation` boolean field in `teambot.json`

### Deployment Notes

Animation auto-disables in non-TTY environments (CI, pipes). No breaking changes to existing configuration files — missing `show_startup_animation` defaults to `true`.
