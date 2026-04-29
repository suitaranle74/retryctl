"""Bridge between FileConfig and JitterConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.jitter import JitterConfig


def jitter_config_from_file(fc: FileConfig) -> JitterConfig:
    """Build a JitterConfig from a FileConfig instance."""
    data: dict = {}

    if fc.jitter_strategy is not None:
        data["strategy"] = fc.jitter_strategy
    if fc.jitter_min_delay is not None:
        data["min_delay"] = fc.jitter_min_delay
    if fc.jitter_max_multiplier is not None:
        data["max_multiplier"] = fc.jitter_max_multiplier

    return JitterConfig.from_dict(data)
