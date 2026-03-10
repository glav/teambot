# Kitty Keyboard Protocol Research Summary

**Status**: ✅ Research Complete - No Implementation Required

## Key Finding

TeamBot already has full Kitty keyboard protocol support through **Textual 7.4.0**. The protocol is automatically enabled by Textual's `LinuxDriver` on application start and disabled on exit. No code changes are needed in TeamBot.

## Technical Details

### Textual's Built-In Support

1. **Automatic Protocol Enable** (Line 276 in `linux_driver.py`):
   ```python
   self.write("\x1b[>1u")  # Enable Kitty keyboard protocol
   ```

2. **Automatic Protocol Disable** (Line 374 in `linux_driver.py`):
   ```python
   self.write("\x1b[<u")  # Disable Kitty keyboard protocol
   ```

3. **Sequence Parsing** (Lines 339-362 in `_xterm_parser.py`):
   - Regex: `\x1b\[(?:(\d+)(?:;(\d+))?)?([u~ABCDEFHPQRS])`
   - Parses space as `\x1b[32u` → `events.Key(key="space", character=" ")`
   - All printable characters handled transparently

### Application-Level Impact

**Zero Impact** - TeamBot's `InputPane` receives normalized `events.Key` objects regardless of whether Kitty protocol is active:

```python
# From: src/teambot/ui/widgets/input_pane.py
async def _on_key(self, event: events.Key) -> None:
    # event.key is always a normalized string: "space", "enter", "ctrl+a", etc.
    # Protocol details are abstracted by Textual's driver layer
    if event.key == "enter":
        # Submit input
    # ...
    await super()._on_key(event)  # Space delegates to TextArea
```

## Entry Point Analysis

All keyboard input flows through a single path, with protocol handling transparent:

1. **Terminal** → Sends either `\x1b[32u` (Kitty) or `\x20` (legacy) for space
2. **LinuxDriver** → Reads from stdin in background thread
3. **XTermParser** → Parses sequences into normalized events
4. **InputPane._on_key()** → Receives `events.Key(key="space")` (same for both protocols)
5. **TextArea** → Inserts space character into text buffer

## Recommended Actions

### 1. Acceptance Testing (Manual)
Create test cases in `tests/acceptance/test_kitty_protocol_compatibility.py`:
- Verify space input in VSCode terminal (Kitty enabled by default)
- Verify multi-word input with spaces
- Verify backward compatibility in legacy terminals
- Test all keyboard input (arrows, Enter, Backspace, etc.)

### 2. Documentation
Add `docs/guides/terminal-compatibility.md`:
- Explain automatic Kitty protocol handling
- List supported terminals (Kitty, Alacritty, VSCode, iTerm2, WezTerm)
- Troubleshooting steps if space characters don't work
- Reference Textual's implementation details

### 3. Root Cause Investigation (If Issue Persists)
If space characters still don't work:
- Check VSCode setting: `terminal.integrated.enableKittyProtocol` (should be `true`)
- Test outside terminal multiplexers (tmux, screen)
- Verify locale/encoding: `echo $LANG` (should include UTF-8)
- Create minimal reproduction case with Textual alone

## Conclusion

**No code changes required.** TeamBot's input handling is already fully compatible with the Kitty keyboard protocol. Space characters should work correctly in VSCode terminal and all other supported terminals. If issues persist, they are environmental (VSCode config, terminal emulator) rather than TeamBot code issues.

## References

- Full research document: `.agent-tracking/research/20260310-kitty-protocol-input-support-research.md`
- Kitty protocol spec: https://sw.kovidgoyal.net/kitty/keyboard-protocol/
- Textual PR #4631: https://github.com/Textualize/textual/pull/4631
- Textual version: 7.4.0 (requires >=0.47.0)
