"""Drain policy: controls graceful shutdown behavior during retry loops."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DrainConfig:
    """Configuration for drain / graceful-shutdown behaviour."""

    enabled: bool = False
    # Maximum seconds to wait for an in-flight attempt to finish before
    # forcibly terminating it on shutdown signal.
    grace_period: float = 5.0
    # When True, the runner will not start a *new* attempt once a drain
    # signal has been received, but will let the current one complete.
    complete_current: bool = True

    @staticmethod
    def from_dict(data: dict) -> "DrainConfig":
        allowed = {"enabled", "grace_period", "complete_current"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return DrainConfig(**filtered)


@dataclass
class DrainState:
    """Runtime state for the drain policy."""

    _draining: bool = field(default=False, init=False)

    @property
    def draining(self) -> bool:
        return self._draining

    def signal_drain(self) -> None:
        """Mark the system as draining (e.g. on SIGTERM)."""
        self._draining = True

    def reset(self) -> None:
        self._draining = False


class DrainController:
    """Combines config and state to answer retry-loop questions."""

    def __init__(self, config: DrainConfig) -> None:
        self.config = config
        self._state = DrainState()

    def signal_drain(self) -> None:
        """Record that a drain has been requested."""
        if self.config.enabled:
            self._state.signal_drain()

    @property
    def is_draining(self) -> bool:
        return self.config.enabled and self._state.draining

    def should_start_attempt(self) -> bool:
        """Return False if we are draining and should not begin new attempts."""
        if not self.config.enabled:
            return True
        return not self._state.draining

    @property
    def grace_period(self) -> float:
        return self.config.grace_period

    def reset(self) -> None:
        self._state.reset()
