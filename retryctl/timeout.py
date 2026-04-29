"""Timeout configuration and enforcement for retryctl."""
from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass
class TimeoutConfig:
    """Configuration for per-attempt and total-run timeouts."""

    attempt_timeout: Optional[float] = None   # seconds; None means no limit
    total_timeout: Optional[float] = None     # seconds; None means no limit

    @classmethod
    def from_dict(cls, data: dict) -> "TimeoutConfig":
        """Create a TimeoutConfig from a plain dictionary, ignoring unknown keys."""
        return cls(
            attempt_timeout=data.get("attempt_timeout"),
            total_timeout=data.get("total_timeout"),
        )

    def validate(self) -> None:
        """Raise ValueError if any value is logically invalid."""
        if self.attempt_timeout is not None and self.attempt_timeout <= 0:
            raise ValueError("attempt_timeout must be a positive number")
        if self.total_timeout is not None and self.total_timeout <= 0:
            raise ValueError("total_timeout must be a positive number")


class TimeoutTracker:
    """Tracks elapsed time and determines remaining budget for timeouts."""

    def __init__(self, config: TimeoutConfig, clock=None) -> None:
        import time
        self._config = config
        self._clock = clock or time.monotonic
        self._start: float = self._clock()

    def elapsed(self) -> float:
        """Return seconds elapsed since this tracker was created."""
        return self._clock() - self._start

    def total_exceeded(self) -> bool:
        """Return True if the total timeout has been exceeded."""
        if self._config.total_timeout is None:
            return False
        return self.elapsed() >= self._config.total_timeout

    def remaining_total(self) -> Optional[float]:
        """Return remaining seconds under the total budget, or None if unlimited."""
        if self._config.total_timeout is None:
            return None
        remaining = self._config.total_timeout - self.elapsed()
        return max(remaining, 0.0)

    def effective_attempt_timeout(self) -> Optional[float]:
        """Return the tightest timeout to apply to the next attempt."""
        attempt = self._config.attempt_timeout
        total_rem = self.remaining_total()
        if attempt is None:
            return total_rem
        if total_rem is None:
            return attempt
        return min(attempt, total_rem)
