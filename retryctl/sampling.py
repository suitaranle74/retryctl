"""Sampling configuration and evaluator for retryctl.

Allows probabilistic sampling of retry attempts for metrics, tracing,
or audit purposes — avoiding overhead on every attempt.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SamplingConfig:
    """Configuration for attempt sampling."""

    enabled: bool = False
    rate: float = 1.0          # 0.0 to 1.0
    seed: Optional[int] = None  # for deterministic tests

    @classmethod
    def from_dict(cls, data: dict) -> "SamplingConfig":
        return cls(
            enabled=data.get("enabled", False),
            rate=float(data.get("rate", 1.0)),
            seed=data.get("seed", None),
        )

    def validate(self) -> None:
        if not (0.0 <= self.rate <= 1.0):
            raise ValueError(f"sampling rate must be between 0.0 and 1.0, got {self.rate}")


class SamplingEvaluator:
    """Decides whether a given attempt should be sampled."""

    def __init__(self, config: SamplingConfig) -> None:
        self._config = config
        self._rng = random.Random(config.seed)

    def should_sample(self, attempt_number: int = 0) -> bool:
        """Return True if this attempt should be sampled.

        Args:
            attempt_number: Zero-based attempt index (unused by default,
                            available for subclasses or future strategies).
        """
        if not self._config.enabled:
            return False
        if self._config.rate >= 1.0:
            return True
        if self._config.rate <= 0.0:
            return False
        return self._rng.random() < self._config.rate

    def reset(self) -> None:
        """Re-seed the RNG (useful between test runs)."""
        self._rng = random.Random(self._config.seed)
