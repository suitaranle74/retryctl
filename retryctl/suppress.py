"""Suppress module: configurable error suppression for non-fatal retry failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SuppressConfig:
    """Configuration for suppressing specific exit codes or output patterns."""
    enabled: bool = False
    exit_codes: List[int] = field(default_factory=list)
    output_patterns: List[str] = field(default_factory=list)
    max_suppressed: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "SuppressConfig":
        known = {"enabled", "exit_codes", "output_patterns", "max_suppressed"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class SuppressState:
    suppressed_count: int = 0

    def record(self) -> None:
        self.suppressed_count += 1

    def reset(self) -> None:
        self.suppressed_count = 0


class SuppressEvaluator:
    """Evaluates whether a failed attempt should be suppressed (treated as non-fatal)."""

    def __init__(self, config: SuppressConfig) -> None:
        self._config = config
        self._state = SuppressState()

    @property
    def suppressed_count(self) -> int:
        return self._state.suppressed_count

    def should_suppress(self, exit_code: int, output: str = "") -> bool:
        if not self._config.enabled:
            return False

        if (
            self._config.max_suppressed is not None
            and self._state.suppressed_count >= self._config.max_suppressed
        ):
            return False

        if exit_code in self._config.exit_codes:
            self._state.record()
            return True

        for pattern in self._config.output_patterns:
            if pattern in output:
                self._state.record()
                return True

        return False

    def reset(self) -> None:
        self._state.reset()
