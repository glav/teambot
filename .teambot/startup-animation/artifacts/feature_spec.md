<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# TeamBot Startup Animation - Feature Specification Document
Version 1.0 | Status Draft | Owner TeamBot Core | Team Visualization | Target v0.2.0 | Lifecycle Design

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-09 |
| Problem & Users | 100% | None | 2026-02-09 |
| Scope | 100% | None | 2026-02-09 |
| Requirements | 100% | None | 2026-02-09 |
| Metrics & Risks | 100% | None | 2026-02-09 |
| Operationalization | 100% | None | 2026-02-09 |
| Finalization | 100% | None | 2026-02-09 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates a team of 6 specialized AI agent personas (PM, BA, Writer, two Builders, Reviewer) working together to achieve software development objectives. It is built in Python using the Rich library for terminal rendering. The current startup experience displays a plain Rich `Panel` with the text "TeamBot Starting" via `display.print_header("TeamBot Starting")` in `cli.py` (line 131). There is no visual branding, no animation, and no representation of the collaborative multi-agent concept that defines TeamBot.

### Core Opportunity
Replace the plain startup header with a branded, animated startup sequence that establishes TeamBot's identity as a collaborative AI team. The animation visually represents agents converging to form a unified team — reinforcing the product's core value proposition at the moment of first (and every) impression. This aligns TeamBot with best-in-class CLI tools like GitHub Copilot CLI that invest in polished startup experiences.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Branded startup animation plays on `teambot run` and `teambot init` | Experience | Plain text panel | Animated ASCII/Unicode sequence | v0.2.0 | P0 |
| G-002 | Animation visually represents agents assembling into a team | Branding | No visual motif | Convergence/assembly animation using 6 agent colours | v0.2.0 | P0 |
| G-003 | Animation uses all 6 agent colours from `AGENT_COLORS` palette | Branding | Single blue panel style | blue, cyan, magenta, green, yellow, red all visible | v0.2.0 | P0 |
| G-004 | Animation duration is 3–4 seconds and feels snappy | Performance | N/A (no animation) | 3–4 seconds total | v0.2.0 | P0 |
| G-005 | Animation disableable via `--no-animation` CLI flag | Configurability | No flag exists | Flag suppresses animation entirely | v0.2.0 | P0 |
| G-006 | Animation disableable via `show_startup_animation` config setting | Configurability | No config field exists | `show_startup_animation: false` suppresses animation | v0.2.0 | P0 |
| G-007 | Graceful degradation in limited terminals | Compatibility | No degradation logic | Static branded banner for non-colour/non-Unicode terminals | v0.2.0 | P1 |
| G-008 | Zero startup cost when animation is disabled | Performance | N/A | No measurable delay when off | v0.2.0 | P0 |
| G-009 | Clean terminal handoff after animation | Reliability | N/A | Overlay, status panel, agent messages render correctly | v0.2.0 | P0 |
| G-010 | Comprehensive test coverage for animation module | Quality | No animation tests | New tests for module, config, degradation; existing tests pass | v0.2.0 | P1 |

## 2. Problem Definition

### Current Situation
When a user runs `teambot run` or `teambot init`, the only startup visual is a Rich `Panel` widget containing the text "TeamBot Starting" (or "TeamBot Resuming" for `--resume`). This is rendered by `ConsoleDisplay.print_header()` which calls `self.console.print(Panel(title, style="bold blue"))`. The result is a simple bordered box with blue text — functional but unremarkable. There is no logo, no colour palette usage beyond a single blue, no animation, and no visual communication of TeamBot's multi-agent identity.

### Problem Statement
TeamBot's startup experience fails to establish brand identity or communicate its core concept of collaborative multi-agent orchestration. This creates a generic first impression that does not differentiate TeamBot from any other CLI tool, reducing user engagement and product memorability.

### Root Causes
* The `print_header()` method was implemented as a minimal placeholder with no branding intent.
* No startup animation module exists in the visualization package.
* The configuration system has no field to control animation behaviour.
* The CLI argument parser has no `--no-animation` flag.
* No terminal capability detection (colour support, Unicode support, TTY status) is performed at startup.

