"""Time management for execution limits."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TimeManager:
    """Tracks elapsed time and enforces execution limits."""

    max_seconds: int = 8 * 60 * 60  # 8 hours default
    _start_time: float | None = field(default=None, repr=False)
    _prior_elapsed: float = field(default=0.0, repr=False)

    def start(self) -> None:
        """Start the timer."""
        self._start_time = time.monotonic()

    def resume(self, prior_elapsed: float) -> None:
        """Resume with prior elapsed time."""
        self._prior_elapsed = prior_elapsed
        self.start()

    @property
    def elapsed_seconds(self) -> float:
        """Get total elapsed seconds."""
        if self._start_time is None:
            return self._prior_elapsed
        return self._prior_elapsed + (time.monotonic() - self._start_time)

    @property
    def remaining_seconds(self) -> float:
        """Get remaining seconds before limit."""
        return max(0, self.max_seconds - self.elapsed_seconds)

    def is_expired(self) -> bool:
        """Check if time limit exceeded."""
        return self.elapsed_seconds >= self.max_seconds

    def format_elapsed(self) -> str:
        """Format elapsed time as HH:MM:SS."""
        total = int(self.elapsed_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def format_remaining(self) -> str:
        """Format remaining time as HH:MM:SS."""
        total = int(self.remaining_seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
