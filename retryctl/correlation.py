"""Correlation ID generation and propagation for retry runs."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CorrelationConfig:
    """Configuration for correlation ID behaviour."""
    enabled: bool = True
    header_name: str = "X-Retry-Correlation-Id"
    env_var: str = "RETRYCTL_CORRELATION_ID"
    # If set, use this fixed ID instead of generating one
    fixed_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CorrelationConfig":
        known = {"enabled", "header_name", "env_var", "fixed_id"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class CorrelationContext:
    """Holds the correlation ID for a single retry run."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None

    def to_env(self, config: CorrelationConfig) -> dict:
        """Return env-var dict to inject into child processes."""
        env: dict = {}
        if not config.enabled:
            return env
        env[config.env_var] = self.correlation_id
        if self.parent_id:
            env[config.env_var + "_PARENT"] = self.parent_id
        return env

    def child(self) -> "CorrelationContext":
        """Create a child context that references this one as the parent."""
        return CorrelationContext(parent_id=self.correlation_id)


class CorrelationManager:
    """Manages creation and retrieval of correlation contexts."""

    def __init__(self, config: CorrelationConfig) -> None:
        self._config = config
        self._context: Optional[CorrelationContext] = None

    def start(self) -> CorrelationContext:
        """Initialise a new correlation context for a run."""
        if not self._config.enabled:
            self._context = CorrelationContext(correlation_id="")
            return self._context
        cid = self._config.fixed_id or str(uuid.uuid4())
        self._context = CorrelationContext(correlation_id=cid)
        return self._context

    @property
    def current(self) -> Optional[CorrelationContext]:
        return self._context

    def env_for_attempt(self) -> dict:
        """Return environment variables to inject for the current context."""
        if self._context is None:
            return {}
        return self._context.to_env(self._config)
