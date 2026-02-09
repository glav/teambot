<!-- markdownlint-disable-file -->
# Task Details: Startup Animation

**Research Reference:** `.agent-tracking/research/20260209-startup-animation-research.md`
**Test Strategy Reference:** `.agent-tracking/test-strategies/20260209-startup-animation-test-strategy.md`
**Plan Reference:** `.agent-tracking/plans/20260209-startup-animation-plan.instructions.md`

---

## Phase 1: Core Animation Module

### T1.1: Create animation.py scaffold (Lines 12-27)

**File:** `src/teambot/visualization/animation.py` (CREATE)

**Specifications:**
- Module docstring: `"""Startup animation for TeamBot CLI."""`
- Imports: `sys`, `os`, `shutil`, `time` from stdlib; `Console`, `Panel`, `Text`, `Live`, `Group` from `rich`; `AGENT_COLORS`, `AGENT_ICONS` from `teambot.visualization.console`
- Class: `StartupAnimation`
  - `__init__(self, console: Console, version: str = "0.1.0")` — store console and version
- Constant: `AGENT_ORDER = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]`

**Research Reference:** Research Lines 282-310 (Architecture section)

**Success Criteria:**
- Module imports without error
- `StartupAnimation(Console())` instantiates without error

---

### T1.2: Implement should_animate() (Lines 31-53)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add method)

**Method signature:**
```python
def should_animate(self, config: dict | None = None, no_animation_flag: bool = False) -> bool:
```

**Logic (ordered — first match returns False):**
1. If `no_animation_flag is True` → return `False`
2. If `config is not None and config.get("show_startup_animation", True) is False` → return `False`
3. If `os.environ.get("TEAMBOT_NO_ANIMATION")` is set (any value) → return `False`
4. If `not sys.stdout.isatty()` → return `False`
5. If `os.environ.get("TERM", "") == "dumb"` → return `False`
6. If terminal size < 60 cols or < 10 rows (via `shutil.get_terminal_size()`) → return `False`
7. Otherwise → return `True`

**Research Reference:** Research Lines 314-340 (should_animate pattern), Lines 452-468 (TTY detection pattern)

**Success Criteria:**
- Returns `True` for standard TTY with animation enabled
- Returns `False` for each of the 6 disable conditions independently

---

### T1.3: Implement static banner and final banner (Lines 57-81)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add methods)

**Methods:**

`_final_banner(self) -> Panel`:
- Detect capabilities: `self.console.color_system`, `self.console.encoding`, `self.console.size.width`
- If width < 60: return compact `Panel(f"TeamBot v{self.version}", style="bold blue")`
- If encoding not UTF-8: use `TEAMBOT_LOGO_ASCII`
- Otherwise: use `TEAMBOT_LOGO` with agent-colored sections
- Build `Text.assemble()` with `(letter_section, color)` tuples for each letter
- Append version line: `f"  v{self.version} — AI agents working together"`
- Return `Panel(assembled_text, style="bold blue", padding=(1, 2))`

`_show_static_banner(self) -> None`:
- Simply call `self.console.print(self._final_banner())`

**Research Reference:** Research Lines 342-388 (banner design), Lines 502-514 (ASCII-safe detection)

**Success Criteria:**
- `_final_banner()` returns a Rich `Panel` renderable
- Banner contains "TeamBot" and version string
- Narrow terminal produces compact banner
- Non-UTF-8 terminal uses ASCII fallback

---

### T1.4: Define ASCII art wordmarks (Lines 85-128)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add constants)

**Constants:**

`TEAMBOT_LOGO` — Unicode box-drawing wordmark (~6 lines, ≤65 cols):
```
 ████████╗███████╗ █████╗ ███╗   ███╗██████╗  ██████╗ ████████╗
 ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝
    ██║   █████╗  ███████║██╔████╔██║██████╔╝██║   ██║   ██║
    ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██╗██║   ██║   ██║
    ██║   ███████╗██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║
    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝
```

