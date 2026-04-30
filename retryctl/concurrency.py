"""Concurrency control for retryctl — limits simultaneous retry attempts."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency limiting."""
    enabled: bool = False
    max_concurrent: int = 1
    timeout: Optional[float] = None  # seconds to wait for a slot; None = wait forever

    @classmethod
    def from_dict(cls, data: dict) -> "ConcurrencyConfig":
        known = {"enabled", "max_concurrent", "timeout"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class ConcurrencyLimiter:
    """Semaphore-backed limiter that gates concurrent retry executions."""

    def __init__(self, config: ConcurrencyConfig) -> None:
        self._config = config
        self._semaphore: Optional[threading.Semaphore] = (
            threading.Semaphore(config.max_concurrent) if config.enabled else None
        )

    # ------------------------------------------------------------------
    # Context-manager interface
    # ------------------------------------------------------------------

    def acquire(self) -> bool:
        """Acquire a concurrency slot.

        Returns True if the slot was acquired (or limiting is disabled).
        Returns False if the timeout elapsed without acquiring a slot.
        """
        if self._semaphore is None:
            return True
        return self._semaphore.acquire(timeout=self._config.timeout)  # type: ignore[arg-type]

    def release(self) -> None:
        """Release a previously acquired concurrency slot."""
        if self._semaphore is not None:
            self._semaphore.release()

    def __enter__(self) -> "ConcurrencyLimiter":
        acquired = self.acquire()
        if not acquired:
            raise TimeoutError(
                f"Could not acquire concurrency slot within "
                f"{self._config.timeout}s (max_concurrent={self._config.max_concurrent})"
            )
        return self

    def __exit__(self, *_exc) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def available(self) -> Optional[int]:
        """Return the number of available slots, or None when disabled."""
        if self._semaphore is None:
            return None
        # Semaphore._value is implementation-specific but widely available.
        return self._semaphore._value  # type: ignore[attr-defined]