### Impact of Inaction
Without a branded startup animation, TeamBot will continue to present a generic, forgettable first impression. During demos, evaluations, and daily use, users will not receive any visual reinforcement of the multi-agent collaboration concept. The existing `AGENT_COLORS` palette and Rich rendering infrastructure will remain underutilised at the most visible moment — application launch.

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Developer (daily user) | Quick, informative startup; visual confirmation that TeamBot is loading correctly | Current startup is bland and provides no sense of progress or identity | High — sees startup on every invocation |
| Evaluator / decision-maker | Polished first impression that communicates product quality and unique value | No visual differentiation from generic CLI tools during demos/trials | High — first impression influences adoption decisions |
| CI/automation pipeline | Zero visual overhead; clean stdout for log parsing | Unexpected animation output could corrupt logs or slow pipelines | Medium — animation must auto-disable for non-TTY |
| Contributor / developer | Clean, maintainable animation code; easy to extend or modify | No existing module to build on | Low — one-time development concern |

## 4. Scope

### In Scope
* New `animation.py` module in `src/teambot/visualization/` containing all animation logic
* ASCII/Unicode "TeamBot" wordmark/logo defined in code
* Frame-based animation sequence representing agents converging to form the logo
* Usage of the 6 existing `AGENT_COLORS` colours during the animation
* Version string and/or tagline displayed after animation completes
* `--no-animation` CLI flag added to `teambot run` and `teambot init` commands
* `show_startup_animation` boolean field added to `teambot.json` configuration schema
* TTY detection to auto-disable animation in non-interactive environments
* Terminal capability detection for colour and Unicode support with static banner fallback
* Clean terminal state restoration after animation completes (before overlay/output begins)
* Unit and integration tests for the animation module, configuration, and degradation paths
* Integration with both `teambot run` and `teambot init` entry points in `cli.py`

### Out of Scope (justify if empty)
* Interactive or user-controllable animation (e.g., press key to skip mid-animation) — complexity outweighs benefit for a 3–4 second sequence
* Custom animation themes or user-defined animation frames — not needed for initial release
* Sound or audio effects — terminal-only tool
* Animation for `teambot status` command — not a launch/startup context
* Changes to the overlay or status panel rendering beyond ensuring clean handoff from the animation
* Loading external animation asset files (GIFs, videos, external frame data) — all frames defined in code

### Assumptions
* The Rich library (≥13.0.0, already a dependency) provides sufficient primitives (`Live`, `Console`, `Panel`, `Text`) for smooth frame-based terminal animation.
* Animation frames are defined as Python data structures (lists of strings or Rich renderables) within the module source code.
* The `AGENT_COLORS` dictionary in `visualization/console.py` (`{"pm": "blue", "ba": "cyan", "writer": "magenta", "builder-1": "green", "builder-2": "yellow", "reviewer": "red"}`) is the canonical colour source.
* The braille spinner pattern `SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"` in `overlay.py` may be reused or referenced for smooth character transitions.
* Cross-platform compatibility targets macOS, Linux, and Windows Terminal. Legacy Windows `cmd.exe` is not a primary target.
* The `ConfigLoader` can be extended with a new optional boolean field without breaking existing `teambot.json` files (missing field defaults to `true`).
* Rich's `Console.is_terminal` property reliably detects TTY status across supported platforms.

### Constraints
* **No new heavy dependencies** — only Rich (already installed) and Python standard library.
* **Terminal-safe characters only** — ASCII plus common Unicode block characters (▀▁▂▃▄▅▆▇█░▒▓) and braille characters (⠀–⣿).
* **No external asset files** — all animation data defined in Python source code.
* **3–4 second maximum duration** — the animation must not feel like it delays the user.
* **Must not corrupt subsequent output** — the overlay (ANSI-positioned), status panel, and agent message streams must render correctly after the animation clears.
* **Must work with existing Rich Console instance** — animation should use or coordinate with the same `Console` object used by `ConsoleDisplay`.

## 5. Product Overview

### Value Proposition
A polished, branded startup animation that establishes TeamBot's identity as a collaborative AI team from the very first moment of interaction. The animation transforms a bland "TeamBot Starting" text panel into a memorable, colourful visual that reinforces the multi-agent concept and signals product quality — all in under 4 seconds.

### Differentiators
* Uses the unique 6-agent colour palette to visually distinguish TeamBot from other CLI tools.
* Convergence motif (agents assembling into a team) directly communicates the product's core value proposition.
* Graceful degradation ensures broad terminal compatibility without sacrificing the premium experience on capable terminals.

### UX / UI
The animation renders directly to the terminal via Rich. No GUI, web, or graphical UI is involved. The animation occupies the full terminal width for its duration, then clears completely before any subsequent output begins.

