"""File-based configuration for retryctl (TOML / JSON / plain dict)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FileConfig:
    # backoff
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True

    # runner
    timeout: Optional[float] = None
    success_codes: List[int] = field(default_factory=lambda: [0])

    # alerts
    on_failure_hook: Optional[str] = None
    on_success_hook: Optional[str] = None

    # journal
    journal_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileConfig":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: Optional[str]) -> FileConfig:
    """Load a FileConfig from *path* (JSON or TOML) or return defaults."""
    if path is None:
        return FileConfig()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = p.suffix.lower()

    if suffix == ".json":
        data: Dict[str, Any] = json.loads(p.read_text())
        return FileConfig.from_dict(data)

    if suffix == ".toml":
        try:
            import tomllib  # type: ignore  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "TOML support requires Python 3.11+ or 'tomli' package."
                ) from exc
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        return FileConfig.from_dict(data)

    raise ValueError(f"Unsupported config format: {suffix!r}. Use .json or .toml.")
