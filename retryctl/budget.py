"""Retry budget: limits total number of retries within a rolling time window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetConfig:
    enabled: bool = False
    max_retries_per_window: int = 10
    window_seconds: float = 60.0

    @staticmethod
    def from_dict(data: dict) -> "BudgetConfig":
        allowed = {"enabled", "max_retries_per_window", "window_seconds"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return BudgetConfig(**filtered)


@dataclass
class BudgetState:
    _timestamps: deque = field(default_factory=deque)

    def record_retry(self, now: Optional[float] = None) -> None:
        self._timestamps.append(now if now is not None else time.monotonic())

    def retry_count_in_window(self, window_seconds: float, now: Optional[float] = None) -> int:
        cutoff = (now if now is not None else time.monotonic()) - window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
        return len(self._timestamps)

    def reset(self) -> None:
        self._timestamps.clear()


class RetryBudget:
    def __init__(self, config: BudgetConfig) -> None:
        self.config = config
        self._state = BudgetState()

    def is_exhausted(self, now: Optional[float] = None) -> bool:
        if not self.config.enabled:
            return False
        count = self._state.retry_count_in_window(self.config.window_seconds, now=now)
        return count >= self.config.max_retries_per_window

    def consume(self, now: Optional[float] = None) -> None:
        self._state.record_retry(now=now)

    def reset(self) -> None:
        self._state.reset()