`TEAMBOT_LOGO_ASCII` — Pure ASCII fallback (~4 lines):
```
 _____ ___   _   __  __ ___  ___ _____
|_   _| __| /_\ |  \/  | _ )/ _ \_   _|
  | | | _| / _ \| |\/| | _ \ (_) || |
  |_| |___/_/ \_\_|  |_|___/\___/ |_|
```

**Color map for letter sections** (each letter block maps to an agent color):
- T (cols 1-9) → `blue` (PM)
- E (cols 10-18) → `cyan` (BA)
- A (cols 19-25) → `magenta` (Writer)
- M (cols 26-39) → `green` (Builder-1)
- B (cols 40-47) → `yellow` (Builder-2)
- O (cols 48-56) → `red` (Reviewer)
- T (cols 57-65) → `blue` (PM — cyclical)

**Research Reference:** Research Lines 360-400 (ASCII art designs, color mapping)

**Success Criteria:**
- Both wordmarks are valid multi-line strings
- Unicode wordmark fits within 65 columns
- ASCII wordmark contains no Unicode characters
- Color map covers all letter positions

---

## Phase 2: Animation Rendering

### T2.1: Implement frame generation (Lines 130-164)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add methods)

**Methods:**

`_generate_convergence_frames(self) -> list[Text]`:
- 20 frames at ~10fps (~2 seconds)
- 6 agent dots, each using its color from `AGENT_COLORS`
- Starting positions: scattered around a notional grid (top-left, top-right, mid-left, mid-right, bottom-left, bottom-right)
- End position: center of grid
- Movement: linear interpolation with ease-out — `t_eased = t * (2 - t)` where `t` goes 0→1 over 20 frames
- Each frame builds a Rich `Text` object representing the grid state
- Use braille characters for dot representation: `⠿` (full braille) or `●` for agent positions
- Grid size: determined by terminal width (capped at 60 cols × 10 rows)

`_generate_logo_frames(self) -> list[Text]`:
- 10 frames at ~10fps (~1 second)
- Progressive reveal of `TEAMBOT_LOGO` from left to right
- Each frame shows an increasing number of columns of the logo
- Revealed portions use agent colors; unrevealed portions are blank
- Final frame shows complete colored logo

**Frame data structure:** Each frame is a `Text` renderable with associated timing:
- Store frames as list of tuples: `(renderable, delay_seconds)`
- Convergence delays: 0.1s each (20 × 0.1 = 2.0s)
- Logo reveal delays: 0.1s each (10 × 0.1 = 1.0s)

**Research Reference:** Research Lines 340-360 (animation phases), Lines 390-420 (frame timing budget)

**Success Criteria:**
- `_generate_convergence_frames()` returns list of 15-25 Rich renderables
- `_generate_logo_frames()` returns list of 8-12 Rich renderables
- No frame raises an exception when rendered to a `Console(file=StringIO())`
- Total frame count yields ~3-3.5s animation at specified delays

---

### T2.2: Implement _play_animated() (Lines 168-195)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add method)

**Method:**
```python
def _play_animated(self) -> None:
```

**Logic:**
1. Generate convergence frames: `convergence = self._generate_convergence_frames()`
2. Generate logo frames: `logo = self._generate_logo_frames()`
3. Combine: `all_frames = convergence + logo`
4. Open `Live(console=self.console, transient=True, refresh_per_second=15)` context
5. Iterate frames: `for renderable, delay in all_frames: live.update(renderable); time.sleep(delay)`
6. After `Live` exits: `self.console.print(self._final_banner())`

**Error handling:**
- Wrap in try/except: if any rendering error occurs, fall back to `_show_static_banner()`
- This ensures animation bugs never break the CLI startup

**Research Reference:** Research Lines 260-280 (Rich Live pattern), Lines 422-435 (graceful degradation)

**Success Criteria:**
- Method completes without error in TTY environment
- Rich `Live` context cleans up animation frames (transient=True)
- Final banner persists after animation
- Errors in animation fall back to static banner

---

### T2.3: Implement play() and convenience function (Lines 199-232)

