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
