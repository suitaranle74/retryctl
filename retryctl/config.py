"""YAML/JSON configuration file loader for retryctl."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


@dataclass
class FileConfig:
    """Structured configuration loaded from a config file."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    alert_on_failure: bool = False
    alert_on_success: bool = False
    shell_hook: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileConfig":
        """Create a FileConfig from a plain dictionary."""
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: str) -> FileConfig:
    """Load a FileConfig from a YAML or JSON file.

    Args:
        path: Path to the config file. Extension determines parser used.

    Returns:
        A populated FileConfig instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or content is invalid.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    if ext in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise ValueError("PyYAML is required to load .yaml/.yml config files.")
        data = yaml.safe_load(raw) or {}
    elif ext == ".json":
        data = json.loads(raw)
    else:
        raise ValueError(f"Unsupported config file format: '{ext}'. Use .yaml or .json.")

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a mapping at the top level.")

    return FileConfig.from_dict(data)
