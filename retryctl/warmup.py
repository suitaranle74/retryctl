"""Warmup delay configuration and management for retryctl.

Allows an initial delay before the first attempt, useful for
services that need time to become ready after a triggering event.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WarmupConfig:
    """Configuration for pre-retry warmup delay."""

    enabled: bool = False
    delay_seconds: float = 0.0
    message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "WarmupConfig":
        """Build a WarmupConfig from a dictionary, ignoring unknown keys."""
        return cls(
            enabled=data.get("enabled", False),
            delay_seconds=float(data.get("delay_seconds", 0.0)),
            message=data.get("message", None),
        )


@dataclass
class WarmupState:
    """Tracks whether the warmup delay has been applied."""

    _applied: bool = field(default=False, init=False)

    @property
    def applied(self) -> bool:
        return self._applied


class WarmupManager:
    """Applies a warmup delay before the first retry attempt."""

    def __init__(self, config: WarmupConfig) -> None:
        self._config = config
        self._state = WarmupState()

    def maybe_warmup(self) -> bool:
        """Apply the warmup delay if enabled and not yet applied.

        Returns True if a delay was applied, False otherwise.
        """
        if not self._config.enabled:
            return False
        if self._state.applied:
            return False
        if self._config.delay_seconds > 0:
            time.sleep(self._config.delay_seconds)
        self._state._applied = True
        return True

    @property
    def message(self) -> Optional[str]:
        return self._config.message

    @property
    def applied(self) -> bool:
        return self._state.applied
