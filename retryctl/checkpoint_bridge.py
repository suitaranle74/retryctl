"""Bridge between FileConfig and CheckpointConfig."""
from retryctl.checkpoint import CheckpointConfig
from retryctl.config import FileConfig


def checkpoint_config_from_file(fc: FileConfig) -> CheckpointConfig:
    """Build a CheckpointConfig from a FileConfig instance."""
    return CheckpointConfig(
        enabled=fc.checkpoint_enabled,
        path=fc.checkpoint_path,
        ttl_seconds=fc.checkpoint_ttl_seconds,
    )
