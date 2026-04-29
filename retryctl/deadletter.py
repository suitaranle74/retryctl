"""Dead-letter queue: persist failed run records for later inspection."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class DeadLetterConfig:
    enabled: bool = False
    path: str = "/tmp/retryctl_deadletter.jsonl"
    max_entries: int = 100

    @classmethod
    def from_dict(cls, data: dict) -> "DeadLetterConfig":
        return cls(
            enabled=data.get("enabled", False),
            path=data.get("path", "/tmp/retryctl_deadletter.jsonl"),
            max_entries=int(data.get("max_entries", 100)),
        )


@dataclass
class DeadLetterEntry:
    command: List[str]
    exit_code: int
    attempts: int
    timestamp: float = field(default_factory=time.time)
    stderr_tail: str = ""
    labels: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, line: str) -> "DeadLetterEntry":
        data = json.loads(line)
        return cls(**data)


class DeadLetterQueue:
    def __init__(self, config: DeadLetterConfig) -> None:
        self._config = config

    def push(self, entry: DeadLetterEntry) -> None:
        """Append a failed-run entry to the dead-letter file."""
        if not self._config.enabled:
            return
        lines = self._read_lines()
        lines.append(entry.to_json())
        # Trim to max_entries (keep newest)
        if len(lines) > self._config.max_entries:
            lines = lines[-self._config.max_entries :]
        with open(self._config.path, "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def entries(self) -> List[DeadLetterEntry]:
        """Return all persisted entries, oldest first."""
        if not self._config.enabled:
            return []
        return [
            DeadLetterEntry.from_json(line)
            for line in self._read_lines()
        ]

    def clear(self) -> None:
        """Remove all persisted entries."""
        if os.path.exists(self._config.path):
            os.remove(self._config.path)

    def _read_lines(self) -> List[str]:
        if not os.path.exists(self._config.path):
            return []
        with open(self._config.path) as fh:
            return [ln.strip() for ln in fh if ln.strip()]
