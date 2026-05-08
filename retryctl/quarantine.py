"""Quarantine module: isolates persistently failing commands to prevent resource exhaustion."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuarantineConfig:
    enabled: bool = False
    failure_threshold: int = 5
    quarantine_duration: float = 60.0  # seconds
    reset_on_success: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "QuarantineConfig":
        allowed = {"enabled", "failure_threshold", "quarantine_duration", "reset_on_success"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


@dataclass
class QuarantineState:
    consecutive_failures: int = 0
    quarantined_until: Optional[float] = None
    _config: QuarantineConfig = field(default_factory=QuarantineConfig, repr=False)

    def is_quarantined(self) -> bool:
        if not self._config.enabled:
            return False
        if self.quarantined_until is None:
            return False
        return time.monotonic() < self.quarantined_until

    def record_failure(self) -> None:
        if not self._config.enabled:
            return
        self.consecutive_failures += 1
        if self.consecutive_failures >= self._config.failure_threshold:
            self.quarantined_until = time.monotonic() + self._config.quarantine_duration

    def record_success(self) -> None:
        if not self._config.enabled:
            return
        if self._config.reset_on_success:
            self.consecutive_failures = 0
            self.quarantined_until = None

    def remaining_seconds(self) -> float:
        if self.quarantined_until is None:
            return 0.0
        remaining = self.quarantined_until - time.monotonic()
        return max(0.0, remaining)


class QuarantineManager:
    def __init__(self, config: QuarantineConfig) -> None:
        self._config = config
        self._state = QuarantineState(_config=config)

    @property
    def state(self) -> QuarantineState:
        return self._state

    def is_quarantined(self) -> bool:
        return self._state.is_quarantined()

    def record_failure(self) -> None:
        self._state.record_failure()

    def record_success(self) -> None:
        self._state.record_success()

    def reset(self) -> None:
        self._state = QuarantineState(_config=self._config)
