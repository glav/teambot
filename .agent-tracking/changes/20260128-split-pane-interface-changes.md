# Implementation Changes: Split-Pane Terminal Interface

**Date**: 2026-01-28
**Feature Spec**: docs/feature-specs/split-pane-interface.md
**Plan**: .agent-tracking/plans/20260128-split-pane-interface-plan.instructions.md

## Summary

Implemented a split-pane terminal interface for TeamBot using the Textual framework. The interface separates user input (left pane, 30%) from agent output (right pane, 70%), enabling stable input and asynchronous output display.

## Files Created

### Source Files
- `src/teambot/ui/__init__.py` - Module exports
- `src/teambot/ui/app.py` - TeamBotApp main application with split-pane layout
- `src/teambot/ui/widgets/__init__.py` - Widget exports
- `src/teambot/ui/widgets/input_pane.py` - InputPane with command history navigation
- `src/teambot/ui/widgets/output_pane.py` - OutputPane with timestamps and status indicators
- `src/teambot/ui/styles.css` - Textual CSS for layout

### Test Files
- `tests/test_ui/__init__.py` - Test module marker
- `tests/test_ui/conftest.py` - Textual test fixtures
- `tests/test_ui/test_app.py` - TeamBotApp tests (6 tests)
- `tests/test_ui/test_input_pane.py` - InputPane tests (4 tests)
- `tests/test_ui/test_output_pane.py` - OutputPane tests (7 tests)
- `tests/test_ui/test_integration.py` - Integration tests (8 tests)

## Files Modified

### pyproject.toml
- Added `textual>=0.47.0` to dependencies
- Added `textual[dev]>=0.47.0` to dev dependencies (note: Textual 7.x doesn't have dev extra)

### src/teambot/repl/loop.py
- Modified `run_interactive_mode()` to choose between Textual and legacy mode
- Added import for `TeamBotApp` and `should_use_split_pane`
- Added fallback logic based on terminal size, TTY, and env vars

## Key Features Implemented

1. **Split-Pane Layout**
   - Left pane (30%): Input with prompt
   - Right pane (70%): Output with auto-scroll
   - CSS-based layout using Textual framework

2. **Fallback Mode**
   - Triggers for terminals < 80 columns
   - Triggers when stdout is not a TTY
   - Triggers when `TEAMBOT_LEGACY_MODE=true`
   - Can force split-pane with `TEAMBOT_SPLIT_PANE=true`

3. **Command History**
   - Up/down arrow navigation
   - Preserves current input when navigating
   - History stored per session

4. **Output Formatting**
   - Timestamps on all messages (HH:MM:SS)
   - Status indicators: ✓ (success), ✗ (error), ℹ (info)
   - Command echo with `>` prefix
   - Auto-scroll to latest output

5. **Integration**
   - Routes @agent commands to TaskExecutor
   - Routes /commands to system router
   - Supports `/clear` command to clear output pane
   - Task completion callback writes to output pane

## Test Coverage

| Component | Coverage |
|-----------|----------|
| ui/__init__.py | 100% |
| ui/app.py | 97% |
| ui/widgets/__init__.py | 100% |
| ui/widgets/input_pane.py | 94% |
| ui/widgets/output_pane.py | 100% |

**Total UI Tests**: 25
**Total Project Tests**: 489 (all passing)

## Environment Variables

| Variable | Effect |
|----------|--------|
| `TEAMBOT_LEGACY_MODE=true` | Force legacy single-pane mode |
| `TEAMBOT_SPLIT_PANE=true` | Force split-pane mode (overrides other checks) |

## Breaking Changes

None. Legacy mode is preserved as fallback.

## Dependencies Added

- `textual>=0.47.0` - Terminal UI framework by Textualize

## How to Test

```bash
# Run split-pane interface (requires wide terminal)
uv run teambot run

# Force split-pane mode
TEAMBOT_SPLIT_PANE=true uv run teambot run

# Force legacy mode
TEAMBOT_LEGACY_MODE=true uv run teambot run

# Run tests
uv run pytest tests/test_ui/ -v
```
