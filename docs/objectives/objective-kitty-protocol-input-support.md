---
feature_name: kitty-protocol-input-support
language: python
framework: textual
test_preference: hybrid
scope: small
acceptance_scenarios:
  - name: "Space input works with Kitty protocol enabled"
    steps:
      - "Start TeamBot in VSCode with Kitty protocol enabled (default in recent VSCode, verify by running `printf '\\x1b[>1u'` to enable Kitty protocol then `cat -v` and pressing Space — you should see `^[[32u`, confirming Kitty protocol is active)"
      - "Attempt to type a space character in the input field"
      - "Type additional text after the space"
      - "Submit the input"
    expected: "Space characters are correctly captured and included in the submitted input, multi-word queries work correctly"
  - name: "Legacy terminal input still works"
    steps:
      - "Start TeamBot in a terminal without Kitty protocol support"
      - "Type input with multiple words separated by spaces"
      - "Submit the input"
    expected: "Space characters work correctly, no regression in non-Kitty terminals"
  - name: "All special keys work with Kitty protocol"
    steps:
      - "Start TeamBot in VSCode with Kitty protocol enabled"
      - "Test arrow keys (Up/Down for history, Left/Right for cursor movement)"
      - "Test Enter, Backspace, Delete keys"
      - "Test Alt+Enter or Ctrl+Enter for multi-line input (if implemented)"
    expected: "All keyboard input including special keys works correctly with Kitty protocol"
---

## Objective

**Goal**: Add native support for the Kitty keyboard protocol in TeamBot's text input handling to ensure space characters and other keyboard input work correctly when VSCode's Kitty protocol support is enabled.

**Problem Statement**: 
- Recent VSCode updates have enabled Kitty keyboard protocol support by default, which changes how keyboard input is encoded and transmitted to terminal applications.
- TeamBot's current input handling (using Textual's `Input` or `TextArea` widgets) does not correctly handle space characters when the Kitty protocol is enabled — spaces are not registered or captured.
- This breaks the most basic input functionality, making it impossible to type multi-word queries or commands.
- Current workarounds (disabling Kitty protocol in devcontainer.json or using legacy fallback modes) are not intuitive and force users into degraded terminal experiences.
- The solution must handle Kitty protocol input natively without requiring users to change their VSCode configuration or fall back to legacy terminal modes.

**Success Criteria**:
- [ ] Space characters are correctly captured and processed when Kitty protocol is enabled in VSCode
- [ ] Multi-word input (e.g., "create a feature spec") works correctly with Kitty protocol
- [ ] All other keyboard input (arrow keys, Enter, Backspace, special keys) continues to work with Kitty protocol
- [ ] No regression in terminals without Kitty protocol support (backward compatibility maintained)
- [ ] No user configuration changes required (no need to disable Kitty protocol in VSCode)
- [ ] Tests verify both Kitty protocol and legacy input modes work correctly
- [ ] Documentation updated if any new configuration options or behaviors are introduced

---

## Technical Context

**Target Codebase**: `src/teambot/ui/widgets/input_pane.py` (Textual split-pane UI), potentially `src/teambot/repl/loop.py` (legacy REPL if affected)

**Primary Language/Framework**: Python / Textual

**Testing Preference**: Hybrid
- Unit tests for key event parsing and handling logic (decoding Kitty protocol sequences, mapping to standard events)
- Acceptance tests for end-to-end terminal compatibility scenarios (Kitty protocol enabled/disabled, various terminal emulators)

**Key Constraints**:
- Must work with VSCode's default Kitty protocol settings (no user configuration changes)
- Must maintain backward compatibility with terminals that don't support Kitty protocol
- Must not break existing keyboard input handling (arrow keys, history navigation, multi-line input if implemented)
- Must work with the current Textual version and follow Textual's event handling patterns
- Performance: Input latency must remain < 50ms (no noticeable degradation with Kitty protocol)
- No additional runtime dependencies should be required

