"""File-based configuration for retryctl."""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclasses.dataclass
class FileConfig:
    """Flat representation of all retryctl TOML config options."""

    # backoff
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True

    # alerts
    alert_on_failure: bool = False
    alert_command: Optional[str] = None

    # runner
    stop_on_success: bool = True

    # condition
    retry_exit_codes: List[int] = dataclasses.field(default_factory=list)
    output_patterns: List[str] = dataclasses.field(default_factory=list)

    # timeout  (new)
    attempt_timeout: Optional[float] = None
    total_timeout: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileConfig":
        """Build a FileConfig from a dict, ignoring unrecognised keys."""
        fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)


def load_config(path: str) -> FileConfig:
    """Load a TOML config file and return a FileConfig."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    flat: Dict[str, Any] = {}
    for section in raw.values():
        if isinstance(section, dict):
            flat.update(section)
    flat.update({k: v for k, v in raw.items() if not isinstance(v, dict)})
    return FileConfig.from_dict(flat)
