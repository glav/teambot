# Problem Statement: TeamBot Startup Animation

## Business Problem

TeamBot currently launches with a plain, unstyled Rich `Panel` header displaying "TeamBot Starting" (in `cli.py` line 131). This provides no visual branding, no sense of identity, and no indication of what makes TeamBot distinctive — a team of specialized AI agents working together.

By contrast, best-in-class CLI tools (including GitHub Copilot CLI) invest in their first-impression experience with branded, animated startup sequences. TeamBot's launch moment is a missed opportunity to:

1. **Establish brand identity** — Users have no visual cue that they are entering a collaborative multi-agent environment.
2. **Communicate the core concept** — The idea of agents assembling as a coordinated team is central to TeamBot's value proposition, but nothing in the startup experience reflects this.
3. **Set a quality bar** — A polished startup animation signals that the tool is well-crafted and inspires confidence, especially in early adopters and evaluators.

## Who Is Affected

| Stakeholder | Impact |
|---|---|
| **End users (developers)** | First-run and every-run experience lacks polish and memorability. No visual reinforcement of the multi-agent concept. |
| **Evaluators / decision-makers** | First impression during demos or trials does not differentiate TeamBot from a generic CLI tool. |
| **Contributors** | The visualization module already supports Rich, colour palettes, and Unicode — these capabilities are underutilised at startup. |

## Current State

- **Startup output**: `display.print_header("TeamBot Starting")` renders a static Rich `Panel` with a title string. No animation, no logo, no colour beyond the default panel style.
- **Existing infrastructure**: The `visualization/` module already provides:
  - An `AGENT_COLORS` palette (blue, cyan, magenta, green, yellow, red) mapped to each persona.
  - Agent icons (📋, 📊, 📝, 🔨, 🔍).
  - Braille spinner frames (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`) for progress indication.
  - Rich `Console`, `Panel`, `Table`, and `Live` rendering.
- **Configuration system**: `ConfigLoader` supports JSON settings and validation, but has no `show_startup_animation` field. The CLI argument parser has no `--no-animation` flag.
- **No graceful degradation logic** exists for non-TTY or colour-limited terminals at startup.

## Desired State

When a user runs `teambot run` or `teambot init`, they see a **brief (3–4 second), branded startup animation** that:

1. Renders a stylised "TeamBot" wordmark or logo in ASCII/Unicode art.
2. Visually conveys **agents converging to form a team** — e.g., individual fragments, icons, or coloured elements assembling into the final logo.
3. Uses the existing `AGENT_COLORS` palette (blue, cyan, magenta, green, yellow, red) so each agent persona is visually represented.
4. Completes with a tagline and/or version string.
5. Transitions cleanly into the existing terminal output (overlay, status panel, agent messages) with no corruption or artefacts.

The animation is **fast, non-blocking, and respectful of context**:

- Disabled instantly via `--no-animation` CLI flag or `show_startup_animation: false` in `teambot.json`.
- Auto-disabled when stdout is not a TTY (CI, piped output, non-interactive environments).
- Degrades to a static branded banner in terminals without colour or Unicode support.
- Adds no perceptible delay when disabled.

## Goals and Measurable Outcomes

| # | Goal | Measurable Outcome |
|---|---|---|
| G1 | Branded startup experience | ASCII/Unicode animation plays on `teambot run` and `teambot init`. |
| G2 | Communicates multi-agent identity | Animation visually represents agents assembling / converging into a team. |
| G3 | Uses existing colour palette | All six agent colours from `AGENT_COLORS` appear during the animation. |
| G4 | Fast and respectful | Total animation duration is 3–4 seconds; feels snappy, not sluggish. |
| G5 | Disableable via CLI flag | `--no-animation` flag suppresses the animation entirely. |
| G6 | Disableable via config | `show_startup_animation: false` in `teambot.json` suppresses the animation. |
| G7 | Graceful degradation | Falls back to a static banner in non-colour or non-Unicode terminals. |
| G8 | Zero cost when off | No measurable delay when animation is disabled. |
| G9 | Clean terminal handoff | Subsequent output (overlay, status, messages) renders correctly after animation. |
| G10 | Test coverage | New tests cover the animation module, configuration integration, and degradation paths. Existing tests continue to pass. |

## Assumptions

1. The Rich library (already a dependency) provides sufficient primitives for frame-based terminal animation — no new heavy dependencies are needed.
2. Animation frames will be defined in code or data structures, not loaded from external asset files.
3. The existing `AGENT_COLORS` dictionary and braille/block character set in the visualization module are the canonical source for colours and character palettes.
4. Cross-platform compatibility (macOS, Linux, Windows Terminal) is required; legacy Windows `cmd.exe` is not a primary target.
5. The `ConfigLoader` schema can be extended with a `show_startup_animation` boolean field without breaking existing configurations.

## Constraints

| Constraint | Rationale |
|---|---|
| No new heavy dependencies | Keep install footprint small; Rich + stdlib are sufficient. |
| Terminal-safe characters only | ASCII + common Unicode block/braille characters for maximum compatibility. |
| No external asset files | Animation defined in code for portability and simplicity. |
| 3–4 second max duration | Developer time is valuable; the animation must not feel like a delay. |
| Must not corrupt subsequent output | The overlay, status panel, and agent message rendering must work correctly after animation completes. |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Animation flickers or tears on some terminals | Medium | Medium | Use Rich's `Live` rendering for atomic frame updates; test on multiple terminal emulators. |
| Animation leaves artefacts that corrupt subsequent output | Medium | High | Clear the animation area completely before handing off; add integration-level tests for post-animation output. |
| Windows Terminal rendering inconsistencies | Low | Medium | Stick to widely-supported Unicode block characters; test on Windows Terminal. |
| Users find the animation annoying after repeated use | Low | Medium | Ensure disable mechanisms (flag + config) are discoverable and documented. |
| CI pipelines break due to unexpected animation output | Medium | High | Auto-detect non-TTY stdout and suppress animation entirely. |

## Dependencies

- **Internal**: `src/teambot/visualization/` (console, overlay, colour palette), `src/teambot/cli.py` (CLI entry points), `src/teambot/config/` (configuration loader and schema).
- **External**: Rich library (already installed).
- **No blockers**: All prerequisite infrastructure exists.

## Success Criteria (Acceptance Tests)

1. ✅ A branded ASCII/Unicode startup animation plays when `teambot run` or `teambot init` is executed.
2. ✅ The animation visually represents agents forming a team (convergence / assembly motif).
3. ✅ The animation uses all six agent colours from the `AGENT_COLORS` palette.
4. ✅ Total animation duration is between 3–4 seconds and feels snappy.
5. ✅ `--no-animation` CLI flag disables the animation.
6. ✅ `show_startup_animation: false` in `teambot.json` disables the animation.
7. ✅ Animation degrades gracefully to a static banner in terminals without colour/Unicode support.
8. ✅ No noticeable delay when animation is disabled.
9. ✅ Subsequent terminal output (overlay, status panel, agent messages) renders correctly after animation.
10. ✅ Existing tests pass; new tests cover the animation module and its configuration.
