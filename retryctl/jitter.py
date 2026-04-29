"""Jitter strategies for randomizing backoff delays."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class JitterStrategy(str, Enum):
    NONE = "none"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


@dataclass
class JitterConfig:
    strategy: JitterStrategy = JitterStrategy.NONE
    min_delay: float = 0.0
    max_multiplier: float = 2.0
    seed: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "JitterConfig":
        known = {"strategy", "min_delay", "max_multiplier", "seed"}
        filtered = {k: v for k, v in data.items() if k in known}
        if "strategy" in filtered:
            filtered["strategy"] = JitterStrategy(filtered["strategy"])
        return cls(**filtered)


class JitterApplicator:
    """Applies a jitter strategy to a computed backoff delay."""

    def __init__(self, config: JitterConfig) -> None:
        self._config = config
        self._rng = random.Random(config.seed)
        self._last_delay: float = config.min_delay

    def apply(self, base_delay: float) -> float:
        cfg = self._config
        strategy = cfg.strategy

        if strategy == JitterStrategy.NONE:
            return base_delay

        if strategy == JitterStrategy.FULL:
            result = self._rng.uniform(cfg.min_delay, base_delay)

        elif strategy == JitterStrategy.EQUAL:
            half = base_delay / 2.0
            result = half + self._rng.uniform(0, half)

        elif strategy == JitterStrategy.DECORRELATED:
            upper = max(cfg.min_delay, self._last_delay * cfg.max_multiplier)
            result = self._rng.uniform(cfg.min_delay, upper)
            self._last_delay = result

        else:
            result = base_delay

        return max(cfg.min_delay, result)

    def reset(self) -> None:
        self._last_delay = self._config.min_delay
        self._rng = random.Random(self._config.seed)
