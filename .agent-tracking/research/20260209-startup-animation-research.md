<!-- markdownlint-disable-file -->
# Research Document: Startup Animation

**Date:** 2026-02-09  
**Feature:** Branded ASCII/Unicode Startup Animation  
**Status:** ✅ Research Complete  
**Spec Reference:** `.teambot/startup-animation/artifacts/`

---

## 📋 Table of Contents

1. [Research Scope](#1-research-scope)
2. [Current Implementation Analysis](#2-current-implementation-analysis)
3. [Entry Point Analysis](#3-entry-point-analysis)
4. [Technical Approach](#4-technical-approach)
5. [Implementation Patterns](#5-implementation-patterns)
6. [Testing Strategy Research](#6-testing-strategy-research)
7. [Task Implementation Requests](#7-task-implementation-requests)
8. [Potential Next Research](#8-potential-next-research)

---

## 1. Research Scope

### 1.1 Objectives

| Objective | Description |
|-----------|-------------|
| **Branded Startup Animation** | Create a distinctive ASCII/Unicode animation that plays during `teambot run` and `teambot init` |
| **Team Assembly Motif** | Visually represent multiple agents converging to form the TeamBot identity |
| **Agent Color Palette** | Use existing 6-agent color palette (blue, cyan, magenta, green, yellow, red) |
| **Duration & Performance** | 3–4 second animation that feels snappy and modern |
| **Configuration Control** | Disable via `--no-animation` CLI flag or `show_startup_animation` in `teambot.json` |
| **Graceful Degradation** | Static banner fallback for non-color/non-Unicode terminals and CI environments |

### 1.2 Success Criteria

- ✅ SC-001: Branded ASCII/Unicode startup animation plays on `teambot run` / `teambot init`
- ✅ SC-002: Animation visually represents agents forming a team (convergence motif)
- ✅ SC-003: Uses existing agent colour palette from `src/teambot/visualization/console.py`
- ✅ SC-004: Total duration 3–4 seconds, feels snappy
- ✅ SC-005: Disableable via `--no-animation` CLI flag
- ✅ SC-006: Disableable via `show_startup_animation` setting in `teambot.json`
- ✅ SC-007: Degrades gracefully to static banner (no color/Unicode, non-TTY)
- ✅ SC-008: No delay when animation is disabled
- ✅ SC-009: Animation does not corrupt subsequent terminal output
- ✅ SC-010: Existing 920 tests pass; new tests cover animation module

### 1.3 Assumptions

- Rich 14.2.0 (installed, `>=13.0.0` in pyproject.toml) provides `Live`, `Panel`, `Text` for animation rendering
- Only ASCII + common Unicode block/braille characters needed (no external assets)
- Must work on macOS, Linux, and Windows Terminal
- Animation auto-disables when `stdout` is not a TTY (CI/non-interactive)

---

## 2. Current Implementation Analysis

### 2.1 Startup Display — Current State

The current startup is a simple styled Rich `Panel` with no animation:

📄 **`src/teambot/cli.py`** (Line 131):
```python
display.print_header("TeamBot Starting")
```

This calls `ConsoleDisplay.print_header()` at **`src/teambot/visualization/console.py`** (Lines 291-293):
```python
def print_header(self, title: str) -> None:
    """Print a styled header."""
    self.console.print(Panel(title, style="bold blue"))
```

Similarly, `cmd_init` uses `display.print_header("Configured Agents")` at **`cli.py`** Line 90, and resume uses `"TeamBot Resuming"` at Line 305.

### 2.2 Agent Color Palette (Reusable)

📄 **`src/teambot/visualization/console.py`** (Lines 44-52):
```python
AGENT_COLORS = {
    "pm": "blue",           # Project Manager
    "ba": "cyan",           # Business Analyst  
    "writer": "magenta",    # Technical Writer
    "builder-1": "green",   # Primary Builder
    "builder-2": "yellow",  # Secondary Builder
    "reviewer": "red",      # Reviewer
}
```

📄 **Agent Icons** (Lines 170-177):
```python
AGENT_ICONS = {
    "pm": "📋",  "ba": "📊",  "writer": "📝",
    "builder-1": "🔨",  "builder-2": "🔨",  "reviewer": "🔍",
}
```

### 2.3 Existing Rich Usage Patterns

| Pattern | Location | Usage |
|---------|----------|-------|
| **Panel** | `console.py:293` | `Panel(title, style="bold blue")` for headers |
| **Table** | `console.py:254-271` | Agent table with columns |
| **Console** | `console.py:209` | `Console()` instance on `ConsoleDisplay` |
| **Live** | `console.py:9` | Imported but used only for `_live` member |
| **Braille Spinner** | `overlay.py:38` | `SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"` |
| **ANSI Sequences** | `overlay.py:28-35` | Cursor save/restore, move, hide/show |
| **Block Characters** | `console.py:277` | `'█'` and `'░'` for progress bars |

### 2.4 TTY / Terminal Capability Detection

Existing pattern in **`src/teambot/visualization/overlay.py`** (Lines 119-142):
```python
def _check_terminal_support(self) -> bool:
    """Check if terminal supports overlay rendering."""
    if not sys.stdout.isatty():
        return False
    try:
        cols, rows = shutil.get_terminal_size()
        if cols < 30 or rows < 10:
            return False
    except (ValueError, OSError):
        return False
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    return True
```

Additional detection in **`src/teambot/ui/app.py`** (Lines 20-41):
```python
def should_use_split_pane() -> bool:
    if os.environ.get("TEAMBOT_LEGACY_MODE"):
        return False
    if not sys.stdout.isatty():
        return False
    cols, _ = shutil.get_terminal_size()
    return cols >= 80
```

### 2.5 Configuration System

📄 **`src/teambot/config/loader.py`**:
- Config loaded from `teambot.json` via `ConfigLoader.load()` (Line 102)
- Validation in `_validate()` (Line 122) — checks agents, default_agent, default_model, overlay
- Defaults applied in `_apply_defaults()` (Line 215) — sets teambot_dir, display defaults, overlay defaults
- Existing pattern for optional section: `overlay` config with `enabled` (bool) and `position` (enum)

📄 **`teambot.json`** — Current structure has no animation settings:
```json
{
    "teambot_dir": ".teambot",
    "default_model": "claude-sonnet-4",
    "default_agent": "pm",
    "agents": [...],
    "workflow": {...}
}
```

### 2.6 CLI Argument Parser

📄 **`src/teambot/cli.py`** (Lines 30-63):
- `create_parser()` defines subparsers for `init`, `run`, `status`
- Global args: `--version`, `-v/--verbose`
- Run-specific args: `objective`, `-c/--config`, `--resume`, `--max-hours`

### 2.7 Package Exports

📄 **`src/teambot/visualization/__init__.py`**:
```python
from teambot.visualization.console import PERSONA_COLORS, AgentStatus, ConsoleDisplay
from teambot.visualization.overlay import OverlayPosition, OverlayRenderer, OverlayState
```

---

## 3. Entry Point Analysis

### 3.1 User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run` (with objective) | `cli.py:main()` → `cmd_run()` → `print_header("TeamBot Starting")` (L131) | ✅ YES | ✅ YES — Replace `print_header` with animation |
| `teambot run` (no objective / REPL) | `cli.py:main()` → `cmd_run()` → `print_header("TeamBot Starting")` (L131) → REPL | ✅ YES | ✅ YES — Same path, animation before REPL |
| `teambot init` | `cli.py:main()` → `cmd_init()` → `print_header("Configured Agents")` (L90) | ✅ YES | ✅ YES — Play animation before init output |
| `teambot run --resume` | `cli.py:main()` → `cmd_run()` → `_run_orchestration_resume()` → `print_header("TeamBot Resuming")` (L305) | ✅ YES | ✅ YES — Animation before resume |
| `teambot status` | `cli.py:main()` → `cmd_status()` → `print_header("TeamBot Status")` (L391) | ❌ NO | ❌ NO — Status is quick info, no animation |
| `teambot --version` | `argparse` handles directly | ❌ NO | ❌ NO |
| Non-TTY / piped output | Same code paths | ⚠️ Degraded | ✅ YES — Static fallback banner |
| CI environment | Same code paths | ⚠️ Degraded | ✅ YES — Auto-detect and skip/degrade |

### 3.2 Code Path Trace

#### Entry Point 1: `teambot run objectives/task.md`
1. User enters: `teambot run objectives/task.md`
2. Handled by: `cli.py:main()` (Lines 411-428) — dispatches to `cmd_run()`
3. Routes to: `cli.py:cmd_run()` (Line 100)
4. Config loaded: `cli.py:111-112` — `ConfigLoader().load(config_path)`
5. **🎯 Animation point**: `cli.py:131` — `display.print_header("TeamBot Starting")`
6. Agents registered: `cli.py:134-142`
7. Status printed: `cli.py:144`
8. Orchestration begins: `cli.py:147-148`

#### Entry Point 2: `teambot init`
1. User enters: `teambot init`
2. Handled by: `cli.py:main()` → `cmd_init()` (Line 66)
3. Config created: `cli.py:76-78`
4. **🎯 Animation point**: `cli.py:90` — `display.print_header("Configured Agents")`
5. Agents displayed: `cli.py:92-95`

#### Entry Point 3: `teambot run --resume`
1. User enters: `teambot run --resume`
2. Handled by: `cli.py:main()` → `cmd_run()` → Line 118-119 → `_run_orchestration_resume()`
3. **🎯 Animation point**: `cli.py:305` — `display.print_header("TeamBot Resuming")`

### 3.3 Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| No `--no-animation` flag | Cannot disable from CLI | Add flag to `create_parser()` |
| No `show_startup_animation` config | Cannot persist disable preference | Add to config validation + defaults |
| No TTY check before animation | Would hang in CI/pipes | Check `sys.stdout.isatty()` before animating |
| No DUMB terminal detection | Would emit broken escape sequences | Check `TERM=dumb` env var |

### 3.4 Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 4. Technical Approach

### 4.1 Recommended Approach: Rich `Live` Display with Frame-Based Animation

**Selected approach:** Use Rich's `Live` display with `transient=True` to render animation frames, then leave a clean final banner.

**Rationale:**
- Rich `Live` is already imported in the codebase (`console.py:9`)
- `Live(transient=True)` cleans up animation frames, leaving only the final banner
- Rich handles terminal color detection and fallback automatically via `Console.color_system`
- Rich's `Text.assemble()` provides efficient styled text composition for each frame
- Frame-based approach gives precise control over timing and effects
- No new dependencies required

### 4.2 Architecture

```
src/teambot/visualization/
├── __init__.py          # Add StartupAnimation export
├── animation.py         # NEW — Animation module
├── console.py           # Existing — import AGENT_COLORS, AGENT_ICONS
└── overlay.py           # Existing — unchanged
```

**New module: `animation.py`** containing:

| Component | Purpose |
|-----------|---------|
| `StartupAnimation` | Main class — orchestrates the animation sequence |
| `TEAMBOT_LOGO` | ASCII art wordmark constant (5-7 lines tall) |
| `AGENT_FRAGMENTS` | Frame data for agent convergence effect |
| `play_startup_animation()` | Public function — convenience wrapper |
| `should_animate()` | Determine if animation should play (TTY, config, flag) |

### 4.3 Animation Design — Team Assembly Concept

**Phase 1 — Agent Convergence (0–2s, ~20 frames at 10fps):**
- Six colored dots/icons start at scattered positions around the terminal
- Each represents an agent using their persona color from `AGENT_COLORS`
- Dots converge toward center, using braille characters (`⠁⠂⠄⡀⢀⠠⠐⠈`) for smooth movement
- Movement uses easing (deceleration) for polished feel

**Phase 2 — Logo Formation (2–3s, ~10 frames at 10fps):**
- Converged elements assemble into the "TeamBot" wordmark
- Logo rendered in block characters (`█▀▄▐▌`) with gradient or multi-color effect
- Each letter section uses a different agent color, reinforcing the team concept

**Phase 3 — Final Banner (3–3.5s, hold):**
- Clean, static final frame showing:
  - TeamBot wordmark in full color
  - Version string: `v0.1.0`
  - Brief tagline: `"AI agents working together"`
- This frame persists (Live context exits, banner remains)

### 4.4 TeamBot ASCII Art Wordmark

Compact block-letter style (~5 lines tall, fits 80-column terminals):

```
 ████████╗███████╗ █████╗ ███╗   ███╗██████╗  ██████╗ ████████╗
 ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝
    ██║   █████╗  ███████║██╔████╔██║██████╔╝██║   ██║   ██║
    ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██╗██║   ██║   ██║
    ██║   ███████╗██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║
    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝
```

**Color mapping for letters** (each letter/section gets an agent color):
- **T** → blue (PM)
- **E** → cyan (BA)
- **A** → magenta (Writer)
- **M** → green (Builder-1)
- **B** → yellow (Builder-2)
- **O** → red (Reviewer)
- **T** → blue (PM — cyclical)

**Fallback (ASCII-only, no Unicode box drawing):**
```
 _____ ___   _   __  __ ___  ___ _____
|_   _| __| /_\ |  \/  | _ )/ _ \_   _|
  | | | _| / _ \| |\/| | _ \ (_) || |
  |_| |___/_/ \_\_|  |_|___/\___/ |_|
```

### 4.5 Animation Rendering Strategy

```python
from rich.live import Live
from rich.text import Text
from rich.console import Console

class StartupAnimation:
    def __init__(self, console: Console, version: str = "0.1.0"):
        self.console = console
        self.version = version

    def should_animate(self, config: dict | None = None, no_animation_flag: bool = False) -> bool:
        """Determine whether to play animation."""
        if no_animation_flag:
            return False
        if config and not config.get("show_startup_animation", True):
            return False
        if not sys.stdout.isatty():
            return False
        term = os.environ.get("TERM", "")
        if term == "dumb":
            return False
        return True

    def play(self, config: dict | None = None, no_animation_flag: bool = False) -> None:
        """Play animation or show static banner."""
        if self.should_animate(config, no_animation_flag):
            self._play_animated()
        else:
            self._show_static_banner()

    def _play_animated(self) -> None:
        """Render animated startup sequence using Rich Live."""
        import time
        frames = self._generate_frames()
        with Live(console=self.console, transient=True, refresh_per_second=15) as live:
            for frame in frames:
                live.update(frame)
                time.sleep(frame.delay)  # stored as metadata
        # Print final persistent banner
        self.console.print(self._final_banner())

    def _show_static_banner(self) -> None:
        """Show non-animated banner for degraded environments."""
        self.console.print(self._final_banner())
```

### 4.6 Frame Generation Approach

**Frame timing budget (3.5s total, ~35 frames):**

| Phase | Frames | Duration | FPS |
|-------|--------|----------|-----|
| Agent dots appear | 6 | 0.5s | 12 |
| Convergence animation | 14 | 1.5s | ~9 |
| Logo reveal | 10 | 1.0s | 10 |
| Final hold | 5 | 0.5s | 10 |
| **Total** | **35** | **3.5s** | ~10 |

Each frame is a Rich `Text` or `Group` renderable composed using `Text.assemble()` with agent-colored spans.

### 4.7 Graceful Degradation Matrix

| Condition | Detection | Behavior |
|-----------|-----------|----------|
| `--no-animation` flag | CLI arg | Skip entirely, no banner |
| `show_startup_animation: false` | Config dict | Skip entirely, no banner |
| Non-TTY (pipe/CI) | `sys.stdout.isatty()` | Static plain-text banner |
| `TERM=dumb` | `os.environ["TERM"]` | Static plain-text banner |
| No Unicode support | `Console.encoding` check | ASCII-only fallback logo |
| No color support | `Console.color_system is None` | Unstyled text banner |
| Narrow terminal (<60 cols) | `shutil.get_terminal_size()` | Compact banner (no ASCII art) |
| `TEAMBOT_NO_ANIMATION` env var | `os.environ` | Skip animation (for testing) |

### 4.8 Configuration Integration

**New `teambot.json` field:**
```json
{
    "show_startup_animation": true
}
```

**Config loader changes** (`src/teambot/config/loader.py`):
1. Add validation for `show_startup_animation` in `_validate()` — must be bool if present
2. Add default `True` in `_apply_defaults()`

**CLI parser changes** (`src/teambot/cli.py`):
1. Add `--no-animation` to global parser (not per-subcommand)
2. Pass flag through to animation logic

---

## 5. Implementation Patterns

### 5.1 Pattern: Rich Live Transient Animation

Based on Rich 14.2.0 `Live` API (verified via docs):
```python
from rich.live import Live
from rich.text import Text

# transient=True removes animation frames on exit
with Live(console=console, transient=True, refresh_per_second=15) as live:
    for frame_text in frames:
        live.update(frame_text)
        time.sleep(0.1)
# After context exit, terminal is clean — print final persistent output
console.print(final_banner)
```

**Key Rich APIs used:**
- `Live(transient=True)` — auto-cleans animation frames
- `Text.assemble(*parts)` — builds styled text from `(str, style)` tuples
- `Console.color_system` — `None`, `"standard"`, `"256"`, `"truecolor"`
- `Console.encoding` — terminal encoding for Unicode detection
- `Console.size` — terminal dimensions (width, height)
- `Panel(content, style=...)` — bordered box for final banner

### 5.2 Pattern: Agent Color Reuse

Import directly from existing module:
```python
from teambot.visualization.console import AGENT_COLORS, AGENT_ICONS

# Colors: {"pm": "blue", "ba": "cyan", "writer": "magenta", ...}
# Icons: {"pm": "📋", "ba": "📊", "writer": "📝", ...}
AGENT_ORDER = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
```

### 5.3 Pattern: TTY Detection (Existing Convention)

Follow the existing overlay pattern from `src/teambot/visualization/overlay.py` (Lines 119-142):
```python
import os
import shutil
import sys

def should_animate() -> bool:
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    try:
        cols, rows = shutil.get_terminal_size()
        if cols < 60 or rows < 10:
            return False
    except (ValueError, OSError):
        return False
    return True
```

### 5.4 Pattern: Config Validation (Existing Convention)

Follow the `overlay` config pattern from `src/teambot/config/loader.py` (Lines 198-213):
```python
# In _validate():
if "show_startup_animation" in config:
    if not isinstance(config["show_startup_animation"], bool):
        raise ConfigError("'show_startup_animation' must be a boolean")

# In _apply_defaults():
if "show_startup_animation" not in config:
    config["show_startup_animation"] = True
```

### 5.5 Pattern: CLI Flag (Existing Convention)

Follow the existing `--verbose` / `--force` patterns:
```python
# In create_parser() — add to main parser (global flag)
parser.add_argument(
    "--no-animation",
    action="store_true",
    help="Disable startup animation",
)
```

### 5.6 Pattern: Visualization Module Test (from test_console.py)

Tests use **direct instantiation** with no mocking of Rich internals:

📄 **`tests/test_visualization/test_console.py`** (Lines 7-14):
```python
def test_create_display(self):
    from teambot.visualization.console import ConsoleDisplay
    display = ConsoleDisplay()
    assert display.agents == {}
    assert display.console is not None
```

For output verification, tests check **data structures** rather than terminal output:
- Assert agent dict values, enum values, table types
- No `capsys` or stdout capture for Rich output (Rich output is trusted)

### 5.7 Pattern: ASCII-Safe Detection

Rich `Console` provides encoding and color system detection:
```python
console = Console()

# Color detection
has_color = console.color_system is not None  # None means no color

# Unicode detection
supports_unicode = console.encoding.lower() in ("utf-8", "utf8")

# Combined
if not has_color:
    # Plain text, no styles
elif not supports_unicode:
    # ASCII-only fallback logo
else:
    # Full Unicode + color animation
```

---

## 6. Testing Strategy Research

### 6.1 Existing Test Infrastructure

| Item | Value |
|------|-------|
| **Framework** | pytest 8.x with pytest-cov, pytest-mock, pytest-asyncio |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` files, `Test*` classes, `test_*` methods |
| **Runner** | `uv run pytest` |
| **Test Count** | 920 tests collected |
| **Coverage** | ~20% overall (per last run), 88% historical for core modules |
| **Config** | `pyproject.toml` Lines 42-48: `testpaths=["tests"]`, `asyncio_mode="auto"` |

### 6.2 Test Patterns Found

📄 **`tests/test_visualization/test_console.py`** (217 lines):
- **No mocking of Rich**: Tests instantiate `ConsoleDisplay` directly
- **Data-focused assertions**: Check dict values, enum states, types
- **Class-per-concern**: `TestConsoleDisplay`, `TestAgentStatus`, `TestPersonaColors`, `TestAgentStyling`
- **No stdout capture**: Rich rendering is not verified (trusted library)

📄 **`tests/test_visualization/test_overlay.py`** (572 lines):
- **Patches terminal support**: `patch.object(OverlayRenderer, "_check_terminal_support", return_value=True)`
- **Mocks sys.stdout.isatty**: For TTY detection tests
- **Mocks shutil.get_terminal_size**: For dimension tests
- **ANSI output verification**: `sys.stdout.write` mock captures escape sequences
- **State mutation tests**: Verify `OverlayState` dataclass changes

📄 **`tests/conftest.py`** (185 lines):
- `temp_teambot_dir` — temporary `.teambot` directory
- `sample_agent_config` — agent configuration dict
- No visualization-specific fixtures

### 6.3 Testing Approach for Animation Module

#### Recommended: **Code-First** (with immediate test coverage)

**Rationale:** The animation module is primarily a visual rendering concern. The core logic (should_animate decision, config integration, frame generation) is testable, but visual output verification is impractical to assert against. Code-first allows rapid iteration on the visual design with test coverage for logic paths.

#### Test Plan

| Test Area | Approach | Coverage Target |
|-----------|----------|-----------------|
| `should_animate()` logic | Unit tests with mock TTY/config/flags | 100% branch coverage |
| Config validation | Unit tests following `test_loader.py` patterns | 100% |
| `--no-animation` flag | CLI parser test | 100% |
| Frame generation | Smoke test (no crash, returns list) | Basic coverage |
| ASCII fallback | Unit test with mock encoding | Full |
| Static banner | Verify returns renderable | Basic |
| Integration | CLI end-to-end with `--no-animation` | Functional |

#### Test File Structure

```
tests/test_visualization/
├── test_console.py          # Existing
├── test_overlay.py          # Existing
└── test_animation.py        # NEW
```

#### Key Test Cases

```python
class TestShouldAnimate:
    """Tests for animation eligibility logic."""
    
    def test_returns_true_when_tty_and_enabled(self): ...
    def test_returns_false_when_no_animation_flag(self): ...
    def test_returns_false_when_config_disabled(self): ...
    def test_returns_false_when_not_tty(self): ...
    def test_returns_false_when_term_is_dumb(self): ...
    def test_returns_false_when_terminal_too_small(self): ...
    def test_returns_true_when_config_is_none(self): ...
    def test_returns_false_when_env_var_set(self): ...

class TestStartupAnimation:
    """Tests for animation rendering."""
    
    def test_play_calls_animated_when_should_animate_true(self): ...
    def test_play_calls_static_when_should_animate_false(self): ...
    def test_static_banner_contains_version(self): ...
    def test_static_banner_contains_teambot_text(self): ...
    def test_frame_generation_returns_nonempty_list(self): ...
    def test_ascii_fallback_uses_no_unicode_box_drawing(self): ...

class TestAnimationConfig:
    """Tests for config integration."""
    
    def test_show_startup_animation_default_true(self): ...
    def test_show_startup_animation_validates_bool(self): ...
    def test_invalid_show_startup_animation_raises_error(self): ...

class TestNoAnimationFlag:
    """Tests for CLI --no-animation flag."""
    
    def test_parser_accepts_no_animation_flag(self): ...
    def test_no_animation_flag_defaults_false(self): ...
```

### 6.4 Coverage Standards

| Component | Target | Rationale |
|-----------|--------|-----------|
| `should_animate()` | 100% | Critical decision logic, all branches |
| Config validation | 100% | Follows existing pattern |
| CLI flag parsing | 100% | Simple, must be correct |
| Frame generation | 80% | Visual output, verify no crash |
| `play()` method | 90% | Integration of above |

---

## 7. Task Implementation Requests

### Task 1: Create Animation Module

**File:** `src/teambot/visualization/animation.py`  
**Description:** New module containing `StartupAnimation` class with:
- `TEAMBOT_LOGO` constant (Unicode) and `TEAMBOT_LOGO_ASCII` (fallback)
- `AGENT_ORDER` list for consistent color cycling
- `should_animate()` method with TTY/config/flag/env checks
- `play()` method orchestrating animated vs static path
- `_play_animated()` using Rich `Live(transient=True)` with frame generation
- `_show_static_banner()` for degraded environments
- `_final_banner()` returning persistent Rich Panel
- `_generate_convergence_frames()` for Phase 1 (agent dots converging)
- `_generate_logo_frames()` for Phase 2 (logo reveal)
- `play_startup_animation()` convenience function

**Dependencies:** Import `AGENT_COLORS`, `AGENT_ICONS` from `console.py`

### Task 2: Update Visualization Package Exports

**File:** `src/teambot/visualization/__init__.py`  
**Description:** Add `StartupAnimation` and `play_startup_animation` to exports

### Task 3: Add `--no-animation` CLI Flag

**File:** `src/teambot/cli.py`  
**Description:**
- Add `--no-animation` argument to main parser in `create_parser()` (after `--verbose`)
- Pass `no_animation` flag to `play_startup_animation()` in `cmd_run()` and `cmd_init()`
- Replace `display.print_header("TeamBot Starting")` (L131) with animation call
- Replace `display.print_header("Configured Agents")` (L90) with animation call
- Replace `display.print_header("TeamBot Resuming")` (L305) with animation call

### Task 4: Add Config Validation for `show_startup_animation`

**File:** `src/teambot/config/loader.py`  
**Description:**
- Add boolean validation for `show_startup_animation` in `_validate()` method
- Add default `True` in `_apply_defaults()` method

### Task 5: Write Animation Tests

**File:** `tests/test_visualization/test_animation.py`  
**Description:** Tests per Section 6.3 test plan covering:
- `should_animate()` all branches
- Static banner content verification
- Config validation integration
- CLI flag parsing
- Frame generation smoke tests

### Task 6: Write Config Validation Tests

**File:** `tests/test_config/test_loader.py` (extend existing)  
**Description:** Add tests for `show_startup_animation` validation:
- Valid boolean accepted
- Non-boolean raises `ConfigError`
- Default applied when missing

---

## 8. Potential Next Research

### 8.1 Visual Design Iteration

- 🎨 **Agent icon convergence patterns**: Research braille/block character combinations that create smooth movement illusion. Consider characters: `⠁⠂⠄⡀⢀⠠⠐⠈` (braille dots), `░▒▓█` (shade blocks)
- 🎨 **Logo color gradient**: Investigate Rich gradient styling for smooth color transitions across the wordmark
- 🎨 **Easing functions**: Research simple easing (ease-out) for convergence deceleration — can use basic quadratic: `t * (2 - t)`

### 8.2 Performance Profiling

- ⏱️ **Animation startup overhead**: Measure time from `import animation` to first frame — should be <50ms
- ⏱️ **`time.sleep()` accuracy**: Python's `time.sleep()` has ~1-15ms jitter on Linux/macOS; acceptable for 10fps animation

### 8.3 Cross-Platform Terminal Testing

- 🖥️ **Windows Terminal**: Verify Unicode box-drawing characters render correctly
- 🖥️ **macOS Terminal.app vs iTerm2**: Test color rendering differences
- 🖥️ **tmux/screen**: Test nested terminal multiplexer compatibility
