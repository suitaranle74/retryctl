"""File-based configuration for retryctl."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class FileConfig:
    # Backoff
    initial_delay: float = 1.0
    multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: bool = False
    max_attempts: int = 3

    # Alerts
    alert_on_failure: bool = False
    alert_on_success: bool = False
    alert_shell_hook: Optional[str] = None

    # Runner
    timeout: Optional[float] = None
    shell: bool = False

    # Conditions
    retry_on_exit_codes: List[int] = field(default_factory=list)
    no_retry_on_exit_codes: List[int] = field(default_factory=list)
    retry_on_output_pattern: Optional[str] = None
    no_retry_on_output_pattern: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "FileConfig":
        known = cls.__dataclass_fields__.keys()  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: str) -> FileConfig:
    """Load a FileConfig from a JSON file."""
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    return FileConfig.from_dict(data)
