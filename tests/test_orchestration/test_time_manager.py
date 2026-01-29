"""Tests for TimeManager (TDD)."""

from __future__ import annotations

import time

from teambot.orchestration.time_manager import TimeManager


class TestTimeManager:
    """Tests for TimeManager class."""

    def test_start_sets_start_time(self) -> None:
        """start() initializes the timer."""
        manager = TimeManager()
        assert manager._start_time is None
        manager.start()
        assert manager._start_time is not None

    def test_elapsed_seconds_increases(self) -> None:
        """elapsed_seconds increases over time."""
        manager = TimeManager()
        manager.start()
        time.sleep(0.05)
        elapsed = manager.elapsed_seconds
        assert elapsed >= 0.05
        time.sleep(0.05)
        assert manager.elapsed_seconds > elapsed

    def test_elapsed_seconds_before_start(self) -> None:
        """elapsed_seconds returns prior elapsed before start."""
        manager = TimeManager()
        assert manager.elapsed_seconds == 0.0

    def test_is_expired_false_before_limit(self) -> None:
        """is_expired returns False at start."""
        manager = TimeManager(max_seconds=3600)
        manager.start()
        assert manager.is_expired() is False

    def test_is_expired_true_at_limit(self) -> None:
        """is_expired returns True at exactly max_seconds."""
        manager = TimeManager(max_seconds=0)
        manager.start()
        assert manager.is_expired() is True

    def test_is_expired_true_past_limit(self) -> None:
        """is_expired returns True past max_seconds."""
        manager = TimeManager(max_seconds=0.01)
        manager.start()
        time.sleep(0.02)
        assert manager.is_expired() is True

    def test_resume_adds_prior_elapsed(self) -> None:
        """resume(prior) adds to elapsed time."""
        manager = TimeManager()
        manager.resume(prior_elapsed=100.0)
        assert manager.elapsed_seconds >= 100.0

    def test_remaining_seconds(self) -> None:
        """remaining_seconds is max - elapsed."""
        manager = TimeManager(max_seconds=3600)
        manager.start()
        remaining = manager.remaining_seconds
        assert remaining <= 3600
        assert remaining > 3500  # Should be close to max

    def test_remaining_seconds_not_negative(self) -> None:
        """remaining_seconds never goes negative."""
        manager = TimeManager(max_seconds=0)
        manager.start()
        time.sleep(0.01)
        assert manager.remaining_seconds == 0

    def test_format_elapsed(self) -> None:
        """format_elapsed returns HH:MM:SS."""
        manager = TimeManager()
        manager._prior_elapsed = 3661.0  # 1 hour, 1 min, 1 sec
        formatted = manager.format_elapsed()
        assert formatted == "01:01:01"

    def test_format_elapsed_zero(self) -> None:
        """format_elapsed works at zero."""
        manager = TimeManager()
        assert manager.format_elapsed() == "00:00:00"

    def test_format_remaining(self) -> None:
        """format_remaining returns HH:MM:SS."""
        manager = TimeManager(max_seconds=3700)  # 1 hour, 1 min, 40 sec
        manager.start()
        formatted = manager.format_remaining()
        # Should start with "01:0" for 1 hour plus
        assert formatted.startswith("01:0")

    def test_default_max_seconds_is_8_hours(self) -> None:
        """Default max is 8 hours."""
        manager = TimeManager()
        assert manager.max_seconds == 8 * 60 * 60
