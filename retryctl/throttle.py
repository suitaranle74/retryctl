"""Throttle support: pause execution when consecutive failures exceed a threshold."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ThrottleConfig:
    """Configuration for the throttle mechanism."""

    enabled: bool = False
    consecutive_failures_threshold: int = 3
    throttle_delay: float = 30.0  # seconds to pause when threshold is hit
    max_throttle_delay: float = 300.0  # ceiling for any computed delay

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleConfig":
        known = {
            "enabled",
            "consecutive_failures_threshold",
            "throttle_delay",
            "max_throttle_delay",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class ThrottleState:
    """Mutable state tracked across attempts."""

    consecutive_failures: int = 0
    total_throttle_events: int = 0
    last_throttle_at: Optional[float] = field(default=None)


class Throttler:
    """Decides whether to throttle and performs the sleep."""

    def __init__(self, config: ThrottleConfig, _sleep=time.sleep) -> None:
        self._cfg = config
        self._sleep = _sleep
        self._state = ThrottleState()

    @property
    def state(self) -> ThrottleState:
        return self._state

    def record_failure(self) -> None:
        """Call after each failed attempt."""
        self._state.consecutive_failures += 1

    def record_success(self) -> None:
        """Reset consecutive failure counter on success."""
        self._state.consecutive_failures = 0

    def maybe_throttle(self) -> bool:
        """Sleep if threshold exceeded. Returns True if throttling occurred."""
        if not self._cfg.enabled:
            return False
        if self._state.consecutive_failures < self._cfg.consecutive_failures_threshold:
            return False

        delay = min(self._cfg.throttle_delay, self._cfg.max_throttle_delay)
        self._state.total_throttle_events += 1
        self._state.last_throttle_at = time.monotonic()
        self._sleep(delay)
        return True

    def reset(self) -> None:
        self._state = ThrottleState()
