"""Bridge between FileConfig and ConcurrencyConfig."""
from retryctl.concurrency import ConcurrencyConfig
from retryctl.config import FileConfig


def concurrency_config_from_file(fc: FileConfig) -> ConcurrencyConfig:
    """Build a ConcurrencyConfig from a FileConfig instance."""
    return ConcurrencyConfig(
        enabled=fc.concurrency_enabled,
        max_concurrent=fc.concurrency_max,
        timeout=fc.concurrency_timeout,
    )
