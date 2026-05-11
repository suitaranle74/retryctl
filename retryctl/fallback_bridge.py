"""Bridge between FileConfig and FallbackConfig."""
from __future__ import annotations

from retryctl.fallback import FallbackConfig


def fallback_config_from_file(file_config) -> FallbackConfig:
    """Build a FallbackConfig from a FileConfig instance."""
    data: dict = {}

    if file_config.fallback_enabled is not None:
        data["enabled"] = file_config.fallback_enabled
    if file_config.fallback_command is not None:
        data["command"] = file_config.fallback_command
    if file_config.fallback_capture_output is not None:
        data["capture_output"] = file_config.fallback_capture_output

    return FallbackConfig.from_dict(data)
