"""Attempt labeling and tagging support for retryctl."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LabelsConfig:
    """Configuration for attempt labels/tags attached to runs."""
    static: Dict[str, str] = field(default_factory=dict)
    include_attempt_number: bool = True
    include_command_hash: bool = False
    prefix: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "LabelsConfig":
        known = {"static", "include_attempt_number", "include_command_hash", "prefix"}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class AttemptLabels:
    """Resolved labels for a single attempt."""
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.labels.get(key, default)

    def as_env(self) -> Dict[str, str]:
        """Return labels as environment variable dict (uppercased keys)."""
        return {
            f"RETRYCTL_LABEL_{k.upper()}": v
            for k, v in self.labels.items()
        }


class LabelResolver:
    """Resolves labels for each attempt based on config."""

    def __init__(self, config: LabelsConfig, command: str) -> None:
        self._config = config
        self._command = command
        self._command_hash = self._hash_command(command)

    @staticmethod
    def _hash_command(command: str) -> str:
        import hashlib
        return hashlib.sha1(command.encode()).hexdigest()[:8]

    def resolve(self, attempt_number: int) -> AttemptLabels:
        """Build the label set for a given attempt number."""
        cfg = self._config
        labels: Dict[str, str] = {}

        for k, v in cfg.static.items():
            key = f"{cfg.prefix}{k}" if cfg.prefix else k
            labels[key] = v

        if cfg.include_attempt_number:
            key = f"{cfg.prefix}attempt" if cfg.prefix else "attempt"
            labels[key] = str(attempt_number)

        if cfg.include_command_hash:
            key = f"{cfg.prefix}command_hash" if cfg.prefix else "command_hash"
            labels[key] = self._command_hash

        return AttemptLabels(labels=labels)
