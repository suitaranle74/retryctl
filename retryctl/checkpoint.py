"""Checkpoint support: persist and restore retry state across process restarts."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckpointConfig:
    enabled: bool = False
    path: Optional[str] = None
    ttl_seconds: Optional[float] = None

    @staticmethod
    def from_dict(d: dict) -> "CheckpointConfig":
        return CheckpointConfig(
            enabled=d.get("enabled", False),
            path=d.get("path"),
            ttl_seconds=d.get("ttl_seconds"),
        )


@dataclass
class CheckpointState:
    attempt: int = 0
    created_at: float = field(default_factory=time.time)
    last_exit_code: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt,
            "created_at": self.created_at,
            "last_exit_code": self.last_exit_code,
        }

    @staticmethod
    def from_dict(d: dict) -> "CheckpointState":
        state = CheckpointState(
            attempt=d.get("attempt", 0),
            created_at=d.get("created_at", time.time()),
            last_exit_code=d.get("last_exit_code"),
        )
        return state


class CheckpointManager:
    def __init__(self, config: CheckpointConfig) -> None:
        self._config = config

    def load(self) -> Optional[CheckpointState]:
        if not self._config.enabled or not self._config.path:
            return None
        if not os.path.exists(self._config.path):
            return None
        try:
            with open(self._config.path, "r") as fh:
                data = json.load(fh)
            state = CheckpointState.from_dict(data)
            if self._config.ttl_seconds is not None:
                age = time.time() - state.created_at
                if age > self._config.ttl_seconds:
                    self.clear()
                    return None
            return state
        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def save(self, state: CheckpointState) -> None:
        if not self._config.enabled or not self._config.path:
            return
        with open(self._config.path, "w") as fh:
            json.dump(state.to_dict(), fh)

    def clear(self) -> None:
        if self._config.path and os.path.exists(self._config.path):
            os.remove(self._config.path)