**File:** `src/teambot/visualization/animation.py` (MODIFY — add method + function)

**Method:**
```python
def play(self, config: dict | None = None, no_animation_flag: bool = False) -> None:
```
- Three-way dispatch per research §4.7 degradation matrix:
  1. Check explicit disable (flag, config setting, `TEAMBOT_NO_ANIMATION` env var) → return immediately, no output
  2. Check environment limitations (non-TTY, `TERM=dumb`, narrow terminal) → call `self._show_static_banner()`
  3. Otherwise → call `self._play_animated()`
- This requires splitting `should_animate()` into two checks or returning a richer signal (e.g., `_get_animation_mode() -> Literal["animate", "static", "skip"]`)

**Module-level function:**
```python
def play_startup_animation(
    console: Console,
    config: dict | None = None,
    no_animation_flag: bool = False,
    version: str = "0.1.0",
) -> None:
```
- Create `StartupAnimation(console, version)` and call `.play(config, no_animation_flag)`

**Research Reference:** Research Lines 310-320 (play dispatcher)

**Success Criteria:**
- `play()` dispatches correctly based on `should_animate()` result
- `play_startup_animation()` is a clean one-call API for CLI integration

---

## Phase 3: Configuration Integration

### T3.1: Config validation and defaults (Lines 234-257)

**File:** `src/teambot/config/loader.py` (MODIFY)

**Changes to `_validate()` method (after `_validate_overlay` call):**
```python
if "show_startup_animation" in config:
    if not isinstance(config["show_startup_animation"], bool):
        raise ConfigError("'show_startup_animation' must be a boolean")
```

**Changes to `_apply_defaults()` method (after overlay defaults):**
```python
if "show_startup_animation" not in config:
    config["show_startup_animation"] = True
```

**Research Reference:** Research Lines 472-480 (config validation pattern)

**Success Criteria:**
- `{"show_startup_animation": true}` passes validation
- `{"show_startup_animation": false}` passes validation
- `{"show_startup_animation": "yes"}` raises `ConfigError`
- Missing field gets default `True`

---

### T3.2: Add --no-animation CLI flag (Lines 261-278)

**File:** `src/teambot/cli.py` (MODIFY)

**Change in `create_parser()` — add after line 37 (`--verbose`):**
```python
parser.add_argument(
    "--no-animation",
    action="store_true",
    help="Disable startup animation",
)
```

**Research Reference:** Research Lines 484-492 (CLI flag pattern)

**Success Criteria:**
- `teambot --no-animation run obj.md` parses without error
- `args.no_animation` is `True` when flag present, `False` when absent

---

### T3.3: Update visualization package exports (Lines 282-305)

**File:** `src/teambot/visualization/__init__.py` (MODIFY)

**Add imports:**
```python
from teambot.visualization.animation import StartupAnimation, play_startup_animation
```

**Add to `__all__`:**
```python
"StartupAnimation",
"play_startup_animation",
```

**Research Reference:** Research Lines 282-290 (architecture, exports)

**Success Criteria:**
- `from teambot.visualization import StartupAnimation` works
- `from teambot.visualization import play_startup_animation` works

---

## Phase 4: CLI Integration

### T4.1: Wire animation into cmd_run() (Lines 307-335)

**File:** `src/teambot/cli.py` (MODIFY)

**Add import at top of file:**
```python
from teambot.visualization.animation import play_startup_animation
```

**Replace line 131:**
```python
# OLD: display.print_header("TeamBot Starting")
# NEW:
play_startup_animation(
    console=display.console,
    config=config,
    no_animation_flag=getattr(args, 'no_animation', False),
    version=__version__,
)
```

**Note:** Use `getattr` with default for backward compatibility if `no_animation` attribute doesn't exist in all parser paths.

**Research Reference:** Research Lines 198-210 (entry point 1 trace)

**Success Criteria:**
- `teambot run obj.md` shows animation instead of plain header
- `teambot run --no-animation obj.md` shows no animation
- Config `show_startup_animation: false` prevents animation

