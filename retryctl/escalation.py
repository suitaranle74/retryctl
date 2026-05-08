"""Escalation policy: trigger alternative actions after repeated failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EscalationConfig:
    """Configuration for escalation behaviour."""
    enabled: bool = False
    threshold: int = 3          # failures before escalating
    cooldown: float = 60.0      # seconds before re-escalating
    hooks: List[str] = field(default_factory=list)  # shell commands to run

    @classmethod
    def from_dict(cls, data: dict) -> "EscalationConfig":
        known = {"enabled", "threshold", "cooldown", "hooks"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class EscalationState:
    failure_count: int = 0
    last_escalated_at: Optional[float] = None

    def record_failure(self) -> None:
        self.failure_count += 1

    def reset(self) -> None:
        self.failure_count = 0
        self.last_escalated_at = None


class EscalationManager:
    """Decides when to escalate and runs escalation hooks."""

    def __init__(self, config: EscalationConfig) -> None:
        self._cfg = config
        self._state = EscalationState()

    def record_failure(self) -> None:
        if self._cfg.enabled:
            self._state.record_failure()

    def should_escalate(self, now: float) -> bool:
        if not self._cfg.enabled:
            return False
        if self._state.failure_count < self._cfg.threshold:
            return False
        if self._state.last_escalated_at is None:
            return True
        return (now - self._state.last_escalated_at) >= self._cfg.cooldown

    def escalate(self, now: float, run_hook) -> None:
        """Run all escalation hooks and update last_escalated_at."""
        self._state.last_escalated_at = now
        for hook in self._cfg.hooks:
            run_hook(hook)

    def reset(self) -> None:
        self._state.reset()