**Technical Risks / Considerations**:
- The Kitty keyboard protocol changes the escape sequences sent for keyboard events, particularly for keys like Space that were previously sent as simple ASCII characters.
- Textual may or may not have built-in Kitty protocol support in the current version — this needs to be investigated first.
- If Textual doesn't have native Kitty protocol support, TeamBot may need to:
  - Upgrade to a newer version of Textual that supports Kitty protocol (check Textual changelog/releases)
  - Implement custom key event handling to decode Kitty protocol sequences
  - Add a Kitty protocol detection mechanism to switch between input handling modes
- Space character (U+0020) may be encoded differently in Kitty protocol vs traditional escape sequences.
- Other special characters and modifier keys (Shift, Alt, Ctrl combinations) may also be affected.
- Testing will require a way to simulate or capture Kitty protocol input sequences, which may not be straightforward in automated tests.

---

## Additional Context

### Background on Kitty Keyboard Protocol
- The Kitty keyboard protocol is a modern terminal protocol that provides more reliable and comprehensive keyboard event reporting than traditional escape sequences.
- It was introduced by the Kitty terminal emulator and is being adopted by other terminal emulators and terminal clients (including VSCode).
- VSCode enabled Kitty protocol support by default in recent updates to improve keyboard handling in integrated terminals.
- The protocol changes how keyboard events are encoded, particularly for keys that were previously ambiguous or unreliable (like Shift+Enter, Ctrl+Space, etc.).

### Related Files
- `src/teambot/ui/widgets/input_pane.py` — Primary text input widget (uses `TextArea` for multi-line input)
- `src/teambot/repl/loop.py` — Legacy REPL input handling (may also be affected if it processes raw keyboard input)
- `pyproject.toml` — Textual version dependency (may need to be updated if newer version has Kitty support)

### Investigation Steps
1. **Check Textual version and Kitty protocol support**:
   - Review current Textual version in `pyproject.toml`
   - Check Textual changelog/documentation for Kitty protocol support (added in Textual 0.40.0+)
   - Determine if a Textual upgrade is needed or if configuration changes can enable Kitty support
2. **Reproduce the issue**:
   - Start TeamBot in VSCode with Kitty protocol enabled (default in recent VSCode)
   - Attempt to type a space in the input field
   - Capture debug logs or keyboard event data to see how space events are encoded
3. **Identify the root cause**:
   - Determine if the issue is in Textual's event handling or TeamBot's input processing
   - Check if Textual's `TextArea` widget correctly handles Kitty protocol space events
   - Review any custom key event handlers in `input_pane.py` that might be filtering or misinterpreting space events
4. **Implement a solution**:
   - If Textual upgrade is needed, update dependencies and test for regressions
   - If configuration is needed, add Kitty protocol support flags or settings
   - If custom handling is needed, implement Kitty protocol event decoding
   - Ensure backward compatibility with non-Kitty terminals
5. **Test thoroughly**:
   - Test in VSCode with Kitty protocol enabled (default)
   - Test in VSCode with Kitty protocol disabled (legacy mode)
   - Test in standalone terminals (Terminal.app, iTerm2, Kitty, GNOME Terminal, etc.)
   - Verify all keyboard input types (space, special keys, arrow keys, modifier combinations)
6. **Validation checkpoint**:
   - Verify against all acceptance scenarios defined in frontmatter
   - Run existing test suite to ensure no regressions
   - Document any terminal compatibility limitations discovered

### Potential Solutions
- **Option 1: Upgrade Textual** — If a newer version of Textual has native Kitty protocol support, upgrade and enable it.
- **Option 2: Configure Textual** — If current Textual version supports Kitty protocol via configuration, enable the appropriate settings.
- **Option 3: Custom key handler** — If Textual doesn't support Kitty protocol, implement a custom key event handler that decodes Kitty protocol sequences and maps them to standard events.
- **Option 4: Protocol detection** — Implement terminal capability detection to switch between Kitty protocol mode and legacy mode automatically.

### Version Bump
- This is a bug fix that restores expected functionality in a common environment (VSCode with default settings).
- Semantic versioning: **patch version bump** (e.g., 0.1.0 → 0.1.1) since it fixes a defect without adding new features or breaking changes.

---