---

### T4.2: Wire animation into cmd_init() (Lines 339-361)

**File:** `src/teambot/cli.py` (MODIFY)

**Replace line 90:**
```python
# OLD: display.print_header("Configured Agents")
# NEW:
play_startup_animation(
    console=display.console,
    config=None,  # Config may not exist yet during init
    no_animation_flag=getattr(args, 'no_animation', False),
    version=__version__,
)
```

**Note:** During `init`, config doesn't exist yet, so pass `None`. The `should_animate()` method handles `None` config by defaulting to enabled.

**Research Reference:** Research Lines 212-218 (entry point 2 trace)

**Success Criteria:**
- `teambot init` shows animation before agent list
- Config settings ignored (config doesn't exist yet during init)

---

### T4.3: Wire animation into _run_orchestration_resume() (Lines 365-388)

**File:** `src/teambot/cli.py` (MODIFY)

**Replace line 305:**
```python
# OLD: display.print_header("TeamBot Resuming")
# NEW:
play_startup_animation(
    console=display.console,
    config=config,
    no_animation_flag=getattr(args, 'no_animation', False),
    version=__version__,
)
```

**Research Reference:** Research Lines 220-224 (entry point 3 trace)

**Success Criteria:**
- `teambot run --resume` shows animation before resume output

---

## Phase 5: Testing (Code-First)

### T5.1: should_animate() tests (Lines 390-418)

**File:** `tests/test_visualization/test_animation.py` (CREATE)

**Class: `TestShouldAnimate`**

Test fixtures needed per test (use `unittest.mock.patch`):
- `sys.stdout.isatty` → return `True` (default for positive tests)
- `shutil.get_terminal_size` → return `os.terminal_size((80, 24))` (default)
- `os.environ` → clean (no `TERM=dumb`, no `TEAMBOT_NO_ANIMATION`)

**Test cases:**

| Test | Setup | Expected | Mocks |
|------|-------|----------|-------|
| `test_returns_true_when_tty_and_enabled` | Default mocks, config=None, flag=False | `True` | isatty=True, size=(80,24) |
| `test_returns_false_when_no_animation_flag` | flag=True | `False` | — |
| `test_returns_false_when_config_disabled` | config={"show_startup_animation": False} | `False` | — |
| `test_returns_false_when_not_tty` | — | `False` | isatty=False |
| `test_returns_false_when_term_is_dumb` | — | `False` | env TERM=dumb |
| `test_returns_false_when_terminal_too_small` | — | `False` | size=(40,5) |
| `test_returns_true_when_config_is_none` | config=None | `True` | isatty=True |
| `test_returns_false_when_env_var_set` | — | `False` | env TEAMBOT_NO_ANIMATION=1 |

**Research Reference:** Research Lines 314-340, Test Strategy Component 1

**Success Criteria:**
- All 8 tests pass
- 100% branch coverage on `should_animate()`

---

### T5.2: StartupAnimation class tests (Lines 422-439)

**File:** `tests/test_visualization/test_animation.py` (MODIFY — add class)

**Class: `TestStartupAnimation`**

| Test | Description | Approach |
|------|-------------|----------|
| `test_play_calls_animated_when_should_animate_true` | Mock `should_animate` → True, verify `_play_animated` called | `patch.object` |
| `test_play_calls_static_when_should_animate_false` | Mock `should_animate` → False, verify `_show_static_banner` called | `patch.object` |
| `test_static_banner_contains_version` | Create instance with version="1.2.3", check banner text | Direct assert on Panel content |
| `test_static_banner_contains_teambot_text` | Check banner contains "TeamBot" | Direct assert |
| `test_frame_generation_returns_nonempty_list` | Call `_generate_convergence_frames()` | `assert len(frames) > 0` |
| `test_ascii_fallback_uses_no_unicode_box_drawing` | Verify `TEAMBOT_LOGO_ASCII` has no `╗╔╝╚║═█▀▄` | String check on constant |

**Success Criteria:**
- All 6 tests pass
- No Rich output captured/asserted (follow `test_console.py` pattern)

---

### T5.3: Config validation tests (Lines 443-459)

**File:** `tests/test_config/test_loader.py` (MODIFY — add to existing)

**Class: `TestAnimationConfig`**

| Test | Input | Expected |
|------|-------|----------|
| `test_show_startup_animation_default_true` | Config without field | After `_apply_defaults()`, field is `True` |
| `test_show_startup_animation_validates_bool` | `{"show_startup_animation": true}` | Passes validation |
| `test_invalid_show_startup_animation_raises_error` | `{"show_startup_animation": "yes"}` | Raises `ConfigError` |

**Pattern:** Follow existing `TestOverlayConfig` structure from same file.

**Success Criteria:**
- All 3 tests pass
- Error message matches `"'show_startup_animation' must be a boolean"`

---

### T5.4: CLI flag parsing tests (Lines 463-474)

**File:** `tests/test_cli.py` (MODIFY — add to existing `TestCLIParser`)

| Test | Command | Expected |
|------|---------|----------|
| `test_parser_accepts_no_animation_flag` | `["--no-animation", "run", "obj.md"]` | Parses without error |
| `test_no_animation_flag_defaults_false` | `["run", "obj.md"]` | `args.no_animation == False` |

**Success Criteria:**
- Both tests pass
- Flag is on main parser (works with all subcommands)

---

### T5.5: CLI integration tests (Lines 478-498)

**File:** `tests/test_visualization/test_animation.py` (MODIFY — add class)

**Class: `TestAnimationCLIIntegration`**

| Test | Description | Approach |
|------|-------------|----------|
| `test_cmd_run_calls_animation` | Mock `play_startup_animation`, call `cmd_run` | Verify mock called |
| `test_cmd_init_calls_animation` | Mock `play_startup_animation`, call `cmd_init` | Verify mock called |
| `test_no_animation_flag_suppresses` | Mock animation, call with `--no-animation` | Verify `no_animation_flag=True` passed |

**Note:** These tests may need additional mocking of config loading and orchestration to isolate the animation call. Follow existing `TestCLIRun` pattern.

**Success Criteria:**
- All 3 tests pass
- Tests verify animation function is called (not visual output)

---

## Phase 6: Validation & Cleanup

### T6.1: Full test suite (Lines 500-512)

**Commands:**
```bash
uv run pytest                                          # All tests pass
uv run pytest --cov=src/teambot/visualization/animation --cov-report=term-missing  # Coverage check
uv run pytest tests/test_visualization/test_animation.py -v  # New tests specifically
```

**Success Criteria:**
- Zero test failures across entire suite
- Animation module coverage ≥ 80%
- `should_animate()` function coverage = 100%

---

### T6.2: Manual visual verification (Lines 516-528)

**Test matrix:**

| Scenario | Command/Setup | Expected Behavior |
|----------|--------------|-------------------|
| Normal TTY | `uv run teambot run objectives/test.md` | Animated sequence → final banner |
| --no-animation | `uv run teambot run --no-animation objectives/test.md` | Static banner only, immediate |
| Piped output | `uv run teambot run objectives/test.md \| cat` | Static banner (detected non-TTY) |
| Dumb terminal | `TERM=dumb uv run teambot run objectives/test.md` | Static banner (no animation) |
| Env var disable | `TEAMBOT_NO_ANIMATION=1 uv run teambot run objectives/test.md` | Static banner |
| Init command | `uv run teambot init` | Animation plays before config display |
| Narrow terminal | Resize to <60 cols, run | Compact banner (no ASCII art) |

---

### T6.3: Lint and format (Lines 532-544)

**Commands:**
```bash
uv run ruff check src/teambot/visualization/animation.py
uv run ruff format --check src/teambot/visualization/animation.py
uv run ruff check tests/test_visualization/test_animation.py
uv run ruff format --check tests/test_visualization/test_animation.py
```

**Success Criteria:**
- Zero ruff errors or warnings
- Files are properly formatted
