"""Rate limiting support for retryctl — prevents retry storms."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimiterConfig:
    """Configuration for the rate limiter."""

    max_attempts_per_minute: Optional[int] = None
    min_gap_seconds: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimiterConfig":
        return cls(
            max_attempts_per_minute=data.get("max_attempts_per_minute"),
            min_gap_seconds=float(data.get("min_gap_seconds", 0.0)),
        )


@dataclass
class RateLimiter:
    """Enforces rate limits between retry attempts."""

    config: RateLimiterConfig
    _attempt_times: list = field(default_factory=list, init=False, repr=False)
    _last_attempt_time: Optional[float] = field(default=None, init=False, repr=False)

    def acquire(self) -> float:
        """Block until the next attempt is allowed. Returns seconds waited."""
        waited = 0.0

        if self.config.min_gap_seconds > 0.0 and self._last_attempt_time is not None:
            elapsed = time.monotonic() - self._last_attempt_time
            gap_remaining = self.config.min_gap_seconds - elapsed
            if gap_remaining > 0:
                time.sleep(gap_remaining)
                waited += gap_remaining

        if self.config.max_attempts_per_minute is not None:
            now = time.monotonic()
            window_start = now - 60.0
            self._attempt_times = [
                t for t in self._attempt_times if t >= window_start
            ]
            if len(self._attempt_times) >= self.config.max_attempts_per_minute:
                oldest = self._attempt_times[0]
                sleep_for = 60.0 - (now - oldest) + 0.01
                if sleep_for > 0:
                    time.sleep(sleep_for)
                    waited += sleep_for

        now = time.monotonic()
        self._attempt_times.append(now)
        self._last_attempt_time = now
        return waited

    def reset(self) -> None:
        """Clear all recorded attempt times."""
        self._attempt_times.clear()
        self._last_attempt_time = None
