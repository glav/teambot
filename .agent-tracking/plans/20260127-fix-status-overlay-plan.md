# Fix Status Display Overlay Issues

## Problem
The status display overlay in the top-right corner has two issues:
1. **Scrolls off screen**: When the user presses Enter or when output is printed, the overlay scrolls off the screen instead of remaining fixed
2. **Box alignment issues**: The box border sides are misaligned

## Root Cause Analysis
Based on code review of `overlay.py`:

1. **Scrolling Issue**: The overlay uses ANSI escape sequences (`SAVE_CURSOR`/`RESTORE_CURSOR`) to render at a fixed position, but:
   - When content scrolls, the saved cursor position scrolls with it
   - The overlay is rendered at absolute row/col positions, but terminal scrolling invalidates these positions
   - Need an "alternate screen buffer" or scroll region approach

2. **Box Alignment**: The `_render_box()` method may have:
   - Unicode character width miscalculations (box drawing chars)
   - Content padding issues with emoji/unicode in spinner and status icons
   - Terminal encoding issues

## Proposed Solution

### Approach 1: Scroll Region (Recommended)
Use ANSI scroll region to reserve the top lines for the overlay:
- Set scroll region to start below the overlay (e.g., rows 5-end)
- Render overlay in reserved area (rows 1-4)
- All output scrolls only in the scroll region, leaving overlay fixed

### Approach 2: Alternate Screen Buffer
Use alternate screen buffer for overlay:
- Switch to alternate buffer for overlay
- Render in main buffer
- More complex, may cause flickering

## Implementation Plan

- [ ] **Task 1**: Add scroll region support to `OverlayRenderer`
  - Add `_set_scroll_region(start_row: int)` method
  - Add `_reset_scroll_region()` method
  - Update `enable()` to set scroll region
  - Update `disable()` to reset scroll region
  - Use ANSI sequences: `\033[{start};{end}r` (set) and `\033[r` (reset)

- [ ] **Task 2**: Fix box alignment issues
  - Audit `_render_box()` for correct padding calculations
  - Test with emoji characters (spinner, checkmarks, etc.)
  - Ensure consistent width calculations for content lines
  - Add explicit character width handling for Unicode

- [ ] **Task 3**: Update `print_with_overlay()` to respect scroll region
  - Ensure prints go to the scroll region, not over the overlay
  - Test that cursor positioning works correctly

- [ ] **Task 4**: Handle terminal resize events
  - Add resize detection
  - Recalculate overlay position and scroll region on resize
  - Ensure overlay redraws correctly

- [ ] **Task 5**: Test fixes
  - Test with rapid Enter key presses
  - Test with various terminal emulators (VSCode terminal, iTerm2, etc.)
  - Test with different terminal sizes
  - Test overlay enable/disable/position changes

## Alternative Considerations

If scroll regions cause issues:
- Fallback to periodic redraw (render overlay every N ms)
- Add terminal capability detection for scroll region support
- Consider using `curses` library for more robust terminal control

## Testing Strategy
1. Manual testing in VSCode devcontainer terminal
2. Test with rapid output generation
3. Test Enter key scrolling behavior
4. Verify box drawing characters render correctly
5. Test different overlay positions (all four corners)

## Notes
- Keep changes minimal and focused on the two issues
- Maintain backward compatibility with terminals that don't support scroll regions
- Document any terminal compatibility limitations
