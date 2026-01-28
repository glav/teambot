"""Input pane widget with command history navigation."""

from textual.widgets import Input


class InputPane(Input):
    """Input pane with command history navigation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""

    def on_input_submitted(self, event) -> None:
        """Store submitted input in history."""
        if event.value.strip():
            self._history.append(event.value)
        self._history_index = -1
        self._current_input = ""

    def on_key(self, event) -> None:
        """Handle up/down arrow for history navigation."""
        if event.key == "up":
            self._navigate_history(1)  # Up goes back in history (higher index)
            event.prevent_default()
        elif event.key == "down":
            self._navigate_history(-1)  # Down goes forward (lower index)
            event.prevent_default()

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
            self._current_input = self.value

        # Calculate new index
        new_index = self._history_index + direction

        # Clamp to valid range
        if new_index < -1:
            new_index = -1
        elif new_index >= len(self._history):
            new_index = len(self._history) - 1

        self._history_index = new_index

        # Update input value
        if self._history_index == -1:
            self.value = self._current_input
        else:
            # Navigate from end of history (most recent first)
            self.value = self._history[-(self._history_index + 1)]
