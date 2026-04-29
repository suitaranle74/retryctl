"""Journal records attempt history for a retryctl run."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from retryctl.output import CapturedOutput


@dataclass
class AttemptRecord:
    """A single attempt entry stored in the journal."""
    attempt: int
    exit_code: int
    duration: float
    timestamp: float = field(default_factory=time.time)
    output: Optional[CapturedOutput] = None

    def succeeded(self) -> bool:
        return self.exit_code == 0


@dataclass
class Journal:
    """Accumulates attempt records for a command execution session."""
    command: List[str]
    records: List[AttemptRecord] = field(default_factory=list)
    _start: float = field(default_factory=time.time, repr=False)

    def record(self, attempt: int, exit_code: int, duration: float,
               output: Optional[CapturedOutput] = None) -> AttemptRecord:
        """Append a new attempt record and return it."""
        entry = AttemptRecord(
            attempt=attempt,
            exit_code=exit_code,
            duration=duration,
            output=output,
        )
        self.records.append(entry)
        return entry

    def succeeded(self) -> bool:
        """Return True if the last recorded attempt was successful."""
        return bool(self.records) and self.records[-1].succeeded()

    def total_attempts(self) -> int:
        return len(self.records)

    def elapsed(self) -> float:
        """Wall-clock seconds since the journal was created."""
        return time.time() - self._start

    def summary(self) -> str:
        """Return a short human-readable summary of the session."""
        status = "succeeded" if self.succeeded() else "failed"
        cmd = " ".join(self.command)
        return (
            f"Command '{cmd}' {status} after "
            f"{self.total_attempts()} attempt(s) "
            f"in {self.elapsed():.2f}s"
        )
