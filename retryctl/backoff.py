"""Exponential backoff strategy with jitter for retryctl."""

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff behavior."""

    initial_delay: float = 1.0       # seconds before first retry
    multiplier: float = 2.0          # factor to multiply delay each attempt
    max_delay: float = 60.0          # ceiling for delay between retries
    jitter: bool = True              # add randomness to avoid thundering herd
    max_attempts: int = 5            # maximum number of retry attempts
    jitter_range: float = 0.5        # fraction of delay to use as jitter window


class ExponentialBackoff:
    """Computes and applies exponential backoff delays between retry attempts."""

    def __init__(self, config: Optional[BackoffConfig] = None) -> None:
        self.config = config or BackoffConfig()
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt

    def reset(self) -> None:
        """Reset attempt counter (e.g. after a successful run)."""
        self._attempt = 0

    def next_delay(self) -> float:
        """Calculate the delay for the current attempt without sleeping."""
        cfg = self.config
        delay = min(cfg.initial_delay * (cfg.multiplier ** self._attempt), cfg.max_delay)
        if cfg.jitter:
            jitter_amount = delay * cfg.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.0, delay)  # ensure non-negative
        return delay

    def wait(self) -> float:
        """Sleep for the appropriate backoff delay and increment the attempt counter.

        Returns the actual delay that was applied.
        """
        delay = self.next_delay()
        self._attempt += 1
        time.sleep(delay)
        return delay

    def should_retry(self) -> bool:
        """Return True if another attempt is permitted under the current config."""
        return self._attempt < self.config.max_attempts
