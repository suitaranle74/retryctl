"""Bridge: build DeadLetterConfig from FileConfig."""
from retryctl.config import FileConfig
from retryctl.deadletter import DeadLetterConfig


def deadletter_config_from_file(fc: FileConfig) -> DeadLetterConfig:
    """Extract dead-letter settings from a FileConfig instance."""
    raw: dict = {}
    if fc.deadletter_enabled is not None:
        raw["enabled"] = fc.deadletter_enabled
    if fc.deadletter_path is not None:
        raw["path"] = fc.deadletter_path
    if fc.deadletter_max_entries is not None:
        raw["max_entries"] = fc.deadletter_max_entries
    return DeadLetterConfig.from_dict(raw)
