## Objective

Create a visually striking ASCII-based startup animation for TeamBot that plays when the CLI launches, establishing brand identity and conveying the collaborative multi-agent nature of the tool.

**Goal**:

- TeamBot currently launches with a simple styled header ("TeamBot Starting") with no visual branding or animation.
- Like the GitHub Copilot CLI which features an animated startup sequence, TeamBot should have its own distinctive and memorable startup animation that reflects its identity as a collaborative AI team.
- The animation should be symbolic of TeamBot's core concept: multiple AI agents working together as a coordinated team.
- The animation should feel modern, polished, and developer-friendly — not gimmicky or slow.
- Visual elements to consider:
  - A stylised "TeamBot" wordmark or logo rendered in ASCII/Unicode art
  - Animated assembly of the logo — e.g. individual agent icons or fragments converging to form the TeamBot identity, symbolising agents coming together as a team
  - Use of the existing agent colour palette (blue, cyan, magenta, green, yellow, red) to reinforce persona identity during the animation
  - Braille or block character based smooth transitions
  - A brief tagline or version string displayed after the animation completes
- The animation should be fast and respectful of the user's time — total duration should be approximately 3–4 seconds
- The animation must be skippable or disableable via configuration (e.g. `--no-animation` flag or a `teambot.json` setting)
- The animation should degrade gracefully in terminals that do not support colour or Unicode

**Problem Statement**:

- TeamBot has no visual branding on startup; it launches with a plain text header that is indistinguishable from any other CLI tool.
- First impressions matter — a polished startup sequence establishes confidence in the tool and reinforces its unique identity.
- The GitHub Copilot CLI sets a precedent for animated CLI startup experiences that developers enjoy and associate with quality tooling.
- Without a branded startup, TeamBot misses an opportunity to visually communicate its core differentiator: coordinated multi-agent collaboration.

**Success Criteria**:

- [ ] A branded ASCII/Unicode startup animation plays when `teambot run` or `teambot init` is executed.
- [ ] The animation visually represents the concept of multiple agents forming a team (convergence, assembly, or collaboration motif).
- [ ] The animation uses the existing agent colour palette from the visualization module.
- [ ] Total animation duration is between 3–4 seconds and feels snappy.
- [ ] Animation can be disabled via a `--no-animation` CLI flag.
- [ ] Animation can be disabled via a `show_startup_animation` setting in `teambot.json`.
- [ ] The animation degrades gracefully to a static banner in terminals without colour/Unicode support.
- [ ] No noticeable delay to the overall startup time when animation is disabled.
- [ ] The animation does not interfere with or corrupt subsequent terminal output (overlay, status panel, agent messages).
- [ ] Existing tests continue to pass; new tests cover the animation module and its configuration.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `src/teambot/visualization/` and `src/teambot/cli.py`

**Primary Language/Framework**:

- Python, using the Rich library for terminal rendering (already a project dependency)

**Testing Preference**:

- Follow existing patterns — pytest with mocking for terminal output

**Key Constraints**:

- Must use only terminal-safe characters (ASCII + common Unicode block/braille characters)
- Must work on macOS, Linux, and Windows Terminal
- Must not add heavy external dependencies — prefer Rich and standard library
- Animation frames should be defined in code or data, not loaded from external asset files
- Must respect CI/non-interactive environments — auto-disable when stdout is not a TTY

---

## Additional Context

- The existing `src/teambot/visualization/console.py` already defines agent colours and icons — the animation should reuse these for consistency.
- The overlay renderer in `src/teambot/visualization/overlay.py` already uses braille spinner patterns and box-drawing characters — similar techniques can be applied to the startup animation.
- Consider implementing the animation as a new module (e.g. `src/teambot/visualization/startup.py`) to keep concerns separated.
- The animation could depict individual agent glyphs or fragments sliding, fading, or assembling into the TeamBot wordmark, visually telling the story of "agents becoming a team."
- Reference animations for inspiration:
  - GitHub Copilot CLI startup sparkle animation
  - `neofetch` system info display with ASCII art
  - `starship` prompt animated initialisation
- The animation module should expose a simple API (e.g. `play_startup_animation(console, config)`) that `cli.py` can call before the existing startup sequence.

---