**Visual Concept**: Individual coloured elements (representing the 6 agent personas) appear separately and converge/assemble to form the "TeamBot" wordmark. After assembly, a brief tagline (e.g., "Collaborative AI Development") and version string (e.g., "v0.1.0") fade in below the logo. The entire sequence uses block and/or braille characters for smooth transitions.

**Fallback (static banner)**: In limited terminals, a simple bordered ASCII "TeamBot" text with version string is displayed — no animation, no colour, no Unicode.

| UX Status: Concept defined — visual design to be finalised during implementation |

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Animation Module | A new `animation.py` module SHALL exist in `src/teambot/visualization/` containing all startup animation logic. | G-001 | All | P0 | Module exists, is importable, and is exported from the visualization package `__init__.py`. | Single module, no sub-package needed. |
| FR-002 | ASCII/Unicode Wordmark | The animation SHALL render a stylised "TeamBot" wordmark using ASCII and/or Unicode block/braille characters. | G-001, G-002 | Developer, Evaluator | P0 | A recognisable "TeamBot" text logo is visible at the end of the animation sequence. | Wordmark defined as Python data in the module. |
| FR-003 | Agent Convergence Animation | The animation SHALL visually represent 6 agent personas converging or assembling to form the TeamBot wordmark/logo. | G-002, G-003 | Developer, Evaluator | P0 | During the animation, distinct coloured elements move, appear, or assemble — viewers can identify a convergence/assembly motif. | Creative implementation flexible; must be perceivable as "coming together". |
| FR-004 | Agent Colour Palette Usage | The animation SHALL use all 6 colours from the `AGENT_COLORS` dictionary: blue, cyan, magenta, green, yellow, red. | G-003 | Developer, Evaluator | P0 | All 6 colours appear in at least one frame of the animation. Colours are sourced from `AGENT_COLORS`. | Colours map to Rich style names. |
| FR-005 | Animation Duration | The total animation duration SHALL be between 3.0 and 4.0 seconds. | G-004 | Developer | P0 | Measured wall-clock time from first frame to animation clear is within 3.0–4.0 seconds. | Use `time.sleep()` or equivalent between frames. |
| FR-006 | Version/Tagline Display | After the animation completes assembly, the animation SHALL briefly display the TeamBot version string (from `teambot.__version__`) and optionally a tagline. | G-001 | Developer | P1 | Version string is visible after the logo assembles. | Tagline text is implementation choice. |
| FR-007 | CLI `--no-animation` Flag | The `teambot run` and `teambot init` commands SHALL accept a `--no-animation` flag that disables the startup animation. | G-005 | Developer, CI | P0 | Passing `--no-animation` results in no animation frames being rendered. | Flag added to argparse for both subcommands. |
| FR-008 | Config `show_startup_animation` Setting | The configuration system SHALL support a `show_startup_animation` boolean field in `teambot.json`. When set to `false`, the animation is disabled. | G-006 | Developer | P0 | Setting `"show_startup_animation": false` in `teambot.json` results in no animation. Missing field defaults to `true`. | Added to `ConfigLoader` defaults and validation. |
| FR-009 | CLI Flag Overrides Config | The `--no-animation` CLI flag SHALL take precedence over the `show_startup_animation` config setting. If the flag is present, animation is disabled regardless of config. | G-005, G-006 | Developer | P0 | With config `true` and flag `--no-animation`, no animation plays. | Standard CLI-overrides-config pattern. |
| FR-010 | TTY Auto-Detection | The animation SHALL auto-disable when stdout is not a TTY (e.g., piped output, CI environments, non-interactive shells). | G-008, G-009 | CI | P0 | When stdout is not a TTY, no animation frames are rendered and no escape sequences are emitted. | Use `Console.is_terminal` or `sys.stdout.isatty()`. |
| FR-011 | Graceful Degradation — No Colour | When the terminal does not support colour, the animation SHALL fall back to a static, uncoloured ASCII banner with the "TeamBot" wordmark and version string. | G-007 | Developer | P1 | In a `NO_COLOR`/`TERM=dumb` environment, a readable ASCII banner is displayed without ANSI colour codes. | Rich's `Console.color_system` can detect this. |
| FR-012 | Graceful Degradation — No Unicode | When the terminal does not support Unicode, the animation SHALL fall back to a static ASCII-only banner. | G-007 | Developer | P1 | In an ASCII-only terminal (`Console.encoding` check), no Unicode block/braille characters are emitted. | Use Rich's encoding detection. |
| FR-013 | Terminal Cleanup After Animation | After the animation completes, the module SHALL fully clear the animation area and restore normal terminal state before returning control to the caller. | G-009 | Developer | P0 | No animation artefacts remain on screen. Subsequent `ConsoleDisplay` output and `OverlayRenderer` output render correctly. | Critical for overlay compatibility. |
| FR-014 | Integration with `teambot run` | The animation SHALL be invoked in the `run_command()` function in `cli.py`, replacing or augmenting the existing `display.print_header("TeamBot Starting")` call. | G-001 | Developer | P0 | Running `teambot run <objective>` displays the animation (when enabled) before agent orchestration begins. | Animation call placed before orchestration logic. |
| FR-015 | Integration with `teambot init` | The animation SHALL be invoked in the `init_command()` function in `cli.py` when the project is initialised. | G-001 | Developer | P1 | Running `teambot init` displays the animation (when enabled) before config creation output. | Simpler integration — init has less terminal complexity. |
| FR-016 | Static Banner When Disabled | When the animation is disabled (by flag, config, or auto-detection), a simple static banner SHALL be displayed instead — the "TeamBot" wordmark without animation, with version string. | G-007, G-008 | All | P0 | A non-animated "TeamBot vX.Y.Z" banner appears when animation is off. No blank startup. | Ensures branded startup in all cases. |

