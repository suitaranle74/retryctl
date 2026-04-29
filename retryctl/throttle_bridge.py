"""Bridge between FileConfig and ThrottleConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.throttle import ThrottleConfig


def throttle_config_from_file(fc: FileConfig) -> ThrottleConfig:
    """Build a ThrottleConfig from a FileConfig instance.

    FileConfig stores throttle settings in an optional ``throttle`` sub-dict.
    If the key is absent the returned config has throttling disabled.
    """
    raw: dict = getattr(fc, "throttle", None) or {}
    return ThrottleConfig.from_dict(raw)
