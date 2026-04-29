"""Metrics collection for retry runs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MetricsConfig:
    enabled: bool = True
    include_durations: bool = True
    include_exit_codes: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "MetricsConfig":
        return cls(
            enabled=data.get("enabled", True),
            include_durations=data.get("include_durations", True),
            include_exit_codes=data.get("include_exit_codes", True),
        )


@dataclass
class AttemptMetric:
    attempt_number: int
    exit_code: int
    duration_seconds: float
    succeeded: bool

    @property
    def failed(self) -> bool:
        return not self.succeeded


@dataclass
class RunMetrics:
    command: str
    started_at: float = field(default_factory=time.time)
    attempts: List[AttemptMetric] = field(default_factory=list)
    finished_at: Optional[float] = None

    def record_attempt(
        self, attempt_number: int, exit_code: int, duration_seconds: float
    ) -> None:
        self.attempts.append(
            AttemptMetric(
                attempt_number=attempt_number,
                exit_code=exit_code,
                duration_seconds=duration_seconds,
                succeeded=(exit_code == 0),
            )
        )

    def finish(self) -> None:
        self.finished_at = time.time()

    @property
    def total_duration(self) -> float:
        if self.finished_at is None:
            return time.time() - self.started_at
        return self.finished_at - self.started_at

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    @property
    def succeeded(self) -> bool:
        return bool(self.attempts) and self.attempts[-1].succeeded

    def summary(self, config: MetricsConfig) -> dict:
        data: dict = {
            "command": self.command,
            "total_attempts": self.total_attempts,
            "succeeded": self.succeeded,
            "total_duration_seconds": round(self.total_duration, 4),
        }
        if config.include_durations:
            data["attempt_durations"] = [
                round(a.duration_seconds, 4) for a in self.attempts
            ]
        if config.include_exit_codes:
            data["attempt_exit_codes"] = [a.exit_code for a in self.attempts]
        return data
