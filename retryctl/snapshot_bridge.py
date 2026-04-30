"""Bridge between FileConfig and SnapshotConfig."""
from __future__ import annotations

from retryctl.config import FileConfig
from retryctl.snapshot import SnapshotConfig


def snapshot_config_from_file(fc: FileConfig) -> SnapshotConfig:
    """Build a SnapshotConfig from a FileConfig instance."""
    return SnapshotConfig(
        enabled=fc.snapshot_enabled,
        compare_stdout=fc.snapshot_compare_stdout,
        compare_exit_code=fc.snapshot_compare_exit_code,
    )