### Feature Hierarchy
```plain
startup-animation/
├── Animation Module (FR-001)
│   ├── Wordmark/Logo (FR-002)
│   ├── Convergence Animation (FR-003)
│   ├── Colour Palette (FR-004)
│   ├── Timing (FR-005)
│   ├── Version/Tagline (FR-006)
│   ├── Terminal Cleanup (FR-013)
│   └── Static Banner Fallback (FR-016)
├── Configuration (FR-007, FR-008, FR-009)
│   ├── CLI Flag (FR-007)
│   ├── Config Setting (FR-008)
│   └── Precedence Logic (FR-009)
├── Environment Detection (FR-010, FR-011, FR-012)
│   ├── TTY Detection (FR-010)
│   ├── Colour Detection (FR-011)
│   └── Unicode Detection (FR-012)
└── CLI Integration (FR-014, FR-015)
    ├── teambot run (FR-014)
    └── teambot init (FR-015)
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Animation total duration MUST be 3.0–4.0 seconds. | Wall-clock time measured with `time.monotonic()` | P0 | Automated test with timing assertion (±0.5s tolerance). | Tolerance accounts for system scheduling. |
| NFR-002 | Performance | When animation is disabled, the startup banner MUST render in <50ms. | <50ms from call to return | P0 | Automated test with timing assertion. | Ensures "zero cost when off". |
| NFR-003 | Reliability | Animation MUST NOT raise unhandled exceptions for any terminal type. | Zero crashes in any detected terminal environment | P0 | Test with mocked terminal capabilities (no colour, no Unicode, not TTY). | Catch and fallback on all rendering errors. |
| NFR-004 | Compatibility | Animation MUST render correctly on macOS Terminal, iTerm2, Linux (GNOME Terminal, Konsole), and Windows Terminal. | No visual corruption on target terminals | P1 | Manual cross-platform verification. | Automated testing covers logic; visual testing is manual. |
| NFR-005 | Maintainability | Animation frames and wordmark MUST be defined as readable Python data structures, not obfuscated binary or encoded strings. | Code review verification | P1 | Code review checklist item. | Enables future modification of animation design. |
| NFR-006 | Maintainability | The animation module MUST have ≥90% test coverage. | Coverage report metric | P1 | `pytest --cov` report. | Matches project quality standards. |
| NFR-007 | Accessibility | Animation MUST respect the `NO_COLOR` environment variable (https://no-color.org/). | When `NO_COLOR` is set, no ANSI colour codes are emitted. | P1 | Automated test with env var set. | Rich supports this natively. |
| NFR-008 | Usability | The static fallback banner MUST be visually coherent and branded — not a blank screen or raw text. | Visual review of fallback output | P1 | Manual and snapshot test. | Fallback is still a "good" experience. |

## 8. Data & Analytics

### Inputs
* `teambot.__version__` — version string displayed in animation/banner.
* `AGENT_COLORS` dictionary — colour palette for animation frames.
* `teambot.json` configuration — `show_startup_animation` boolean.
* CLI arguments — `--no-animation` flag.
* Terminal environment — TTY status, colour support, Unicode support, `NO_COLOR` env var.

### Outputs / Events
* Terminal output — animated frames or static banner rendered to stdout.
* No persistent data, logs, or files are created by the animation.

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| N/A — No telemetry or analytics instrumentation required for this feature. | | | | |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Animation plays on startup | Functional | Does not exist | Plays on every `run`/`init` when enabled | v0.2.0 release | Manual + automated test |
| Animation duration | Performance | N/A | 3.0–4.0 seconds | Per invocation | Automated timing test |
| Disabled startup overhead | Performance | N/A | <50ms | Per invocation | Automated timing test |
| Test coverage of animation module | Quality | 0% | ≥90% | v0.2.0 release | `pytest --cov` |
| Existing test suite pass rate | Quality | 100% (941 tests) | 100% | v0.2.0 release | `uv run pytest` |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Rich library (≥13.0.0) | External (existing) | High | PyPI | Low — already a dependency, stable API | Pin minimum version in `pyproject.toml` (already done). |
| `AGENT_COLORS` dict in `visualization/console.py` | Internal | High | Visualization module | Low — stable, well-tested | Import directly; any colour changes automatically reflected. |
| `SPINNER_FRAMES` in `visualization/overlay.py` | Internal | Low | Visualization module | Low — optional reference for character palette | Copy or import as needed. |
| `ConsoleDisplay` class in `visualization/console.py` | Internal | Medium | Visualization module | Low — animation must coordinate with same `Console` | Share or accept `Console` instance as parameter. |
| `ConfigLoader` in `config/loader.py` | Internal | Medium | Config module | Low — additive change (new optional field) | Default `true` when field is missing for backward compatibility. |
| CLI argparse in `cli.py` | Internal | Medium | CLI module | Low — additive change (new flag) | Add `--no-animation` to both `run` and `init` subparsers. |
| `teambot.__version__` in `__init__.py` | Internal | Low | Package root | Low — simple string import | Import at animation call time. |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Animation flickers or tears on some terminal emulators due to partial frame rendering. | Medium | Medium | Use Rich's `Live` context manager for atomic frame updates. Buffer complete frames before rendering. | Builder | Open |
| R-002 | Animation leaves ANSI artefacts that corrupt the subsequent overlay rendering. | High | Medium | Explicitly clear the animation area, reset cursor position, and restore scroll region after animation completes. Test with overlay enabled. | Builder | Open |
| R-003 | Windows Terminal renders Unicode block/braille characters differently than macOS/Linux. | Medium | Low | Use only widely-supported Unicode code points. Test on Windows Terminal. Graceful degradation handles failures. | Builder | Open |
| R-004 | Users find the animation annoying or wasteful after repeated use. | Medium | Low | Ensure `--no-animation` flag and `show_startup_animation` config setting are documented in `--help` and user guides. | Writer | Open |
| R-005 | CI pipelines break due to unexpected animation output or escape sequences in logs. | High | Medium | TTY auto-detection (FR-010) prevents animation in non-interactive environments. Static banner fallback emits no ANSI codes. | Builder | Open |
| R-006 | Animation timing is inconsistent across machines with different CPU loads. | Low | Medium | Use `time.sleep()` for inter-frame delays rather than busy-waiting. Accept ±0.5s timing tolerance in tests. | Builder | Open |
| R-007 | New animation module introduces import-time side effects that slow startup when animation is disabled. | Medium | Low | Lazy-import the animation module only when animation is about to play. No module-level I/O. | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
No user data, PII, or sensitive information is involved. The animation is purely a visual rendering of static, hardcoded content (logo, version string, colours).

### PII Handling
N/A — No PII is collected, processed, or displayed by the animation.

### Threat Considerations
N/A — The animation module performs no I/O beyond terminal stdout rendering. No network calls, file reads (beyond config which is already loaded), or system modifications.

### Regulatory / Compliance
N/A — No regulatory requirements apply to a terminal animation.

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard Python package update via `uv sync` | No special deployment steps. |
| Rollback | Set `show_startup_animation: false` in config or pass `--no-animation` | Instant disable without code rollback. |
| Monitoring | N/A — no runtime monitoring needed for a startup animation | Animation is stateless and ephemeral. |
| Alerting | N/A | |
| Support | Document `--no-animation` flag in `teambot run --help` and user guide | Ensures users can disable if needed. |
| Capacity Planning | N/A — negligible resource usage (terminal I/O only) | |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|--------------|-------|
| 1. Implementation | Animation module created, unit tests passing, integrated into `cli.py` | Builder |
| 2. Config Integration | `--no-animation` flag and `show_startup_animation` config working, tests passing | Builder |
| 3. Cross-platform Verification | Manual testing on macOS, Linux, Windows Terminal confirms no visual corruption | Builder + Reviewer |
| 4. Documentation | User guide updated with animation configuration section | Writer |
| 5. Release | All tests pass, code reviewed, merged to main | Reviewer |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| `show_startup_animation` (config) | Enable/disable startup animation | `true` | Permanent configuration option — no sunset. |
| `--no-animation` (CLI) | One-time override to disable animation | Animation plays | Permanent CLI flag — no sunset. |

## 14. Open Questions
| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| None | All questions resolved during specification. | | Closed |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-09 | BA Agent | Initial specification created from objective and codebase analysis. | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | `.teambot/startup-animation/artifacts/problem_statement.md` | Business problem definition, goals, assumptions, risks | Source of truth for problem context. |
| REF-002 | Codebase | `src/teambot/visualization/console.py` | `AGENT_COLORS` dict, `ConsoleDisplay` class, `print_header()` method | Canonical colour palette and display API. |
| REF-003 | Codebase | `src/teambot/visualization/overlay.py` | `SPINNER_FRAMES`, ANSI sequences, overlay rendering, cleanup logic | Reference for terminal rendering patterns. |
| REF-004 | Codebase | `src/teambot/cli.py` | CLI entry points, argparse structure, `display.print_header("TeamBot Starting")` | Integration target for animation calls. |
| REF-005 | Codebase | `src/teambot/config/loader.py` | `ConfigLoader` validation and defaults logic | Integration target for new config field. |
| REF-006 | Codebase | `teambot.json` | Default configuration structure | Schema extension target. |
| REF-007 | Codebase | `src/teambot/__init__.py` | `__version__ = "0.1.0"` | Version string source for animation display. |

## 17. Acceptance Test Scenarios

### AT-001: Default Startup Animation Plays
**Description**: User runs `teambot run` with default configuration and observes the startup animation.
**Preconditions**: `teambot.json` exists with default settings (no `show_startup_animation` field). Terminal supports colour and Unicode. Stdout is a TTY.
**Steps**:
1. User runs `teambot run objectives/my-task.md`
2. Observe terminal output during startup
3. Wait for animation to complete
4. Observe subsequent agent status output
**Expected Result**: A branded ASCII/Unicode animation plays showing coloured elements (blue, cyan, magenta, green, yellow, red) converging to form the "TeamBot" wordmark. Version string is displayed. Animation lasts 3–4 seconds. After animation, normal agent output and overlay render correctly with no artefacts.
**Verification**: Visual inspection confirms 6 colours visible, convergence motif perceivable, duration within range, and clean transition to normal output.

### AT-002: Animation on `teambot init`
**Description**: User runs `teambot init` and observes the startup animation before initialisation output.
**Preconditions**: No existing `teambot.json`. Terminal supports colour and Unicode. Stdout is a TTY.
**Steps**:
1. User runs `teambot init`
2. Observe terminal output
3. Wait for animation to complete
4. Observe initialisation output (config creation, agent table)
**Expected Result**: Animation plays before the "Created teambot.json" and agent table output. All subsequent init output renders correctly.
**Verification**: Animation visible before init output; no visual corruption of agent table.

### AT-003: `--no-animation` Flag Disables Animation
**Description**: User passes `--no-animation` flag and animation does not play.
**Preconditions**: Default config (animation enabled). Stdout is a TTY.
**Steps**:
1. User runs `teambot run --no-animation objectives/my-task.md`
2. Observe terminal output
**Expected Result**: No animation plays. A static "TeamBot" banner with version string appears instead. Startup proceeds immediately to normal operation.
**Verification**: No animated frames visible. Static banner present. Startup time is noticeably faster (sub-50ms for banner).

### AT-004: Config Setting Disables Animation
**Description**: User sets `show_startup_animation: false` in `teambot.json` and animation does not play.
**Preconditions**: `teambot.json` contains `"show_startup_animation": false`. No `--no-animation` flag passed.
**Steps**:
1. User edits `teambot.json` to add `"show_startup_animation": false`
2. User runs `teambot run objectives/my-task.md`
3. Observe terminal output
**Expected Result**: No animation plays. Static banner appears instead. Behaviour is identical to AT-003.
**Verification**: No animated frames visible. Static banner present.

### AT-005: CLI Flag Overrides Config Setting
**Description**: Config enables animation but CLI flag disables it; flag wins.
**Preconditions**: `teambot.json` contains `"show_startup_animation": true`. User passes `--no-animation`.
**Steps**:
1. Ensure `teambot.json` has `"show_startup_animation": true`
2. User runs `teambot run --no-animation objectives/my-task.md`
3. Observe terminal output
**Expected Result**: No animation plays despite config enabling it. CLI flag takes precedence.
**Verification**: Static banner displayed, not animated sequence.

### AT-006: Auto-Disable in Non-TTY Environment
**Description**: When stdout is piped (not a TTY), animation auto-disables.
**Preconditions**: Default config (animation enabled). No `--no-animation` flag.
**Steps**:
1. User runs `teambot run objectives/my-task.md | cat`
2. Examine captured output
**Expected Result**: No ANSI escape sequences or animation frames in the piped output. A plain text banner (no colour codes) may appear. No terminal corruption.
**Verification**: Piped output contains no `\033[` escape sequences from the animation. Output is parseable plain text.

### AT-007: Graceful Degradation — Colour-Limited Terminal
**Description**: In a terminal without colour support, a static ASCII banner is displayed instead of the animated sequence.
**Preconditions**: `NO_COLOR=1` environment variable set, or `TERM=dumb`. Animation is enabled in config.
**Steps**:
1. Set `NO_COLOR=1` in the environment
2. Run `teambot run objectives/my-task.md`
3. Observe terminal output
**Expected Result**: A static, uncoloured ASCII "TeamBot" banner with version string is displayed. No ANSI colour codes in output. No animation frames.
**Verification**: Output contains no ANSI colour escape sequences. "TeamBot" text and version are visible.

### AT-008: Clean Handoff to Overlay
**Description**: After animation completes, the persistent status overlay renders correctly in its configured position.
**Preconditions**: Animation enabled. Overlay enabled in config (default). Terminal supports colour and Unicode.
**Steps**:
1. Run `teambot run objectives/my-task.md`
2. Wait for animation to complete
3. Observe overlay rendering in top-right corner
4. Observe agent output in main terminal area
**Expected Result**: Overlay renders in correct position with no overlap or corruption from the animation. Agent messages print in the normal scroll area. Spinner in overlay animates correctly.
**Verification**: Overlay position correct; no ghost characters or misplaced text from animation; overlay spinner works.

## 18. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| AGENT_COLORS | Dictionary mapping agent persona IDs to Rich colour names, defined in `visualization/console.py`. |
| Braille characters | Unicode block U+2800–U+28FF, used for smooth visual transitions in terminal animations. |
| Block characters | Unicode characters like ▀▁▂▃▄▅▆▇█░▒▓ used for visual rendering in terminals. |
| TTY | Teletype — refers to an interactive terminal session (as opposed to piped/redirected output). |
| Wordmark | A logo consisting of the name of a product rendered in a distinctive typographic style. |
| Rich | Python library for rich text and beautiful formatting in the terminal. |
| Graceful degradation | Design strategy where a feature provides a reduced but functional experience when optimal conditions are not met. |

### Technical Context for Builders
**Files to modify**:
* `src/teambot/visualization/animation.py` — NEW: animation module
* `src/teambot/visualization/__init__.py` — Export new animation classes/functions
* `src/teambot/cli.py` — Add `--no-animation` flag; call animation at startup
* `src/teambot/config/loader.py` — Add `show_startup_animation` to defaults and validation
* `teambot.json` — Add `show_startup_animation` field (optional, defaults to `true`)

**Key imports to use**:
* `from teambot.visualization.console import AGENT_COLORS` (or the exported `PERSONA_COLORS` alias)
* `from teambot import __version__`
* `from rich.console import Console`
* `from rich.live import Live` (for atomic frame rendering)
* `from rich.text import Text` (for coloured text assembly)

**Testing files to create**:
* `tests/test_visualization/test_animation.py` — Unit tests for animation module

Generated 2026-02-09T00:13:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
