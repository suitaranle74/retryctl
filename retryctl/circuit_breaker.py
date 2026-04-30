"""Circuit breaker to halt retries after sustained failure."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"      # normal operation
    OPEN = "open"          # blocking calls
    HALF_OPEN = "half_open"  # testing recovery


@dataclass
class CircuitBreakerConfig:
    enabled: bool = False
    failure_threshold: int = 5        # failures before opening
    recovery_timeout: float = 60.0    # seconds before half-open
    success_threshold: int = 1        # successes in half-open to close

    @staticmethod
    def from_dict(data: dict) -> "CircuitBreakerConfig":
        known = {"enabled", "failure_threshold", "recovery_timeout", "success_threshold"}
        filtered = {k: v for k, v in data.items() if k in known}
        return CircuitBreakerConfig(**filtered)


@dataclass
class CircuitBreaker:
    config: CircuitBreakerConfig
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _opened_at: Optional[float] = field(default=None, init=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
        return self._state

    def is_open(self) -> bool:
        """Return True if the circuit is open (calls should be blocked)."""
        if not self.config.enabled:
            return False
        return self.state == CircuitState.OPEN

    def record_success(self) -> None:
        if not self.config.enabled:
            return
        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._opened_at = None
        elif self.state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        if not self.config.enabled:
            return
        self._failure_count += 1
        if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
