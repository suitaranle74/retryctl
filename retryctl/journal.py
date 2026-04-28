"""Execution journal: records attempt history for a single retryctl run."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AttemptRecord:
    attempt: int
    exit_code: int
    duration_s: float
    timestamp: float = field(default_factory=time.time)

    def succeeded(self) -> bool:
        return self.exit_code == 0


@dataclass
class Journal:
    command: List[str]
    records: List[AttemptRecord] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    # ------------------------------------------------------------------ #
    def record(self, attempt: int, exit_code: int, duration_s: float) -> AttemptRecord:
        """Append a new attempt record and return it."""
        rec = AttemptRecord(
            attempt=attempt,
            exit_code=exit_code,
            duration_s=duration_s,
        )
        self.records.append(rec)
        return rec

    # ------------------------------------------------------------------ #
    def succeeded(self) -> bool:
        """True if the last recorded attempt was successful."""
        return bool(self.records) and self.records[-1].succeeded()

    def total_attempts(self) -> int:
        return len(self.records)

    def total_duration_s(self) -> float:
        return sum(r.duration_s for r in self.records)

    # ------------------------------------------------------------------ #
    def save(self, path: Path) -> None:
        """Persist the journal to *path* as newline-delimited JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "command": self.command,
            "started_at": self.started_at,
            "succeeded": self.succeeded(),
            "total_attempts": self.total_attempts(),
            "total_duration_s": self.total_duration_s(),
            "attempts": [asdict(r) for r in self.records],
        }
        path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> "Journal":
        """Re-hydrate a Journal from a previously saved JSON file."""
        data = json.loads(Path(path).read_text())
        journal = cls(
            command=data["command"],
            started_at=data["started_at"],
        )
        for rec in data.get("attempts", []):
            journal.records.append(AttemptRecord(**rec))
        return journal
