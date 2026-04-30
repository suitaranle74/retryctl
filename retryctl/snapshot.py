"""Snapshot support: capture and compare attempt output for change detection."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SnapshotConfig:
    enabled: bool = False
    compare_stdout: bool = True
    compare_exit_code: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotConfig":
        known = {"enabled", "compare_stdout", "compare_exit_code"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class AttemptSnapshot:
    stdout_hash: Optional[str]
    exit_code: Optional[int]

    def matches(self, other: "AttemptSnapshot", config: SnapshotConfig) -> bool:
        """Return True if both snapshots are considered equal under config rules."""
        if config.compare_stdout:
            if self.stdout_hash != other.stdout_hash:
                return False
        if config.compare_exit_code:
            if self.exit_code != other.exit_code:
                return False
        return True

    def to_dict(self) -> dict:
        return {"stdout_hash": self.stdout_hash, "exit_code": self.exit_code}

    @classmethod
    def from_dict(cls, data: dict) -> "AttemptSnapshot":
        return cls(stdout_hash=data.get("stdout_hash"), exit_code=data.get("exit_code"))


class SnapshotManager:
    def __init__(self, config: SnapshotConfig) -> None:
        self.config = config
        self._last: Optional[AttemptSnapshot] = None

    def capture(self, stdout: str, exit_code: int) -> AttemptSnapshot:
        """Create a snapshot from the given output and exit code."""
        stdout_hash = hashlib.sha256(stdout.encode()).hexdigest() if stdout else None
        snap = AttemptSnapshot(
            stdout_hash=stdout_hash if self.config.compare_stdout else None,
            exit_code=exit_code if self.config.compare_exit_code else None,
        )
        return snap

    def record(self, snapshot: AttemptSnapshot) -> None:
        """Store the latest snapshot for future comparison."""
        self._last = snapshot

    def has_changed(self, snapshot: AttemptSnapshot) -> bool:
        """Return True if the new snapshot differs from the last recorded one."""
        if self._last is None:
            return True
        return not self._last.matches(snapshot, self.config)

    def reset(self) -> None:
        self._last = None
