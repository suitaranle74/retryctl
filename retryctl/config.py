"""File-based configuration loader for retryctl."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class FileConfig:
    """Represents the parsed content of a retryctl config file."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: Dict[str, Any] = field(default_factory=dict)
    condition: Dict[str, Any] = field(default_factory=dict)
    timeout: Dict[str, Any] = field(default_factory=dict)
    throttle: Dict[str, Any] = field(default_factory=dict)
    budget: Dict[str, Any] = field(default_factory=dict)
    circuit_breaker: Dict[str, Any] = field(default_factory=dict)
    concurrency: Dict[str, Any] = field(default_factory=dict)
    checkpoint: Dict[str, Any] = field(default_factory=dict)
    warmup: Dict[str, Any] = field(default_factory=dict)
    labels: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)
    policy: Dict[str, Any] = field(default_factory=dict)
    profiles: Dict[str, Any] = field(default_factory=dict)
    sampling: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileConfig":
        known = {
            "max_attempts", "initial_delay", "max_delay", "multiplier",
            "jitter", "condition", "timeout", "throttle", "budget",
            "circuit_breaker", "concurrency", "checkpoint", "warmup",
            "labels", "trace", "audit", "policy", "profiles", "sampling",
        }
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: Optional[str]) -> FileConfig:
    """Load a FileConfig from a JSON file path, or return defaults."""
    if path is None:
        return FileConfig()
    text = Path(path).read_text()
    data = json.loads(text)
    return FileConfig.from_dict(data)
