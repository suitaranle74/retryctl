"""Bridge between FileConfig and TimeoutConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.timeout import TimeoutConfig


def timeout_config_from_file(fc: FileConfig) -> TimeoutConfig:
    """Construct a TimeoutConfig from a FileConfig instance."""
    return TimeoutConfig(
        attempt_timeout=fc.attempt_timeout,
        total_timeout=fc.total_timeout,
    )
