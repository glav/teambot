"""Input pane widget with multi-line editing and command history navigation."""

from textual import events
from textual.message import Message
from textual.widgets import TextArea


class InputPane(TextArea):
    """Multi-line input pane with command history navigation.

    Extends TextArea to provide:
    - Enter to submit (posts Submitted message)
    - Ctrl+Enter / Alt+Enter / Shift+Enter to insert newline
    - Conditional Up/Down history navigation (only at first/last line)
    """

    class Submitted(Message):
        """Posted when user presses Enter to submit input."""

        def __init__(self, input: "InputPane", value: str) -> None:
            super().__init__()
            self.input = input
            self.value = value

    def __init__(self, placeholder: str = "", **kwargs):
        super().__init__(
            soft_wrap=True,
            show_line_numbers=False,
            **kwargs,
        )
        self.placeholder = placeholder
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""

    async def _on_key(self, event: events.Key) -> None:
        """Handle key events for submit, newline, and history."""
        if event.key in ("ctrl+enter", "alt+enter", "shift+enter"):
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return

        if event.key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text
            if text.strip():
                self._history.append(text)
            self._history_index = -1
            self._current_input = ""
            self.post_message(self.Submitted(self, text))
            self.clear()
            return

        if event.key == "up" and self.cursor_at_first_line:
            event.stop()
            event.prevent_default()
            self._navigate_history(1)
            return

        if event.key == "down" and self.cursor_at_last_line:
            event.stop()
            event.prevent_default()
            self._navigate_history(-1)
            return

        # All other keys: default TextArea behavior
        await super()._on_key(event)

    def _navigate_history(self, direction: int) -> None:
        """Navigate through command history.

        Index -1 means current input (not in history).
        Index 0 means most recent history entry.
        Index len-1 means oldest history entry.
        """
        if not self._history:
            return

        # Save current input when starting navigation
        if self._history_index == -1 and direction > 0:
            self._current_input = self.text

        # Calculate new index
        new_index = self._history_index + direction

        # Clamp to valid range
        if new_index < -1:
            new_index = -1
        elif new_index >= len(self._history):
            new_index = len(self._history) - 1

        self._history_index = new_index

        # Update input text
        if self._history_index == -1:
            self.text = self._current_input
        else:
            # Navigate from end of history (most recent first)
            self.text = self._history[-(self._history_index + 1)]
