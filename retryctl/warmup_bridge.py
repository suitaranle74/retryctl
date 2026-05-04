"""Bridge between FileConfig and WarmupConfig."""

from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.warmup import WarmupConfig


def warmup_config_from_file(file_config: FileConfig) -> WarmupConfig:
    """Derive a WarmupConfig from a FileConfig instance."""
    return WarmupConfig(
        enabled=file_config.warmup_enabled,
        delay_seconds=file_config.warmup_delay_seconds,
        message=file_config.warmup_message,
    )
