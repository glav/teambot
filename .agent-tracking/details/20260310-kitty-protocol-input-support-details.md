<!-- markdownlint-disable-file -->
# Task Details: Kitty Protocol Input Support

**Research Reference**: `.agent-tracking/research/20260310-kitty-protocol-input-support-research.md`

**Implementation Note**: Research confirms that Textual 7.4.0 already has full Kitty protocol support built-in (Research Lines 96-106, 241-259). No application code changes are required. This details file focuses on verification, testing, and documentation tasks only.

---

## Phase 1: Acceptance Test Creation

### Task 1.1: Create acceptance test file structure

**Research Reference**: Lines 45-73 (Testing Infrastructure), Lines 432-493 (Acceptance Test Strategy)

**File to Create**: `tests/acceptance/test_kitty_protocol_compatibility.py`

**Purpose**: Create the test file structure with proper pytest markers and module documentation explaining why these are manual verification tests.

**Implementation Details**:

```python
"""
Acceptance tests for Kitty keyboard protocol compatibility.

These tests verify TeamBot's input handling works correctly in terminals
with and without Kitty protocol support. They require real terminal
environments and cannot be run with Textual's HeadlessDriver.

All tests in this module should be marked with @pytest.mark.acceptance
and are excluded from the default pytest run.
"""

import pytest

# Module-level marker to exclude from default runs
pytestmark = pytest.mark.acceptance
```

**Success Criteria**:
- [ ] File created in `tests/acceptance/` directory
- [ ] Module docstring explains manual verification requirement
- [ ] `pytestmark = pytest.mark.acceptance` applied at module level
- [ ] File follows TeamBot's pytest conventions (Lines 45-51 in research)

---

### Task 1.2: Add space character input test case

**Research Reference**: Lines 273-277 (Space Character Examples), Lines 448-462 (Space Input Test)

**Test Function**: `test_space_character_input_with_kitty_protocol()`

**Purpose**: Document manual verification steps for space character input when Kitty protocol is enabled.

**Implementation Details**:

```python
@pytest.mark.acceptance
def test_space_character_input_with_kitty_protocol():
    """Verify space characters work when Kitty protocol is enabled.
    
    MANUAL TEST CASE - Requires real terminal with Kitty protocol support.
    
    Prerequisites:
    * Terminal with Kitty protocol support (Kitty, Alacritty, VSCode, WezTerm)
    * TeamBot installed: `uv sync`
    
    Steps:
    1. Enable Kitty protocol manually (optional, to verify):
       printf '\x1b[>1u'
    2. Launch TeamBot: `uv run teambot status`
    3. In input pane, type: "hello world" (with space between words)
    4. Observe: Space character should appear correctly
    5. Press Enter to submit
    6. Verify: Command echoed correctly in output pane
    
    Expected Result:
    ✅ Space appears immediately as typed
    ✅ Input shows "hello world" (not "helloworld")
    ✅ No error messages or protocol warnings
    
    Troubleshooting:
    * If space doesn't appear: Check terminal Kitty protocol support
    * VSCode users: Verify terminal.integrated.enableKittyProtocol is true
    """
    pass  # Manual test case - no automated assertion
```

**Success Criteria**:
- [ ] Test documents clear manual verification steps
- [ ] Prerequisites listed (terminal requirements)
- [ ] Expected results explicitly stated
- [ ] Troubleshooting guidance included

---

### Task 1.3: Add multi-word input test case for VSCode

**Research Reference**: Lines 310-320 (VSCode Terminal Settings), Lines 465-478 (Multi-word Test)

**Test Function**: `test_multi_word_input_in_vscode_terminal()`

**Purpose**: Verify multi-word input works correctly in VSCode integrated terminal with default Kitty protocol enabled.

**Implementation Details**:

