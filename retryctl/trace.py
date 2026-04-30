"""Distributed tracing support for retry attempts."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TraceConfig:
    enabled: bool = False
    header_name: str = "X-Retry-Trace-Id"
    propagate_env: bool = True
    env_var: str = "RETRYCTL_TRACE_ID"

    @classmethod
    def from_dict(cls, data: Dict) -> "TraceConfig":
        allowed = {"enabled", "header_name", "propagate_env", "env_var"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


@dataclass
class TraceContext:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    attempt: int = 0

    def to_env(self) -> Dict[str, str]:
        env: Dict[str, str] = {
            "RETRYCTL_TRACE_ID": self.trace_id,
            "RETRYCTL_SPAN_ID": self.span_id,
            "RETRYCTL_ATTEMPT": str(self.attempt),
        }
        if self.parent_span_id is not None:
            env["RETRYCTL_PARENT_SPAN_ID"] = self.parent_span_id
        return env

    def child(self, attempt: int) -> "TraceContext":
        """Create a child span for a specific attempt."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            attempt=attempt,
        )


class Tracer:
    def __init__(self, config: TraceConfig) -> None:
        self._config = config
        self._root: Optional[TraceContext] = None

    def start(self) -> TraceContext:
        self._root = TraceContext()
        return self._root

    def span_for_attempt(self, attempt: int) -> Optional[TraceContext]:
        if not self._config.enabled or self._root is None:
            return None
        return self._root.child(attempt)

    def env_for_attempt(self, attempt: int) -> Dict[str, str]:
        if not self._config.enabled:
            return {}
        span = self.span_for_attempt(attempt)
        return span.to_env() if span else {}
