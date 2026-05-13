"""Debounce support: suppress rapid successive retries within a quiet window."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DebounceConfig:
    """Configuration for debounce behaviour."""

    enabled: bool = False
    window_seconds: float = 1.0  # minimum quiet period before a retry is allowed

    @classmethod
    def from_dict(cls, data: dict) -> "DebounceConfig":
        allowed = {"enabled", "window_seconds"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


@dataclass
class DebounceState:
    """Runtime state for the debounce tracker."""

    config: DebounceConfig
    _last_attempt_time: Optional[float] = field(default=None, repr=False)

    def should_debounce(self) -> bool:
        """Return True if a retry should be suppressed (too soon after last attempt)."""
        if not self.config.enabled:
            return False
        if self._last_attempt_time is None:
            return False
        elapsed = time.monotonic() - self._last_attempt_time
        return elapsed < self.config.window_seconds

    def record_attempt(self) -> None:
        """Record that an attempt just occurred."""
        self._last_attempt_time = time.monotonic()

    def remaining_wait(self) -> float:
        """Return how many seconds must still elapse before the next retry is allowed."""
        if not self.config.enabled or self._last_attempt_time is None:
            return 0.0
        elapsed = time.monotonic() - self._last_attempt_time
        remaining = self.config.window_seconds - elapsed
        return max(0.0, remaining)

    def reset(self) -> None:
        """Clear debounce state (e.g. after a successful run)."""
        self._last_attempt_time = None
