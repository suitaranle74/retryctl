"""Audit log for retry attempts — structured event records for compliance and debugging."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, IO
import sys


@dataclass
class AuditConfig:
    enabled: bool = False
    output_file: Optional[str] = None
    include_output: bool = False
    include_env: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "AuditConfig":
        return cls(
            enabled=data.get("enabled", False),
            output_file=data.get("output_file", None),
            include_output=data.get("include_output", False),
            include_env=data.get("include_env", False),
        )


@dataclass
class AuditEvent:
    event: str
    command: str
    attempt: int
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    elapsed: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    labels: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str) -> "AuditEvent":
        return cls(**json.loads(raw))


class AuditLogger:
    def __init__(self, config: AuditConfig, stream: IO = None):
        self._config = config
        self._stream = stream or sys.stdout
        self._file_handle: Optional[IO] = None
        if config.enabled and config.output_file:
            self._file_handle = open(config.output_file, "a", encoding="utf-8")

    def log(self, event: AuditEvent) -> None:
        if not self._config.enabled:
            return
        if not self._config.include_output:
            event.stdout = None
            event.stderr = None
        line = event.to_json() + "\n"
        target = self._file_handle if self._file_handle else self._stream
        target.write(line)
        target.flush()

    def close(self) -> None:
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def __enter__(self) -> "AuditLogger":
        return self

    def __exit__(self, *_) -> None:
        self.close()