```python
@pytest.mark.acceptance
def test_multi_word_input_in_vscode_terminal():
    """Verify multi-word input works in VSCode terminal.
    
    MANUAL TEST CASE - Specific to VSCode integrated terminal.
    
    Prerequisites:
    * VSCode with integrated terminal
    * Default setting: terminal.integrated.enableKittyProtocol: true
    * TeamBot installed: `uv sync`
    
    Steps:
    1. Open VSCode integrated terminal (Ctrl+`)
    2. Launch TeamBot: `uv run teambot status`
    3. Type complex multi-word command: "create a feature spec for authentication"
    4. Observe each space character as it's typed
    5. Press Enter to submit
    6. Verify command is echoed correctly in output pane
    
    Expected Result:
    ✅ All spaces appear correctly during typing
    ✅ Input shows full command: "create a feature spec for authentication"
    ✅ Command submission works without truncation
    ✅ Output pane echoes command accurately
    
    VSCode Configuration Check:
    * Ctrl+Shift+P → "Preferences: Open Settings (JSON)"
    * Verify: "terminal.integrated.enableKittyProtocol": true (or not present = default true)
    
    Known Issues:
    * If spaces missing: Check VSCode version (update to latest)
    * Restart terminal: Ctrl+Shift+P → "Terminal: Kill All Terminals"
    """
    pass  # Manual test case
```

**Success Criteria**:
- [ ] Test specific to VSCode terminal environment
- [ ] Configuration check instructions included
- [ ] Complex multi-word test case documented
- [ ] Known issues and resolution steps provided

---

### Task 1.4: Add backward compatibility test case

**Research Reference**: Lines 349-358 (Legacy Terminal Path), Lines 480-492 (Backward Compatibility Test)

**Test Function**: `test_backward_compatibility_without_kitty_protocol()`

**Purpose**: Verify TeamBot works correctly in terminals that do not support Kitty protocol.

**Implementation Details**:

```python
@pytest.mark.acceptance
def test_backward_compatibility_without_kitty_protocol():
    """Verify TeamBot works in terminals without Kitty protocol support.
    
    MANUAL TEST CASE - Requires legacy terminal (no Kitty protocol).
    
    Prerequisites:
    * Legacy terminal: xterm, GNOME Terminal, or standard Linux console
    * TeamBot installed: `uv sync`
    
    Steps:
    1. Ensure Kitty protocol is not enabled (most legacy terminals)
    2. Optionally disable explicitly: printf '\x1b[<u'
    3. Launch TeamBot: `uv run teambot status`
    4. Type: "hello world" (with space)
    5. Verify space appears correctly
    6. Test arrow keys: Up, Down, Left, Right
    7. Test special keys: Enter, Backspace, Tab
    8. Test history navigation: Up arrow to recall previous command
    
    Expected Result:
    ✅ Space character works identically to Kitty protocol terminals
    ✅ All keyboard input types function correctly
    ✅ History navigation works (Up/Down arrows)
    ✅ No protocol-related warnings or errors
    
    Terminal Compatibility:
    * Tested terminals: xterm, GNOME Terminal, Konsole, Terminal.app
    * Expected behavior: Identical input handling regardless of protocol
    
    Technical Note:
    * Legacy terminals send space as plain 0x20 byte (not escape sequence)
    * Textual's XTermParser handles both paths (Research Lines 349-358)
    * Application receives same events.Key objects in both modes
    """
    pass  # Manual test case
```

**Success Criteria**:
- [ ] Test covers terminals without Kitty protocol support
- [ ] All keyboard input types tested (not just space)
- [ ] History navigation verified (key TeamBot feature)
- [ ] Technical note explains backward compatibility mechanism

---

### Task 1.5: Add keyboard input comprehensive test

**Research Reference**: Lines 77-86 (InputPane Key Handling), Lines 198-238 (Current Key Handling Code)

**Test Function**: `test_all_keyboard_input_with_kitty_protocol()`

**Purpose**: Verify all keyboard input types work correctly with Kitty protocol enabled.

**Implementation Details**:

```python
@pytest.mark.acceptance
def test_all_keyboard_input_with_kitty_protocol():
    """Verify all keyboard input types with Kitty protocol enabled.
    
    MANUAL TEST CASE - Comprehensive keyboard input verification.
    
    Prerequisites:
    * Terminal with Kitty protocol support
    * TeamBot installed: `uv sync`
    
    Test Cases:
    
    1. Basic Printable Characters:
       - Type: "abcdefghijklmnopqrstuvwxyz"
       - Type: "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (with Shift)
       - Type: "0123456789"
       - Type: "!@#$%^&*()_+-=[]{}|;':\",./<>?"
       - Expected: All characters appear correctly
    
    2. Space and Whitespace:
       - Type: "word1 word2  word3   word4" (varying spaces)
       - Expected: All spaces preserved
    
    3. Navigation Keys:
       - Type: "test", press Left arrow 2 times, type "xx"
       - Expected: "texxst" (cursor navigation works)
       - Press Home, type "start"
       - Expected: "starttexxst" (Home key works)
       - Press End, type "end"
       - Expected: "starttexxstend" (End key works)
    
    4. Modifier Key Combinations:
       - Ctrl+Enter: Insert newline (don't submit)
       - Alt+Enter: Insert newline (don't submit)
       - Shift+Enter: Insert newline (don't submit)
       - Expected: Multi-line input works
    
    5. History Navigation:
       - Type: "command one", press Enter
       - Type: "command two", press Enter
       - Press Up arrow: Should show "command two"
       - Press Up arrow again: Should show "command one"
       - Press Down arrow: Should show "command two"
       - Expected: History navigation works correctly
    
    6. Special Characters with Modifiers:
       - Ctrl+A (if custom binding exists)
       - Ctrl+C (interrupt - may exit app)
       - Ctrl+D (EOF - may exit app)
       - Expected: Modifiers recognized correctly
    
    Expected Result:
    ✅ All printable characters input correctly
    ✅ Space character works in all contexts
    ✅ Navigation keys move cursor properly
    ✅ Modifier combinations work as designed (Research Lines 77-86)
    ✅ History navigation functions correctly
    
    Reference:
    * InputPane key handling: Research Lines 198-238
    * Custom key bindings: Enter, Ctrl+Enter, Up, Down
    * Other keys delegated to TextArea default behavior
    """
    pass  # Manual test case
```

**Success Criteria**:
- [ ] Test covers all keyboard input categories
- [ ] Modifier key combinations tested (Ctrl, Alt, Shift)
- [ ] History navigation tested (Up/Down arrows)
- [ ] Custom key bindings verified (Enter, Ctrl+Enter)
- [ ] Test references InputPane's actual key handling logic

---

## Phase 2: Documentation Creation

### Task 2.1: Create terminal compatibility guide

**Research Reference**: Lines 143-152 (External Research - Supported Terminals), Lines 497-545 (Documentation Addition)

**File to Create**: `docs/guides/terminal-compatibility.md`

**Purpose**: Document TeamBot's terminal compatibility, focusing on Kitty keyboard protocol support.

**Implementation Details**:

```markdown
# Terminal Compatibility Guide

TeamBot's split-pane UI is built with the Textual framework, which includes native support for modern terminal features including the Kitty keyboard protocol.

## Supported Terminals

### Kitty Protocol Enabled (Recommended)

These terminals support the Kitty keyboard protocol, providing enhanced keyboard handling with unambiguous key codes and better modifier key support:

* **Kitty** - Native implementation
* **Alacritty** - Full support
* **Ghostty** - Full support
* **Foot** - Full support
* **iTerm2** - Earlier version (backward compatible)
* **WezTerm** - Full support
* **VSCode Integrated Terminal** - Enabled by default (`terminal.integrated.enableKittyProtocol: true`)

### Legacy Terminals (Fully Compatible)

These terminals work correctly with TeamBot but do not support the Kitty keyboard protocol:

* **xterm** - Standard terminal emulator
* **GNOME Terminal** - GNOME desktop default
* **Konsole** - KDE desktop default
* **Terminal.app** - macOS default
* **Windows Terminal** - Windows 10/11 default

## Automatic Protocol Handling

The Kitty protocol is **automatically enabled** when TeamBot starts in supported terminals and **automatically disabled** on exit. **No configuration is required from users.**

**Technical Details:**
* **Protocol Enable**: Textual sends `CSI > 1 u` (`\x1b[>1u`) on application start
* **Protocol Disable**: Textual sends `CSI < u` (`\x1b[<u`) on application exit
* **Transparent to Application**: TeamBot's code receives normalized key events regardless of protocol

## What is the Kitty Keyboard Protocol?

The Kitty keyboard protocol solves long-standing terminal keyboard handling problems:
* **Ambiguous escape codes** - Many key combinations produce identical sequences
* **Limited modifiers** - Difficult to distinguish Shift+Key vs plain key in all cases
* **No press/release events** - Only key press is reported

The protocol is backward compatible - terminals that don't support it continue to work normally.

**Reference**: [Official Kitty Keyboard Protocol Documentation](https://sw.kovidgoyal.net/kitty/keyboard-protocol/)
```

**Success Criteria**:
- [ ] File created with proper markdown formatting
- [ ] All supported terminals listed (from Research Lines 511-518)
- [ ] Legacy terminals explicitly marked as compatible
- [ ] Automatic protocol handling explained clearly
- [ ] Link to official Kitty protocol specification included

---

### Task 2.2: Add technical details section

**Research Reference**: Lines 96-127 (Textual Framework - Kitty Protocol Implementation), Lines 263-295 (API Documentation)

**File**: `docs/guides/terminal-compatibility.md` (append to Task 2.1)

**Purpose**: Add technical implementation details for developers and advanced users.

**Implementation Details**:

```markdown
## Technical Implementation

### How Textual Handles the Kitty Protocol

TeamBot uses Textual 7.4.0, which includes native Kitty protocol support since PR #4631.

**Automatic Lifecycle Management:**

1. **Application Start** (`LinuxDriver.__enter__`):
   ```python
   self.write("\x1b[>1u")  # Enable Kitty keyboard protocol
   ```

2. **Application Exit** (`LinuxDriver.__exit__`):
   ```python
   self.write("\x1b[<u")  # Disable Kitty keyboard protocol
   ```

**Key Event Parsing:**

When Kitty protocol is active, keyboard input is encoded as escape sequences:
* Format: `CSI number ; modifiers u`
* Example: Space = `\x1b[32u` (where 32 is Unicode codepoint for space)
* Modifiers: Bit field (shift=1, alt=2, ctrl=4, super=8)

**Example Space Character Sequences:**
* Plain space: `\x1b[32u`
* Shift+Space: `\x1b[32;2u`
* Ctrl+Space: `\x1b[32;5u` (where 5 = 1 + 4)

**Legacy Terminals** (no Kitty protocol):
* Space sent as plain ASCII: `0x20` (single byte)
* Both paths produce identical `events.Key(key="space")` for application code

**Reference**:
* Textual implementation: `textual/drivers/linux_driver.py`
* Key parser: `textual/_xterm_parser.py`
* Protocol spec: https://sw.kovidgoyal.net/kitty/keyboard-protocol/
```

**Success Criteria**:
- [ ] Technical details section added after main content
- [ ] Escape sequence examples included
- [ ] Automatic lifecycle management explained
- [ ] References to Textual source code provided
- [ ] Legacy terminal path contrasted with Kitty protocol path

---

### Task 2.3: Add troubleshooting section

**Research Reference**: Lines 533-544 (Troubleshooting), Lines 568-627 (Root Cause Analysis)

**File**: `docs/guides/terminal-compatibility.md` (append to Task 2.2)

**Purpose**: Provide diagnostic steps for space character input issues and other Kitty protocol problems.

**Implementation Details**:

```markdown
## Troubleshooting

### Space Characters Not Working in VSCode

If space characters don't appear when typing in TeamBot:

1. **Check VSCode Kitty Protocol Setting:**
   * Press `Ctrl+Shift+P` → "Preferences: Open Settings (JSON)"
   * Verify: `"terminal.integrated.enableKittyProtocol": true` (or not present, which defaults to true)
   * If explicitly set to `false`, change to `true` or remove the setting

2. **Restart VSCode Terminal:**
   * Press `Ctrl+Shift+P` → "Terminal: Kill All Terminals"
   * Open new terminal: `Ctrl+`` (backtick)
   * Re-launch TeamBot: `uv run teambot status`

3. **Verify Textual Version:**
   ```bash
   python -c "import textual; print(textual.__version__)"
   # Should be 7.4.0 or higher (requires >=0.47.0 for Kitty protocol support)
   ```

4. **Check for Conflicting Software:**
   * **Terminal multiplexers**: tmux or screen may interfere with escape sequences
     - Test outside multiplexer: Exit tmux/screen, run TeamBot directly
   * **Shell configurations**: Custom key bindings in `.bashrc` or `.zshrc` may capture input
     - Test with clean shell: `bash --norc` or `zsh -f`, then run TeamBot
   * **VSCode extensions**: Terminal-focused extensions may intercept keyboard input
     - Disable extensions temporarily to isolate issue

### Manual Protocol Verification

Test if your terminal supports Kitty protocol:

```bash
# Enable Kitty protocol manually
printf '\x1b[>1u'

# Use cat -v to visualize input (or od -c for detailed output)
cat -v
# Press space bar - you should see: ^[[32u (Kitty protocol)
# Without protocol, you'd see just a space character

# Press Ctrl+C to exit cat

# Disable Kitty protocol
printf '\x1b[<u'
```

### Character Encoding Issues

If input appears garbled or spaces are replaced with other characters:

```bash
# Check locale settings
locale
# Verify UTF-8 encoding:
echo $LANG  # Should include UTF-8 (e.g., en_US.UTF-8)

# If not UTF-8, set temporarily:
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Still Having Issues?

If problems persist after troubleshooting:

1. **Create minimal test case** with Textual alone:
   ```python
   from textual.app import App
   from textual.widgets import TextArea
   
   class TestApp(App):
       def compose(self):
           yield TextArea()
   
   if __name__ == "__main__":
       TestApp().run()
   ```
   * Type "hello world" - if space works here, issue is TeamBot-specific
   * If space doesn't work, issue is environmental (terminal/Textual)

2. **Report issue** with details:
   * Terminal emulator and version
   * Operating system
   * Textual version (`python -c "import textual; print(textual.__version__)"`)
   * TeamBot version (`teambot --version`)
   * Steps to reproduce
```

**Success Criteria**:
- [ ] VSCode-specific troubleshooting steps provided
- [ ] Manual protocol verification commands included
- [ ] Common issues documented (tmux, encoding, extensions)
- [ ] Minimal test case provided for isolation
- [ ] Clear escalation path if issues persist

---

### Task 2.4: Update user guides with Kitty protocol references

**Research Reference**: Lines 497-545 (Documentation Addition - Keyboard Protocol Support)

**Files to Update**:
* `docs/guides/getting-started.md`
* `README.md` (if terminal requirements section exists)

**Purpose**: Add cross-references to terminal compatibility guide for users encountering input issues.

**Implementation Details**:

**In `docs/guides/getting-started.md`** (add after installation section):

```markdown
## Terminal Compatibility

TeamBot works with all modern terminal emulators. For the best experience, we recommend:

* **VSCode Integrated Terminal** (recommended) - Kitty protocol enabled by default
* **Kitty**, **Alacritty**, **WezTerm** - Full keyboard protocol support
* **iTerm2** (macOS) - Enhanced keyboard handling
* **Legacy terminals** (xterm, GNOME Terminal, etc.) - Fully compatible

TeamBot automatically adapts to your terminal's capabilities. No configuration is required.

**Having input issues?** See the [Terminal Compatibility Guide](./terminal-compatibility.md) for troubleshooting.
```

**In `README.md`** (add to Prerequisites or Installation section):

```markdown
### Terminal Requirements

TeamBot's split-pane UI works with all modern terminal emulators. For the best experience:

* **VSCode integrated terminal** - Recommended (Kitty protocol support enabled by default)
* **Kitty**, **Alacritty**, **WezTerm** - Full support for enhanced keyboard protocol
* **Standard terminals** - xterm, GNOME Terminal, Konsole, Terminal.app all work correctly

For troubleshooting input issues, see [Terminal Compatibility Guide](docs/guides/terminal-compatibility.md).
```

**Success Criteria**:
- [ ] Getting started guide updated with terminal compatibility note
- [ ] README updated with terminal requirements
- [ ] Cross-references to terminal compatibility guide added
- [ ] VSCode highlighted as recommended terminal
- [ ] Legacy terminals explicitly marked as compatible

---

## Phase 3: Verification and Validation

### Task 3.1: Manual testing in VSCode terminal

**Research Reference**: Lines 310-320 (VSCode Terminal Settings), Lines 465-478 (Multi-word Input Test)

**Purpose**: Verify space character input and multi-word commands work correctly in VSCode's integrated terminal with default Kitty protocol enabled.

**Prerequisites**:
* VSCode installed with integrated terminal
* TeamBot installed: `uv sync`
* Default VSCode settings (Kitty protocol enabled)

**Test Procedure**:

1. **Launch VSCode Terminal:**
   * Press `Ctrl+`` (backtick) to open integrated terminal
   * Verify terminal type: `echo $TERM` (should be `xterm-256color` or similar)

2. **Start TeamBot:**
   ```bash
   cd /workspaces/teambot
   uv run teambot status
   ```

3. **Test Single Space:**
   * Type: "hello world"
   * Observe: Space should appear immediately after "hello"
   * Press Enter
   * Verify: Command echoed in output pane as "hello world"

4. **Test Multiple Spaces:**
   * Type: "word1  word2   word3" (varying space counts)
   * Observe: All spaces preserved
   * Press Enter
   * Verify: Output shows exact spacing

5. **Test Multi-Word Command:**
   * Type: "create a feature spec for authentication"
   * Observe: Each space appears as typed
   * Press Enter
   * Verify: Full command submitted without truncation

6. **Test History Navigation:**
   * Press Up arrow
   * Verify: Previous multi-word command recalled correctly
   * Press Down arrow
   * Verify: Moves forward in history

**Success Criteria**:
- [ ] Space characters appear immediately during typing
- [ ] Multi-word commands submit correctly
- [ ] Multiple spaces preserved (not collapsed)
- [ ] History navigation works with multi-word entries
- [ ] No error messages or protocol warnings

**If Test Fails**: Follow troubleshooting steps in Task 2.3 (VSCode terminal restart, configuration check)

---

### Task 3.2: Manual testing in Kitty terminal

**Research Reference**: Lines 143-152 (Supported Terminals), Lines 241-259 (Kitty Protocol Initialization)

**Purpose**: Verify TeamBot works correctly in native Kitty terminal emulator.

**Prerequisites**:
* Kitty terminal installed: `apt install kitty` or from https://sw.kovidgoyal.net/kitty/
* TeamBot installed: `uv sync`

**Test Procedure**:

1. **Launch Kitty Terminal:**
   ```bash
   kitty
   ```

2. **Verify Kitty Protocol Support:**
   ```bash
   # Enable protocol manually (should already be enabled by Kitty)
   printf '\x1b[>1u'
   
   # Test with cat -v (optional verification)
   cat -v
   # Press space - should see: ^[[32u
   # Press Ctrl+C to exit
   ```

3. **Start TeamBot:**
   ```bash
   cd /workspaces/teambot
   uv run teambot status
   ```

4. **Test All Keyboard Input Types:**
   * Printable characters: "abcdefg ABCDEFG 1234567 !@#$%^&*()"
   * Space characters: "multiple word input test"
   * Navigation: Type "test", Left arrow, "xx" → "texxst"
   * Modifiers: Ctrl+Enter for newline (don't submit)
   * Special keys: Home, End, Backspace, Delete

5. **Compare with VSCode Behavior:**
   * All input types should work identically
   * No differences in space character handling
   * Same responsiveness and behavior

**Success Criteria**:
- [ ] All keyboard input works correctly
- [ ] Space characters function identically to VSCode terminal
- [ ] Modifier combinations work (Ctrl+Enter, Alt+Enter)
- [ ] Navigation keys work (arrows, Home, End)
- [ ] Behavior matches VSCode terminal exactly

**If Test Fails**: Verify Kitty version supports protocol (version 0.26.0+)

---

### Task 3.3: Manual testing in legacy terminal

**Research Reference**: Lines 349-358 (Legacy Terminal Path), Lines 520-523 (Legacy Terminals List)

**Purpose**: Verify backward compatibility with terminals that do not support Kitty keyboard protocol.

**Prerequisites**:
* Access to legacy terminal (xterm, GNOME Terminal, or Linux console)
* TeamBot installed: `uv sync`

**Test Procedure**:

1. **Launch Legacy Terminal:**
   * xterm: `xterm` command
   * GNOME Terminal: Launch from applications menu
   * Linux console: Ctrl+Alt+F2 (switch back with Ctrl+Alt+F1)

2. **Verify No Kitty Protocol:**
   ```bash
   # Disable protocol explicitly (should already be disabled)
   printf '\x1b[<u'
   
   # Test with cat (optional verification)
   cat
   # Press space - should see: just a space (not escape sequence)
   # Press Ctrl+C to exit
   ```

3. **Start TeamBot:**
   ```bash
   cd /workspaces/teambot
   uv run teambot status
   ```

4. **Test Space Character Input:**
   * Type: "hello world"
   * Observe: Space should appear identically to Kitty terminals
   * Press Enter
   * Verify: Command submitted correctly

5. **Test All Input Types:**
   * Multi-word input: "create a feature spec"
   * Arrow keys: Left, Right, Up (history), Down (history)
   * Enter key: Submit command
   * Backspace: Delete character
   * Tab: (may be intercepted by shell completion)

6. **Verify No Protocol Warnings:**
   * Check output pane for error messages
   * Verify no protocol-related warnings in logs

**Success Criteria**:
- [ ] Space characters work identically to Kitty protocol terminals
- [ ] All keyboard input functions correctly
- [ ] History navigation works (Up/Down arrows)
- [ ] No error messages or protocol warnings
- [ ] Behavior indistinguishable from modern terminals (from user perspective)

**If Test Fails**: This indicates a regression in backward compatibility - escalate immediately

---

### Task 3.4: Validate documentation accuracy

**Research Reference**: Lines 1-689 (entire research document)

**Purpose**: Cross-check all documentation against research findings to ensure technical accuracy.

**Validation Checklist**:

1. **Protocol Escape Sequences:**
   - [ ] Enable sequence `\x1b[>1u` matches research (Lines 96-100)
   - [ ] Disable sequence `\x1b[<u` matches research (Lines 101-106)
   - [ ] Space encoding `\x1b[32u` matches research (Lines 273-277)

2. **Supported Terminal List:**
   - [ ] All terminals from research listed (Lines 143-152, 511-518)
   - [ ] VSCode marked as recommended (Lines 310-320)
   - [ ] Legacy terminals marked as compatible (Lines 520-523)

3. **Technical Details:**
   - [ ] Textual version requirement (>=0.47.0, current 7.4.0) accurate
   - [ ] LinuxDriver enable/disable lifecycle correct
   - [ ] XTermParser parsing mechanism accurately described

4. **Troubleshooting Steps:**
   - [ ] VSCode configuration setting name correct: `terminal.integrated.enableKittyProtocol`
   - [ ] Diagnostic commands tested and working: `printf '\x1b[>1u'`, `cat -v`
   - [ ] Common issues accurately identified (tmux, encoding, extensions)

5. **Code References:**
   - [ ] InputPane key handling path correct (Research Lines 77-86, 198-238)
   - [ ] Event flow trace accurate (Research Lines 333-365)
   - [ ] Protocol-agnostic application code confirmed (Research Lines 77-86, 409-420)

6. **External Links:**
   - [ ] Kitty protocol specification link valid: https://sw.kovidgoyal.net/kitty/keyboard-protocol/
   - [ ] Textual PR #4631 link valid: https://github.com/Textualize/textual/pull/4631

**Validation Commands:**

```bash
# Test diagnostic commands from documentation
printf '\x1b[>1u'  # Should not produce visible output
cat -v             # Press space, verify escape sequence visible
# Ctrl+C to exit
printf '\x1b[<u'   # Should not produce visible output

# Verify Textual version
python -c "import textual; print(textual.__version__)"  # Should output 7.4.0

# Verify TeamBot version
uv run teambot --version

# Test markdown formatting
uv run ruff format --check docs/
```

**Success Criteria**:
- [ ] All protocol sequences verified against research
- [ ] All terminal lists complete and accurate
- [ ] All code references point to correct locations
- [ ] All external links tested and working
- [ ] All diagnostic commands tested and accurate
- [ ] No technical inaccuracies identified

**If Validation Fails**: Update documentation to match research findings before completing Phase 3

---

## Summary

This implementation plan focuses on **verification and documentation** because research confirms Textual 7.4.0 already provides complete Kitty protocol support. No application code changes are required in TeamBot.

**Key Deliverables**:
1. Acceptance tests for manual verification of Kitty protocol compatibility
2. Comprehensive terminal compatibility guide with troubleshooting
3. Manual testing in multiple terminal environments (VSCode, Kitty, legacy)
4. Documentation validation against research findings

**Estimated Total Effort**: ~4.5 hours (mostly documentation and manual testing)

**Risk**: LOW - No code changes reduce risk of regressions
